// =====================================================================
// script.js
// =========
// Toàn bộ logic PHÍA CLIENT. File này KHÔNG chứa luật chơi (luật nằm ở
// backend/game_engine.py) - nó chỉ gọi API, nhận state mới nhất, và
// vẽ lại giao diện. Nguyên tắc: state luôn là "nguồn sự thật" trả về
// từ server, client không tự tính toán số liệu.
// =====================================================================

const API = {
  async post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || "Có lỗi xảy ra.");
    return data.state;
  },
  async get(url) {
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) throw new Error(data.error || "Có lỗi xảy ra.");
    return data.state;
  },
};

// ---------------------------------------------------------------------
// STATE CỤC BỘ
// ---------------------------------------------------------------------
let latestState = null;
let playerCount = 2;
let timerInterval = null;

const TYPE_LABEL = {
  TRONG: "•", VANG: "$", DO: "X", XANH: "»", TIM: "?", CAM: "!", HONG: "Π", DICH: "🏁",
};

// ---------------------------------------------------------------------
// MÀN HÌNH SETUP
// ---------------------------------------------------------------------
function renderPlayerInputs() {
  const wrap = document.getElementById("player-inputs");
  wrap.innerHTML = "";
  for (let i = 0; i < playerCount; i++) {
    const input = document.createElement("input");
    input.placeholder = `Tên chú hề #${i + 1}`;
    input.id = `player-name-${i}`;
    wrap.appendChild(input);
  }
}

document.getElementById("btn-add-player").addEventListener("click", () => {
  if (playerCount < 4) { playerCount++; renderPlayerInputs(); }
});
document.getElementById("btn-remove-player").addEventListener("click", () => {
  if (playerCount > 2) { playerCount--; renderPlayerInputs(); }
});

document.getElementById("btn-start-game").addEventListener("click", async () => {
  const names = [];
  for (let i = 0; i < playerCount; i++) {
    names.push(document.getElementById(`player-name-${i}`).value || `Chú Hề ${i + 1}`);
  }
  try {
    const state = await API.post("/api/new_game", { names });
    onStateUpdated(state);
    document.getElementById("screen-setup").classList.add("hidden");
    document.getElementById("screen-game").classList.remove("hidden");
    startTimerLoop();
  } catch (e) {
    document.getElementById("setup-error").textContent = e.message;
  }
});

renderPlayerInputs();

// ---------------------------------------------------------------------
// VẼ LẠI TOÀN BỘ GIAO DIỆN TỪ STATE MỚI NHẤT
// ---------------------------------------------------------------------
function onStateUpdated(state) {
  latestState = state;
  renderBoard(state);
  renderPlayers(state);
  renderLog(state);
  renderTopbarStats(state);
  renderPendingModal(state);
  renderShopModal(state);
  renderEndModal(state);
  renderRollButtonState(state);
}

function renderTopbarStats(state) {
  document.getElementById("stat-fund").textContent = state.common_fund;
  document.getElementById("stat-turn").textContent = state.turn_count;
}

function startTimerLoop() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    if (!latestState || latestState.game_over) return;
    const elapsed = Date.now() / 1000 - latestState.started_at;
    const remain = Math.max(0, latestState.time_limit_seconds - elapsed);
    const m = Math.floor(remain / 60).toString().padStart(2, "0");
    const s = Math.floor(remain % 60).toString().padStart(2, "0");
    document.getElementById("stat-timer").textContent = `${m}:${s}`;
    if (remain <= 0) refreshState();
  }, 1000);
}

async function refreshState() {
  const state = await API.get("/api/state");
  onStateUpdated(state);
}

// ---------------------------------------------------------------------
// BOARD (100 ô, snake layout 10x10)
// ---------------------------------------------------------------------
function renderBoard(state) {
  const board = document.getElementById("board");
  board.innerHTML = "";

  const grid = [];
  for (let row = 9; row >= 0; row--) {
    const rowStart = row * 10 + 1;
    let nums = Array.from({ length: 10 }, (_, i) => rowStart + i);
    if (row % 2 === 1) nums = nums.reverse();
    grid.push(...nums);
  }

  const tilesByIndex = {};
  state.board.forEach((t) => (tilesByIndex[t.index] = t));

  const playersByPos = {};
  state.players.forEach((p) => {
    if (!p.finished) {
      playersByPos[p.position] = playersByPos[p.position] || [];
      playersByPos[p.position].push(p);
    }
  });

  const colorEmoji = { "Đỏ": "🔴", "Xanh": "🔵", "Vàng": "🟡", "Tím": "🟣" };

  grid.forEach((num) => {
    const tile = tilesByIndex[num];
    const div = document.createElement("div");
    div.className = `tile tile-${tile.type}`;
    const label = document.createElement("span");
    label.textContent = num;
    div.appendChild(label);

    const tokWrap = document.createElement("div");
    tokWrap.className = "tile-tokens";
    (playersByPos[num] || []).forEach((p) => {
      const t = document.createElement("span");
      t.className = "tok";
      t.title = p.name;
      t.textContent = "🤡";
      t.style.filter = `hue-rotate(${p.id * 70}deg)`;
      tokWrap.appendChild(t);
    });
    div.appendChild(tokWrap);
    board.appendChild(div);
  });
}

