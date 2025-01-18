from threading import Thread
from time import sleep
import os

from deepface import DeepFace
import cv2 as cv
import face_recognition

from mo import const
from mo import util

tracking_emotions = True
tracking_head = True
display_window = True


class MoTransform:
    def __init__(self, pos=None, rot=None):
        if rot is None:
            rot = [0, 0, 0]
        if pos is None:
            pos = [0, 0, 0]
        self.pos = pos
        self.rot = rot

    def lerp(self, target, r_pos, r_rot):
        try:
            self.pos = util.lerp_array(self.pos, target.pos, r_pos)
            self.rot = util.lerp_array(self.rot, target.rot, r_rot)
        except AttributeError:
            print("tried to lerp to this: " + str(target))

    def spring(self, target, delta, r_target_pos, r_target_rot, r_delta_pos, r_delta_rot):
        # also writes to delta.
        self.lerp(target, r_target_pos, r_target_rot)
        delta_target = MoTransform(pos=util.vector_a_b(self.pos, target.pos, const.DELTA_SPRING),
                                   rot=util.vector_a_b(self.rot, target.rot, const.DELTA_SPRING))
        delta.lerp(delta_target, r_delta_pos, r_delta_rot)
        self.pos = util.translate_pos(self.pos, delta.pos)


class MoCaptureManager:
    def __init__(self):
        # threads
        self.thread_main = None
        self.thread_camera = None
        self.thread_emotions = None
        self.thread_head = None

        # capturing
        self.cap = None
        self.frame = None
        self.frame_height = None
        self.frame_width = None

        # tracking
        self.trans_zero = None
        self.trans_track = None
        self.trans_lerp = None
        self.trans_spring_delta = None
        self.trans_spring = None
        self.emotion = "neutral"

        self.quit = False

    def is_capturing(self):
        return self.frame is not None and len(self.frame) > 0

    def is_tracking_head(self):
        return self.trans_zero is not None

    def calibrate(self):
        # zero to currently tracked transform, initialize all transforms
        pos = self.trans_track.pos
        rot = self.trans_track.rot
        self.trans_zero = MoTransform(pos=pos, rot=rot)
        self.trans_lerp = MoTransform(pos=pos, rot=rot)
        self.trans_spring_delta = MoTransform()
        self.trans_spring = MoTransform(pos=pos, rot=rot)

    def ease(self):
        self.trans_lerp.lerp(self.trans_track,
                             const.FACE_MOVE_EASING,
                             const.FACE_TURN_EASING)
        self.trans_spring.spring(self.trans_lerp,
                                 self.trans_spring_delta,
                                 const.FACE_MOVE_EASING,
                                 const.FACE_TURN_EASING,
                                 const.FACE_MOVE_SPRING,
                                 const.FACE_TURN_SPRING)

    def capture(self):
        if not self.cap:
            self.cap = cv.VideoCapture(0)
            if not self.cap.isOpened():
                print("No camera open, sorry")
                return False
            self.frame_height = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
            self.frame_width = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)

        ret, self.frame = self.cap.read()
        if not ret:
            print("No ret, can't receive stream.")
            return False

        # process frame for facial recognition
        lab = cv.cvtColor(self.frame, cv.COLOR_BGR2LAB)
        l_channel, a, b = cv.split(lab)
        clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        l_img = cv.merge((cl, a, b))
        self.frame = cv.cvtColor(l_img, cv.COLOR_LAB2BGR)
        if self.is_tracking_head():
            self.ease()
        return True

    def display(self):
        if not display_window:
            return
        cv.imshow("MO", self.frame)

    def read_head(self):
        if not self.is_capturing():
            return
        frame_rgb = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
        face = face_recognition.face_landmarks(frame_rgb)
        if face:
            face = face[0]

            side_a = face['chin'][0]
            side_b = face['chin'][-1]
            face_center_pos = util.midpoint_pos(side_a, side_b)
            nose_bridge_pos = face['nose_bridge'][0]
            face_turn = util.vector_a_b(face_center_pos, nose_bridge_pos)
            size = util.capture_size(side_a, side_b, self.frame_width)
            roll = ((side_a[1] / self.frame_height) - (side_b[1] / self.frame_height)) / size

            self.trans_track = MoTransform(pos=[util.capture_pos(face_center_pos[0], self.frame_width),
                                           util.capture_pos(face_center_pos[1], self.frame_height),
                                           util.capture_distance_pos(side_a, side_b, self.frame_height)],
                                           rot=[roll,
                                           face_turn[1] / const.FACE_TURN_MAX,
                                           face_turn[0] / const.FACE_TURN_MAX])

            if not self.is_tracking_head():
                # this is the first head track call
                self.calibrate()

    def read_emotions(self):
        if not self.is_capturing():
            return
        try:
            cv.imwrite(const.CAPTURE_FILE, self.frame)
            emotions = DeepFace.analyze(const.CAPTURE_FILE, actions=['emotion'])
            self.emotion = emotions[0]['dominant_emotion']
        except ValueError:
            return

    def update_camera(self):
        while not self.quit:
            self.capture()
            self.display()
            cv.waitKey(1)

    def update_head(self):
        while not self.quit:
            if tracking_head:
                self.read_head()

    def update_emotions(self):
        while not self.quit:
            if tracking_emotions:
                self.read_emotions()
                sleep(const.SLEEP_EMOTIONS)

    def update_main(self):
        self.thread_camera = Thread(target=self.update_camera)
        self.thread_head = Thread(target=self.update_head)
        self.thread_emotions = Thread(target=self.update_emotions)

        self.thread_camera.start()
        self.thread_head.start()
        self.thread_emotions.start()

        self.thread_camera.join()
        self.thread_head.join()
        self.thread_emotions.join()

        self.cap.release()
        cv.destroyAllWindows()

    def start(self):
        self.quit = False
        self.thread_main = Thread(target=self.update_main)
        self.thread_main.start()

    def stop(self):
        self.quit = True
        self.thread_main.join()

    def get_data(self):
        if not self.is_tracking_head():
            return {"message": "Initializing", }
        pos_diff = util.vector_a_b(self.trans_zero.pos, self.trans_spring.pos)
        return {"pos": f"{pos_diff[0]:.2f}, {pos_diff[1]:.2f}, {pos_diff[2]:.2f}",
                "rot": f"{self.trans_spring.rot[0]:.2f}, {self.trans_spring.rot[1]:.2f}, {self.trans_spring.rot[2]:.2f}",
                "vibe": const.EMOTION_VIBE_MAP[self.emotion], }
