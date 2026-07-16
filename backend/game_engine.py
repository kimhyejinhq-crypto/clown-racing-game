# -*- coding: utf-8 -*-
"""
game_engine.py
==============
"Trái tim" của toàn bộ game. File này là nơi DUY NHẤT chứa luật chơi.
- constants.py   -> chỉ số / enum
- models.py      -> hình dạng dữ liệu
- board_builder  -> tạo bản đồ ngẫu nhiên
- cards.py       -> nội dung bài (chữ nghĩa)
- game_engine.py -> XỬ LÝ mọi hành động (tung xúc xắc, rút bài, mua/dùng
                     vật phẩm, kết thúc ván...)
- app.py         -> lớp mỏng expose engine ra thành REST API cho frontend

=== CƠ CHẾ "PENDING ACTION" (rất quan trọng, đọc trước khi sửa code) ===
Một số lá bài cần người chơi CHỌN (ví dụ "chọn 1 người chơi", "chọn 1 ô",
"chọn 1 khu vực"...). Vì engine không thể tự hỏi & chờ trong lúc chạy,
mỗi effect-function có thể trả về:
  - một chuỗi string  -> nghĩa là đã xử lý xong, string đó là log message.
  - một dict {"await": "<loại lựa chọn>", "options": [...]}
        -> nghĩa là CẦN người chơi chọn thêm. Engine sẽ lưu vào
        state.pending_action và tạm dừng, đợi frontend gọi
        resolve_pending(choice) để gọi lại đúng effect-function đó với
        choice đã có.
Nhờ vậy 1 hàm effect chỉ cần viết 1 lần, dùng lại được cho cả 2 tình
huống (có sẵn lựa chọn / chưa có lựa chọn).
"""

import random
import time

from .constants import (
    TileType, ItemType, ITEM_INFO, START_TILE, FINISH_TILE, BOARD_SIZE,
    SHOP_TILES, START_GOLD, MAX_ITEMS_CARRIED, MAX_CHAIN_REACTION,
    GAME_TIME_LIMIT_SECONDS,
)
from .models import Player, GameState, StatusEffect
from .board_builder import build_board
from .cards import EVENT_CARDS, TRAP_CARDS


PLAYER_COLORS = ["Đỏ", "Xanh", "Vàng", "Tím"]


class GameError(Exception):
    """Lỗi nghiệp vụ (sai lượt, không đủ tiền, hành động không hợp lệ...)."""
    pass


