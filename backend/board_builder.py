# -*- coding: utf-8 -*-
"""
board_builder.py
================
Chịu trách nhiệm DUY NHẤT: tạo ra bản đồ ngẫu nhiên lúc bắt đầu ván
(tương đương bước "rút 100/150 thẻ ô, xếp map" trong luật gốc).

Không chứa luật xử lý khi người chơi đáp vào ô - việc đó thuộc về
game_engine.py.
"""

import random
from .constants import TileType, TILE_POOL_COUNTS, TILES_TO_DRAW, BOARD_SIZE, START_TILE, FINISH_TILE
from .models import Tile


def _build_tile_pool():
    """Tạo túi vải 150 thẻ theo tỉ lệ TILE_POOL_COUNTS."""
    pool = []
    for tile_type, count in TILE_POOL_COUNTS.items():
        pool.extend([tile_type] * count)
    random.shuffle(pool)
    return pool


def build_board():
    """
    Trả về (board, reserve_pool):
      - board: list độ dài 101 (index 0 bỏ trống cho dễ tính toán 1..100)
      - reserve_pool: 50 thẻ Tile dư ra, dùng cho lá Sự kiện C3 "Phù thủy thời gian"

    Ô số 1 luôn là TRONG (xuất phát), ô số 100 luôn là DICH (đích) -
    xem constants.py ghi chú (2).
    """
    pool = _build_tile_pool()

    drawn_types = pool[:TILES_TO_DRAW]      # 100 thẻ dùng để xếp map
    reserve_types = pool[TILES_TO_DRAW:]    # 50 thẻ dư, làm kho dự trữ

    board = [None] * (BOARD_SIZE + 1)  # index 0 không dùng
    for i in range(1, BOARD_SIZE + 1):
        t_type = drawn_types[i - 1]
        board[i] = Tile(index=i, type=t_type)

    # Ép cứng ô xuất phát & ô đích (ghi chú 2)
    board[START_TILE] = Tile(index=START_TILE, type=TileType.TRONG)
    board[FINISH_TILE] = Tile(index=FINISH_TILE, type=TileType.DICH)

    # Gán đích nhảy cóc ngẫu nhiên cho mọi ô Xanh (ghi chú 4)
    for i in range(1, BOARD_SIZE + 1):
        if board[i].type == TileType.XANH:
            choices = [x for x in range(1, BOARD_SIZE + 1) if x != i]
            board[i].jump_target = random.choice(choices)

    reserve_pool = [Tile(index=-1, type=t) for t in reserve_types]

    return board, reserve_pool
