import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from google.colab.patches import cv2_imshow
import cv2
import numpy as np

model_path = "hand_landmarker.task"
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)              # Palm connections
]

def to_pixel(x_norm: float, y_norm: float, w: int, h: int) -> tuple[int, int]:
    # keep to [0,1] to avoid occasional out-of-range artifacts
    x = min(max(x_norm, 0.0), 1.0)
    y = min(max(y_norm, 0.0), 1.0)
    return int(x * w), int(y * h)

def draw_hand_landmarks_tasks_only(
    image_bgr: np.ndarray,
    hand_landmarks_list,
    connections=HAND_CONNECTIONS,
    draw_points=True,
    draw_connections=True,
    point_radius=3,
    point_thickness=-1,
    line_thickness=2,
):
    annotated = image_bgr.copy()
    h, w = annotated.shape[:2]

    for hand_landmarks in hand_landmarks_list:
        # Convert normalized landmarks to pixel coords
        pts = [to_pixel(lm.x, lm.y, w, h) for lm in hand_landmarks]

        if draw_connections:
            for a, b in connections:
                cv2.line(annotated, pts[a], pts[b], (0, 255, 0), line_thickness)

        if draw_points:
            for (x, y) in pts:
                cv2.circle(annotated, (x, y), point_radius, (0, 0, 255), point_thickness)

    return annotated

def run_hand_landmarker_on_image_tasks_only(image_path: str):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        running_mode=vision.RunningMode.IMAGE
    )

    with vision.HandLandmarker.create_from_options(options) as landmarker:
        cv_image = cv2.imread(image_path)
        if cv_image is None:
            print("Image not found:", image_path)
            return

        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        result = landmarker.detect(mp_image)

    if result.hand_landmarks:
        annotated = draw_hand_landmarks_tasks_only(cv_image, result.hand_landmarks)
        cv2_imshow(annotated)
    else:
        print("No hands detected.")