// ---------------------------------------------------------------------
// BẢNG NGƯỜI CHƠI
// ---------------------------------------------------------------------
function renderPlayers(state) {
  const panel = document.getElementById("players-panel");
  panel.innerHTML = "<h3 style='margin-top:0;color:var(--text-dim);font-size:1rem;'>🎭 Người chơi</h3>";
  const colorHex = { "Đỏ": "#CE4A4A", "Xanh": "#66C7F4", "Vàng": "#FFB8E3", "Tím": "#6C6EA0" };

  state.players.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "player-card";
    if (idx === state.current_player_index && !state.game_over) card.classList.add("active");
    if (p.finished) card.classList.add("finished");

    const itemsText = p.items.length
      ? p.items.map((i) => state.item_info[i].emoji).join(" ")
      : "—";
    const debtText = p.debt > 0 ? ` (nợ ${p.debt})` : "";

    card.innerHTML = `
      <div class="p-name"><span class="player-dot" style="background:${colorHex[p.color]}"></span>${p.name}${p.finished ? " 🏆" : ""}</div>
      <div class="p-row"><span>Ô</span><span>${p.position}</span></div>
      <div class="p-row"><span>Vàng</span><span>${p.gold}${debtText}</span></div>
      <div class="p-row"><span>Vật phẩm</span><span>${itemsText}</span></div>
    `;

    if (idx === state.current_player_index && !state.game_over && !state.pending_action && !state.pending_shop_tile && p.items.length) {
      const useWrap = document.createElement("div");
      useWrap.style.marginTop = "0.4rem";
      p.items.forEach((itemType) => {
        const btn = document.createElement("button");
        btn.className = "btn-ghost";
        btn.style.marginRight = "4px";
        btn.style.marginBottom = "4px";
        btn.textContent = `Dùng ${state.item_info[itemType].emoji}`;
        btn.addEventListener("click", () => handleUseItem(itemType));
        useWrap.appendChild(btn);
      });
      card.appendChild(useWrap);
    }

    panel.appendChild(card);
  });
}

// ---------------------------------------------------------------------
// NHẬT KÝ
// ---------------------------------------------------------------------
function renderLog(state) {
  const list = document.getElementById("log-list");
  list.innerHTML = "";
  [...state.log].reverse().forEach((line) => {
    const div = document.createElement("div");
    div.textContent = line;
    list.appendChild(div);
  });
}

// ---------------------------------------------------------------------
// TUNG XÚC XẮC
// ---------------------------------------------------------------------
function renderRollButtonState(state) {
  const btn = document.getElementById("btn-roll");
  const luckyPicker = document.getElementById("lucky-picker");
  const cur = state.players[state.current_player_index];

  const blocked = state.game_over || state.pending_action || state.pending_shop_tile;
  btn.disabled = blocked;

  const luckyStatus = (cur.statuses || []).find((s) => s.kind === "lucky_charm");
  if (luckyStatus && !blocked) {
    btn.classList.add("hidden");
    luckyPicker.classList.remove("hidden");
  } else {
    btn.classList.remove("hidden");
    luckyPicker.classList.add("hidden");
  }
}

document.getElementById("btn-roll").addEventListener("click", async () => {
  const cur = latestState.players[latestState.current_player_index];
  const dice = document.getElementById("dice-face");
  dice.classList.add("rolling");
  try {
    const state = await API.post("/api/roll", { player_id: cur.id });
    onStateUpdated(state);
  } catch (e) {
    alert(e.message);
  } finally {
    setTimeout(() => dice.classList.remove("rolling"), 500);
  }
});

document.querySelectorAll(".lucky-numbers button").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const cur = latestState.players[latestState.current_player_index];
    try {
      const state = await API.post("/api/roll", {
        player_id: cur.id,
        chosen_number: Number(btn.dataset.n),
      });
      onStateUpdated(state);
    } catch (e) {
      alert(e.message);
    }
  });
});

