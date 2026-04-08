// ── Theme ──────────────────────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.querySelectorAll(".theme-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.theme === theme);
  });
}

function setTheme(theme) {
  applyTheme(theme);
  fetch("/set-theme/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `theme=${theme}`,
  });
}

const savedTheme = document.body.dataset.userTheme || "dark";
applyTheme(savedTheme);

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".theme-btn");
  if (btn) setTheme(btn.dataset.theme);
});

// ── CSRF helper ────────────────────────────────────────────────────────────
function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach((c) => {
    const [k, val] = c.trim().split("=");
    if (k === name) v = decodeURIComponent(val);
  });
  return v;
}

// ── Toast auto-dismiss ─────────────────────────────────────────────────────
document.querySelectorAll(".msg-toast").forEach((toast) => {
  const close = toast.querySelector(".close-btn");
  if (close) close.addEventListener("click", () => toast.remove());
  setTimeout(() => toast.remove(), 4000);
});

// ── Password show/hide ─────────────────────────────────────────────────────
document.querySelectorAll(".pw-toggle").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = btn.previousElementSibling;
    if (input && input.type) {
      input.type = input.type === "password" ? "text" : "password";
      btn.textContent = input.type === "password" ? "👁️" : "🙈";
    }
  });
});

// ── Role picker (signup) ───────────────────────────────────────────────────
document.querySelectorAll(".role-option").forEach((opt) => {
  opt.addEventListener("click", () => {
    document
      .querySelectorAll(".role-option")
      .forEach((o) => o.classList.remove("selected"));
    opt.classList.add("selected");
    const radio = opt.querySelector("input[type=radio]");
    if (radio) radio.checked = true;
  });
});

// ── Mobile Sidebar ─────────────────────────────────────────────────────────
// ✅ FIX: wrapped in DOMContentLoaded so elements are guaranteed to exist
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("mobileMenuToggle");
  var overlay = document.getElementById("sidebarOverlay");
  var sidebar = document.getElementById("mainSidebar");

  if (!toggle || !sidebar) return;

  function openMenu() {
    sidebar.classList.add("mobile-open");
    if (overlay) overlay.classList.add("active");
    toggle.textContent = "✕";
    document.body.style.overflow = "hidden";
  }

  function closeMenu() {
    sidebar.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("active");
    toggle.textContent = "☰";
    document.body.style.overflow = "";
  }

  toggle.addEventListener("click", function () {
    sidebar.classList.contains("mobile-open") ? closeMenu() : openMenu();
  });

  if (overlay) overlay.addEventListener("click", closeMenu);

  // Close on nav link click (mobile)
  sidebar.querySelectorAll(".nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
      if (window.innerWidth <= 768) closeMenu();
    });
  });

  // Close on resize to desktop
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768) closeMenu();
  });

  // Swipe left to close sidebar
  var touchStartX = 0;
  sidebar.addEventListener(
    "touchstart",
    function (e) {
      touchStartX = e.changedTouches[0].screenX;
    },
    { passive: true }
  );
  sidebar.addEventListener(
    "touchend",
    function (e) {
      var dx = e.changedTouches[0].screenX - touchStartX;
      if (dx < -60) closeMenu();
    },
    { passive: true }
  );
});

// ── Guru AI ────────────────────────────────────────────────────────────────
var guruPanel = document.getElementById("guruPanel");
var guruFab = document.getElementById("guruFab");
var guruInput = document.getElementById("guruInput");
var guruMessages = document.getElementById("guruMessages");
var guruHistory = [];

if (guruFab) {
  guruFab.addEventListener("click", function () {
    guruPanel.classList.toggle("open");
    if (guruPanel.classList.contains("open") && guruInput) guruInput.focus();
  });
}

document.getElementById("guruClose") &&
  document.getElementById("guruClose").addEventListener("click", function () {
    guruPanel.classList.remove("open");
  });

document.getElementById("guruSend") &&
  document
    .getElementById("guruSend")
    .addEventListener("click", sendGuruMessage);
guruInput &&
  guruInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendGuruMessage();
    }
  });

document.querySelectorAll(".quick-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    if (guruInput) {
      guruInput.value = btn.textContent;
      sendGuruMessage();
    }
  });
});

