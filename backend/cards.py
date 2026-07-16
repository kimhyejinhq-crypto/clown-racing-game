# -*- coding: utf-8 -*-
"""
cards.py
========
Nội dung các lá bài Sự kiện (29 lá) và Bẫy (12 lá).
Mỗi lá là một dict với các trường:
- id: định danh duy nhất (dùng để lưu vết)
- name: tên hiển thị
- text: mô tả ngắn
- effect_id: tên hàm xử lý trong GameEngine (phải khớp với tên method)
"""

EVENT_CARDS = [
    {"id": "E01", "name": "Cướp biển", "text": "Lấy 2 vàng của mỗi người khác.", "effect_id": "e_pirate"},
    {"id": "E02", "name": "Lừa đảo", "text": "Chọn 1 người, tặng họ 3 vàng và khiến họ mất lượt.", "effect_id": "e_scam"},
    {"id": "E03", "name": "Đường hầm", "text": "Chui hầm đến ô gần nhất, đá người ở đó lùi 2 ô.", "effect_id": "e_tunnel"},
    {"id": "E04", "name": "Siêu trộm", "text": "Đổi chỗ với 1 người khác.", "effect_id": "e_super_thief"},
    {"id": "E05", "name": "Phù thủy tham lam", "text": "Lấy 2 vàng của mỗi người khác.", "effect_id": "e_greedy_witch"},
    {"id": "E06", "name": "Số mệnh", "text": "Tung 2 xúc xắc: ≥8 → tiến 6 ô +5 vàng; ngược lại lùi 4 ô.", "effect_id": "e_destiny"},
    {"id": "E07", "name": "Cứu trợ", "text": "Nhận miễn nhiễm Đỏ và Cổng trong 2 lượt.", "effect_id": "e_relief"},
    {"id": "E08", "name": "Bẫy ngược", "text": "Chọn 1 ô trống để gài bẫy, ai đáp trúng phải nộp 3 vàng cho bạn.", "effect_id": "e_reverse_trap"},
    {"id": "E09", "name": "Vũ điệu", "text": "Chọn 2 người đổi chỗ cho nhau.", "effect_id": "e_dance"},
    {"id": "E10", "name": "Lời nguyền", "text": "Người nghèo nhất mất 1 vàng cho người giàu nhất.", "effect_id": "e_curse"},
    {"id": "E11", "name": "Sao chép", "text": "Chọn 1 người, sao chép vị trí hoặc vàng của họ.", "effect_id": "e_copy"},
    {"id": "E12", "name": "Lính đánh thuê", "text": "Trả 4 vàng, thuê lính giúp chịu Ô Đỏ trong 3 lượt.", "effect_id": "e_mercenary"},
    {"id": "E13", "name": "Bùa may mắn", "text": "2 lượt tới được tự chọn số xúc xắc.", "effect_id": "e_lucky_charm"},
    {"id": "E14", "name": "Ánh sáng", "text": "Tiến 6 ô.", "effect_id": "e_light_ahead"},
    {"id": "E15", "name": "Kho báu", "text": "+7 vàng.", "effect_id": "e_treasure"},
    {"id": "E16", "name": "Sóng thần", "text": "Tất cả người khác lùi 2 ô.", "effect_id": "e_tsunami"},
    {"id": "E17", "name": "Phù thủy ngủ", "text": "Mất 1 vàng và ngủ mất 1 lượt.", "effect_id": "e_sleepy_witch"},
    {"id": "E18", "name": "Tảng đá", "text": "Lùi 4 ô và mất 2 vàng.", "effect_id": "e_boulder"},
    {"id": "E19", "name": "Hướng dẫn", "text": "Chọn 1 người, giúp họ tiến 3 ô.", "effect_id": "e_guide"},
    {"id": "E20", "name": "Bão tuyết", "text": "Mỗi người khác mất 1 vàng.", "effect_id": "e_blizzard"},
    {"id": "E21", "name": "Lạc lối", "text": "Lùi 2 ô và mất 1 lượt.", "effect_id": "e_lost"},
    {"id": "E22", "name": "Thần gió", "text": "Tiến 5 ô và +2 vàng.", "effect_id": "e_wind_god"},
    {"id": "E23", "name": "Kho báu cướp biển", "text": "+8 vàng.", "effect_id": "e_pirate_treasure"},
    {"id": "E24", "name": "Nấm độc", "text": "Lùi 3 ô và mất 1 vàng.", "effect_id": "e_poison_mushroom"},
    {"id": "C1",  "name": "Động đất", "text": "Xáo tung toàn bộ bản đồ!", "effect_id": "e_earthquake"},
    {"id": "C2",  "name": "Bão tố", "text": "Đảo ngược 1 khu vực 25 ô.", "effect_id": "e_storm"},
    {"id": "C3",  "name": "Phù thủy thời gian", "text": "Thay 5 ô bằng thẻ dự trữ.", "effect_id": "e_time_witch"},
    {"id": "C4",  "name": "Lốc xoáy", "text": "Hoán đổi 2 ô bất kỳ.", "effect_id": "e_tornado"},
    {"id": "C5",  "name": "Máy trộn", "text": "Tung xúc xắc: 1-2 đổi 2 người, 3-4 đảo thứ tự chơi, 5-6 thổi bay mọi người.", "effect_id": "e_blender"},
]

TRAP_CARDS = [
    {"id": "T01", "name": "Hố tử thần", "text": "Lùi 5 ô, mất 2 vàng.", "effect_id": "t_deathpit"},
    {"id": "T02", "name": "Nấm độc", "text": "Mất lượt và mất 3 vàng.", "effect_id": "t_poison"},
    {"id": "T03", "name": "Dung nham", "text": "Tiến ngẫu nhiên 1-6 ô, nếu đáp Ô Đỏ mất 6 vàng.", "effect_id": "t_lava"},
    {"id": "T04", "name": "Sao băng", "text": "Mọi người trong bán kính 5 ô lùi 2 ô.", "effect_id": "t_meteor"},
    {"id": "T05", "name": "Điện giật", "text": "Đổi chỗ với người ở vị trí thấp nhất.", "effect_id": "t_shock"},
    {"id": "T06", "name": "Mưa vàng", "text": "Rải 5 vàng vào các ô xung quanh, ai đứng đó nhận.", "effect_id": "t_gold_rain"},
    {"id": "T07", "name": "Cát lún", "text": "Lùi 2 ô, mất 2 vàng.", "effect_id": "t_quicksand"},
    {"id": "T08", "name": "Bão cát", "text": "Mỗi người khác mất 2 vàng.", "effect_id": "t_sandstorm"},
    {"id": "T09", "name": "Cây ăn thịt", "text": "Mất 4 vàng hoặc lùi 6 ô.", "effect_id": "t_carnivorous_plant"},
    {"id": "T10", "name": "Hầm ngầm", "text": "Tung xúc xắc: chẵn tiến 4, lẻ lùi 4.", "effect_id": "t_underground"},
    {"id": "T11", "name": "Vết nứt", "text": "Chọn 1 người cùng lùi 3 ô.", "effect_id": "t_crack"},
    {"id": "T12", "name": "Kho báu giả", "text": "Mất lượt và mất 5 vàng.", "effect_id": "t_fake_treasure"},
]
