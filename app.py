import json
import random
import re
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from nltk.stem.lancaster import LancasterStemmer

STEMMER = LancasterStemmer()
IGNORE_WORDS = {"?", "!", ".", ",", "'s", "a", "an", "the", "to", "of"}
BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "intents.json", encoding="utf-8") as f:
    INTENTS_DATA = json.load(f)

app = Flask(__name__)
context_store: dict[str, str] = {}


def tokenize(sentence: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9']+", sentence.lower())
    return [STEMMER.stem(w) for w in tokens if w not in IGNORE_WORDS]


def pattern_score(user_tokens: set[str], pattern: str) -> float:
    pattern_tokens = set(tokenize(pattern))
    if not pattern_tokens:
        return 0.0
    overlap = len(user_tokens & pattern_tokens)
    return overlap / max(len(pattern_tokens), 1)


def classify(sentence: str, user_id: str = "default", threshold: float = 0.35):
    user_tokens = set(tokenize(sentence))
    current_context = context_store.get(user_id, "")
    ranked = []

    for intent in INTENTS_DATA["intents"]:
        context_filter = intent.get("context_filter")
        if context_filter and context_filter != current_context:
            continue

        best = 0.0
        for pattern in intent["patterns"]:
            best = max(best, pattern_score(user_tokens, pattern))

        # Boost exact / near-exact short matches like "today"
        if any(set(tokenize(p)) == user_tokens for p in intent["patterns"]):
            best = max(best, 1.0)

        if best >= threshold:
            ranked.append((best, intent))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def get_response(sentence: str, user_id: str = "default") -> str:
    results = classify(sentence, user_id=user_id)
    if not results:
        return "I'm not sure I understand. Could you rephrase that?"

    _, intent = results[0]
    if intent.get("context_set") is not None:
        context_store[user_id] = intent.get("context_set", "")

    return random.choice(intent["responses"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    user_id = payload.get("user_id") or request.remote_addr or "default"

    if not message:
        return jsonify({"error": "Message is required"}), 400

    reply = get_response(message, user_id=user_id)
    return jsonify({"reply": reply, "user_message": message})


@app.route("/api/suggestions")
def suggestions():
    samples = [
        "Hello",
        "What are your hours?",
        "What kinds of mopeds are there?",
        "Do you take credit cards?",
        "I'd like to rent a moped",
        "Are you open today?",
    ]
    return jsonify({"suggestions": samples})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5050)
