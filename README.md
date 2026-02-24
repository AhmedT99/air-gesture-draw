# Virtual Air-Drawing System

A local macOS application that lets you draw in the air using your built-in camera and hand gestures. No cloud APIs—everything runs offline.

## Features

- **Real-time webcam** capture with drawing overlay
- **Hand gesture controls** (MediaPipe):
  - **Index finger up** → Draw mode
  - **Two fingers up** → Move cursor without drawing
  - **Pinch** → Toggle drawing on/off
  - **Open palm** → Clear canvas
- **Color toolbar** at top for brush color
- **Brush thickness** and color changes
- **Save drawing** as image file (e.g. PNG)
- **Smooth drawing** with interpolation and noise filtering
- **Instruction box** with dynamic mode feedback

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.8 or higher
- Built-in or USB webcam

## Installation

1. **Create and activate a virtual environment (recommended):**

   ```bash
   cd DRAW_SOFT
   python3 -m venv venv
   source venv/bin/activate   # On macOS/Linux
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **No extra environment variables or API keys needed.** On first run, the app may download the hand-landmarker model once (from Google) into `DRAW_SOFT/models/`; after that it runs fully offline.

## Running the Application

From the project root (`DRAW_SOFT`):

```bash
python -m src.main
```

Or, if you prefer running the module directly:

```bash
python src/main.py
```

(Ensure `src` is run as a module from the project root so imports resolve correctly.)

**First run:** Grant camera permission when macOS prompts you. The camera window will show the live feed with the drawing overlay and instruction box.

**To quit:** Close the window or press `q` in the terminal (if running from terminal) or use the window close button.

## Project Structure

```
DRAW_SOFT/
├── README.md           # This file
├── requirements.txt    # pip dependencies
└── src/
    ├── __init__.py
    ├── main.py         # Entry point, main loop
    ├── config.py       # Constants and configuration
    ├── camera.py       # Webcam capture (OpenCV)
    ├── gesture_detector.py  # Hand detection and gesture logic (MediaPipe)
    ├── canvas.py       # Virtual canvas, brush, save image
    └── ui.py           # Overlay UI (instructions, toolbar)
```

## Performance

The app aims for ≥20 FPS. If performance is low, try:

- Reducing camera resolution in `config.py`
- Closing other camera-heavy applications
- Using a smaller window size

## Saving a Drawing

Press **S** while the app window is focused to save the current drawing. The file is saved in the project directory (or current working directory) as `drawing_YYYYMMDD_HHMMSS.png`.

## License

Use and modify as needed for personal or educational use.
