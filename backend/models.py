# -*- coding: utf-8 -*-
"""
models.py
=========
Các cấu trúc dữ liệu thuần tuý (không chứa luật chơi) mô tả trạng thái ván
game. Toàn bộ logic "khi nào thì làm gì" nằm ở game_engine.py - file này
chỉ định nghĩa HÌNH DẠNG dữ liệu, giúp code dễ đọc và dễ test.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import time

from .constants import TileType, ItemType


@dataclass
class Tile:
    """Một ô trên bản đồ 1..100."""
    index: int
    type: TileType
    # Chỉ Ô XANH mới dùng: ô đích khi nhảy cóc
    jump_target: Optional[int] = None

    def to_dict(self):
        return {
            "index": self.index,
            "type": self.type.value,
            "jump_target": self.jump_target,
        }


@dataclass
class StatusEffect:
    """
    Hiệu ứng "còn hiệu lực trong N lượt tới" gắn trên người chơi.
    Dùng chung cho nhiều hiệu ứng bài Sự kiện (miễn nhiễm, bùa may mắn,
    lính đánh thuê...) thay vì viết field riêng cho từng cái.
    """
    kind: str                 # ví dụ: "immune_negative", "lucky_charm", "mercenary"
    turns_left: int
    data: dict = field(default_factory=dict)

    def to_dict(self):
        return {"kind": self.kind, "turns_left": self.turns_left, "data": self.data}


@dataclass
class Player:
    id: int
    name: str
    color: str                 # "Đỏ" / "Xanh" / "Vàng" / "Tím"
    position: int = 1
    gold: int = 10
    debt: int = 0               # nợ do không đủ tiền qua Cổng / Đỏ
    items: list = field(default_factory=list)     # list[ItemType]
    statuses: list = field(default_factory=list)  # list[StatusEffect]
    skip_next_turn: bool = False
    finished: bool = False
    finish_rank: Optional[int] = None

    # Các trạng thái tạm cho lượt chơi (được reset sau mỗi hành động)
    pending_double_action: bool = False
    pending_double_roll: bool = False
    pending_lens_delta: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "position": self.position,
            "gold": self.gold,
            "debt": self.debt,
            "items": [i.value for i in self.items],
            "statuses": [s.to_dict() for s in self.statuses],
            "skip_next_turn": self.skip_next_turn,
            "finished": self.finished,
            "finish_rank": self.finish_rank,
        }


@dataclass
class GameState:
    players: list = field(default_factory=list)         # list[Player]
    board: list = field(default_factory=list)            # list[Tile], index 0 unused, 1..100
    reserve_pool: list = field(default_factory=list)      # list[Tile] - 50 thẻ dự trữ (dùng cho C3)
    event_deck: list = field(default_factory=list)        # list[dict] xáo sẵn
    trap_deck: list = field(default_factory=list)
    item_stock: dict = field(default_factory=dict)        # {ItemType: số lượng còn lại}
    common_fund: int = 0
    current_player_index: int = 0
    turn_count: int = 0
    started_at: float = field(default_factory=time.time)
    game_over: bool = False
    winner_id: Optional[int] = None
    log: list = field(default_factory=list)               # list[str] - nhật ký hiển thị cho người chơi

    pending_shop_tile: bool = False   # cờ báo frontend: người chơi vừa dừng đúng ô có shop
    pending_action: Optional[dict] = None  # đang chờ người chơi chọn

    # Dùng cho bẫy ngược (reverse trap) – lưu ô nào do ai đặt
    reverse_trap_tiles: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "players": [p.to_dict() for p in self.players],
            "board": [t.to_dict() for t in self.board[1:]],  # bỏ phần tử rác index 0
            "common_fund": self.common_fund,
            "current_player_index": self.current_player_index,
            "turn_count": self.turn_count,
            "started_at": self.started_at,
            "game_over": self.game_over,
            "winner_id": self.winner_id,
            "log": self.log[-40:],   # chỉ trả về 40 dòng log gần nhất cho gọn
            "pending_shop_tile": self.pending_shop_tile,
            "pending_action": self.pending_action,
            "item_stock": {k.value: v for k, v in self.item_stock.items()},
            "reserve_count": len(self.reserve_pool),
            "event_deck_count": len(self.event_deck),
            "trap_deck_count": len(self.trap_deck),
        }
