"""
Resolve path to the Hand Landmarker model file.
On first run (with network), the model can be downloaded and cached locally so the app runs offline afterward.
"""

import os
import urllib.request
from pathlib import Path

# Default model URL (Google MediaPipe hosted model)
HAND_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


def get_model_path():
    """
    Return path to hand_landmarker.task. Uses PROJECT_ROOT/models/hand_landmarker.task
    if present; otherwise attempts a one-time download to that path.
    Project root is the directory containing the 'src' package.
    """
    # Project root: parent of directory containing this file (src)
    project_root = Path(__file__).resolve().parent.parent
    models_dir = project_root / "models"
    model_path = models_dir / "hand_landmarker.task"

    if model_path.is_file():
        return str(model_path)

    models_dir.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(HAND_LANDMARKER_MODEL_URL, model_path)
    except Exception as e:
        raise FileNotFoundError(
            "Hand landmarker model not found and download failed (no network?).\n"
            f"Download manually from:\n  {HAND_LANDMARKER_MODEL_URL}\n"
            f"Save as: {model_path}\n"
            f"Error: {e}"
        ) from e

    return str(model_path)