// ---------------------------------------------------------------------
// CỬA HÀNG (ô 20 / 50 / 80)
// ---------------------------------------------------------------------
function renderShopModal(state) {
  const modal = document.getElementById("modal-shop");
  if (!state.pending_shop_tile || state.game_over) {
    modal.classList.add("hidden");
    return;
  }
  modal.classList.remove("hidden");
  const cur = state.players[state.current_player_index];
  const wrap = document.getElementById("shop-items");
  wrap.innerHTML = "";

  Object.entries(state.item_info).forEach(([key, info]) => {
    const stock = state.item_stock[key];
    const div = document.createElement("div");
    div.className = "shop-item";
    const canBuy = stock > 0 && cur.gold >= info.price && cur.items.length < 2;
    div.innerHTML = `
      <div>
        <strong>${info.emoji} ${info.name}</strong> — ${info.price} vàng (còn ${stock})
        <div class="si-info">${info.desc}</div>
      </div>
    `;
    const btn = document.createElement("button");
    btn.textContent = "Mua";
    btn.disabled = !canBuy;
    btn.addEventListener("click", async () => {
      try {
        const s = await API.post("/api/buy_item", { player_id: cur.id, item_type: key });
        onStateUpdated(s);
      } catch (e) { alert(e.message); }
    });
    div.appendChild(btn);
    wrap.appendChild(div);
  });
}

document.getElementById("btn-skip-shop").addEventListener("click", async () => {
  const cur = latestState.players[latestState.current_player_index];
  const state = await API.post("/api/skip_shop", { player_id: cur.id });
  onStateUpdated(state);
});

// ---------------------------------------------------------------------
// PENDING ACTION (bài Sự kiện / Bẫy cần chọn thêm)
// ---------------------------------------------------------------------
function renderPendingModal(state) {
  const modal = document.getElementById("modal-pending");
  if (!state.pending_action) {
    modal.classList.add("hidden");
    return;
  }
  modal.classList.remove("hidden");
  const pa = state.pending_action;
  document.getElementById("pending-title").textContent = `🃏 ${pa.card_name}`;

  const desc = document.getElementById("pending-desc");
  const optWrap = document.getElementById("pending-options");
  optWrap.innerHTML = "";

  const playerName = (id) => state.players.find((p) => p.id === id)?.name || `#${id}`;

  const submit = async (choice) => {
    try {
      const s = await API.post("/api/resolve_pending", { choice });
      onStateUpdated(s);
    } catch (e) { alert(e.message); }
  };

  if (pa.await === "single_target") {
    desc.textContent = "Chọn 1 người chơi:";
    pa.options.forEach((pid) => {
      const b = document.createElement("button");
      b.textContent = playerName(pid);
      b.onclick = () => submit({ target_id: pid });
      optWrap.appendChild(b);
    });
  } else if (pa.await === "two_targets") {
    desc.textContent = "Chọn 2 người chơi để họ đổi chỗ cho nhau (bấm lần lượt):";
    let picked = [];
    pa.options.forEach((pid) => {
      const b = document.createElement("button");
      b.textContent = playerName(pid);
      b.onclick = () => {
        picked.push(pid);
        b.disabled = true;
        if (picked.length === 2) submit({ target_id_1: picked[0], target_id_2: picked[1] });
      };
      optWrap.appendChild(b);
    });
  } else if (pa.await === "copy_choice") {
    desc.textContent = "Chọn người để sao chép, rồi chọn sao chép Vị trí hay Vàng:";
    pa.options.forEach((pid) => {
      const rowWrap = document.createElement("div");
      rowWrap.style.display = "flex";
      rowWrap.style.gap = "4px";
      const bPos = document.createElement("button");
      bPos.textContent = `${playerName(pid)} (vị trí)`;
      bPos.onclick = () => submit({ target_id: pid, field: "position" });
      const bGold = document.createElement("button");
      bGold.textContent = `${playerName(pid)} (vàng)`;
      bGold.onclick = () => submit({ target_id: pid, field: "gold" });
      rowWrap.append(bPos, bGold);
      optWrap.appendChild(rowWrap);
    });
  } else if (pa.await === "tile_choice") {
    desc.textContent = "Nhập số ô muốn chọn (2-99):";
    renderTileNumberInput(optWrap, (tile) => submit({ tile }));
  } else if (pa.await === "two_tile_choice") {
    desc.textContent = "Nhập 2 số ô muốn hoán đổi loại ô:";
    renderTwoTileInput(optWrap, (a, b) => submit({ tile_a: a, tile_b: b }));
  } else if (pa.await === "five_tile_choice") {
    desc.textContent = "Nhập đúng 5 số ô (cách nhau bằng dấu phẩy) để thay bằng thẻ mới:";
    renderFiveTileInput(optWrap, (tiles) => submit({ tiles }));
  } else if (pa.await === "area_choice") {
    desc.textContent = "Chọn khu vực để đảo ngược thứ tự ô:";
    pa.options.forEach((area) => {
      const b = document.createElement("button");
      b.textContent = `Ô ${area}`;
      b.onclick = () => submit({ area });
      optWrap.appendChild(b);
    });
  }
}

