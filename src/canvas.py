"""
Virtual drawing canvas overlay.
Handles brush strokes with interpolation for smooth lines, brush settings, and export.
"""

import cv2
import numpy as np
from . import config


class Canvas:
    """
    Full-frame canvas matching camera resolution. Drawings are stored as a single
    layer; new strokes are blended onto the canvas. Supports interpolation between
    points for smooth drawing and configurable brush size/color.
    """

    def __init__(self, width, height):
        """
        :param width: Canvas width in pixels (matches frame width)
        :param height: Canvas height in pixels (matches frame height)
        """
        self._width = width
        self._height = height
        # Persistent drawing layer (BGR, same size as frame)
        self._layer = np.zeros((height, width, 3), dtype=np.uint8)
        self._layer[:] = config.CANVAS_BG_BGR

        self._brush_size = config.DEFAULT_BRUSH_SIZE
        self._brush_color = list(config.DEFAULT_BRUSH_COLOR_BGR)
        self._drawing_enabled = True  # Drawing is always enabled in this version
        self._last_point = None  # (x, y) for interpolation

    @property
    def brush_size(self):
        return self._brush_size

    @brush_size.setter
    def brush_size(self, value):
        self._brush_size = max(config.MIN_BRUSH_SIZE, min(config.MAX_BRUSH_SIZE, int(value)))

    @property
    def brush_color(self):
        return tuple(self._brush_color)

    @brush_color.setter
    def brush_color(self, bgr_tuple):
        self._brush_color = list(bgr_tuple)

    @property
    def drawing_enabled(self):
        # Exposed for UI text; currently always True (pinch pause/resume removed).
        return self._drawing_enabled

    def clear(self):
        """Clear the canvas to background color and reset last point."""
        self._layer[:] = config.CANVAS_BG_BGR
        self._last_point = None

    def _interpolate_points(self, start, end, steps):
        """
        Generate points between start and end for smooth line.
        :param start: (x, y)
        :param end: (x, y)
        :param steps: number of intermediate points (>= 1)
        :return: list of (x, y) including start and end
        """
        if steps <= 0:
            return [start, end]
        points = []
        for i in range(steps + 1):
            t = i / (steps + 1) if steps > 0 else 0
            x = int(start[0] + t * (end[0] - start[0]))
            y = int(start[1] + t * (end[1] - start[1]))
            points.append((x, y))
        points.append(end)
        return points

    def draw_point(self, x, y, is_drawing):
        """
        Add stroke segment from last position to (x, y) if drawing is enabled.
        Uses interpolation for smooth lines. Updates last point in all cases.
        :param x: pixel x
        :param y: pixel y
        :param is_drawing: if True and drawing_enabled, draw; else just move cursor
        """
        pt = (int(x), int(y))
        if self._last_point is not None and is_drawing and self._drawing_enabled:
            # Smooth line: interpolate between last and current
            steps = config.INTERPOLATION_STEPS
            for p in self._interpolate_points(self._last_point, pt, steps):
                cv2.circle(
                    self._layer,
                    p,
                    self._brush_size,
                    self._brush_color,
                    -1,
                    lineType=cv2.LINE_AA,
                )
        self._last_point = pt

    def drop_last_point(self):
        """Call when finger is lifted so next stroke doesn’t connect to previous."""
        self._last_point = None

    def render_overlay(self, frame_bgr, alpha=0.0):
        """
        Blend canvas layer onto frame. Where canvas is not background, blend it.
        :param frame_bgr: camera frame (modified in place if alpha > 0)
        :param alpha: 0 = only draw where we have strokes; 1 = full canvas opacity.
          We use a fixed blend: canvas strokes drawn with partial transparency over frame.
        """
        # Only blend non-background pixels. Create mask where canvas differs from BG.
        bg = np.array(config.CANVAS_BG_BGR, dtype=np.uint8)
        diff = np.any(self._layer != bg, axis=2)
        mask = diff.astype(np.uint8)
        if mask.sum() == 0:
            return
        mask_3 = cv2.merge([mask, mask, mask])
        # Blend: frame = frame * (1 - mask) + layer * mask (with stroke alpha)
        stroke_alpha = 0.85  # How visible the stroke is on top of camera
        overlay = frame_bgr.copy()
        overlay = (overlay.astype(np.float32) * (1 - stroke_alpha * mask_3) +
                   self._layer.astype(np.float32) * (stroke_alpha * mask_3))
        frame_bgr[:] = np.clip(overlay, 0, 255).astype(np.uint8)

    def get_drawing_only(self):
        """Return the canvas layer as BGR image (e.g. for saving)."""
        return self._layer.copy()

    def save_to_file(self, path):
        """
        Save the current drawing (canvas only) to an image file.
        :param path: file path (e.g. .png)
        :return: True if successful
        """
        try:
            img = self.get_drawing_only()
            return cv2.imwrite(path, img)
        except Exception:
            return False
