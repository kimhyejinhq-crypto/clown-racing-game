from flask import Flask, request, jsonify
from flask_cors import CORS
from game_engine import GameEngine
import traceback

app = Flask(__name__)
CORS(app)  # Cho phép frontend gọi API từ domain khác

engine = GameEngine()


# ------------------ HÀM SERIALIZE (chuyển object -> dict) ------------------
def serialize_player(player):
    """
    Chuyển một đối tượng Player thành dict.
    Nếu các thuộc tính (cards, properties, items) có phương thức to_dict() thì dùng,
    ngược lại chuyển thành chuỗi.
    """
    return {
        "name": player.name,
        "position": player.position,
        "money": player.money,
        "cards": [
            card.to_dict() if hasattr(card, "to_dict") else str(card)
            for card in getattr(player, "cards", [])
        ],
        "properties": [
            prop.to_dict() if hasattr(prop, "to_dict") else str(prop)
            for prop in getattr(player, "properties", [])
        ],
        "items": [
            item.to_dict() if hasattr(item, "to_dict") else str(item)
            for item in getattr(player, "items", [])
        ],
    }


def serialize_state(state):
    """
    Chuyển toàn bộ GameState thành dict.
    """
    if state is None:
        return None
    return {
        "players": [serialize_player(p) for p in state.players],
        "current_turn": state.current_turn,
        "phase": state.phase,
        "dice_value": getattr(state, "dice_value", None),
        "pending_actions": getattr(state, "pending_actions", []),
        "board": getattr(state, "board", None),  # Có thể là object phức tạp, tạm giữ nguyên
        "turn_phase": getattr(state, "turn_phase", None),
        "winner": getattr(state, "winner", None),
    }


# ------------------ CÁC ENDPOINT API ------------------
@app.route("/api/state", methods=["GET"])
def get_state():
    """Lấy trạng thái hiện tại của game (dành cho frontend lấy dữ liệu ban đầu)"""
    try:
        if engine.state is None:
            return jsonify({"error": "Game chưa được khởi tạo"}), 400
        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/new_game", methods=["POST"])
def new_game():
    """
    Khởi tạo game mới.
    Body JSON: { "names": ["Player1", "Player2", ...] }
    """
    try:
        data = request.get_json()
        if not data or "names" not in data:
            return jsonify({"error": "Thiếu trường 'names' trong body"}), 400
        names = data["names"]
        if not names or len(names) < 2:
            return jsonify({"error": "Cần ít nhất 2 người chơi"}), 400

        engine.new_game(names)
        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/roll_dice", methods=["POST"])
def roll_dice():
    """Tung xúc xắc cho người chơi hiện tại."""
    try:
        if engine.state is None:
            return jsonify({"error": "Game chưa được khởi tạo"}), 400
        engine.roll_dice()
        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/action", methods=["POST"])
def handle_action():
    """
    Xử lý hành động của người chơi.
    Body JSON: { "action": "buy_house", "data": { "property": "Park Place" } }
    """
    try:
        data = request.get_json()
        if not data or "action" not in data:
            return jsonify({"error": "Thiếu trường 'action' trong body"}), 400
        action = data["action"]
        payload = data.get("data", {})

        if engine.state is None:
            return jsonify({"error": "Game chưa được khởi tạo"}), 400

        engine.handle_action(action, payload)
        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/resolve_pending", methods=["POST"])
def resolve_pending():
    """Giải quyết các sự kiện đang chờ (ví dụ: trả tiền thuê, rút thẻ, đến ô đặc biệt)."""
    try:
        if engine.state is None:
            return jsonify({"error": "Game chưa được khởi tạo"}), 400
        engine.resolve_pending()
        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/shop_buy", methods=["POST"])
def shop_buy():
    """
    Mua vật phẩm từ cửa hàng.
    Body JSON: { "item": "shield" }
    """
    try:
        data = request.get_json()
        if not data or "item" not in data:
            return jsonify({"error": "Thiếu trường 'item' trong body"}), 400
        item = data["item"]

        if engine.state is None:
            return jsonify({"error": "Game chưa được khởi tạo"}), 400

        # Gọi phương thức mua tương ứng (tên có thể là buy_item, purchase_item, ...)
        if hasattr(engine, "buy_item"):
            engine.buy_item(item)
        elif hasattr(engine, "purchase_item"):
            engine.purchase_item(item)
        else:
            return jsonify({"error": "Engine không hỗ trợ mua vật phẩm"}), 501

        return jsonify(serialize_state(engine.state))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ------------------ CHẠY SERVER (chỉ khi chạy trực tiếp) ------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
