document.addEventListener("DOMContentLoaded", () => {
    const inputEl = document.getElementById("input-text");
    const runBtn = document.getElementById("run-btn");
    const charCountEl = document.getElementById("input-char-count");
    
    const resultsArea = document.getElementById("results-area");
    const spansContainer = document.getElementById("spans-container");
    const langDistBar = document.getElementById("lang-dist-bar");
    const langDistLegend = document.getElementById("lang-dist-legend");
    const tokensTbody = document.getElementById("tokens-tbody");
    
    const statLatency = document.getElementById("stat-latency");
    const statTokens = document.getElementById("stat-tokens");
    const statSpans = document.getElementById("stat-spans");

    // Real-time character count
    inputEl.addEventListener("input", () => {
        charCountEl.textContent = inputEl.value.length;
    });

    // Enter key triggers detection
    inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            runAnalysis();
        }
    });

    runBtn.addEventListener("click", runAnalysis);

    async function runAnalysis() {
        const text = inputEl.value.trim();
        if (!text) return;

        runBtn.disabled = true;
        runBtn.textContent = "Processing...";

        try {
            const response = await fetch("/api/identify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, allowed_langs: "all" })
            });

            if (response.ok) {
                const data = await response.json();
                renderResults(data);
            }
        } catch (err) {
            console.error("Inference request failed:", err);
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = "Identify Languages";
        }
    }

    function renderResults(data) {
        const { spans, enriched_spans, tokens, metrics } = data;
        if (!spans || spans.length === 0) return;

        resultsArea.style.display = "flex";

        // 1. Stats Bar
        statLatency.textContent = `Latency: ${metrics.latency_ms || 0} ms`;
        statTokens.textContent = `Tokens: ${metrics.total_tokens || 0}`;
        statSpans.textContent = `Spans: ${metrics.total_spans || 0}`;

        // 2. Language Distribution Bar & Legend
        langDistBar.innerHTML = "";
        langDistLegend.innerHTML = "";
        if (metrics.languages && metrics.languages.length > 0) {
            metrics.languages.forEach(l => {
                const seg = document.createElement("div");
                seg.className = "lang-dist-segment";
                seg.style.width = `${l.percentage}%`;
                seg.style.backgroundColor = l.color || "#2563eb";
                seg.title = `${l.name} (${l.percentage}%)`;
                langDistBar.appendChild(seg);

                const pill = document.createElement("div");
                pill.className = "dist-pill";
                pill.innerHTML = `
                    <span class="dist-dot" style="background-color: ${l.color};"></span>
                    <span>${l.name} (${l.code}): <strong>${l.percentage}%</strong></span>
                `;
                langDistLegend.appendChild(pill);
            });
        }

        // 3. Highlighted Spans Output Box
        spansContainer.innerHTML = "";
        const spanList = enriched_spans || spans.map(([text, lang]) => ({
            text, lang, name: lang.toUpperCase(), color: "#2563eb"
        }));

        spanList.forEach(item => {
            const tag = document.createElement("div");
            tag.className = "span-tag";
            tag.style.borderColor = item.color ? `${item.color}40` : "#cbd5e1";
            tag.innerHTML = `
                <span class="span-text">${escapeHtml(item.text)}</span>
                <span class="span-badge" style="--span-color: ${item.color || '#2563eb'};">
                    <span>${escapeHtml(item.name || item.lang)}</span>
                </span>
            `;
            spansContainer.appendChild(tag);
        });

        // 4. Token-by-Token Breakdown Table
        tokensTbody.innerHTML = "";
        if (tokens && tokens.length > 0) {
            tokens.forEach(t => {
                const tr = document.createElement("tr");
                const confPercent = Math.round((t.confidence || 1.0) * 100);
                tr.innerHTML = `
                    <td class="tok-word">${escapeHtml(t.token)}</td>
                    <td><span class="chip-code">${escapeHtml(t.script || 'Latin')}</span></td>
                    <td>
                        <span class="span-badge" style="--span-color: ${t.lang_color || '#2563eb'};">
                            <span>${escapeHtml(t.lang_name || t.label)}</span>
                        </span>
                    </td>
                    <td><strong>${confPercent}%</strong></td>
                    <td><span class="hint-text">${escapeHtml(t.reason || t.decided_by || 'Direct Model Decision')}</span></td>
                `;
                tokensTbody.appendChild(tr);
            });
        }
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Tab Navigation Logic
    const tabs = [
        { btn: document.getElementById("btn-tab-main"), pane: document.getElementById("tab-main") },
        { btn: document.getElementById("btn-tab-arch"), pane: document.getElementById("tab-arch") },
        { btn: document.getElementById("btn-tab-eval"), pane: document.getElementById("tab-eval") }
    ];

    tabs.forEach(({ btn, pane }) => {
        if (!btn || !pane) return;
        btn.addEventListener("click", async () => {
            tabs.forEach(t => {
                if (t.btn) t.btn.classList.remove("active");
                if (t.pane) t.pane.style.display = "none";
            });
            btn.classList.add("active");
            pane.style.display = "block";

            // If navigating to Architecture tab, render Mermaid flowchart
            if (btn.id === "btn-tab-arch" && window.mermaid && !pane.dataset.mermaidRendered) {
                pane.dataset.mermaidRendered = "true";
                try {
                    await window.mermaid.run({ querySelector: '.mermaid' });
                } catch (e) {
                    console.error("Mermaid execution error:", e);
                }
            }
        });
    });

    // Example Buttons Logic
    const exampleBtns = document.querySelectorAll(".example-btn");
    exampleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (inputEl) {
                inputEl.value = btn.getAttribute("data-text");
                charCountEl.textContent = inputEl.value.length;
                runAnalysis();
            }
        });
    });
});
