// =====================================================================
// STEP 1: Paste your API Gateway Invoke URL here (ends with /generate)
// e.g. "https://abc123xyz.execute-api.us-east-1.amazonaws.com/generate"
// =====================================================================
const API_URL = "PASTE_YOUR_API_URL_HERE/generate";

const form = document.getElementById("career-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const button = document.getElementById("submit-btn");
const hours = document.getElementById("hours");

hours.addEventListener("input", () => {
  document.getElementById("hours-value").textContent = hours.value;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    goal: document.getElementById("goal").value,
    level: document.getElementById("level").value,
    interests: document.getElementById("interests").value,
    hours: hours.value,
  };

  button.disabled = true;
  resultEl.hidden = true;
  setStatus("Building your roadmap with Amazon Bedrock... (about 5-15 seconds)");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || data.message || `Request failed (${res.status})`);

    if (data.roadmap) renderRoadmap(data.roadmap, payload.goal);
    else renderRaw(data.raw);
    setStatus("");
  } catch (err) {
    setStatus(`Something went wrong: ${err.message}`, true);
  } finally {
    button.disabled = false;
  }
});

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "error" : "";
}

// Escape model text before putting it into HTML
function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function list(items, render) {
  return (items || []).map((item) => `<li>${render(item)}</li>`).join("");
}

function renderRoadmap(r, goal) {
  const phases = (r.plan_90_days || [])
    .map(
      (p) => `
      <div class="phase">
        <h3>${esc(p.phase)}: ${esc(p.focus)}</h3>
        <ul>${list(p.tasks, esc)}</ul>
      </div>`
    )
    .join("");

  resultEl.innerHTML = `
    <div class="card">
      <h2>Your ${esc(goal)} Roadmap</h2>
      <p>${esc(r.summary)}</p>
    </div>
    <div class="card">
      <h2>Skills to Learn</h2>
      <ol>${list(r.skills, esc)}</ol>
    </div>
    <div class="card">
      <h2>Recommended Certifications</h2>
      <ul>${list(r.certifications, (c) => `<strong>${esc(c.name)}</strong> - ${esc(c.why)}`)}</ul>
    </div>
    <div class="card">
      <h2>Portfolio Projects</h2>
      <ul>${list(r.projects, (p) => `<strong>${esc(p.title)}</strong> - ${esc(p.description)}`)}</ul>
    </div>
    <div class="card">
      <h2>Your 90-Day Plan</h2>
      ${phases}
    </div>
    <div class="card next-step">
      <h2>Do This Today</h2>
      <p>${esc(r.next_step)}</p>
    </div>`;
  resultEl.hidden = false;
  resultEl.scrollIntoView({ behavior: "smooth" });
}

function renderRaw(text) {
  resultEl.innerHTML = `<div class="card"><h2>Your Roadmap</h2><pre>${esc(text)}</pre></div>`;
  resultEl.hidden = false;
}
