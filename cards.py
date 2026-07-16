# -*- coding: utf-8 -*-
"""
cards.py
========
Dữ liệu THUẦN TUÝ của 29 lá Sự kiện + 12 lá Bẫy. Mỗi lá có một
"effect_id" trỏ tới hàm xử lý tương ứng được định nghĩa trong
game_engine.py (phần EVENT_EFFECTS / TRAP_EFFECTS).

Tách dữ liệu ra khỏi logic giúp:
  - Dễ đọc / dễ chỉnh sửa câu chữ, số liệu mà không đụng vào code xử lý.
  - Dễ thêm bớt lá bài sau này.
"""

EVENT_CARDS = [
    {"id": "E1", "name": "Cướp biển", "text": "Lấy 2 vàng từ mỗi người chơi khác.", "effect_id": "e_pirate"},
    {"id": "E2", "name": "Lừa đảo", "text": "Đưa 3 vàng cho 1 người chơi bất kỳ. Người đó mất lượt tới.", "effect_id": "e_scam"},
    {"id": "E3", "name": "Đường hầm", "text": "Tiến đến ô gần nhất có người chơi khác. Nếu vượt qua họ, họ lùi 2 ô.", "effect_id": "e_tunnel"},
    {"id": "E4", "name": "Siêu trộm", "text": "Chọn 1 người chơi: đổi vị trí với họ ngay.", "effect_id": "e_super_thief"},
    {"id": "E5", "name": "Phù thủy tham lam", "text": "Tất cả người khác mất 2 vàng cho bạn.", "effect_id": "e_greedy_witch"},
    {"id": "E6", "name": "Số mệnh", "text": "Tung 2D6. Nếu tổng ≥ 8: tiến 6 ô, +5 vàng. Nếu < 8: lùi 4 ô.", "effect_id": "e_destiny"},
    {"id": "E7", "name": "Cứu trợ", "text": "Miễn nhiễm Ô Đỏ và Ô Cổng trong 2 lượt tới.", "effect_id": "e_relief"},
    {"id": "E8", "name": "Bẫy ngược", "text": "Đặt 1 lá Bẫy lên 1 ô trống bất kỳ (trừ ô 1). Ai đáp trúng mất 3 vàng cho bạn.", "effect_id": "e_reverse_trap"},
    {"id": "E9", "name": "Khiêu vũ", "text": "Chọn 2 người chơi bất kỳ, đổi chỗ cho nhau.", "effect_id": "e_dance"},
    {"id": "E10", "name": "Nguyền rủa", "text": "Người ít vàng nhất đưa 1 vàng cho người nhiều vàng nhất.", "effect_id": "e_curse"},
    {"id": "E11", "name": "Sao chép", "text": "Copy vị trí HOẶC số vàng của 1 người chơi bất kỳ.", "effect_id": "e_copy"},
    {"id": "E12", "name": "Lính đánh thuê", "text": "Trả 4 vàng. Trong 3 lượt tới, khi đáp Ô Đỏ, chuyển tiền mất sang người khác.", "effect_id": "e_mercenary"},
    {"id": "E13", "name": "Bùa may mắn", "text": "2 lượt tới, thay vì tung xúc xắc, tự chọn số 1-6.", "effect_id": "e_lucky_charm"},
    {"id": "E14", "name": "Ánh sáng cuối đường hầm", "text": "Tiến thêm 6 ô.", "effect_id": "e_light_ahead"},
    {"id": "E15", "name": "Kho báu", "text": "Nhận 7 vàng.", "effect_id": "e_treasure"},
    {"id": "E16", "name": "Sóng thần", "text": "Tất cả người khác lùi 2 ô.", "effect_id": "e_tsunami"},
    {"id": "E17", "name": "Phù thủy ngủ", "text": "Mất 1 vàng và mất 1 lượt.", "effect_id": "e_sleepy_witch"},
    {"id": "E18", "name": "Đá tảng", "text": "Lùi 4 ô và mất 2 vàng vào Quỹ chung.", "effect_id": "e_boulder"},
    {"id": "E19", "name": "Hướng dẫn viên", "text": "Chọn 1 người khác: họ tiến thêm 3 ô.", "effect_id": "e_guide"},
    {"id": "E20", "name": "Cơn bão tuyết", "text": "Tất cả người khác mất 1 vàng vào Quỹ chung.", "effect_id": "e_blizzard"},
    {"id": "E21", "name": "Mất phương hướng", "text": "Lùi 2 ô và mất 1 lượt.", "effect_id": "e_lost"},
    {"id": "E22", "name": "Thần gió", "text": "Tiến thêm 5 ô và nhận 2 vàng.", "effect_id": "e_wind_god"},
    {"id": "E23", "name": "Kho báu cướp biển", "text": "Nhận 8 vàng.", "effect_id": "e_pirate_treasure"},
    {"id": "E24", "name": "Nấm độc", "text": "Lùi 3 ô và mất 1 vàng vào Quỹ chung.", "effect_id": "e_poison_mushroom"},
    # Nhóm C: 5 lá thay đổi map - "troll cực mạnh"
    {"id": "C1", "name": "Động đất", "text": "Xáo trộn toàn bộ 100 ô trên map. Mọi người bị áp dụng ô mới ngay.", "effect_id": "e_earthquake", "map_changer": True},
    {"id": "C2", "name": "Bão tố", "text": "Đảo ngược thứ tự 1 khu vực 25 ô (1-25 / 26-50 / 51-75 / 76-100).", "effect_id": "e_storm", "map_changer": True},
    {"id": "C3", "name": "Phù thủy thời gian", "text": "Rút 5 thẻ từ kho dự trữ, thay 5 ô bất kỳ trên map.", "effect_id": "e_time_witch", "map_changer": True},
    {"id": "C4", "name": "Lốc xoáy", "text": "Chọn 2 ô bất kỳ, đổi loại ô cho nhau.", "effect_id": "e_tornado", "map_changer": True},
    {"id": "C5", "name": "Máy trộn", "text": "Tung 1D6 và làm theo hiệu ứng tương ứng (đổi chỗ / đảo thứ tự / di chuyển ngẫu nhiên).", "effect_id": "e_blender", "map_changer": True},
]

