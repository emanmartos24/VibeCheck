from pathlib import Path

import joblib
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
TRANSFORMER_MODEL_CANDIDATES = [
    BASE_DIR / "emotion_transformer_model.joblib",
    BASE_DIR / "models" / "emotion_transformer_model.joblib",
]

app = Flask(__name__)

EMOTION_ID_TO_NAME = {
    0: "Sadness",
    1: "Joy",
    2: "Love",
    3: "Anger",
    4: "Fear",
    5: "Surprise",
}

EMOTION_NAME_TO_ID = {name.lower(): idx for idx, name in EMOTION_ID_TO_NAME.items()}


def _parse_emotion_label(raw_label: str) -> tuple[int | None, str]:
    normalized = str(raw_label).strip().lower()

    if normalized.startswith("label_"):
        label_id_str = normalized.split("_")[-1]
        if label_id_str.isdigit():
            label_id = int(label_id_str)
            return label_id, EMOTION_ID_TO_NAME.get(label_id, f"Class {label_id}")

    if normalized in EMOTION_NAME_TO_ID:
        label_id = EMOTION_NAME_TO_ID[normalized]
        return label_id, EMOTION_ID_TO_NAME[label_id]

    return None, str(raw_label).replace("_", " ").title().strip()


def _load_transformer_model():
    for candidate in TRANSFORMER_MODEL_CANDIDATES:
        if candidate.exists():
            return joblib.load(candidate)
    raise FileNotFoundError(
        "Could not find emotion_transformer_model.joblib in project root or models directory."
    )


model = None


def _get_model():
    global model
    if model is None:
        model = _load_transformer_model()
    return model


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify({"error": "Please enter text."}), 400

    try:
        loaded_model = _get_model()
    except Exception as exc:
        return jsonify({"error": f"Failed to load model: {exc}"}), 500

    raw_result = loaded_model(text[:512], top_k=None)

    if isinstance(raw_result, list) and raw_result and isinstance(raw_result[0], list):
        raw_result = raw_result[0]
    elif isinstance(raw_result, dict):
        raw_result = [raw_result]

    ranked_scores = []
    for item in (raw_result or []):
        label_id, emotion_name = _parse_emotion_label(item.get("label", "Unknown"))
        ranked_scores.append(
            {
                "label": label_id,
                "emotion": emotion_name,
                "probability": float(item.get("score", 0.0)),
            }
        )

    ranked_scores.sort(key=lambda item: item["probability"], reverse=True)

    if not ranked_scores:
        return jsonify({"error": "Model did not return valid prediction scores."}), 500

    top_prediction = ranked_scores[0]

    return jsonify(
        {
            "predicted_label": top_prediction["label"],
            "predicted_emotion": top_prediction["emotion"],
            "predicted_probability": round(top_prediction["probability"], 4),
            "emotion_scores": [
                {
                    "label": item["label"],
                    "emotion": item["emotion"],
                    "probability": round(item["probability"], 4),
                }
                for item in ranked_scores
            ],
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
