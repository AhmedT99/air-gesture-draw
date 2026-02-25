"""
Webcam capture module for macOS.
Uses OpenCV's VideoCapture to access the built-in camera.
Optimized for low latency: minimal buffer, requested FPS where supported.
"""

import cv2
from . import config


class Camera:
    """
    Wraps OpenCV VideoCapture for consistent frame size and optional mirroring.
    """

    def __init__(self, camera_index=0):
        """
        Initialize camera.
        :param camera_index: Usually 0 for built-in webcam on Mac.
        """
        self._cap = cv2.VideoCapture(camera_index)
        self._camera_index = camera_index
        if not self._cap.isOpened():
            raise RuntimeError("Could not open camera. Check permissions and that no other app is using it.")

        # Set resolution (may be capped by driver)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

        # Minimal buffer for lowest latency (perf: avoid stale frames)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Request target FPS on macOS (AVFoundation may honor this)
        self._cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)

    @property
    def width(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self):
        """
        Read one frame from the camera.
        :return: (success: bool, frame: numpy array BGR or None)
        """
        success, frame = self._cap.read()
        if not success or frame is None:
            return False, None
        if config.MIRROR_CAMERA:
            frame = cv2.flip(frame, 1)
        return True, frame

    def release(self):
        """Release camera resource."""
        self._cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
