# Performance Optimizations – Virtual Air-Drawing System

This document lists the performance improvements applied to the codebase. **Core functionality and UI behavior are unchanged**; only latency, FPS, and efficiency were optimized.

---

## 1. Performance Optimization

| Change | File(s) | Description |
|--------|---------|-------------|
| **Downscale before inference** | `config.py`, `gesture_detector.py` | Hand detection runs on **320×240** (`DETECTION_WIDTH` × `DETECTION_HEIGHT`) instead of full 640×480. Landmarks are in normalized coords, so they are mapped back to display size. This cuts MediaPipe work by ~4×. |
| **Reuse output dict** | `gesture_detector.py` | `process()` reuses a single `_out` dict and updates it in place instead of allocating a new dict every frame. |
| **Cursor smoothing without extra allocations** | `gesture_detector.py` | Cursor average uses `sum(...)/n` over the buffer instead of `np.mean([...])` to avoid building a list and calling NumPy. |
| **No full-frame copy in overlay** | `canvas.py` | `render_overlay()` no longer does `frame_bgr.copy()`. Blend is computed into a pre-allocated float buffer and written into `frame_bgr`. |
| **Cached background for mask** | `canvas.py` | Canvas background is stored as `self._bg` (numpy array) once in `__init__` and reused for the diff mask every frame. |
| **Pre-allocated blend buffer** | `canvas.py` | `self._blend_buf` (float32, same shape as frame) is created once and reused in `render_overlay()` to avoid per-frame float allocation. |
| **FPS cap only when ahead** | `main.py` | Sleep is only applied when loop iteration finished faster than `target_dt`. When already slow, no extra delay is added (comment clarified). |

---

## 2. MediaPipe Optimization

| Change | File(s) | Description |
|--------|---------|-------------|
| **Lower-resolution input** | `gesture_detector.py` | Frames are resized to 320×240 with `cv2.INTER_LINEAR` before `cvtColor` and `detect_for_video`. Same behavior, less work. |
| **VIDEO mode** | (already in place) | `VisionRunningMode.VIDEO` and `detect_for_video()` with monotonic timestamps are used for temporal consistency. |
| **Single hand** | `config.py` | `MAX_NUM_HANDS = 1` is documented as the fastest option; no change to logic. |
| **Contiguous check only when needed** | `gesture_detector.py` | `np.ascontiguousarray(rgb)` is only called when `rgb.flags["C_CONTIGUOUS"]` is False (resize typically returns contiguous). |

---

## 3. OpenCV Optimization

| Change | File(s) | Description |
|--------|---------|-------------|
| **Resize once for detection** | `gesture_detector.py` | Single `cv2.resize(..., INTER_LINEAR)` to detection size; display frame is left at camera resolution. |
| **ROI-only copy in UI** | `ui.py` | `draw_instruction_box` and `draw_toolbar` copy and blend only the affected rectangle (instruction box or toolbar strip) instead of the full frame. |
| **Numpy-based interpolation** | `canvas.py` | `_interpolate_points()` uses `np.linspace` and array ops to generate interpolated points in one go instead of a Python loop. |

---

## 4. macOS / Apple Silicon

| Change | File(s) | Description |
|--------|---------|-------------|
| **Request FPS** | `camera.py` | `CAP_PROP_FPS` is set to `config.TARGET_FPS` so the backend (e.g. AVFoundation) can target that rate if supported. |
| **Minimal buffer** | (already in place) | `CAP_PROP_BUFFERSIZE = 1` keeps capture latency low. |

No separate threading or hardware-acceleration APIs were added; MediaPipe and OpenCV already use available CPU/GPU on Apple Silicon.

---

## 5. Code Quality

- Comments were added at optimization points (e.g. “Perf: …”).
- No change to gesture semantics, key bindings, or UI layout.
- Config is centralized: detection size is controlled by `DETECTION_WIDTH` and `DETECTION_HEIGHT` in `config.py`.

---

## Estimated FPS Impact

| Factor | Effect |
|--------|--------|
| **Detection at 320×240** | Largest gain: often **~2–3×** faster inference (depends on device). |
| **No full-frame overlay copy** | Saves one full-frame copy per frame; noticeable at higher resolutions. |
| **Reused buffers (blend, output dict)** | Reduces allocations and GC; helps sustain FPS. |
| **UI ROI-only blend** | Smaller memory traffic; modest gain. |
| **Numpy interpolation + sum/len** | Small per-frame savings. |

**Rough expectation:**  
- **Before:** ~10–18 FPS (e.g. 640×480 full-frame detection, full-frame overlay copy).  
- **After:** ~25–35+ FPS on Apple Silicon (e.g. M2) at 640×480 display, with detection at 320×240.  

Actual numbers depend on the Mac model and background load. The in-app FPS counter reflects the result.

---

## Config Knobs for Tuning

- **`config.DETECTION_WIDTH` / `DETECTION_HEIGHT`**: Lower (e.g. 256×192) for more FPS, higher (e.g. 416×312) for slightly better hand detail.
- **`config.TARGET_FPS`**: Upper limit for the main loop sleep; 30 is a good default.
- **`config.SMOOTHING_BUFFER_SIZE`**: Lower = less latency, more jitter; higher = smoother cursor, more lag.
