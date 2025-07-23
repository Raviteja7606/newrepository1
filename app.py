from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import re
import spacy
import fitz  # PyMuPDF
from langdetect import detect

app = Flask(__name__)
CORS(app)

# Language model mapping
model_map = {
    "en": "en_core_web_sm",
    "fr": "fr_core_news_sm",
    "de": "de_core_news_sm",
    "es": "es_core_news_sm"
}

# Load cached models
loaded_models = {}

def get_nlp_model(text):
    try:
        lang = detect(text)
    except:
        lang = "en"
    model_name = model_map.get(lang, "en_core_web_sm")
    if model_name not in loaded_models:
        loaded_models[model_name] = spacy.load(model_name)
    return loaded_models[model_name], lang

# Regex patterns
patterns = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
    "Password": r"(?i)(password)\s*[:=]\s*\S+",
    "Phone Number": r"\b\d{10}\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "API Key": r"\b(?:AKIA|AIza|sk_live|ghp_)[A-Za-z0-9]{16,}\b"
}

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def scan():
    if request.content_type.startswith("multipart/form-data"):
        file = request.files.get("file")
        if file and file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(file)
        else:
            return jsonify({"error": "Invalid or missing PDF"}), 400
    else:
        data = request.get_json()
        text = data.get("text", "")

    nlp, lang = get_nlp_model(text)
    doc = nlp(text)
    results = []

    # Named Entity Recognition (NER)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "PER", "LOC"]:
            results.append({
                "type": ent.label_,
                "text": ent.text,
                "method": f"NER ({lang})"
            })

    # Regex matching
    for label, pattern in patterns.items():
        for match in re.findall(pattern, text):
            results.append({
                "type": label,
                "text": match,
                "method": "Regex"
            })

    risk_score = len(results) * 30
    blocked = risk_score >= 60

    return jsonify({
        "detected": results,
        "risk_score": risk_score,
        "blocked": blocked,
        "language": lang
    })

if __name__ == "__main__":
    app.run(debug=True)
