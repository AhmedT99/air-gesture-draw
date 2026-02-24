"""
Overlay UI: instruction box and top toolbar for color selection.
Minimal styling so the drawing area stays unobstructed.
"""

import cv2
import numpy as np
from . import config


def draw_instruction_box(frame_bgr, lines, position="bottom_left"):
    """
    Draw a semi-transparent box with instruction text in one corner.
    :param frame_bgr: BGR frame (modified in place)
    :param lines: list of strings to display
    :param position: one of 'top_left', 'top_right', 'bottom_left', 'bottom_right'
    """
    if not lines:
        return
    h, w = frame_bgr.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = config.INSTRUCTION_FONT_SCALE
    thickness = 1
    line_height = config.INSTRUCTION_LINE_HEIGHT
    padding = config.INSTRUCTION_BOX_PADDING

    # Measure text to compute box size
    max_width = 0
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, scale, thickness)
        max_width = max(max_width, tw)
    box_w = max_width + 2 * padding
    box_h = len(lines) * line_height + 2 * padding

    # Position box
    margin = 10
    if position == "top_left":
        x1, y1 = margin, margin
    elif position == "top_right":
        x1, y1 = w - margin - box_w, margin
    elif position == "bottom_right":
        x1, y1 = w - margin - box_w, h - margin - box_h
    else:
        x1, y1 = margin, h - margin - box_h
    x2, y2 = x1 + box_w, y1 + box_h

    # Semi-transparent background
    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (40, 40, 40), -1)
    cv2.addWeighted(overlay, config.INSTRUCTION_BG_ALPHA, frame_bgr, 1 - config.INSTRUCTION_BG_ALPHA, 0, frame_bgr)
    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (200, 200, 200), 1)

    # Text (white)
    for i, line in enumerate(lines):
        y = y1 + padding + (i + 1) * line_height - 4
        cv2.putText(frame_bgr, line, (x1 + padding, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)


def get_instruction_lines(gesture_mode, drawing_enabled):
    """
    Build dynamic instruction lines based on current mode.
    :param gesture_mode: current gesture or mode string (e.g. 'draw', 'move', etc.)
    :param drawing_enabled: whether brush is active (after pinch toggle)
    """
    lines = [
        "Index finger up: Draw",
        "Two fingers up: Move cursor",
        "Open palm: Clear canvas",
        "Toolbar: Pinch on color to select",
        "",
    ]
    if gesture_mode == "draw":
        status = "Drawing Mode Active"
    elif gesture_mode == "move":
        status = "Move Mode (cursor only)"
    else:
        status = "Show a gesture to start"
    lines.append(status)
    lines.append("+/-: Brush size | S: Save | Q: Quit")
    return lines


def draw_toolbar(frame_bgr, current_color_bgr, brush_size):
    """
    Draw top toolbar with color swatches and optional brush size indicator.
    :param frame_bgr: BGR frame (modified in place)
    :param current_color_bgr: (b, g, r) for current brush
    :param brush_size: current brush size (for display)
    """
    h, w = frame_bgr.shape[:2]
    th = config.TOOLBAR_HEIGHT
    btn_size = config.TOOLBAR_COLOR_BUTTON_SIZE
    padding = config.TOOLBAR_PADDING
    colors = config.TOOLBAR_COLORS_BGR

    # Toolbar background (semi-transparent)
    overlay = frame_bgr.copy()
    cv2.rectangle(overlay, (0, 0), (w, th), (50, 50, 50), -1)
    cv2.addWeighted(overlay, config.TOOLBAR_BG_ALPHA, frame_bgr, 1 - config.TOOLBAR_BG_ALPHA, 0, frame_bgr)
    cv2.line(frame_bgr, (0, th), (w, th), (180, 180, 180), 1)

    # Color buttons in a row
    start_x = padding
    for i, bgr in enumerate(colors):
        bx = start_x + i * (btn_size + 4)
        by = (th - btn_size) // 2
        cv2.rectangle(frame_bgr, (bx, by), (bx + btn_size, by + btn_size), (255, 255, 255), 1)
        cv2.rectangle(frame_bgr, (bx + 2, by + 2), (bx + btn_size - 2, by + btn_size - 2), bgr, -1)
        if bgr == current_color_bgr:
            cv2.rectangle(frame_bgr, (bx - 1, by - 1), (bx + btn_size + 1, by + btn_size + 1), (0, 255, 0), 2)

    # Label or brush size on the right
    label = f"Brush: {brush_size}px"
    cv2.putText(frame_bgr, label, (w - 150, th // 2 + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)


def toolbar_color_at_position(px, py):
    """
    Return the BGR color index (0..len(TOOLBAR_COLORS_BGR)-1) if (px, py) is over a color button, else None.
    Used for gesture-based color selection: when cursor is over a color and user pinches, we set that color.
    """
    th = config.TOOLBAR_HEIGHT
    if py < 0 or py > th:
        return None
    btn_size = config.TOOLBAR_COLOR_BUTTON_SIZE
    padding = config.TOOLBAR_PADDING
    n = len(config.TOOLBAR_COLORS_BGR)
    start_x = padding
    for i in range(n):
        bx = start_x + i * (btn_size + 4)
        by = (th - btn_size) // 2
        if bx <= px <= bx + btn_size and by <= py <= by + btn_size:
            return i
    return None


def get_toolbar_color_by_index(index):
    """Return BGR color for toolbar index, or default if out of range."""
    colors = config.TOOLBAR_COLORS_BGR
    if 0 <= index < len(colors):
        return colors[index]
    return config.DEFAULT_BRUSH_COLOR_BGR
