from pathlib import Path
import json
import numpy as np
import tensorflow as tf

# Paths
ROOT        = Path(__file__).resolve().parents[1]
MODEL_PATH  = ROOT / "model" / "best_cnn.keras"
LABELS_PATH = Path(__file__).resolve().with_name("label_map.json")

# Load model + labels
MODEL     = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
COMPOSERS = json.load(open(LABELS_PATH))  # e.g. ["Bach","Beethoven","Chopin","Mozart"]

SEQ_T  = 512
N_KEYS = 88

def _prep_roll(pr: np.ndarray):
    """
    Match training preprocessing:
      - accept (T,88) or (88,T)
      - clip to 0..127 (raw velocities)
      - left-pad/trim to 512 frames
      - return model tensor (1,512,88,1) and viz roll (88,512)
    """
    pr = np.asarray(pr)

    if pr.ndim != 2:
        raise ValueError(f"Expected 2D piano-roll, got {pr.shape}")

    # If coming as (88, T) from pretty_midi, flip to (T, 88)
    if pr.shape[0] == N_KEYS and pr.shape[1] != N_KEYS:
        pr = pr.T  # -> (T, 88)

    # Raw velocity scale like training (NO normalization to [0,1])
    pr = np.clip(pr, 0, 127).astype(np.float32)

    # Pad/trim to 512 frames
    T = pr.shape[0]
    if T < SEQ_T:
        pr = np.pad(pr, ((0, SEQ_T - T), (0, 0)), mode="constant")
    elif T > SEQ_T:
        pr = pr[:SEQ_T, :]

    x   = pr.reshape(1, SEQ_T, N_KEYS, 1)  # for the model
    viz = pr.T                             # (88,512) for plotting
    return x, viz

def predict_composer(piano_roll: np.ndarray):
    """
    Returns (probabilities_dict, viz_roll_88x512)
    """
    x, viz_roll_88x512 = _prep_roll(piano_roll)     # x: (1,512,88,1)
    probs = MODEL.predict(x, verbose=0)[0]          # (4,)
    order = np.argsort(probs)[::-1]
    probs_dict = {COMPOSERS[i]: float(probs[i]) for i in order}
    return probs_dict, viz_roll_88x512
