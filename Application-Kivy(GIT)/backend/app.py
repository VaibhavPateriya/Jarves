from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load API Key once
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCeJpZvFgdNtOAt2mtyDcsEgK3kFv2WEh0")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")  # ✅ Load model once, not inside the request

def clean_response(text: str) -> str:
    """Remove unwanted characters and clean the text."""
    return text.replace("**", "").strip()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"response": "⚠️ No message provided!"}), 400

    try:
        response = model.generate_content(user_message)

        if not getattr(response, "text", None):
            return jsonify({"response": "❌ AI response is empty"}), 500

        response_text = clean_response(response.text)

        return jsonify({"response": response_text})

    except Exception as e:
        app.logger.error(f"❌ ERROR: {e}")
        return jsonify({"response": f"❌ Internal Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
