const $ = (sel) => document.querySelector(sel);

const sourceEl = $("#source");
const statusEl = $("#status");
const charCountEl = $("#char-count");
const btnAnalyze = $("#btn-analyze");
const btnExecute = $("#btn-execute");
const btnClear = $("#btn-clear");

let busy = false;

function setBusy(on) {
  busy = on;
  btnAnalyze.disabled = on;
  btnExecute.disabled = on;
  btnClear.disabled = on;
}

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? ` ${kind}` : "");
}

function updateCharCount() {
  charCountEl.textContent = `${sourceEl.value.length.toLocaleString()} chars`;
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.classList.remove("active");
      p.hidden = true;
    });
    tab.classList.add("active");
    const panel = $(`#panel-${tab.dataset.tab}`);
    panel.hidden = false;
    panel.classList.add("active");
  });
});

function resetPipeline() {
  document.querySelectorAll("#pipeline span").forEach((s) => {
    s.classList.remove("pass", "fail", "active");
  });
}

function paintPipeline(data, executed) {
  resetPipeline();
  const marks = {
    source: "pass",
    lexical: data.lexical_error ? "fail" : "pass",
    syntax: data.lexical_error
      ? ""
      : data.syntax_error
        ? "fail"
        : data.syntax_valid
          ? "pass"
          : "",
    ast: data.syntax_valid ? "pass" : "",
    execution: "",
  };
  if (executed) {
    if (data.execution_ok === true) marks.execution = "pass";
    else if (data.execution_ok === false) marks.execution = "fail";
    else if (data.lexical_error || data.syntax_error) marks.execution = "";
  }
  Object.entries(marks).forEach(([stage, cls]) => {
    const el = document.querySelector(`#pipeline [data-stage="${stage}"]`);
    if (el && cls) el.classList.add(cls);
  });
}

