from flask import Flask, request, jsonify
import os
import json
import asyncio
from metaapi_cloud_sdk import MetaApi

app = Flask(__name__)
WEBHOOK_SECRET = "MY_SECRET_KEY_123"

def get_account_config(account_name):
    """Fetches account credentials dynamically from Render environment variables"""
    accounts_db = os.environ.get("ACCOUNTS_DB", "{}")
    try:
        accounts = json.loads(accounts_db)
        return accounts.get(account_name)
    except Exception as e:
        print(f"Error parsing accounts database: {e}")
        return None

async def execute_prop_trade(config, symbol, action, volume, sl=None, tp=None):
    api = MetaApi(token=config["token"])
    account = await api.metatrader_account_api.get_account(config["account_id"])
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()

    if action.lower() == "buy":
        result = await connection.create_market_buy_order(
            symbol=symbol,
            volume=float(volume),
            stop_loss=float(sl) if sl else None,
            take_profit=float(tp) if tp else None
        )
    else:
        result = await connection.create_market_sell_order(
            symbol=symbol,
            volume=float(volume),
            stop_loss=float(sl) if sl else None,
            take_profit=float(tp) if tp else None
        )
    return result

@app.route("/", methods=["GET"])
def home():
    return "Dynamic Multi-Account FVG Router is Online", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data or data.get("secret") != WEBHOOK_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Read which account to target from the incoming signal (defaults to "ftmo")
    target_account = data.get("account", "ftmo")
    config = get_account_config(target_account)

    if not config:
        return jsonify({"status": "error", "message": f"Account '{target_account}' is not configured in server settings."}), 400

    symbol = data.get("symbol", "EURUSD")
    action = data.get("action", "buy")
    volume = data.get("volume", 0.01)
    sl = data.get("sl")
    tp = data.get("tp")

    try:
        result = asyncio.run(execute_prop_trade(config, symbol, action, volume, sl, tp))
        return jsonify({"status": "success", "message": f"Trade executed successfully on {target_account}", "details": str(result)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
