"""
Configuration and constants for the virtual air-drawing system.
Central place for camera, display, gesture, and canvas settings.
"""

# -----------------------------------------------------------------------------
# Camera & display
# -----------------------------------------------------------------------------
# Target FPS for main loop (higher = lower latency, more CPU)
TARGET_FPS = 30

# Camera resolution (width, height). Lower = better performance and lower latency.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Resolution used for hand detection only (smaller = faster MediaPipe, same UX).
# Display stays at CAMERA_WIDTH x CAMERA_HEIGHT; landmarks are scaled back to display.
DETECTION_WIDTH = 320
DETECTION_HEIGHT = 240

# Mirror the camera so drawing feels natural (like a mirror)
MIRROR_CAMERA = True

# -----------------------------------------------------------------------------
# MediaPipe / hand detection
# -----------------------------------------------------------------------------
# Maximum number of hands to detect (1 is enough for drawing; keeps pipeline fastest)
MAX_NUM_HANDS = 1

# Model complexity: 0 = lite, 1 = full. Lite is faster.
MODEL_COMPLEXITY = 0

# Minimum detection confidence (0.0–1.0)
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# -----------------------------------------------------------------------------
# Gesture thresholds (tune if gestures are misdetected)
# -----------------------------------------------------------------------------
# Finger considered "up" if tip is above this landmark (lower index = more up)
# MediaPipe hand landmarks: 4=index_tip, 8=index_pip, 12=middle_tip, etc.
FINGER_UP_THRESHOLD_Y = 0.02  # tip must be this much above pip (in normalized coords)

# Pinch: distance between thumb tip (4) and index tip (8) in normalized coords
PINCH_DISTANCE_THRESHOLD = 0.06

# Open palm: multiple fingers extended; we use simple heuristic (e.g. 3+ fingers up)
PALM_MIN_FINGERS_UP = 4

# -----------------------------------------------------------------------------
# Smoothing & noise filtering
# -----------------------------------------------------------------------------
# Number of previous positions to average for cursor smoothing (reduces jitter, but too high adds lag)
SMOOTHING_BUFFER_SIZE = 2

# Interpolation: number of points to insert between last and current position for smooth lines.
# Slightly higher value keeps strokes connected even when moving the finger faster.
INTERPOLATION_STEPS = 4

# How many consecutive non-drawing frames before we break the current stroke.
# This prevents tiny detection glitches from disconnecting the line mid-stroke.
NON_DRAW_DROP_FRAMES = 3

# -----------------------------------------------------------------------------
# Canvas & brush
# -----------------------------------------------------------------------------
# Default brush size (radius in pixels)
DEFAULT_BRUSH_SIZE = 8
MIN_BRUSH_SIZE = 2
MAX_BRUSH_SIZE = 30

# Default brush color (BGR for OpenCV)
DEFAULT_BRUSH_COLOR_BGR = (0, 0, 255)  # Red

# Canvas background color (BGR)
CANVAS_BG_BGR = (255, 255, 255)

# Preset colors for toolbar (BGR order for OpenCV)
TOOLBAR_COLORS_BGR = [
    (0, 0, 0),       # Black
    (0, 0, 255),     # Red
    (0, 128, 255),   # Orange
    (0, 255, 255),   # Yellow
    (0, 255, 0),     # Green
    (255, 0, 0),     # Blue
    (128, 0, 128),   # Purple
    (255, 192, 203), # Pink
    (255, 255, 255), # White
]

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
# Instruction box position: 'top_left', 'top_right', 'bottom_left', 'bottom_right'
INSTRUCTION_BOX_POSITION = "bottom_left"

# Instruction box dimensions and style
INSTRUCTION_BOX_WIDTH = 280
INSTRUCTION_BOX_PADDING = 12
INSTRUCTION_BG_ALPHA = 0.75  # Semi-transparent background
INSTRUCTION_FONT_SCALE = 0.5
INSTRUCTION_LINE_HEIGHT = 20

# Toolbar
TOOLBAR_HEIGHT = 56
TOOLBAR_COLOR_BUTTON_SIZE = 36
TOOLBAR_PADDING = 8
TOOLBAR_BG_ALPHA = 0.85

# Hit-test margin for toolbar color buttons (pixels from top)
TOOLBAR_HIT_MARGIN_TOP = 8
TOOLBAR_HIT_MARGIN_BOTTOM = 8

# Default path for saving (drawings saved here when you press S)
# Use "." for current working directory, or an absolute path.
DEFAULT_SAVE_DIR = "."
