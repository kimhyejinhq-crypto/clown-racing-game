# -*- coding: utf-8 -*-
"""
app.py
======
Lớp MỎNG biến GameEngine (backend/game_engine.py) thành REST API cho
frontend gọi bằng fetch(). File này KHÔNG chứa luật chơi - chỉ nhận
request, gọi engine, trả JSON, và bắt lỗi GameError để trả về mã 400
kèm thông báo dễ hiểu.

Chạy: python app.py   (mặc định http://127.0.0.1:5000)
"""

from flask import Flask, request, jsonify, render_template

from backend.game_engine import GameEngine, GameError

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)

engine = GameEngine()


def ok(data):
    return jsonify({"success": True, "state": data})


def fail(message, code=400):
    return jsonify({"success": False, "error": message}), code


@app.errorhandler(GameError)
def handle_game_error(e):
    return fail(str(e))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/new_game", methods=["POST"])
def new_game():
    body = request.get_json(force=True) or {}
    names = body.get("names", [])
    state = engine.new_game(names)
    return ok(state.to_dict() | {"pending_action": None})


@app.route("/api/state", methods=["GET"])
def get_state():
    return ok(engine.get_state())


@app.route("/api/roll", methods=["POST"])
def roll():
    body = request.get_json(force=True) or {}
    player_id = body["player_id"]
    chosen_number = body.get("chosen_number")
    engine.roll_dice(player_id, chosen_number)
    return ok(engine.get_state())


@app.route("/api/resolve_pending", methods=["POST"])
def resolve_pending():
    body = request.get_json(force=True) or {}
    choice = body.get("choice", {})
    engine.resolve_pending(choice)
    return ok(engine.get_state())


@app.route("/api/buy_item", methods=["POST"])
def buy_item():
    body = request.get_json(force=True) or {}
    engine.buy_item(body["player_id"], body["item_type"])
    return ok(engine.get_state())


@app.route("/api/skip_shop", methods=["POST"])
def skip_shop():
    body = request.get_json(force=True) or {}
    engine.skip_shop(body["player_id"])
    return ok(engine.get_state())


@app.route("/api/use_item", methods=["POST"])
def use_item():
    body = request.get_json(force=True) or {}
    engine.use_item(
        body["player_id"],
        body["item_type"],
        target_id=body.get("target_id"),
        delta=body.get("delta"),
    )
    return ok(engine.get_state())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
