# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Virtual Air-Drawing System — a single-process Python desktop app that uses OpenCV + MediaPipe for webcam-based hand gesture drawing. See `README.md` for full details.

### Running in a headless / cloud VM

- The app requires a **webcam** (`/dev/video0`) and a **display server**. In cloud VMs neither is available by default.
- Start a virtual display before any OpenCV GUI work: `Xvfb :99 -screen 0 1280x720x24 &` then `export DISPLAY=:99`.
- `python -m src.main` will fail with `RuntimeError: Could not open camera` — this is expected without a physical camera. To exercise the full pipeline without a camera, create synthetic frames and drive `Canvas`, `GestureDetector`, and `UI` modules directly (see the test patterns used during environment setup).

### Dependencies

- Python 3.12 with venv at `/workspace/venv`. Activate with `source /workspace/venv/bin/activate`.
- `pip install -r requirements.txt` installs the 3 runtime deps: `opencv-python`, `mediapipe`, `numpy`.
- The MediaPipe model file is pre-committed at `models/hand_landmarker.task`; no download needed.

### Lint / type-check

- `flake8 src/ --max-line-length=120` — pre-existing warnings exist (unused imports, etc.); do not fix unless asked.
- `pyright src/ --pythonversion 3.12` — passes clean.

### Running the app (with a camera)

Per `README.md`: `python -m src.main` from the project root.

### System packages needed on fresh Ubuntu cloud VMs

`python3.12-venv`, `xvfb`, `libgl1`, `libglib2.0-0` — these are installed during initial setup but are not part of the update script.
