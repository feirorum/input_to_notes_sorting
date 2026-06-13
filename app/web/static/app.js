"use strict";

const $ = (sel) => document.querySelector(sel);
const api = async (url, opts) => {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return r.status === 204 ? null : r.json();
};
const post = (url, body) =>
  api(url, { method: "POST", headers: { "Content-Type": "application/json" },
             body: JSON.stringify(body || {}) });
const esc = (s) => (s || "").replace(/[&<>]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

// --- left pane ------------------------------------------------------------
document.querySelectorAll(".example").forEach((b) =>
  b.addEventListener("click", () => { $("#text").value = b.dataset.text; }));

$("#btn-explain").addEventListener("click", async () => {
  const text = $("#text").value.trim();
  if (!text) return;
  try { renderDecision(await post("/explain", { text })); }
  catch (e) { alert("Explain failed: " + e.message); }
});

$("#btn-capture").addEventListener("click", async () => {
  const text = $("#text").value.trim();
  if (!text) return;
  await post("/capture", { text, source: "web_form" });
  $("#text").value = "";
  switchTab("inbox");
});

// --- middle + right panes -------------------------------------------------
function renderDecision(d) {
  const pct = Math.round((d.confidence || 0) * 100);
  let asks = "";
  if (d.ask_reasons && d.ask_reasons.length) {
    asks = `<div class="asks"><b>Asks the user because:</b><ul>` +
      d.ask_reasons.map((r) => `<li>${esc(r)}</li>`).join("") + `</ul></div>`;
  }
  $("#decision").classList.remove("empty");
  $("#decision").innerHTML = `
    <div class="decision-head">
      <span class="action ${d.decision}">${d.decision}</span>
      <span class="conf">confidence ${pct}%</span>
      ${d.needs_user_confirmation ? '<span class="chip warn">needs confirmation</span>'
                                  : '<span class="chip">auto</span>'}
    </div>
    <div class="bar"><i style="width:${pct}%"></i></div>
    <div class="reason">${esc(d.reason)}</div>
    ${d.destination ? `<div class="path">${esc(d.destination)}</div>` : ""}
    ${asks}`;

  // signals
  const s = d.signals || {};
  const chips = [];
  if (s.is_task) chips.push('<span class="chip warn">task/reminder</span>');
  if (s.is_sensitive) chips.push('<span class="chip warn">sensitive</span>');
  if (s.ambiguous) chips.push('<span class="chip warn">ambiguous</span>');
  (s.entities || []).forEach((e) => chips.push(`<span class="chip">entity: ${esc(e)}</span>`));
  (s.timestamps || []).forEach((t) => chips.push(`<span class="chip">⏱ ${esc(t)}</span>`));
  if (s.example_match && s.example_match.similarity >= 0.5)
    chips.push(`<span class="chip">example ${Math.round(s.example_match.similarity*100)}%</span>`);
  if (s.podcast_session)
    chips.push(`<span class="chip">session: ${s.podcast_session.related_timestamped_captures} related</span>`);
  $("#signals").innerHTML = chips.length ? `<div class="chips">${chips.join("")}</div>` : "";

  // scores table
  const tbody = $("#scores tbody");
  tbody.innerHTML = (d.scores || []).map((row) => `
    <tr>
      <td>${esc(row.label)}<br><span class="muted">${esc(row.destination_key)}</span></td>
      <td class="score-total">${row.total.toFixed(2)}</td>
      <td>${row.contributions.map((c) =>
        `<span class="mscore"><b>${esc(c.matcher)} +${c.score.toFixed(2)}</b> — ${esc(c.explanation)}</span>`
      ).join("")}</td>
    </tr>`).join("");
  $("#scores").classList.toggle("hidden", !(d.scores && d.scores.length));

  renderTarget(d.preview, d.proposed_content);
}

function renderTarget(preview, proposed) {
  const el = $("#target");
  if (!preview || !preview.path) {
    el.classList.add("empty");
    el.textContent = "No target note (item kept in inbox / needs review).";
    return;
  }
  el.classList.remove("empty");
  const result = preview.proposed_result || "";
  const line = (proposed || "").trim();
  const highlighted = line
    ? esc(result).replace(esc(line), `<span class="added">${esc(line)}</span>`)
    : esc(result);
  el.innerHTML = `
    <div class="path">${esc(preview.path)}</div>
    <h3 style="font-size:13px;margin:8px 0 4px">After sorting:</h3>
    <pre class="note">${highlighted}</pre>`;
}

// --- workflow tabs --------------------------------------------------------
let currentTab = "inbox";
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => switchTab(t.dataset.tab)));

function switchTab(name) {
  currentTab = name;
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === name));
  refreshTab();
}

async function refreshTab() {
  const body = $("#tab-body");
  body.innerHTML = '<p class="muted">Loading…</p>';
  try {
    if (currentTab === "inbox") return renderInbox(await api("/inbox"));
    if (currentTab === "review") return renderReview(await api("/review"));
    if (currentTab === "processed") return renderProcessed(await api("/processed"));
    if (currentTab === "audit") return renderAudit(await api("/audit"));
  } catch (e) { body.innerHTML = `<p class="muted">${esc(e.message)}</p>`; }
}