TRAP_CARDS = [
    {"id": "T1", "name": "Hố tử thần", "text": "Lùi 5 ô và mất 2 vàng vào Quỹ chung.", "effect_id": "t_deathpit"},
    {"id": "T2", "name": "Nấm độc", "text": "Mất 1 lượt và mất 3 vàng vào Quỹ chung.", "effect_id": "t_poison"},
    {"id": "T3", "name": "Hồ dung nham", "text": "Tung 1D6, tiến số ô đó. Nếu rơi vào Ô Đỏ, mất gấp đôi tiền.", "effect_id": "t_lava"},
    {"id": "T4", "name": "Sao băng", "text": "Mọi người trong bán kính 5 ô quanh bạn bị lùi 2 ô.", "effect_id": "t_meteor"},
    {"id": "T5", "name": "Điện giật", "text": "Đổi vị trí với người đứng thấp nhất trên bản đồ.", "effect_id": "t_shock"},
    {"id": "T6", "name": "Mưa vàng", "text": "Rải 5 vàng ra 5 ô xung quanh (trong vòng 10 ô). Ai đáp trúng thì nhặt được.", "effect_id": "t_gold_rain"},
    {"id": "T7", "name": "Cát lún", "text": "Mất 2 vàng và lùi 2 ô.", "effect_id": "t_quicksand"},
    {"id": "T8", "name": "Bão cát", "text": "Tất cả người khác mất 2 vàng vào Quỹ chung.", "effect_id": "t_sandstorm"},
    {"id": "T9", "name": "Cây ăn thịt", "text": "Mất 4 vàng. Nếu không đủ, lùi 6 ô.", "effect_id": "t_carnivorous_plant"},
    {"id": "T10", "name": "Hầm ngầm", "text": "Tung 1D6. Chẵn: tiến 4 ô. Lẻ: lùi 4 ô.", "effect_id": "t_underground"},
    {"id": "T11", "name": "Vết nứt", "text": "Chọn 1 người khác: cả hai cùng lùi 3 ô.", "effect_id": "t_crack"},
    {"id": "T12", "name": "Kho báu giả", "text": "Mất 1 lượt và mất 5 vàng vào Quỹ chung.", "effect_id": "t_fake_treasure"},
]
