"""
Hand landmark detection and gesture interpretation using MediaPipe Tasks API.
Runs entirely locally; no cloud APIs (model is loaded from a local .task file).
"""

import math
from collections import deque

import cv2
import numpy as np
import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

from . import config
from .model_utils import get_model_path


# MediaPipe Hand Landmark indices (Tasks API: 21 landmarks per hand, same 0-20)
# https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
class LandmarkIndex:
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


class Gesture:
    """Gesture types used by the drawing app."""
    NONE = "none"
    INDEX_UP = "index_up"       # Draw mode
    TWO_FINGERS = "two_fingers" # Move cursor only
    PINCH = "pinch"             # Color selection on toolbar
    OPEN_PALM = "open_palm"     # Clear canvas


def _normalized_to_pixel(norm_x, norm_y, width, height):
    """Convert MediaPipe normalized (0–1) coords to pixel coords (clamped)."""
    x = int(np.clip(norm_x, 0, 1) * width)
    y = int(np.clip(norm_y, 0, 1) * height)
    return x, y


def _distance(a, b):
    """Euclidean distance between two points (each (x, y) in normalized coords)."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class GestureDetector:
    """
    Detects hand landmarks and classifies gestures for drawing control.
    Uses MediaPipe Tasks HandLandmarker and a small smoothing buffer for cursor position.
    """

    def __init__(self):
        model_path = get_model_path()
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=config.MAX_NUM_HANDS,
            min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        # Smoothing buffer for index fingertip (normalized x, y)
        self._cursor_buffer = deque(maxlen=config.SMOOTHING_BUFFER_SIZE)
        self._frame_width = 640
        self._frame_height = 480
        self._timestamp_ms = 0

    def set_frame_size(self, width, height):
        """Update frame size for converting normalized coords to pixels."""
        self._frame_width = width
        self._frame_height = height

    def _get_landmark_xy(self, landmarks_list, index):
        """Get (x, y) in normalized [0,1] for a landmark. landmarks_list is list of NormalizedLandmark."""
        lm = landmarks_list[index]
        return lm.x, lm.y

    def _is_finger_up(self, landmarks_list, tip_idx, pip_idx):
        """
        Finger is "up" if tip is above pip (lower y in image coords).
        MediaPipe y increases downward.
        """
        tip = self._get_landmark_xy(landmarks_list, tip_idx)
        pip = self._get_landmark_xy(landmarks_list, pip_idx)
        return tip[1] < pip[1] - config.FINGER_UP_THRESHOLD_Y

    def _count_fingers_up(self, landmarks_list):
        """Count how many fingers (index, middle, ring, pinky) are extended. Thumb not included."""
        count = 0
        if self._is_finger_up(landmarks_list, LandmarkIndex.INDEX_TIP, LandmarkIndex.INDEX_PIP):
            count += 1
        if self._is_finger_up(landmarks_list, LandmarkIndex.MIDDLE_TIP, LandmarkIndex.MIDDLE_PIP):
            count += 1
        if self._is_finger_up(landmarks_list, LandmarkIndex.RING_TIP, LandmarkIndex.RING_PIP):
            count += 1
        if self._is_finger_up(landmarks_list, LandmarkIndex.PINKY_TIP, LandmarkIndex.PINKY_PIP):
            count += 1
        return count

    def _detect_gesture(self, landmarks_list):
        """
        Classify current hand pose into one of our gestures.
        Priority: open palm > pinch > two fingers > index up > none.
        """
        index_up = self._is_finger_up(landmarks_list, LandmarkIndex.INDEX_TIP, LandmarkIndex.INDEX_PIP)
        middle_up = self._is_finger_up(landmarks_list, LandmarkIndex.MIDDLE_TIP, LandmarkIndex.MIDDLE_PIP)
        fingers_up = self._count_fingers_up(landmarks_list)

        if fingers_up >= config.PALM_MIN_FINGERS_UP:
            return Gesture.OPEN_PALM

        thumb_tip = self._get_landmark_xy(landmarks_list, LandmarkIndex.THUMB_TIP)
        index_tip = self._get_landmark_xy(landmarks_list, LandmarkIndex.INDEX_TIP)
        if _distance(thumb_tip, index_tip) < config.PINCH_DISTANCE_THRESHOLD:
            return Gesture.PINCH

        if index_up and middle_up and fingers_up == 2:
            return Gesture.TWO_FINGERS

        if index_up and not middle_up and fingers_up == 1:
            return Gesture.INDEX_UP

        return Gesture.NONE

    def process(self, frame_bgr):
        """
        Run hand detection on the frame and return gesture + smoothed cursor.
        :param frame_bgr: BGR image (numpy array)
        :return: dict with gesture, cursor_xy, cursor_xy_normalized, landmarks
        """
        self.set_frame_size(frame_bgr.shape[1], frame_bgr.shape[0])
        h, w = frame_bgr.shape[0], frame_bgr.shape[1]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb_contiguous = np.ascontiguousarray(rgb)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_contiguous)

        # Use VIDEO mode API with monotonically increasing timestamp
        self._timestamp_ms += 33  # ~30 FPS; value only needs to be increasing
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)

        out = {
            "gesture": Gesture.NONE,
            "cursor_xy": None,
            "cursor_xy_normalized": None,
            "landmarks": None,
        }

        if not result.hand_landmarks:
            self._cursor_buffer.clear()
            return out

        # Use first hand only
        hand_landmarks = result.hand_landmarks[0]
        gesture = self._detect_gesture(hand_landmarks)
        out["gesture"] = gesture

        # Cursor = index fingertip (smoothed)
        index_tip = self._get_landmark_xy(hand_landmarks, LandmarkIndex.INDEX_TIP)
        self._cursor_buffer.append(index_tip)
        avg_x = np.mean([p[0] for p in self._cursor_buffer])
        avg_y = np.mean([p[1] for p in self._cursor_buffer])
        out["cursor_xy_normalized"] = (avg_x, avg_y)
        out["cursor_xy"] = _normalized_to_pixel(avg_x, avg_y, w, h)

        out["landmarks"] = [
            _normalized_to_pixel(lm.x, lm.y, w, h)
            for lm in hand_landmarks
        ]

        return out

    def close(self):
        """Release MediaPipe resources."""
        self._landmarker.close()
