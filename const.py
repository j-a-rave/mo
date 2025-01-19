EMOTIONS = ["angry", "disgust", "fear", "happy" "neutral", "sad", "surprise"]
VIBE_UP = "up"
VIBE_MID = "mid"
VIBE_DOWN = "down"
EMOTION_VIBE_MAP = {"angry": VIBE_MID,
                    "disgust": VIBE_DOWN,
                    "fear": VIBE_DOWN,
                    "happy": VIBE_UP,
                    "neutral": VIBE_MID,
                    "sad": VIBE_DOWN,
                    "surprise": VIBE_UP}
VIBE_FACTOR_MAP = {VIBE_UP: 1,
                   VIBE_MID: 0,
                   VIBE_DOWN: -1}

CAPTURE_PATH = r"C:\Users\User\.deepface\captures"
CAPTURE_FILE = CAPTURE_PATH + "cap.png"

SLEEP_EMOTIONS = 3  # seconds between checks
SLEEP_CAPTURE = 0.03 # seconds between captures (30 fps ish)

FACE_MOVE_EASING = 0.04  # lerp r
FACE_TURN_EASING = 0.08

FACE_TURN_MAX = 40

FACE_MOVE_SPRING = 0.05
FACE_TURN_SPRING = 0.05
DELTA_SPRING = 0.5

COLOR_FACE_CONTROLS = (0, 0, 255)  # BGR color value of head tracking on screen drawing
COLOR_LERP_CONTROLS = (255, 0, 0)
COLOR_SPRING_CONTROLS = (0, 255, 0)
