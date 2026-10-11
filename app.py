from flask import Flask, request, jsonify
import os

app = Flask(__name__)
WEBHOOK_SECRET = "MY_SECRET_KEY_123"

@app.route("/", methods=["GET"])
def home():
    return "FVG Webhook Router is Online", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data or data.get("secret") != WEBHOOK_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    symbol = data.get("symbol")
    action = data.get("action")
    volume = data.get("volume", 0.01)
    sl = data.get("sl")
    tp = data.get("tp")

    print(f"Signal Received: {action} {symbol} | SL: {sl} | TP: {tp}")
    return jsonify({"status": "success", "message": f"Processed {action} on {symbol}"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

