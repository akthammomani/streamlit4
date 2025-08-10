from pathlib import Path
import json
import numpy as np
import tensorflow as tf

# Paths (utils/ is one level under repo root)
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "best_cnn.keras"
LABELS_PATH = Path(__file__).resolve().with_name("label_map.json")

# Load model + labels
MODEL = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
COMPOSERS = json.load(open(LABELS_PATH))  # e.g. ["Bach","Beethoven","Chopin","Mozart"]

SEQ_T = 512
N_KEYS = 88

def _prep_roll(pr: np.ndarray) -> np.ndarray:
    """Match training preproc: (T,88) float32 in [0,1] -> (1,512,88,1)."""
    pr = np.asarray(pr, dtype=np.float32)

    # Accept (88,T) from pretty_midi and flip to (T,88)
    if pr.ndim != 2:
        raise ValueError(f"Expected 2D piano-roll, got {pr.shape}")
    if pr.shape[0] == N_KEYS and pr.shape[1] != N_KEYS:
        pr = pr.T  # -> (T, 88)

    # Clip, pad/trim to 512 frames
    pr = np.clip(pr, 0, 127)
    T = pr.shape[0]
    if T < SEQ_T:
        pr = np.pad(pr, ((0, SEQ_T - T), (0, 0)), mode="constant")
    elif T > SEQ_T:
        pr = pr[:SEQ_T, :]

    # **Normalize exactly like your earlier working path**
    pr = pr / 127.0

    return pr.reshape(1, SEQ_T, N_KEYS, 1)


def predict_composer(piano_roll: np.ndarray):
    """
    Returns (probabilities_dict, processed_roll) where:
      - probabilities_dict maps composer -> probability (sorted desc)
      - processed_roll is (512, 88) pianoroll for plotting
    """
    x = _prep_roll(piano_roll)                 # (1,512,88,1)
    probs = MODEL.predict(x, verbose=0)[0]     # shape (4,)
    order = np.argsort(probs)[::-1]
    probs_dict = {COMPOSERS[i]: float(probs[i]) for i in order}
    roll_512x88 = x[0, :, :, 0]                # (512,88) for viz
    return probs_dict, roll_512x88

