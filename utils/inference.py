import os
os.environ.setdefault("KERAS_BACKEND", "tensorflow")  # ensure TF backend

import numpy as np
import keras  # Keras 3
MODEL_PATH = "model/best_cnn.keras"
MODEL = keras.models.load_model(MODEL_PATH, compile=False)


COMPOSERS = ["Bach", "Beethoven", "Chopin", "Mozart"]

def _prep_roll(pr: np.ndarray) -> np.ndarray:
    pr = np.asarray(pr, dtype=np.float32)

    # If it looks like (88, T), flip to (T, 88)
    if pr.ndim != 2:
        raise ValueError(f"Expected 2D pianoroll, got {pr.shape}")
    if pr.shape[0] == 88 and pr.shape[1] != 88:
        pr = pr.T  # -> (T, 88)

    # Pad/trim time dimension to 512
    T = pr.shape[0]
    if T < 512:
        pr = np.pad(pr, ((0, 512 - T), (0, 0)), mode="constant")
    elif T > 512:
        pr = pr[:512, :]

    # Normalize and add batch & channel axes -> (1, 512, 88, 1)
    pr = (pr / 127.0).reshape(1, 512, 88, 1)
    return pr

def predict_composer(pianoroll: np.ndarray):
    x = pianoroll.astype("float32") / 127.0           # (512, 88)
    x = np.expand_dims(x, axis=(0, -1))               # (1, 512, 88, 1)
    probs = MODEL.predict(x, verbose=0)[0]
    top = np.argsort(probs)[::-1][:3]
    return {COMPOSERS[i]: float(probs[i]) for i in top}, x[0, :, :, 0]


