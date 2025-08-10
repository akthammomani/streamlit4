from pathlib import Path
import json
import numpy as np
import tensorflow as tf

# Paths
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "best_cnn.keras"
LABELS_PATH = Path(__file__).resolve().with_name("label_map.json")

MODEL = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
COMPOSERS = json.load(open(LABELS_PATH))   # e.g. ["Bach","Beethoven","Chopin","Mozart"]

SEQ_T  = 512
N_KEYS = 88

def _prep_roll(pr: np.ndarray) -> np.ndarray:
    """
    Match training preprocessing EXACTLY:
      - accept (88, T) or (T, 88)
      - clip to 0..127
      - DO NOT normalize to [0,1]
      - left-pad/trim to 512
      - return shape (1, 512, 88, 1), dtype uint8 (TF will cast)
    """
    pr = np.asarray(pr)
    if pr.ndim != 2:
        raise ValueError(f"Expected 2D piano-roll, got {pr.shape}")

    # If coming from pretty_midi as (88, T), flip to (T, 88)
    if pr.shape[0] == N_KEYS and pr.shape[1] != N_KEYS:
        pr = pr.T  # -> (T, 88)

    pr = np.clip(pr, 0, 127).astype(np.uint8)

    T = pr.shape[0]
    if T < SEQ_T:
        pr = np.pad(pr, ((0, SEQ_T - T), (0, 0)), mode="constant")
    elif T > SEQ_T:
        pr = pr[:SEQ_T, :]

    # (1, 512, 88, 1)
    x = pr.reshape(1, SEQ_T, N_KEYS, 1)
    return x

def predict_composer(piano_roll: np.ndarray):
    """
    Returns (probs_dict, roll_512x88) for display.
    """
    x = _prep_roll(piano_roll)                # (1,512,88,1), uint8 in 0..127
    probs = MODEL.predict(x, verbose=0)[0]    # shape (4,)
    order = np.argsort(probs)[::-1]
    probs_dict = {COMPOSERS[i]: float(probs[i]) for i in order}
    roll_512x88 = x[0, :, :, 0]               # (512,88) for visualization
    return probs_dict, roll_512x88

