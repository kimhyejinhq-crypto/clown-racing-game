# -*- coding: utf-8 -*-
"""
constants.py
============
Toàn bộ các hằng số / enum dùng chung cho game "Pathfinders".
Tách riêng ra file này để khi cần chỉnh số lượng thẻ, giá vật phẩm,...
chỉ cần sửa một chỗ duy nhất, không phải mò trong logic game.

GHI CHÚ VỀ CÁC CHỖ LUẬT GỐC CHƯA RÕ - MÌNH ĐÃ QUYẾT ĐỊNH NHƯ SAU:
1) Bản mô tả gốc không nói rõ 150 thẻ ô chia theo tỉ lệ bao nhiêu cho mỗi màu.
   -> Mình chọn tỉ lệ ở TILE_POOL_COUNTS bên dưới (có thể chỉnh lại thoải mái).
2) Ô số 1 (xuất phát) và ô số 100 (đích) luôn được ép cứng là ô đặc biệt
   (TRONG cho ô 1, và một loại "ĐÍCH" riêng cho ô 100) để tránh xung đột
   luật (ví dụ ô 100 lại là ô Đỏ thì "về đích" nghĩa là gì?).
3) Luật gốc có 2 chỗ MÂU THUẪN nhau:
   - Bước 2 nói "nếu vượt quá ô 100 thì bật ngược lại số dư"
   - Phần "Điều kiện chiến thắng" lại nói "không cần đúng số, đến hoặc
     vượt quá 100 đều thắng".
   -> Mình chọn phương án 2 (vượt quá 100 = thắng luôn), bỏ luật bật
   ngược, vì nó đơn giản, công bằng và không mâu thuẫn với phần thắng thua.
4) Ô Xanh "nhảy đến ô được ghi sẵn trên thẻ": vì thẻ được rút ngẫu nhiên
   trong 150 tấm nên không thể in sẵn số ô cụ thể (ô đó có thể không tồn
   tại trong ván đang chơi). -> Mình để máy TỰ RANDOM một ô đích hợp lệ
   (1-100, khác ô hiện tại) ngay lúc dựng bản đồ, cố định cho cả ván.
5) "Ô Trống": nếu có người khác đứng cùng ô thì được cướp 1 vàng.
   -> Ô số 1 (xuất phát, ai cũng đứng chung lúc đầu) được loại trừ khỏi
   luật cướp này, nếu không ai cũng bị cướp ngay từ đầu ván.
6) Vật phẩm "dùng 1 lần rồi trả lại": hiểu là thẻ vật phẩm có SỐ LƯỢNG
   GIỚI HẠN (5 cái/loại). Mua xong dùng 1 lần thì thẻ được trả về kho
   chung để người khác có thể mua lại (không phải người chơi giữ mãi).
7) Ô Đỏ / Ô Cổng khi không đủ tiền: cho phép nợ âm, tự động trừ bù khi
   có tiền sau này. Để tránh vòng lặp vô hạn khi liên tục bị đá lùi vào
   ô Đỏ khác mà vẫn không đủ tiền, mình giới hạn tối đa
   MAX_CHAIN_REACTION lần xử lý dây chuyền trong một lượt.
8) Giới hạn thời gian ván đấu 45 phút được xử lý ở phía frontend
   (đồng hồ đếm ngược) + backend chỉ cần API kiểm tra "đã hết giờ chưa"
   dựa trên thời điểm bắt đầu ván.
"""

from enum import Enum


class TileType(str, Enum):
    TRONG = "TRONG"      # Ô trống - trắng
    VANG = "VANG"        # Ô vàng - +5 vàng
    DO = "DO"            # Ô đỏ - -3 vàng hoặc lùi 3 ô
    XANH = "XANH"        # Ô xanh dương - nhảy cóc
    TIM = "TIM"          # Ô tím - rút bài Sự kiện
    CAM = "CAM"          # Ô cam - rút bài Bẫy
    HONG = "HONG"        # Ô hồng - cổng, trả phí đi qua
    DICH = "DICH"        # Ô 100 - đích (ép cứng, không nằm trong 150 thẻ)


# Số lượng mỗi loại thẻ ô trong túi vải 150 thẻ (xem ghi chú (1) ở trên).
# Tổng phải = 150. Rút ngẫu nhiên 100/150 để xếp map, 50 thẻ dư làm "kho dự trữ".
TILE_POOL_COUNTS = {
    TileType.TRONG: 40,
    TileType.VANG: 25,
    TileType.DO: 25,
    TileType.XANH: 15,
    TileType.TIM: 20,
    TileType.CAM: 15,
    TileType.HONG: 10,
}

BOARD_SIZE = 100          # Bản đồ 1 -> 100
TILES_TO_DRAW = 100        # số thẻ rút ra để xếp map mỗi ván
START_TILE = 1
FINISH_TILE = 100
SHOP_TILES = (20, 50, 80)  # các mốc được mua vật phẩm (chỉ khi ĐÁP ĐÚNG)

START_GOLD = 10
MAX_ITEMS_CARRIED = 2
MAX_CHAIN_REACTION = 10     # chặn vòng lặp vô hạn (ghi chú 7)

GAME_TIME_LIMIT_SECONDS = 45 * 60   # 45 phút


class ItemType(str, Enum):
    XUC_XAC_X2 = "XUC_XAC_X2"
    LA_CHAN = "LA_CHAN"
    DAO_GAM = "DAO_GAM"
    BUA_HO_MENH = "BUA_HO_MENH"
    KINH_AP_TRONG = "KINH_AP_TRONG"


ITEM_INFO = {
    ItemType.XUC_XAC_X2: {
        "name": "Xúc Xắc Của Gã Hề Song Sinh",
        "price": 7,
        "stock": 5,
        "desc": "Lượt tới tung 2 lần, lấy kết quả cao hơn.",
        "emoji": "🎲",
    },
    ItemType.LA_CHAN: {
        "name": "Lá Chắn Mặt Nạ Vỡ",
        "price": 5,
        "stock": 5,
        "desc": "Chặn 1 hiệu ứng xấu (Đỏ / Bẫy / Sự kiện xấu).",
        "emoji": "🛡️",
    },
    ItemType.DAO_GAM: {
        "name": "Dao Găm Nụ Cười",
        "price": 8,
        "stock": 5,
        "desc": "Đá lùi 4 ô 1 người trong bán kính 3 ô.",
        "emoji": "🔪",
    },
    ItemType.BUA_HO_MENH: {
        "name": "Bùa Hộ Mệnh Con Rối",
        "price": 10,
        "stock": 5,
        "desc": "Được tung xúc xắc & di chuyển 2 lần trong 1 lượt.",
        "emoji": "🪆",
    },
    ItemType.KINH_AP_TRONG: {
        "name": "Kính Áp Tròng Ba Mắt",
        "price": 6,
        "stock": 5,
        "desc": "Sau khi tung xúc xắc, +-1 điểm tuỳ chọn.",
        "emoji": "👁️",
    },
}