function renderTileNumberInput(wrap, cb) {
  const input = document.createElement("input");
  input.type = "number"; input.min = 2; input.max = 99;
  input.style.cssText = "padding:0.5rem;border-radius:8px;border:1px solid var(--line);background:white;color:var(--text-main);margin-right:0.5rem;";
  const btn = document.createElement("button");
  btn.textContent = "Xác nhận";
  btn.onclick = () => cb(Number(input.value));
  wrap.append(input, btn);
}
function renderTwoTileInput(wrap, cb) {
  const a = document.createElement("input"); a.type = "number"; a.placeholder = "Ô A";
  const b = document.createElement("input"); b.type = "number"; b.placeholder = "Ô B";
  [a, b].forEach((el) => (el.style.cssText = "padding:0.5rem;border-radius:8px;border:1px solid var(--line);background:white;color:var(--text-main);margin-right:0.5rem;width:80px;"));
  const btn = document.createElement("button");
  btn.textContent = "Xác nhận";
  btn.onclick = () => cb(Number(a.value), Number(b.value));
  wrap.append(a, b, btn);
}
function renderFiveTileInput(wrap, cb) {
  const input = document.createElement("input");
  input.placeholder = "vd: 5,12,40,71,88";
  input.style.cssText = "padding:0.5rem;border-radius:8px;border:1px solid var(--line);background:white;color:var(--text-main);margin-right:0.5rem;width:220px;";
  const btn = document.createElement("button");
  btn.textContent = "Xác nhận";
  btn.onclick = () => cb(input.value.split(",").map((s) => Number(s.trim())));
  wrap.append(input, btn);
}

// ---------------------------------------------------------------------
// DÙNG VẬT PHẨM
// ---------------------------------------------------------------------
async function handleUseItem(itemType) {
  const cur = latestState.players[latestState.current_player_index];

  if (itemType === "DAO_GAM") {
    openItemTargetModal("Chọn mục tiêu trong bán kính 3 ô để đâm Dao Găm:",
      latestState.players.filter((p) => p.id !== cur.id && !p.finished),
      async (targetId) => {
        try {
          const s = await API.post("/api/use_item", { player_id: cur.id, item_type: itemType, target_id: targetId });
          onStateUpdated(s);
        } catch (e) { alert(e.message); }
      });
    return;
  }

  if (itemType === "KINH_AP_TRONG") {
    const modal = document.getElementById("modal-item-target");
    const opt = document.getElementById("item-target-options");
    document.getElementById("item-target-title").textContent = "Chọn +1 hoặc -1 cho lượt tung tới:";
    opt.innerHTML = "";
    [1, -1].forEach((d) => {
      const b = document.createElement("button");
      b.textContent = d > 0 ? "+1" : "-1";
      b.onclick = async () => {
        modal.classList.add("hidden");
        try {
          const s = await API.post("/api/use_item", { player_id: cur.id, item_type: itemType, delta: d });
          onStateUpdated(s);
        } catch (e) { alert(e.message); }
      };
      opt.appendChild(b);
    });
    modal.classList.remove("hidden");
    return;
  }

  // LA_CHAN, BUA_HO_MENH, XUC_XAC_X2 - không cần chọn thêm gì
  try {
    const s = await API.post("/api/use_item", { player_id: cur.id, item_type: itemType });
    onStateUpdated(s);
  } catch (e) { alert(e.message); }
}

function openItemTargetModal(title, players, onPick) {
  const modal = document.getElementById("modal-item-target");
  document.getElementById("item-target-title").textContent = title;
  const opt = document.getElementById("item-target-options");
  opt.innerHTML = "";
  players.forEach((p) => {
    const b = document.createElement("button");
    b.textContent = p.name;
    b.onclick = () => { modal.classList.add("hidden"); onPick(p.id); };
    opt.appendChild(b);
  });
  modal.classList.remove("hidden");
}

// ---------------------------------------------------------------------
// KẾT THÚC VÁN
// ---------------------------------------------------------------------
function renderEndModal(state) {
  const modal = document.getElementById("modal-end");
  if (!state.game_over) { modal.classList.add("hidden"); return; }
  modal.classList.remove("hidden");
  const winner = state.players.find((p) => p.id === state.winner_id);
  document.getElementById("end-title").textContent = "🏆 Ván đấu kết thúc!";
  document.getElementById("end-desc").textContent = winner
    ? `${winner.name} chiến thắng với ${winner.gold} vàng!`
    : "Ván đấu đã kết thúc.";
}

document.getElementById("btn-restart").addEventListener("click", () => {
  window.location.reload();
});
