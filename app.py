# -*- coding: utf-8 -*-
"""
app.py - Flask server cung cấp API cho frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.game_engine import GameEngine, GameError

app = Flask(__name__)
CORS(app)

# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory  # <--- Thêm 'send_from_directory' vào dòng này
from flask_cors import CORS
from backend.game_engine import GameEngine, GameError

app = Flask(__name__, static_folder='frontend')  # <--- Sửa dòng này, thêm static_folder='frontend'
CORS(app)

# ===== THÊM ĐOẠN CODE SAU ĐÂY VÀO =====
# Route để phục vụ file HTML và các file tĩnh (CSS, JS, ảnh...)
@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

# Route để phục vụ tất cả các file trong thư mục frontend (style.css, scripts.js, ...)
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('frontend', filename)
# ===== KẾT THÚC ĐOẠN CODE THÊM VÀO =====

# ... phần code API còn lại của bạn giữ nguyên

engine = GameEngine()


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data = request.get_json()
    names = data.get("names", [])
    try:
        state = engine.new_game(names)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/state", methods=["GET"])
def get_state():
    try:
        state = engine.get_state()
        return jsonify({"success": True, "state": state})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/roll", methods=["POST"])
def roll():
    data = request.get_json()
    player_id = data.get("player_id")
    chosen_number = data.get("chosen_number")
    try:
        state = engine.roll_dice(player_id, chosen_number)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/buy_item", methods=["POST"])
def buy_item():
    data = request.get_json()
    player_id = data.get("player_id")
    item_type = data.get("item_type")
    try:
        state = engine.buy_item(player_id, item_type)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/skip_shop", methods=["POST"])
def skip_shop():
    data = request.get_json()
    player_id = data.get("player_id")
    try:
        state = engine.skip_shop(player_id)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/use_item", methods=["POST"])
def use_item():
    data = request.get_json()
    player_id = data.get("player_id")
    item_type = data.get("item_type")
    target_id = data.get("target_id")
    delta = data.get("delta")
    try:
        state = engine.use_item(player_id, item_type, target_id, delta)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/resolve_pending", methods=["POST"])
def resolve_pending():
    data = request.get_json()
    choice = data.get("choice", {})
    try:
        state = engine.resolve_pending(choice)
        return jsonify({"success": True, "state": state.to_dict()})
    except GameError as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
