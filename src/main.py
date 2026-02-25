"""
Virtual Air-Drawing System - Main entry point.
Runs the main loop: capture frame -> detect gestures -> update canvas -> render overlay -> display.
All processing is local (no cloud APIs).
"""

import time
from datetime import datetime
from pathlib import Path

import cv2

from . import config
from .camera import Camera
from .canvas import Canvas
from .gesture_detector import GestureDetector, Gesture
from .ui import (
    draw_instruction_box,
    draw_toolbar,
    get_instruction_lines,
    get_toolbar_color_by_index,
    toolbar_color_at_position,
)


def main():
    # -------------------------------------------------------------------------
    # Setup: camera, gesture detector, canvas, window
    # -------------------------------------------------------------------------
    camera = Camera(0)
    width = camera.width
    height = camera.height

    detector = GestureDetector()
    canvas = Canvas(width, height)
    window_name = "Air Drawing"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Mode derived from gesture (for UI and drawing logic)
    current_gesture = Gesture.NONE
    prev_gesture = Gesture.NONE
    frame_count = 0
    fps_start = time.perf_counter()
    fps_value = 0.0
    non_draw_streak = 0

    # Save directory (default: project folder)
    save_dir = Path(config.DEFAULT_SAVE_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    try:
        while True:
            loop_start = time.perf_counter()

            # -----------------------------------------------------------------
            # Capture frame
            # -----------------------------------------------------------------
            success, frame = camera.read()
            if not success or frame is None:
                continue

            # -----------------------------------------------------------------
            # Hand detection and gesture
            # -----------------------------------------------------------------
            result = detector.process(frame)
            current_gesture = result["gesture"]
            cursor_xy = result["cursor_xy"]
            cursor_norm = result["cursor_xy_normalized"]

            # -----------------------------------------------------------------
            # Gesture actions: clear, toggle draw, toolbar color selection
            # -----------------------------------------------------------------
            if current_gesture == Gesture.OPEN_PALM:
                canvas.clear()
                canvas.drop_last_point()

            if current_gesture == Gesture.PINCH:
                # Only react once per pinch (debounce: act on transition into pinch).
                # Pinch is now used only for toolbar color selection, not for pausing drawing.
                if prev_gesture != Gesture.PINCH and cursor_xy is not None:
                    color_index = toolbar_color_at_position(cursor_xy[0], cursor_xy[1])
                    if color_index is not None:
                        canvas.brush_color = get_toolbar_color_by_index(color_index)
                canvas.drop_last_point()

            if current_gesture == Gesture.TWO_FINGERS:
                canvas.drop_last_point()

            # -----------------------------------------------------------------
            # Drawing: if index up and drawing enabled, add stroke
            # -----------------------------------------------------------------
            is_draw_gesture = current_gesture == Gesture.INDEX_UP
            if cursor_xy is not None:
                canvas.draw_point(cursor_xy[0], cursor_xy[1], is_draw_gesture)

            # Only break the stroke after a few consecutive non-drawing frames
            # so tiny detection glitches don't disconnect the line.
            if is_draw_gesture:
                non_draw_streak = 0
            else:
                non_draw_streak += 1
                if non_draw_streak >= config.NON_DRAW_DROP_FRAMES:
                    canvas.drop_last_point()

            prev_gesture = current_gesture

            # -----------------------------------------------------------------
            # Render: canvas overlay on frame
            # -----------------------------------------------------------------
            canvas.render_overlay(frame)

            # -----------------------------------------------------------------
            # UI: toolbar (top) and instruction box (corner)
            # -----------------------------------------------------------------
            draw_toolbar(frame, canvas.brush_color, canvas.brush_size)

            gesture_mode_str = "draw" if is_draw_gesture else ("move" if current_gesture == Gesture.TWO_FINGERS else "none")
            instruction_lines = get_instruction_lines(gesture_mode_str, canvas.drawing_enabled)
            draw_instruction_box(frame, instruction_lines, config.INSTRUCTION_BOX_POSITION)

            # -----------------------------------------------------------------
            # Cursor indicator (small circle at finger position)
            # -----------------------------------------------------------------
            if cursor_xy is not None:
                cx, cy = cursor_xy
                # Don't draw cursor over toolbar (optional: clip cy to below toolbar)
                if cy > config.TOOLBAR_HEIGHT + 5:
                    cv2.circle(frame, cursor_xy, 6, (0, 255, 0), 2, lineType=cv2.LINE_AA)

            # -----------------------------------------------------------------
            # FPS (optional, small text top-left below toolbar)
            # -----------------------------------------------------------------
            frame_count += 1
            if frame_count % 15 == 0:
                elapsed = time.perf_counter() - fps_start
                fps_value = frame_count / elapsed if elapsed > 0 else 0
            cv2.putText(frame, f"FPS: {fps_value:.1f}", (10, config.TOOLBAR_HEIGHT + 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

            # -----------------------------------------------------------------
            # Show and handle keys
            # -----------------------------------------------------------------
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                break
            if key == ord("+") or key == ord("="):
                canvas.brush_size = canvas.brush_size + 2
            if key == ord("-"):
                canvas.brush_size = canvas.brush_size - 2
            if key == ord("s") or key == ord("S"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = save_dir / f"drawing_{timestamp}.png"
                if canvas.save_to_file(str(path)):
                    print(f"Saved: {path}")
                else:
                    print("Save failed.")

            # -----------------------------------------------------------------
            # FPS limiting: only sleep when we're ahead of target (perf: don't add delay when already slow)
            # -----------------------------------------------------------------
            elapsed = time.perf_counter() - loop_start
            target_dt = 1.0 / config.TARGET_FPS
            if elapsed < target_dt:
                time.sleep(target_dt - elapsed)

    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
