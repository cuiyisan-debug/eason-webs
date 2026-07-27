const ADMIN_ENDPOINT = (() => {
  if (window.location.hostname === "mycys.top" || window.location.hostname === "www.mycys.top") {
    return "/api/visitor-stats/admin";
  }
  return "https://mycys.top/api/visitor-stats/admin";
})();

const tokenInput = document.querySelector("[data-admin-token]");
const rememberInput = document.querySelector("[data-admin-remember]");
const loginPanel = document.querySelector("[data-admin-login]");
const dashboard = document.querySelector("[data-admin-dashboard]");
const message = document.querySelector("[data-admin-message]");
const rows = document.querySelector("[data-admin-rows]");
const limitInput = document.querySelector("[data-admin-limit]");
const revealInput = document.querySelector("[data-admin-reveal]");
const moreButton = document.querySelector("[data-admin-more]");
const pageInfo = document.querySelector("[data-admin-page-info]");

let adminToken = window.sessionStorage.getItem("mycys-admin-token") || "";
let nextBefore = null;
let loadedVisits = [];

function formatNumber(value) {
  const number = Number(value || 0);
  return number.toLocaleString("zh-CN");
}

function formatTime(value) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

function text(value) {
  return String(value || "--");
}

function escapeCsv(value) {
  const clean = String(value || "").replace(/\r?\n/g, " ");
  return `"${clean.replace(/"/g, '""')}"`;
}

function setMessage(value, tone = "") {
  message.textContent = value;
  message.dataset.tone = tone;
}

function renderMetrics(payload) {
  document.querySelector("[data-admin-pv]").textContent = formatNumber(payload?.site?.pv);
  document.querySelector("[data-admin-uv]").textContent = formatNumber(payload?.site?.uv);
  document.querySelector("[data-admin-raw-pv]").textContent = formatNumber(payload?.rawSite?.pv);
  document.querySelector("[data-admin-raw-uv]").textContent = formatNumber(payload?.rawSite?.uv);
}

function renderRows(visits) {
  if (!visits.length) {
    rows.innerHTML = `<tr><td colspan="7">暂无访问记录</td></tr>`;
    return;
  }

  rows.innerHTML = visits
    .map(
      (visit) => `
        <tr>
          <td>${formatTime(visit.at)}</td>
          <td>${text(visit.path)}</td>
          <td>${text(visit.referrer)}</td>
          <td>${text(visit.country)}</td>
          <td>${text(visit.ip || visit.maskedIp)}</td>
          <td>${text(visit.ipHash)}</td>
          <td>${text(visit.userAgent)}</td>
        </tr>
      `
    )
    .join("");
}

async function fetchAdmin({ append = false } = {}) {
  if (!adminToken) {
    setMessage("请输入 VISITOR_ADMIN_TOKEN。", "error");
    return;
  }

  const params = new URLSearchParams({
    limit: limitInput.value,
  });
  if (revealInput.checked) params.set("reveal", "1");
  if (append && nextBefore) params.set("before", nextBefore);

  setMessage("正在读取访问记录...");
  const response = await fetch(`${ADMIN_ENDPOINT}?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${adminToken}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    throw new Error("Token 不正确，或 Cloudflare Worker 还没有设置 VISITOR_ADMIN_TOKEN。");
  }
  if (!response.ok) {
    throw new Error(`读取失败：HTTP ${response.status}`);
  }

  const payload = await response.json();
  renderMetrics(payload);
  const visits = Array.isArray(payload.visits) ? payload.visits : [];
  loadedVisits = append ? [...loadedVisits, ...visits] : visits;
  nextBefore = payload.nextBefore || null;
  renderRows(loadedVisits);
  moreButton.disabled = !nextBefore;
  pageInfo.textContent = `已载入 ${loadedVisits.length} 条${nextBefore ? "，还有更早记录" : ""}`;
  setMessage("访问记录已更新。", "success");
}

async function enterDashboard() {
  adminToken = tokenInput.value.trim();
  if (!adminToken) {
    setMessage("请输入 VISITOR_ADMIN_TOKEN。", "error");
    return;
  }
  if (rememberInput.checked) {
    window.sessionStorage.setItem("mycys-admin-token", adminToken);
  }

  try {
    await fetchAdmin();
    loginPanel.hidden = true;
    dashboard.hidden = false;
  } catch (error) {
    setMessage(error.message, "error");
  }
}

function exportCsv() {
  const header = ["时间", "页面", "来源", "国家", "IP", "IP Hash", "User-Agent"];
  const lines = [
    header.map(escapeCsv).join(","),
    ...loadedVisits.map((visit) =>
      [
        formatTime(visit.at),
        visit.path,
        visit.referrer,
        visit.country,
        visit.ip || visit.maskedIp,
        visit.ipHash,
        visit.userAgent,
      ]
        .map(escapeCsv)
        .join(",")
    ),
  ];
  const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `mycys-visits-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

loginPanel.addEventListener("submit", (event) => {
  event.preventDefault();
  enterDashboard();
});
document.querySelector("[data-admin-load]").addEventListener("click", enterDashboard);
document.querySelector("[data-admin-refresh]").addEventListener("click", () => fetchAdmin().catch((error) => setMessage(error.message, "error")));
document.querySelector("[data-admin-more]").addEventListener("click", () => fetchAdmin({ append: true }).catch((error) => setMessage(error.message, "error")));
document.querySelector("[data-admin-export]").addEventListener("click", exportCsv);
document.querySelector("[data-admin-logout]").addEventListener("click", () => {
  adminToken = "";
  loadedVisits = [];
  nextBefore = null;
  window.sessionStorage.removeItem("mycys-admin-token");
  tokenInput.value = "";
  dashboard.hidden = true;
  loginPanel.hidden = false;
  setMessage("已退出。");
});

tokenInput.value = adminToken;
if (adminToken) rememberInput.checked = true;