function fillTokens(data) {
  const status = $("#token-status");
  const tbody = $("#token-table tbody");
  tbody.innerHTML = "";
  if (data.lexical_error) {
    const n = data.error_count || (data.diagnostics || []).length || 1;
    const multi = n > 1 ? ` (${n} errors — see Summary)` : "";
    status.textContent = `Lexical analysis: FAILED — ${data.lexical_error}${multi}`;
    status.className = "panel-status fail";
  } else {
    status.textContent = `Lexical analysis: PASSED — ${data.token_count} token(s)`;
    status.className = "panel-status ok";
  }
  $("#token-stream").textContent = data.token_stream || "(empty)";
  (data.tokens || []).forEach((tok, i) => {
    const tr = document.createElement("tr");
    if (tok.type === "ERROR") tr.className = "error-row";
    const value =
      tok.value === null || tok.value === undefined
        ? ""
        : typeof tok.value === "string"
          ? JSON.stringify(tok.value)
          : String(tok.value);
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${escapeHtml(tok.type)}</td>
      <td>${escapeHtml(tok.lexeme)}</td>
      <td>${escapeHtml(value)}</td>
      <td>${tok.line}</td>
      <td>${tok.column}</td>`;
    tbody.appendChild(tr);
  });
}

function fillAst(data) {
  const status = $("#ast-status");
  if (data.lexical_error) {
    status.textContent = "AST skipped (lexical error)";
    status.className = "panel-status";
    $("#ast-tree").textContent = "(no AST)";
    return;
  }
  if (data.syntax_error) {
    const n = data.error_count || (data.diagnostics || []).length || 1;
    const multi = n > 1 ? ` (${n} errors — see Summary)` : "";
    status.textContent = `Syntax analysis: FAILED — ${data.syntax_error}${multi}`;
    status.className = "panel-status fail";
  } else {
    status.textContent = `Syntax analysis: PASSED — ${data.statement_count} statement(s)`;
    status.className = "panel-status ok";
  }
  $("#ast-tree").textContent = data.ast_tree || "(empty AST)";
}

function fillOutput(data, executed) {
  const status = $("#output-status");
  const out = $("#output");
  if (!executed) {
    status.textContent = "Optional execution: skipped";
    status.className = "panel-status";
    out.textContent = "Use Analyze + Execute to run the program.";
    return;
  }
  if (data.lexical_error || data.syntax_error) {
    status.textContent = "Optional execution: skipped (earlier stage failed)";
    status.className = "panel-status";
    out.textContent = "(not run)";
    return;
  }
  if (data.execution_ok) {
    status.textContent = "Optional execution: PASSED";
    status.className = "panel-status ok";
    out.textContent = data.execution_output || "(no output)";
  } else {
    status.textContent = `Optional execution: FAILED — ${(data.execution_error || "").split(".")[0]}.`;
    status.className = "panel-status fail";
    let body = data.execution_output || "";
    if (data.execution_error) {
      if (body && !body.endsWith("\n")) body += "\n";
      body += `\n--- Runtime stopped ---\n${data.execution_error}\n`;
    }
    out.textContent = body || "(no output)";
  }
}

function fillSummary(data, executed) {
  const lines = [
    "PNC Analysis Summary",
    "====================",
    `Tokens:              ${data.token_count}`,
    `Statements / AST:    ${data.statement_count}`,
    `Syntax valid:        ${data.syntax_valid}`,
  ];
  if (data.lexical_error) {
    lines.push(`First lexical error: ${data.lexical_error}`);
    if (data.lexical_tip) lines.push(`Tip:                 ${data.lexical_tip}`);
  }
  if (data.syntax_error) {
    lines.push(`First syntax error:  ${data.syntax_error}`);
    if (data.syntax_tip) lines.push(`Tip:                 ${data.syntax_tip}`);
  }
  if (data.diagnostics_report || (data.diagnostics && data.diagnostics.length)) {
    lines.push("");
    lines.push("All errors (lexical + syntax), ordered by line number.");
    lines.push("Token table / FA / AST still stop at the first pipeline failure.");
    lines.push("");
    if (data.diagnostics_report) {
      lines.push(data.diagnostics_report);
    } else {
      lines.push(`Errors found: ${data.diagnostics.length}`);
      lines.push("-".repeat(40));
      data.diagnostics.forEach((d, i) => {
        const stage = d.stage === "lexical" ? "Lexical" : "Syntax";
        lines.push(`${i + 1}. [${stage}] line ${d.line}, column ${d.column}`);
        lines.push(`   ${d.message}`);
        if (d.tip) lines.push(`   Suggestion: ${d.tip}`);
        if (i < data.diagnostics.length - 1) lines.push("");
      });
    }
  }
  if (executed) {
    lines.push(`Execution:           ${data.execution_ok ? "PASSED" : "FAILED"}`);
    if (data.execution_error) lines.push(`Runtime error:       ${data.execution_error}`);
  } else {
    lines.push("Execution:           SKIPPED");
  }
  $("#summary").textContent = lines.join("\n");
}

function fillFa(data) {
  const status = $("#fa-status");
  const list = $("#fa-list");
  const svg = $("#fa-svg");
  svg.innerHTML = "";

  if (!data.automaton) {
    status.textContent = "No FA trace.";
    status.className = "panel-status";
    list.textContent = "";
    return;
  }

  const fa = data.automaton;
  if (fa.has_dead_state || data.lexical_error) {
    status.textContent = data.lexical_error
      ? `FA reached DEAD — ${data.lexical_error}`
      : "FA path includes a dead state";
    status.className = "panel-status fail";
  } else {
    status.textContent = `FA path: ${fa.states.length} state(s), ${fa.transitions.length} transition(s)`;
    status.className = "panel-status ok";
  }

  const lines = fa.states.map((s) => {
    const info = s.accept_info ? ` [${s.accept_info}]` : "";
    return `${s.id}  (${s.kind})  ${s.label}${info}`;
  });
  if (fa.transitions.length) {
    lines.push("", "Transitions:");
    fa.transitions.forEach((t) => {
      lines.push(`  ${t.from_id} --${JSON.stringify(t.symbol)}--> ${t.to_id}`);
    });
  }
  list.textContent = lines.join("\n");

  drawFaSvg(fa);
}

function drawFaSvg(fa) {
  const svg = $("#fa-svg");
  const states = fa.states.slice(0, 40);
  const gap = 78;
  const y = 90;
  const width = Math.max(640, states.length * gap + 40);
  svg.setAttribute("viewBox", `0 0 ${width} 180`);
  svg.setAttribute("width", String(width));

  const ns = "http://www.w3.org/2000/svg";
  const colors = {
    start: "#1a2420",
    normal: "#3d5c50",
    final: "#0f6b5c",
    warn: "#9a5b12",
    dead: "#a12a2a",
  };

  states.forEach((s, i) => {
    const x = 30 + i * gap;
    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", String(x));
    circle.setAttribute("cy", String(y));
    circle.setAttribute("r", "18");
    circle.setAttribute("fill", colors[s.kind] || colors.normal);
    svg.appendChild(circle);

    if (s.kind === "final") {
      const ring = document.createElementNS(ns, "circle");
      ring.setAttribute("cx", String(x));
      ring.setAttribute("cy", String(y));
      ring.setAttribute("r", "22");
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", colors.final);
      ring.setAttribute("stroke-width", "2");
      svg.appendChild(ring);
    }

    const label = document.createElementNS(ns, "text");
    label.setAttribute("x", String(x));
    label.setAttribute("y", String(y + 4));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "#f4fffb");
    label.setAttribute("font-size", "10");
    label.setAttribute("font-family", "IBM Plex Mono, monospace");
    label.textContent = s.id.length > 5 ? s.id.slice(0, 4) : s.id;
    svg.appendChild(label);

    const kind = document.createElementNS(ns, "text");
    kind.setAttribute("x", String(x));
    kind.setAttribute("y", String(y + 38));
    kind.setAttribute("text-anchor", "middle");
    kind.setAttribute("fill", "#5c6b63");
    kind.setAttribute("font-size", "10");
    kind.setAttribute("font-family", "DM Sans, sans-serif");
    kind.textContent = s.kind;
    svg.appendChild(kind);

    if (i < states.length - 1) {
      const line = document.createElementNS(ns, "line");
      line.setAttribute("x1", String(x + 20));
      line.setAttribute("y1", String(y));
      line.setAttribute("x2", String(x + gap - 20));
      line.setAttribute("y2", String(y));
      line.setAttribute("stroke", "#8aa193");
      line.setAttribute("stroke-width", "1.5");
      svg.appendChild(line);
    }
  });

  if (fa.states.length > 40) {
    const note = document.createElementNS(ns, "text");
    note.setAttribute("x", "20");
    note.setAttribute("y", "24");
    note.setAttribute("fill", "#9a5b12");
    note.setAttribute("font-size", "12");
    note.textContent = `Showing first 40 of ${fa.states.length} states — see list below.`;
    svg.appendChild(note);
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function showResult(data, executed) {
  paintPipeline(data, executed);
  fillSummary(data, executed);
  fillTokens(data);
  fillFa(data);
  fillAst(data);
  fillOutput(data, executed);

  if (data.lexical_error) {
    setStatus(`Lexical error — ${data.lexical_error}`, "error");
    activateTab("tokens");
  } else if (data.syntax_error) {
    setStatus(`Syntax error — ${data.syntax_error}`, "error");
    activateTab("ast");
  } else if (executed) {
    setStatus(data.execution_ok ? "Analysis + execution complete." : "Execution stopped by runtime limit/error.", data.execution_ok ? "ok" : "error");
    activateTab("output");
  } else {
    setStatus("Analysis complete.", "ok");
    activateTab("summary");
  }
}

function activateTab(name) {
  const tab = document.querySelector(`.tab[data-tab="${name}"]`);
  if (tab) tab.click();
}

async function runAnalyze(execute) {
  if (busy) return;
  const source = sourceEl.value;
  if (!source.trim()) {
    setStatus("Please enter PNC source code first.", "error");
    return;
  }
  setBusy(true);
  setStatus(execute ? "Analyzing + executing..." : "Analyzing...");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, execute }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    showResult(data, execute);
  } catch (err) {
    setStatus(`Request failed: ${err.message}`, "error");
  } finally {
    setBusy(false);
  }
}

btnAnalyze.addEventListener("click", () => runAnalyze(false));
btnExecute.addEventListener("click", () => runAnalyze(true));
btnClear.addEventListener("click", () => {
  sourceEl.value = "";
  updateCharCount();
  resetPipeline();
  $("#summary").textContent = "Run Analyze to see pipeline results.";
  $("#token-table tbody").innerHTML = "";
  $("#token-stream").textContent = "";
  $("#token-status").textContent = "";
  $("#fa-status").textContent = "";
  $("#fa-list").textContent = "";
  $("#fa-svg").innerHTML = "";
  $("#ast-status").textContent = "";
  $("#ast-tree").textContent = "No AST yet.";
  $("#output-status").textContent = "Optional execution: not run";
  $("#output").textContent = "Use Analyze + Execute to run the program.";
  setStatus("Cleared.");
  activateTab("summary");
});

sourceEl.addEventListener("input", updateCharCount);

(async function init() {
  try {
    const res = await fetch("/api/defaults");
    const data = await res.json();
    sourceEl.value = data.source || "";
  } catch {
    sourceEl.value = 'int a = 5;\nint b = 10;\nprint(a + b);\nprint("Hello World");\n';
  }
  updateCharCount();
})();