function appendGuruMessage(role, text) {
  if (!guruMessages) return;
  var div = document.createElement("div");
  div.className = "guru-msg" + (role === "user" ? " user" : "");
  var bubble = document.createElement("div");
  bubble.className = "guru-bubble " + (role === "user" ? "user-b" : "bot");
  bubble.textContent = text;
  if (role !== "user") {
    var icon = document.createElement("div");
    icon.style.cssText =
      "width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#a855f7,#6366f1);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0";
    icon.textContent = "🦉";
    div.appendChild(icon);
  }
  div.appendChild(bubble);
  guruMessages.appendChild(div);
  guruMessages.scrollTop = guruMessages.scrollHeight;
}

function showTyping() {
  var div = document.createElement("div");
  div.className = "guru-msg";
  div.id = "guruTyping";
  var icon = document.createElement("div");
  icon.style.cssText =
    "width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#a855f7,#6366f1);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0";
  icon.textContent = "🦉";
  var dots = document.createElement("div");
  dots.className = "typing-dots";
  dots.innerHTML =
    '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  div.appendChild(icon);
  div.appendChild(dots);
  guruMessages.appendChild(div);
  guruMessages.scrollTop = guruMessages.scrollHeight;
}

function removeTyping() {
  var el = document.getElementById("guruTyping");
  if (el) el.remove();
}

async function sendGuruMessage() {
  if (!guruInput) return;
  var text = guruInput.value.trim();
  if (!text) return;
  guruInput.value = "";
  appendGuruMessage("user", text);
  guruHistory.push({ role: "user", content: text });
  showTyping();
  try {
    var resp = await fetch("/guru/ask/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ message: text, history: guruHistory.slice(-10) }),
    });
    var data = await resp.json();
    removeTyping();
    var reply = data.reply || "দুঃখিত, সমস্যা হচ্ছে।";
    appendGuruMessage("bot", reply);
    guruHistory.push({ role: "assistant", content: reply });
  } catch (e) {
    removeTyping();
    appendGuruMessage("bot", "সংযোগ সমস্যা। একটু পরে চেষ্টা করুন।");
  }
}

// ── Chat polling ───────────────────────────────────────────────────────────
var lastMsgId = 0;
var chatOtherUserId =
  document.getElementById("chatOtherUserId") &&
  document.getElementById("chatOtherUserId").value;

function appendChatMessage(msg, myId) {
  var container = document.getElementById("chatMessages");
  if (!container) return;
  var isMine = msg.sender_id == myId;
  var div = document.createElement("div");
  div.className = "msg-bubble " + (isMine ? "mine" : "theirs");
  div.innerHTML = msg.text + '<div class="msg-time">' + msg.time + "</div>";
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  lastMsgId = Math.max(lastMsgId, msg.id);
}

if (chatOtherUserId) {
  document.querySelectorAll("[data-msg-id]").forEach(function (el) {
    lastMsgId = Math.max(lastMsgId, parseInt(el.dataset.msgId) || 0);
  });
  setInterval(async function () {
    try {
      var myId =
        document.getElementById("myUserId") &&
        document.getElementById("myUserId").value;
      var resp = await fetch(
        "/chat/messages/" + chatOtherUserId + "/?after=" + lastMsgId
      );
      var data = await resp.json();
      data.messages.forEach(function (msg) {
        appendChatMessage(msg, myId);
      });
    } catch (e) {}
  }, 2500);
}

var chatForm = document.getElementById("chatForm");
if (chatForm) {
  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    var input = document.getElementById("chatInput");
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    var myId =
      document.getElementById("myUserId") &&
      document.getElementById("myUserId").value;
    try {
      var resp = await fetch("/chat/send/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body:
          "receiver_id=" +
          chatOtherUserId +
          "&text=" +
          encodeURIComponent(text),
      });
      var data = await resp.json();
      if (data.ok) appendChatMessage(data, myId);
    } catch (e) {}
  });
}

// ── Notification mark read ─────────────────────────────────────────────────
document.querySelectorAll(".notif-item[data-id]").forEach(function (item) {
  item.addEventListener("click", async function () {
    if (item.classList.contains("read")) return;
    var id = item.dataset.id;
    await fetch("/notifications/" + id + "/read/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    });
    item.classList.add("read");
    item.style.opacity = "0.6";
    var dot = item.querySelector(".pulse-dot");
    if (dot) dot.remove();
    var badge = item.querySelector(".badge-accent");
    if (badge) badge.remove();
  });
});

// ── Scroll chat to bottom on load ──────────────────────────────────────────
var chatMessages = document.getElementById("chatMessages");
if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;