class GameEngine:
    def __init__(self):
        self.state = GameState()
        self._game_started = False

    # ------------------------------------------------------------------
    # KHỞI TẠO VÁN MỚI
    # ------------------------------------------------------------------
    def new_game(self, player_names):
        if not (2 <= len(player_names) <= 4):
            raise GameError("Cần từ 2 đến 4 chú hề (người chơi).")

        board, reserve = build_board()
        event_deck = list(EVENT_CARDS)
        random.shuffle(event_deck)
        trap_deck = list(TRAP_CARDS)
        random.shuffle(trap_deck)

        players = []
        for i, name in enumerate(player_names):
            players.append(Player(
                id=i,
                name=name.strip() or f"Chú Hề {i+1}",
                color=PLAYER_COLORS[i % len(PLAYER_COLORS)],
                position=START_TILE,
                gold=START_GOLD,
            ))

        item_stock = {it: info["stock"] for it, info in ITEM_INFO.items()}

        self.state = GameState(
            players=players,
            board=board,
            reserve_pool=reserve,
            event_deck=event_deck,
            trap_deck=trap_deck,
            item_stock=item_stock,
            common_fund=0,
            current_player_index=0,
            turn_count=1,
            started_at=time.time(),
            game_over=False,
            winner_id=None,
            log=[],
            reverse_trap_tiles={},
        )
        self._game_started = True
        self._log(f"🎪 Rạp xiếc mở màn! {len(players)} chú hề bước vào cuộc chơi điên loạn.")
        self._log(f"Lượt của {self._current().name}.")
        return self.state

    def _require_started(self):
        if not self._game_started:
            raise GameError("Chưa có ván nào được bắt đầu.")

    # ------------------------------------------------------------------
    # TIỆN ÍCH CHUNG
    # ------------------------------------------------------------------
    def _log(self, msg):
        self.state.log.append(msg)

    def _current(self):
        return self.state.players[self.state.current_player_index]

    def _player(self, pid):
        for p in self.state.players:
            if p.id == pid:
                return p
        raise GameError("Không tìm thấy người chơi.")

    def _others(self, player):
        return [p for p in self.state.players if p.id != player.id and not p.finished]

    def _tile(self, index):
        return self.state.board[index]

    def _has_status(self, player, kind):
        return next((s for s in player.statuses if s.kind == kind), None)

    def _tick_statuses(self, player):
        """Giảm turns_left của mọi status khi lượt của player này kết thúc."""
        alive = []
        for s in player.statuses:
            s.turns_left -= 1
            if s.turns_left > 0:
                alive.append(s)
        player.statuses = alive

    def add_gold(self, player, amount):
        """Cộng vàng cho người chơi, TỰ ĐỘNG trừ bù nợ trước (ghi chú 7)."""
        if amount <= 0:
            return
        if player.debt > 0:
            pay = min(player.debt, amount)
            player.debt -= pay
            amount -= pay
        player.gold += amount

    def try_pay(self, player, amount, to_fund=True):
        """Trả `amount` vàng nếu đủ. Trả về True nếu trả được, False nếu không đủ."""
        if player.gold >= amount:
            player.gold -= amount
            if to_fund:
                self.state.common_fund += amount
            return True
        return False

    def move_player_raw(self, player, delta):
        """Di chuyển thô (không tự kiểm tra thắng), kẹp tối thiểu ở ô 1."""
        player.position = max(START_TILE, player.position + delta)

    # ------------------------------------------------------------------
    # LƯỢT CHƠI
    # ------------------------------------------------------------------
    def roll_dice(self, player_id, chosen_number=None):
        self._require_started()
        self._check_timeout()
        if self.state.game_over:
            raise GameError("Ván đấu đã kết thúc.")
        if self.state.pending_action:
            raise GameError("Còn một lựa chọn đang chờ xử lý (pending_action).")

        player = self._current()
        if player.id != player_id:
            raise GameError("Chưa đến lượt của bạn.")

        moves = 2 if player.pending_double_action else 1
        player.pending_double_action = False

        for _ in range(moves):
            if self.state.game_over or self.state.pending_action:
                break
            dice_value = self._determine_dice(player, chosen_number)
            chosen_number = None  # chỉ áp dụng cho lượt tung đầu tiên
            self._log(f"🎲 {player.name} tung được {dice_value}.")
            self._advance_token(player, dice_value)

        # Nếu có pending_action đang chờ lựa chọn -> dừng ở đây, CHƯA sang lượt kế.
        if self.state.pending_action or self.state.game_over:
            return self.state

        self._maybe_end_turn(player)
        return self.state

    def _determine_dice(self, player, chosen_number):
        lucky = self._has_status(player, "lucky_charm")
        if lucky:
            if chosen_number is None or not (1 <= chosen_number <= 6):
                raise GameError("Bạn đang có Bùa May Mắn: hãy chọn 1 số từ 1-6 (chosen_number).")
            value = chosen_number
        elif player.pending_double_roll:
            value = max(random.randint(1, 6), random.randint(1, 6))
        else:
            value = random.randint(1, 6)

        player.pending_double_roll = False

        if player.pending_lens_delta:
            value = max(1, value + player.pending_lens_delta)
            player.pending_lens_delta = 0

        return value

    def _advance_token(self, player, delta):
        new_pos = player.position + delta
        if new_pos >= FINISH_TILE:
            player.position = FINISH_TILE
            self._log(f"🏁 {player.name} đã VỀ ĐÍCH!")
            self._finish_game(player)
            return
        player.position = new_pos
        self.resolve_tile(player)

    def _maybe_end_turn(self, player):
        """Kiểm tra ô mua sắm; nếu không thì kết thúc lượt luôn."""
        if player.position in SHOP_TILES and not player.finished:
            self.state.pending_shop_tile = True
            self._log(f"🛒 {player.name} dừng đúng ô {player.position} - có thể ghé cửa hàng của gã hề bán đồ.")
            return
        self.end_turn()

    def skip_shop(self, player_id):
        player = self._current()
        if player.id != player_id:
            raise GameError("Chưa đến lượt của bạn.")
        self.state.pending_shop_tile = False
        self.end_turn()
        return self.state

    def end_turn(self):
        self.state.pending_shop_tile = False
        current = self._current()
        self._tick_statuses(current)

        if self.state.game_over:
            return

        n = len(self.state.players)
        idx = self.state.current_player_index
        for _ in range(n):
            idx = (idx + 1) % n
            nxt = self.state.players[idx]
            if nxt.finished:
                continue
            if nxt.skip_next_turn:
                nxt.skip_next_turn = False
                self._log(f"😵 {nxt.name} bị chóng mặt, mất lượt này.")
                continue
            self.state.current_player_index = idx
            self.state.turn_count += 1
            self._log(f"➡️ Lượt của {nxt.name}.")
            return
        # Không còn ai chơi được (hiếm khi xảy ra) -> kết thúc ván theo giờ
        self._finish_by_timeout()

    # ------------------------------------------------------------------
    # XỬ LÝ Ô ĐÁP
    # ------------------------------------------------------------------
    def resolve_tile(self, player, chain_depth=0):
        # Kiểm tra bẫy ngược trước khi xử lý loại ô
        if player.position in self.state.reverse_trap_tiles:
            trapper_id = self.state.reverse_trap_tiles[player.position]
            trapper = self._player(trapper_id)
            if player.id != trapper.id and not player.finished:
                # Chuyển 3 vàng từ người đáp ô sang kẻ gài bẫy
                if player.gold >= 3:
                    player.gold -= 3
                    self.add_gold(trapper, 3)
                    self._log(f"🪤 {player.name} dính bẫy ngược tại ô {player.position}, mất 3 vàng cho {trapper.name}!")
                else:
                    # Nếu không đủ, chuyển toàn bộ vàng còn lại
                    self.add_gold(trapper, player.gold)
                    player.gold = 0
                    self._log(f"🪤 {player.name} dính bẫy ngược nhưng chỉ có {player.gold} vàng, mất hết cho {trapper.name}!")
                # Xoá bẫy sau khi kích hoạt (dùng 1 lần)
                del self.state.reverse_trap_tiles[player.position]

        if chain_depth > MAX_CHAIN_REACTION:
            self._log("⚠️ Chuỗi hiệu ứng quá dài, dừng lại để tránh vòng lặp vô hạn.")
            return
        tile = self._tile(player.position)

        if tile.type == TileType.DICH:
            self._finish_game(player)
            return
        if tile.type == TileType.TRONG:
            self._resolve_trong(player)
        elif tile.type == TileType.VANG:
            self.add_gold(player, 5)
            self._log(f"💰 {player.name} đáp Ô Vàng, nhận 5 vàng.")
        elif tile.type == TileType.DO:
            self._resolve_do(player, chain_depth)
        elif tile.type == TileType.XANH:
            self._resolve_xanh(player, tile, chain_depth)
        elif tile.type == TileType.TIM:
            self.draw_event(player)
        elif tile.type == TileType.CAM:
            self.draw_trap(player)
        elif tile.type == TileType.HONG:
            self._resolve_hong(player)

    def _resolve_trong(self, player):
        others_here = [p for p in self.state.players
                        if p.id != player.id and p.position == player.position and not p.finished]
        if others_here and player.position != START_TILE:
            victim = random.choice(others_here)
            if victim.gold > 0:
                victim.gold -= 1
                self.add_gold(player, 1)
                self._log(f"🤡 {player.name} móc túi trộm 1 vàng của {victim.name} ngay giữa ô trống!")
            else:
                self._log(f"{player.name} định móc túi {victim.name} nhưng túi rỗng tuếch.")
        else:
            self._log(f"{player.name} đáp Ô Trống, không có gì xảy ra.")

    def _resolve_do(self, player, chain_depth):
        if self._has_status(player, "immune_negative"):
            self._log(f"✨ {player.name} được Cứu Trợ che chở, miễn nhiễm Ô Đỏ.")
            return
        if self._consume_shield(player):
            self._log(f"🛡️ {player.name} giơ Lá Chắn Mặt Nạ Vỡ, chặn đứng Ô Đỏ.")
            return

        payer = player
        mercenary = self._has_status(player, "mercenary")
        if mercenary:
            candidates = self._others(player)
            if candidates:
                payer = max(candidates, key=lambda p: p.gold)

        if self.try_pay(payer, 3, to_fund=True):
            if payer is player:
                self._log(f"🔴 {player.name} đáp Ô Đỏ, mất 3 vàng vào Quỹ chung.")
            else:
                self._log(f"🔴 {player.name} đáp Ô Đỏ nhưng nhờ Lính Đánh Thuê, {payer.name} è cổ trả 3 vàng thay!")
        else:
            self._log(f"🔴 {payer.name} không đủ vàng trả Ô Đỏ, {player.name} bị lùi 3 ô!")
            self.move_player_raw(player, -3)
            self.resolve_tile(player, chain_depth + 1)

    def _resolve_xanh(self, player, tile, chain_depth):
        target = tile.jump_target
        self._log(f"🔵 {player.name} rơi vào cổng dịch chuyển, bay tới ô {target}!")
        occupant = next((p for p in self.state.players
                          if p.id != player.id and p.position == target and not p.finished), None)
        player.position = target
        if occupant:
            self.move_player_raw(occupant, -2)
            self._log(f"💥 {player.name} đáp trúng chỗ {occupant.name} đang đứng, đá bay {occupant.name} lùi 2 ô!")
        self.resolve_tile(player, chain_depth + 1)

    def _resolve_hong(self, player):
        if self._has_status(player, "immune_negative"):
            self._log(f"✨ {player.name} được Cứu Trợ che chở, miễn nhiễm Ô Cổng.")
            return
        if self._consume_shield(player):
            self._log(f"🛡️ {player.name} giơ Lá Chắn Mặt Nạ Vỡ, chặn đứng Ô Cổng.")
            return
        if self.try_pay(player, 2, to_fund=True):
            self._log(f"🎪 {player.name} nộp 2 vàng qua Cổng Hồng an toàn.")
        else:
            player.skip_next_turn = True
            player.debt += 2
            self._log(f"🚧 {player.name} không đủ tiền qua Cổng, bị kẹt mất 1 lượt và nợ 2 vàng.")

    def _consume_shield(self, player):
        shield = self._has_status(player, "shield")
        if shield:
            player.statuses = [s for s in player.statuses if s.kind != "shield"]
            return True
        return False

    # ------------------------------------------------------------------
    # BÀI SỰ KIỆN / BẪY
    # ------------------------------------------------------------------
    def draw_event(self, player):
        if not self.state.event_deck:
            self.state.event_deck = list(EVENT_CARDS)
            random.shuffle(self.state.event_deck)
        card = self.state.event_deck.pop(0)
        self._log(f"🟣 {player.name} rút bài Sự Kiện: “{card['name']}” - {card['text']}")
        self._run_card_effect("event", card, player)
        self.state.event_deck.append(card)

    def draw_trap(self, player):
        if not self.state.trap_deck:
            self.state.trap_deck = list(TRAP_CARDS)
            random.shuffle(self.state.trap_deck)
        card = self.state.trap_deck.pop(0)
        self._log(f"🟠 {player.name} rút bài Bẫy: “{card['name']}” - {card['text']}")
        self._run_card_effect("trap", card, player)
        self.state.trap_deck.append(card)

    def _run_card_effect(self, source, card, player, choice=None):
        effect_fn = getattr(self, card["effect_id"])
        result = effect_fn(player, choice)
        if isinstance(result, dict) and result.get("await"):
            self.state.pending_action = {
                "source": source,
                "card_id": card["id"],
                "card_name": card["name"],
                "effect_id": card["effect_id"],
                "player_id": player.id,
                "await": result["await"],
                "options": result.get("options", []),
            }
            self._log(f"⏳ Cần {player.name} chọn thêm ({result['await']}) để hoàn tất lá bài.")
            return
        if isinstance(result, str):
            self._log(result)

    def resolve_pending(self, choice):
        self._require_started()
        pending = self.state.pending_action
        if not pending:
            raise GameError("Không có lựa chọn nào đang chờ xử lý.")
        player = self._player(pending["player_id"])
        effect_fn = getattr(self, pending["effect_id"])
        result = effect_fn(player, choice)
        self.state.pending_action = None
        if isinstance(result, dict) and result.get("await"):
            self.state.pending_action = {**pending, "await": result["await"], "options": result.get("options", [])}
            return self.state
        if isinstance(result, str):
            self._log(result)

        if not self.state.game_over and not self.state.pending_action:
            player_now_current = self._current()
            if player.id == player_now_current.id:
                self._maybe_end_turn(player)
        return self.state

    # ------------------ EVENT EFFECTS (29 lá) ------------------
    def e_pirate(self, player, choice):
        total = 0
        for o in self._others(player):
            take = min(2, o.gold)
            o.gold -= take
            total += take
        self.add_gold(player, total)
        return f"🏴‍☠️ {player.name} hoá trang cướp biển, vơ vét {total} vàng từ mọi người!"

    def e_scam(self, player, choice):
        others = self._others(player)
        if not others:
            return f"{player.name} định lừa đảo nhưng chẳng còn ai để lừa."
        if choice is None:
            return {"await": "single_target", "options": [o.id for o in others]}
        target = self._player(choice["target_id"])
        give = min(3, player.gold)
        player.gold -= give
        self.add_gold(target, give)
        target.skip_next_turn = True
        return f"🃏 {player.name} dúi {give} vàng cho {target.name} rồi... {target.name} bị lừa mất luôn lượt tới!"

    def e_tunnel(self, player, choice):
        others = [p for p in self._others(player) if p.position != player.position]
        if not others:
            return f"{player.name} rơi vào đường hầm nhưng chẳng có ai gần đó."
        nearest = min(others, key=lambda p: abs(p.position - player.position))
        old_pos = player.position
        player.position = nearest.position
        if nearest.position != old_pos:
            self.move_player_raw(nearest, -2)
            return f"🕳️ {player.name} chui hầm trồi lên ngay chỗ {nearest.name}, đá {nearest.name} lùi 2 ô!"
        return f"🕳️ {player.name} chui hầm nhưng vẫn kẹt tại chỗ."

    def e_super_thief(self, player, choice):
        others = self._others(player)
        if not others:
            return f"{player.name} không tìm được ai để đổi chỗ."
        if choice is None:
            return {"await": "single_target", "options": [o.id for o in others]}
        target = self._player(choice["target_id"])
        player.position, target.position = target.position, player.position
        return f"🕵️ {player.name} tráo đổi vị trí y hệt với {target.name} trong nháy mắt!"

    def e_greedy_witch(self, player, choice):
        total = 0
        for o in self._others(player):
            take = min(2, o.gold)
            o.gold -= take
            total += take
        self.add_gold(player, total)
        return f"🧙 Phù thuỷ tham lam trong {player.name} trỗi dậy, bòn rút {total} vàng từ tất cả!"

    def e_destiny(self, player, choice):
        roll = random.randint(1, 6) + random.randint(1, 6)
        if roll >= 8:
            self.move_player_raw(player, 6)
            self.add_gold(player, 5)
            msg = f"🔮 Số Mệnh tung ra {roll}: {player.name} tiến 6 ô và nhận 5 vàng!"
        else:
            self.move_player_raw(player, -4)
            msg = f"🔮 Số Mệnh tung ra {roll}: {player.name} lùi 4 ô, vận rủi đeo bám."
        self.resolve_tile(player, 1)
        return msg

    def e_relief(self, player, choice):
        player.statuses.append(StatusEffect(kind="immune_negative", turns_left=2))
        return f"🕊️ {player.name} được phép màu Cứu Trợ che chắn, miễn nhiễm Đỏ & Cổng trong 2 lượt."

    def e_reverse_trap(self, player, choice):
        empties = [i for i in range(2, BOARD_SIZE) if self._tile(i).type != TileType.DICH and i not in self.state.reverse_trap_tiles]
        if not empties:
            return f"{player.name} không tìm được ô trống để đặt bẫy ngược."
        if choice is None:
            return {"await": "tile_choice", "options": empties}
        idx = choice["tile"]
        if idx not in empties:
            raise GameError("Ô không hợp lệ để đặt bẫy ngược.")
        self.state.reverse_trap_tiles[idx] = player.id
        return f"🪤 {player.name} gài bẫy ngược tại ô {idx}. Ai xui xẻo đáp trúng sẽ mất 3 vàng cho {player.name}!"

    def e_dance(self, player, choice):
        pool = self.state.players
        if choice is None:
            return {"await": "two_targets", "options": [p.id for p in pool]}
        a = self._player(choice["target_id_1"])
        b = self._player(choice["target_id_2"])
        a.position, b.position = b.position, a.position
        return f"💃 {a.name} và {b.name} bị {player.name} bắt khiêu vũ đổi chỗ giữa vòng xoáy hỗn loạn!"

    def e_curse(self, player, choice):
        alive = [p for p in self.state.players if not p.finished]
        poorest = min(alive, key=lambda p: p.gold)
        richest = max(alive, key=lambda p: p.gold)
        if poorest.id == richest.id or poorest.gold <= 0:
            return "😈 Lời nguyền vang lên nhưng không ai đủ nghèo (hoặc đủ giàu) để thi hành."
        poorest.gold -= 1
        self.add_gold(richest, 1)
        return f"😈 Lời nguyền bắt {poorest.name} (nghèo nhất) nộp 1 vàng cho {richest.name} (giàu nhất)."

    def e_copy(self, player, choice):
        others = self._others(player)
        if not others:
            return f"{player.name} chẳng có ai để sao chép."
        if choice is None:
            return {"await": "copy_choice", "options": [o.id for o in others]}
        target = self._player(choice["target_id"])
        field = choice.get("field", "gold")
        if field == "position":
            player.position = target.position
            return f"📋 {player.name} bản sao lỗi thời gian, dịch chuyển tới đúng ô của {target.name}!"
        player.gold = target.gold
        return f"📋 {player.name} sao chép y hệt {target.gold} vàng của {target.name}!"

    def e_mercenary(self, player, choice):
        cost = min(4, player.gold)
        self.try_pay(player, cost, to_fund=True)
        player.statuses.append(StatusEffect(kind="mercenary", turns_left=3))
        return f"💼 {player.name} thuê Lính Đánh Thuê (trả {cost} vàng), 3 lượt tới sẽ có người trả Ô Đỏ giúp!"

    def e_lucky_charm(self, player, choice):
        player.statuses.append(StatusEffect(kind="lucky_charm", turns_left=2))
        return f"🍀 {player.name} nhận Bùa May Mắn: 2 lượt tới tự chọn số xúc xắc!"

    def e_light_ahead(self, player, choice):
        self.move_player_raw(player, 6)
        self.resolve_tile(player, 1)
        return f"💡 Ánh sáng cuối đường hầm kéo {player.name} tiến vọt 6 ô!"

    def e_treasure(self, player, choice):
        self.add_gold(player, 7)
        return f"💎 {player.name} đào được kho báu, +7 vàng!"

    def e_tsunami(self, player, choice):
        for o in self._others(player):
            self.move_player_raw(o, -2)
        return f"🌊 {player.name} triệu hồi sóng thần, đẩy lùi tất cả mọi người 2 ô!"

    def e_sleepy_witch(self, player, choice):
        player.gold = max(0, player.gold - 1)
        player.skip_next_turn = True
        return f"😴 Phù thuỷ buồn ngủ khiến {player.name} mất 1 vàng và ngủ quên mất 1 lượt."

    def e_boulder(self, player, choice):
        self.move_player_raw(player, -4)
        self.try_pay(player, min(2, player.gold), to_fund=True)
        self.resolve_tile(player, 1)
        return f"🪨 Tảng đá khổng lồ đè {player.name} lùi 4 ô và mất 2 vàng!"

    def e_guide(self, player, choice):
        others = self._others(player)
        if not others:
            return f"{player.name} không tìm thấy ai để hướng dẫn."
        if choice is None:
            return {"await": "single_target", "options": [o.id for o in others]}
        target = self._player(choice["target_id"])
        self.move_player_raw(target, 3)
        self.resolve_tile(target, 1)
        return f"🧭 {player.name} hào phóng dẫn đường, giúp {target.name} tiến thêm 3 ô!"

    def e_blizzard(self, player, choice):
        for o in self._others(player):
            self.try_pay(o, min(1, o.gold), to_fund=True)
        return f"🌨️ Bão tuyết của {player.name} cuốn đi 1 vàng của mỗi người khác."

    def e_lost(self, player, choice):
        self.move_player_raw(player, -2)
        player.skip_next_turn = True
        self.resolve_tile(player, 1)
        return f"🌀 {player.name} mất phương hướng, lùi 2 ô và mất 1 lượt."

    def e_wind_god(self, player, choice):
        self.move_player_raw(player, 5)
        self.add_gold(player, 2)
        self.resolve_tile(player, 1)
        return f"🌬️ Thần Gió đẩy {player.name} tiến 5 ô và ban 2 vàng!"

    def e_pirate_treasure(self, player, choice):
        self.add_gold(player, 8)
        return f"🏆 {player.name} vớ được kho báu cướp biển, +8 vàng!"

    def e_poison_mushroom(self, player, choice):
        self.move_player_raw(player, -3)
        self.try_pay(player, min(1, player.gold), to_fund=True)
        self.resolve_tile(player, 1)
        return f"🍄 Nấm độc khiến {player.name} lùi 3 ô và mất 1 vàng."

    # ---- 5 lá đổi map (C1-C5) ----
    def e_earthquake(self, player, choice):
        types = [self.state.board[i].type for i in range(1, BOARD_SIZE)]
        random.shuffle(types)
        for i in range(1, BOARD_SIZE):
            self.state.board[i].type = types[i - 1]
            self.state.board[i].jump_target = None
        for i in range(1, BOARD_SIZE):
            if self.state.board[i].type == TileType.XANH:
                choices_ = [x for x in range(1, BOARD_SIZE + 1) if x != i]
                self.state.board[i].jump_target = random.choice(choices_)
        for p in self.state.players:
            if not p.finished and p.position != FINISH_TILE:
                self.resolve_tile(p, 1)
        return f"🌍 ĐỘNG ĐẤT! {player.name} vừa xáo tung toàn bộ bản đồ, mọi ô đều đổi loại!"

    def e_storm(self, player, choice):
        areas = ["1-25", "26-50", "51-75", "76-100"]
        if choice is None:
            return {"await": "area_choice", "options": areas}
        area = choice["area"]
        start = {"1-25": 1, "26-50": 26, "51-75": 51, "76-100": 76}[area]
        end = start + 24
        seg = list(range(start, end + 1))
        types = [self.state.board[i].type for i in seg]
        types.reverse()
        for offset, i in enumerate(seg):
            self.state.board[i].type = types[offset]
            self.state.board[i].jump_target = None
        for i in seg:
            if self.state.board[i].type == TileType.XANH:
                choices_ = [x for x in range(1, BOARD_SIZE + 1) if x != i]
                self.state.board[i].jump_target = random.choice(choices_)
        for p in self.state.players:
            if not p.finished and p.position in seg:
                self.resolve_tile(p, 1)
        return f"🌪️ Bão tố của {player.name} đảo ngược toàn bộ khu vực {area}!"

    def e_time_witch(self, player, choice):
        if len(self.state.reserve_pool) < 5:
            return f"{player.name} rút Phù Thuỷ Thời Gian nhưng kho dự trữ đã cạn."
        if choice is None:
            valid = [i for i in range(2, BOARD_SIZE)]
            return {"await": "five_tile_choice", "options": valid}
        tiles = choice["tiles"]
        if len(set(tiles)) != 5:
            raise GameError("Cần chọn đúng 5 ô khác nhau.")
        random.shuffle(self.state.reserve_pool)
        for idx in tiles:
            new_tile = self.state.reserve_pool.pop(0)
            old_tile = self.state.board[idx]
            self.state.reserve_pool.append(old_tile)
            new_tile.index = idx
            new_tile.jump_target = None
            if new_tile.type == TileType.XANH:
                choices_ = [x for x in range(1, BOARD_SIZE + 1) if x != idx]
                new_tile.jump_target = random.choice(choices_)
            self.state.board[idx] = new_tile
        for p in self.state.players:
            if not p.finished and p.position in tiles:
                self.resolve_tile(p, 1)
        return f"⏳ Phù Thuỷ Thời Gian của {player.name} thay hình đổi dạng 5 ô: {tiles}!"

    def e_tornado(self, player, choice):
        if choice is None:
            return {"await": "two_tile_choice", "options": list(range(2, BOARD_SIZE))}
        a, b = choice["tile_a"], choice["tile_b"]
        if a == b:
            raise GameError("Phải chọn 2 ô khác nhau.")
        ta, tb = self.state.board[a], self.state.board[b]
        ta.type, tb.type = tb.type, ta.type
        ta.jump_target, tb.jump_target = tb.jump_target, ta.jump_target
        for p in self.state.players:
            if not p.finished and p.position in (a, b):
                self.resolve_tile(p, 1)
        return f"🌀 Lốc xoáy của {player.name} hoán đổi ô {a} và ô {b}!"

    def e_blender(self, player, choice):
        roll = random.randint(1, 6)
        if roll <= 2:
            others = self._others(player)
            if len(others) >= 2:
                a, b = random.sample(others, 2)
                a.position, b.position = b.position, a.position
                return f"🥤 Máy Trộn ({roll}): {a.name} và {b.name} bị đổi chỗ ngẫu nhiên!"
            return f"🥤 Máy Trộn ({roll}) không đủ người để đổi chỗ."
        elif roll <= 4:
            self.state.players.reverse()
            for i, p in enumerate(self.state.players):
                if p.id == player.id:
                    self.state.current_player_index = i
            return f"🥤 Máy Trộn ({roll}): đảo ngược toàn bộ thứ tự chơi!"
        else:
            msgs = []
            for p in self.state.players:
                if p.finished:
                    continue
                d = random.randint(1, 6)
                self.move_player_raw(p, d)
                msgs.append(f"{p.name}+{d}")
            for p in self.state.players:
                if not p.finished:
                    self.resolve_tile(p, 1)
            return f"🥤 Máy Trộn ({roll}): mọi người bị thổi bay ngẫu nhiên ({', '.join(msgs)})!"

    # ------------------ TRAP EFFECTS (12 lá) ------------------
    def _blockable(self, player):
        if self._has_status(player, "immune_negative"):
            self._log(f"✨ {player.name} miễn nhiễm nhờ Cứu Trợ, lá Bẫy vô hiệu.")
            return True
        if self._consume_shield(player):
            self._log(f"🛡️ {player.name} giơ Lá Chắn, chặn đứng lá Bẫy!")
            return True
        return False

    def t_deathpit(self, player, choice):
        if self._blockable(player):
            return None
        self.move_player_raw(player, -5)
        self.try_pay(player, min(2, player.gold), to_fund=True)
        self.resolve_tile(player, 1)
        return f"☠️ Hố Tử Thần nuốt {player.name}: lùi 5 ô, mất 2 vàng."

    def t_poison(self, player, choice):
        if self._blockable(player):
            return None
        player.skip_next_turn = True
        self.try_pay(player, min(3, player.gold), to_fund=True)
        return f"🍄 Nấm Độc khiến {player.name} mất lượt và mất 3 vàng."

    def t_lava(self, player, choice):
        if self._blockable(player):
            return None
        d = random.randint(1, 6)
        self.move_player_raw(player, d)
        tile = self._tile(player.position)
        msg = f"🌋 Hồ Dung Nham: {player.name} tiến {d} ô."
        if tile.type == TileType.DO:
            self.try_pay(player, min(6, player.gold), to_fund=True)
            msg += " Xui xẻo rơi đúng Ô Đỏ, mất gấp đôi (6 vàng)!"
        self.resolve_tile(player, 1)
        return msg

    def t_meteor(self, player, choice):
        if self._blockable(player):
            return None
        affected = []
        for p in self.state.players:
            if p.id != player.id and not p.finished and abs(p.position - player.position) <= 5:
                self.move_player_raw(p, -2)
                affected.append(p.name)
        if affected:
            return f"☄️ Sao Băng rơi trúng {', '.join(affected)}, tất cả lùi 2 ô!"
        return "☄️ Sao Băng rơi xuống nhưng không trúng ai."

    def t_shock(self, player, choice):
        if self._blockable(player):
            return None
        alive = [p for p in self.state.players if not p.finished]
        lowest = min(alive, key=lambda p: p.position)
        if lowest.id == player.id:
            return f"⚡ {player.name} đã là người thấp nhất rồi, Điện Giật vô tác dụng."
        player.position, lowest.position = lowest.position, player.position
        return f"⚡ Điện Giật hoán đổi {player.name} với {lowest.name} (người thấp nhất)!"

    def t_gold_rain(self, player, choice):
        if self._blockable(player):
            return None
        lo, hi = max(1, player.position - 10), min(BOARD_SIZE, player.position + 10)
        pool = [i for i in range(lo, hi + 1) if i != player.position]
        random.shuffle(pool)
        picked = pool[:5]
        collected_msgs = []
        for tile_idx in picked:
            standee = next((p for p in self.state.players if p.position == tile_idx and not p.finished), None)
            if standee:
                self.add_gold(standee, 1)
                collected_msgs.append(f"{standee.name}(+1 tại ô {tile_idx})")
            else:
                self.state.common_fund += 1
        extra = f" ({'; '.join(collected_msgs)})" if collected_msgs else " (không ai đứng trúng, vàng rơi vào Quỹ chung)"
        return f"🌧️ Mưa Vàng rải khắp ô {picked}{extra}."

    def t_quicksand(self, player, choice):
        if self._blockable(player):
            return None
        self.try_pay(player, min(2, player.gold), to_fund=True)
        self.move_player_raw(player, -2)
        self.resolve_tile(player, 1)
        return f"🏜️ Cát Lún kéo {player.name} lùi 2 ô và mất 2 vàng."

    def t_sandstorm(self, player, choice):
        if self._blockable(player):
            return None
        for o in self._others(player):
            self.try_pay(o, min(2, o.gold), to_fund=True)
        return f"🏜️ Bão Cát của {player.name} cuốn 2 vàng của mỗi người khác vào Quỹ chung."

    def t_carnivorous_plant(self, player, choice):
        if self._blockable(player):
            return None
        if self.try_pay(player, 4, to_fund=True):
            return f"🌱 Cây Ăn Thịt cắn {player.name} mất 4 vàng."
        self.move_player_raw(player, -6)
        self.resolve_tile(player, 1)
        return f"🌱 {player.name} không đủ vàng nuôi Cây Ăn Thịt, bị nhai lùi 6 ô!"

    def t_underground(self, player, choice):
        if self._blockable(player):
            return None
        d = random.randint(1, 6)
        if d % 2 == 0:
            self.move_player_raw(player, 4)
            msg = f"🕳️ Hầm Ngầm ({d} - chẵn): {player.name} tiến 4 ô!"
        else:
            self.move_player_raw(player, -4)
            msg = f"🕳️ Hầm Ngầm ({d} - lẻ): {player.name} lùi 4 ô!"
        self.resolve_tile(player, 1)
        return msg

    def t_crack(self, player, choice):
        if self._blockable(player):
            return None
        others = self._others(player)
        if not others:
            return f"{player.name} không tìm được ai để cùng lùi."
        if choice is None:
            return {"await": "single_target", "options": [o.id for o in others]}
        target = self._player(choice["target_id"])
        self.move_player_raw(player, -3)
        self.move_player_raw(target, -3)
        self.resolve_tile(player, 1)
        self.resolve_tile(target, 1)
        return f"💥 Vết Nứt xé toạc mặt đất: cả {player.name} và {target.name} cùng lùi 3 ô!"

    def t_fake_treasure(self, player, choice):
        if self._blockable(player):
            return None
        player.skip_next_turn = True
        self.try_pay(player, min(5, player.gold), to_fund=True)
        return f"🎁 Kho Báu Giả lừa {player.name} mất lượt và mất 5 vàng."

    # ------------------------------------------------------------------
    # VẬT PHẨM
    # ------------------------------------------------------------------
    def buy_item(self, player_id, item_type_str):
        self._require_started()
        player = self._current()
        if player.id != player_id:
            raise GameError("Chưa đến lượt của bạn.")
        if not self.state.pending_shop_tile:
            raise GameError("Bạn không đang đứng ở ô cửa hàng (20/50/80).")
        try:
            item_type = ItemType(item_type_str)
        except ValueError:
            raise GameError("Vật phẩm không hợp lệ.")
        info = ITEM_INFO[item_type]
        if self.state.item_stock.get(item_type, 0) <= 0:
            raise GameError(f"{info['name']} đã hết hàng.")
        if len(player.items) >= MAX_ITEMS_CARRIED:
            raise GameError("Bạn đang cầm tối đa 2 vật phẩm, hãy dùng bớt trước khi mua thêm.")
        if player.gold < info["price"]:
            raise GameError("Không đủ vàng.")
        player.gold -= info["price"]
        self.state.item_stock[item_type] -= 1
        player.items.append(item_type)
        self._log(f"🛍️ {player.name} mua {info['emoji']} {info['name']} với giá {info['price']} vàng.")
        return self.state

    def use_item(self, player_id, item_type_str, target_id=None, delta=None):
        self._require_started()
        player = self._current()
        if player.id != player_id:
            raise GameError("Chưa đến lượt của bạn.")
        try:
            item_type = ItemType(item_type_str)
        except ValueError:
            raise GameError("Vật phẩm không hợp lệ.")
        if item_type not in player.items:
            raise GameError("Bạn không sở hữu vật phẩm này.")

        info = ITEM_INFO[item_type]

        if item_type == ItemType.LA_CHAN:
            player.statuses.append(StatusEffect(kind="shield", turns_left=99))
            msg = f"🛡️ {player.name} giơ cao {info['name']}, sẵn sàng chặn đòn xấu tiếp theo!"

        elif item_type == ItemType.DAO_GAM:
            if target_id is None:
                raise GameError("Cần chọn mục tiêu cho Dao Găm.")
            target = self._player(target_id)
            if target.id == player.id:
                raise GameError("Không thể tự đâm chính mình.")
            if abs(target.position - player.position) > 3:
                raise GameError("Mục tiêu phải trong bán kính 3 ô.")
            self.move_player_raw(target, -4)
            msg = f"🔪 {player.name} phóng {info['name']} trúng {target.name}, đá lùi 4 ô!"

        elif item_type == ItemType.BUA_HO_MENH:
            player.pending_double_action = True
            msg = f"🪆 {player.name} triệu hồi {info['name']}: lượt này được tung xúc xắc 2 lần!"

        elif item_type == ItemType.XUC_XAC_X2:
            player.pending_double_roll = True
            msg = f"🎲 {player.name} chuẩn bị {info['name']}: lượt tới tung 2 lần lấy điểm cao hơn!"

        elif item_type == ItemType.KINH_AP_TRONG:
            if delta not in (1, -1):
                raise GameError("Cần chọn delta = +1 hoặc -1 cho Kính Áp Tròng.")
            player.pending_lens_delta = delta
            sign = "+1" if delta == 1 else "-1"
            msg = f"👁️ {player.name} đeo {info['name']}: lượt tới xúc xắc sẽ {sign}."
        else:
            raise GameError("Vật phẩm chưa được hỗ trợ.")

        player.items.remove(item_type)
        self.state.item_stock[item_type] = self.state.item_stock.get(item_type, 0) + 1
        self._log(msg)
        return self.state

    # ------------------------------------------------------------------
    # KẾT THÚC VÁN
    # ------------------------------------------------------------------
    def _finish_game(self, winner):
        winner.finished = True
        winner.finish_rank = 1
        self.add_gold(winner, self.state.common_fund)
        self._log(f"👑 {winner.name} về đích đầu tiên và ẵm trọn {self.state.common_fund} vàng trong Quỹ chung!")
        self.state.common_fund = 0
        self.state.game_over = True
        self.state.winner_id = winner.id
        self.state.pending_action = None
        self.state.pending_shop_tile = False

    def _check_timeout(self):
        if self.state.game_over:
            return
        elapsed = time.time() - self.state.started_at
        if elapsed >= GAME_TIME_LIMIT_SECONDS:
            self._finish_by_timeout()

    def _finish_by_timeout(self):
        alive = [p for p in self.state.players if not p.finished]
        if not alive:
            return
        best = max(alive, key=lambda p: (p.position, p.gold, len(p.items), random.random()))
        best.finish_rank = 1
        self.add_gold(best, self.state.common_fund)
        self._log(f"⏰ Hết giờ 45 phút! {best.name} ở xa nhất (ô {best.position}) chiến thắng và ẵm Quỹ chung!")
        self.state.common_fund = 0
        self.state.game_over = True
        self.state.winner_id = best.id
        self.state.pending_action = None
        self.state.pending_shop_tile = False

    def get_state(self):
        self._require_started()
        self._check_timeout()
        d = self.state.to_dict()
        d["time_limit_seconds"] = GAME_TIME_LIMIT_SECONDS
        d["shop_tiles"] = list(SHOP_TILES)
        d["item_info"] = {k.value: v for k, v in ITEM_INFO.items()}
        return d
