from threading import Thread
from time import sleep

from deepface import DeepFace
import cv2 as cv
import face_recognition

import bpy
from bpy.props import *
import mathutils

from mo import const
from mo import util


class PGMoData(bpy.types.PropertyGroup):
    vibe: bpy.props.StringProperty(name="Vibe",
                                   default=const.VIBE_MID)


class PGMoSettings(bpy.types.PropertyGroup):
    show_camera: bpy.props.BoolProperty(name="Show Camera",
                                        default=True)
    track_head: bpy.props.BoolProperty(name="Track Head",
                                       default=True)
    track_emotions: bpy.props.BoolProperty(name="Track Emotions",
                                           default=True)
    absolute_position: bpy.props.BoolProperty(name="Absolute Position",
                                              default=False)
    control_object: bpy.props.PointerProperty(name="Control Object",
                                              type=bpy.types.Object)
    pos_scale: bpy.props.FloatVectorProperty(name="Position Scale",
                                             default=(1.0, 1.0, 1.0))
    rot_scale: bpy.props.FloatVectorProperty(name="Rotation Scale",
                                             default=(1.0, 1.0, 1.0))


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

        # settings
        self.quit = False

    def is_capturing(self):
        return self.frame is not None and len(self.frame) > 0

    def head_tracking_data_exists(self):
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
        if self.head_tracking_data_exists():
            self.ease()
            self.update_scene()
        return True

    def display(self):
        if not bpy.context.scene.mo_settings.show_camera:
            cv.destroyAllWindows()
            return

        def draw_text_lines(frame, lines, color):
            for x in range(len(lines)):
                cv.putText(frame, lines[x], (0, 36 * (x + 1)), cv.FONT_HERSHEY_SIMPLEX, 1, color)

        draw_text_lines(self.frame,
                        [f"{key}: {value}" for key, value in self.get_data().items()],
                        const.COLOR_SPRING_CONTROLS)
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
            roll = ((side_b[1] / self.frame_height) - (side_a[1] / self.frame_height)) / size

            pos_scale = bpy.context.scene.mo_settings.pos_scale
            rot_scale = bpy.context.scene.mo_settings.rot_scale

            # -Y forward.
            self.trans_track = MoTransform(pos=[util.capture_pos(face_center_pos[0], self.frame_width) * pos_scale[0],
                                           -1.0 * util.capture_distance_pos(side_a, side_b, self.frame_height) * pos_scale[1],
                                           -1.0 * util.capture_pos(face_center_pos[1], self.frame_height) * pos_scale[2]],
                                           rot=[face_turn[1] / const.FACE_TURN_MAX * rot_scale[0],
                                                roll * rot_scale[1],
                                                face_turn[0] / const.FACE_TURN_MAX * rot_scale[2]])

            if not self.head_tracking_data_exists():
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
            if bpy.context.scene.mo_settings.track_head:
                self.read_head()
            else:
                sleep(const.SLEEP_CAPTURE)

    def update_emotions(self):
        while not self.quit:
            if bpy.context.scene.mo_settings.track_emotions:
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

    def update_scene(self):
        ctrl_obj = bpy.context.scene.mo_settings.control_object
        if ctrl_obj is None:
            return
        pos = mathutils.Vector(self.trans_spring.pos if bpy.context.scene.mo_settings.absolute_position
                               else util.vector_a_b(self.trans_zero.pos, self.trans_spring.pos))
        ctrl_obj.delta_location = pos
        ctrl_obj.delta_rotation_euler = self.trans_spring.rot
        ctrl_obj.mo_data.vibe = const.EMOTION_VIBE_MAP[self.emotion]

    def start(self):
        self.quit = False
        self.thread_main = Thread(target=self.update_main)
        self.thread_main.start()

    def stop(self):
        self.quit = True
        self.thread_main.join()

    def get_data(self):
        if not self.head_tracking_data_exists():
            return {}
        pos_diff = util.vector_a_b(self.trans_zero.pos, self.trans_spring.pos)
        return {"pos": f"{self.trans_spring.pos[0]:.2f}, {self.trans_spring.pos[1]:.2f}, {self.trans_spring.pos[2]:.2f}",
                "zero": f"{self.trans_zero.pos[0]:.2f}, {self.trans_zero.pos[1]:.2f}, {self.trans_zero.pos[2]:.2f}",
                "delta": f"{pos_diff[0]:.2f}, {pos_diff[1]:.2f}, {pos_diff[2]:.2f}",
                "rot": f"{self.trans_spring.rot[0]:.2f}, {self.trans_spring.rot[1]:.2f}, {self.trans_spring.rot[2]:.2f}",
                "vibe": const.EMOTION_VIBE_MAP[self.emotion], }