function itemShell(c, inner) {
  return `<div class="item">
    <div class="meta">${esc(c.id)} · ${esc(c.source)} · ${esc(c.created_at)}</div>
    <div class="text">${esc(c.text)}</div>${inner}</div>`;
}

function renderInbox(items) {
  const body = $("#tab-body");
  if (!items.length) { body.innerHTML = '<p class="muted">Inbox empty.</p>'; return; }
  body.innerHTML = items.map((c) => itemShell(c,
    `<div class="actions"><button class="small" data-process="${c.id}">Process</button></div>`)).join("");
  body.querySelectorAll("[data-process]").forEach((b) =>
    b.addEventListener("click", async () => {
      const d = await post(`/process/${b.dataset.process}`);
      renderDecision(d);
      refreshTab();
    }));
}

function renderReview(items) {
  const body = $("#tab-body");
  if (!items.length) { body.innerHTML = '<p class="muted">Nothing to review.</p>'; return; }
  body.innerHTML = items.map((c) => {
    const d = c.decision || {};
    const canConfirm = d.destination && (d.decision === "append_to_existing_note"
                       || d.decision === "create_new_note");
    return itemShell(c, `
      <div class="meta">proposed: ${esc(d.decision || "?")} →
        <span class="path">${esc(d.destination || "—")}</span>
        ${d.ask_reasons && d.ask_reasons.length ? "· " + esc(d.ask_reasons.join("; ")) : ""}</div>
      <div class="actions">
        <button class="small" data-show="${c.id}">Show</button>
        ${canConfirm ? `<button class="small" data-confirm="${c.id}">Confirm</button>` : ""}
        <button class="small" data-correct="${c.id}">Correct →</button>
      </div>`);
  }).join("");
  body.querySelectorAll("[data-show]").forEach((b) =>
    b.addEventListener("click", async () =>
      renderDecision(await post("/explain", { text: itemText(items, b.dataset.show) }))));
  body.querySelectorAll("[data-confirm]").forEach((b) =>
    b.addEventListener("click", async () => {
      try { renderDecision(await post(`/confirm/${b.dataset.confirm}`)); refreshTab(); }
      catch (e) { alert(e.message); }
    }));
  body.querySelectorAll("[data-correct]").forEach((b) =>
    b.addEventListener("click", () => correctFlow(b.dataset.correct)));
}

function itemText(items, id) {
  const it = items.find((x) => x.id === id);
  return it ? it.text : "";
}

function renderProcessed(items) {
  const body = $("#tab-body");
  if (!items.length) { body.innerHTML = '<p class="muted">Nothing processed yet.</p>'; return; }
  body.innerHTML = items.map((c) => itemShell(c, `
    <div class="actions">
      <button class="small" data-undo="${c.id}">Undo</button>
      <button class="small" data-correct="${c.id}">Correct →</button>
    </div>`)).join("");
  body.querySelectorAll("[data-undo]").forEach((b) =>
    b.addEventListener("click", async () => {
      try { await post(`/undo/${b.dataset.undo}`); refreshTab(); }
      catch (e) { alert(e.message); }
    }));
  body.querySelectorAll("[data-correct]").forEach((b) =>
    b.addEventListener("click", () => correctFlow(b.dataset.correct)));
}

function renderAudit(items) {
  const body = $("#tab-body");
  if (!items.length) { body.innerHTML = '<p class="muted">No audit entries.</p>'; return; }
  body.innerHTML = items.map((a) => `<div class="item">
    <div class="meta">#${a.id} · ${esc(a.processed_at)} · conf ${a.confidence}
      ${a.undone ? "· <b>undone</b>" : ""}</div>
    <div><span class="action ${a.action}">${a.action}</span>
      <span class="path">${esc(a.destination || "—")}</span></div>
    <div class="text">${esc(a.change_made || a.reasoning || "")}</div>
    ${a.undo_available && !a.undone ?
      `<div class="actions"><button class="small" data-undo="${a.capture_id}">Undo</button></div>` : ""}
  </div>`).join("");
  body.querySelectorAll("[data-undo]").forEach((b) =>
    b.addEventListener("click", async () => {
      try { await post(`/undo/${b.dataset.undo}`); refreshTab(); }
      catch (e) { alert(e.message); }
    }));
}

async function correctFlow(id) {
  const key = prompt("Correct destination key (e.g. family, work, podcasts, " +
                     "learning, projects, health, shopping, references):");
  if (!key) return;
  const notePath = prompt("Append to existing note path? (blank = category note / new note)\n" +
                          "e.g. notes/family/flora.md", "") || null;
  try {
    const d = await post(`/correct/${id}`, {
      destination_key: key.trim(),
      action: notePath ? "append_to_existing_note" : "create_new_note",
      note_path: notePath,
      save_example: true,
    });
    renderDecision(d);
    refreshTab();
  } catch (e) { alert("Correction failed: " + e.message); }
}

// init
switchTab("inbox");
