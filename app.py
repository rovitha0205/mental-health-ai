import os
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request
from tensorflow.keras.models import load_model
from transformers import pipeline

app = Flask(__name__)

# ------------------ PATHS ------------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ MODELS ------------------

# Face emotion model (CNN)
face_model = load_model("models/emotion_model.h5", compile=False)

face_cascade = cv2.CascadeClassifier(
    "models/haarcascade_frontalface_default.xml"
)

face_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

# Text emotion model (Transformer)
text_model = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=None
)

# ------------------ FUNCTIONS ------------------

def analyze_face(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60)
    )

    if len(faces) == 0:
        return "No Face Detected", 0

    x, y, w, h = faces[0]
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (64, 64))
    face = face / 255.0
    face = face.reshape(1, 64, 64, 1)

    pred = face_model.predict(face)
    emotion = face_labels[np.argmax(pred)]
    confidence = round(float(np.max(pred)) * 100, 2)

    return emotion, confidence


def analyze_text(text):
    results = text_model(text)[0]
    top = max(results, key=lambda x: x["score"])
    return top["label"], round(top["score"] * 100, 2)

# ------------------ ROUTES ------------------

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/analyze_all", methods=["POST"])
def analyze_all():

    # ---------- TEXT ----------
    text = request.form.get("text", "")
    text_emotion, text_conf = analyze_text(text)

    # ---------- PSYCHOLOGICAL QUESTIONS (INDIRECT) ----------
    sleep = request.form["sleep"]
    stress_freq = request.form["stress_freq"]
    interest = request.form["interest"]

    psycho_score = 0

    if sleep == "poor":
        psycho_score += 2
    elif sleep == "disturbed":
        psycho_score += 1

    if stress_freq == "often":
        psycho_score += 2
    elif stress_freq == "sometimes":
        psycho_score += 1

    if interest == "yes":
        psycho_score += 2
    elif interest == "sometimes":
        psycho_score += 1

    # ---------- FACE ----------
    image_path = os.path.join(UPLOAD_FOLDER, "live_face.png")
    face_emotion, face_conf = analyze_face(image_path)

    # ---------- FUSION LOGIC ----------
    if psycho_score >= 5 or text_emotion in ["sadness", "fear"]:
        stress_level = "High Stress 😟"
        explanation = (
            "Facial expressions, language patterns, and daily behavior indicators "
            "such as sleep disturbance and high stress suggest emotional strain."
        )
        suggestion = (
            "Consider taking regular breaks, practicing deep breathing, "
            "and talking to someone you trust."
        )

    elif psycho_score >= 3:
        stress_level = "Moderate Stress 😐"
        explanation = (
            "Some indicators of stress are present based on facial cues, text input, "
            "and behavioral responses."
        )
        suggestion = (
            "Light exercise, relaxation techniques, and proper rest may help."
        )

    else:
        stress_level = "Low Stress 😊"
        explanation = (
            "Your facial cues, responses, and text suggest emotional stability."
        )
        suggestion = (
            "Continue maintaining healthy habits and routines."
        )

    return render_template(
        "index.html",
        final_result=True,
        face_emotion=face_emotion,
        face_conf=face_conf,
        text_emotion=text_emotion,
        text_conf=text_conf,
        stress_level=stress_level,
        explanation=explanation,
        suggestion=suggestion
    )


@app.route("/upload_face", methods=["POST"])
def upload_face():
    image_data = request.form["image_data"]
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    image_path = os.path.join(UPLOAD_FOLDER, "live_face.png")
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return render_template("index.html", image_path=image_path)


if __name__ == "__main__":
    app.run(debug=True)
