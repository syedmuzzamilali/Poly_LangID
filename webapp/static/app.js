document.addEventListener("DOMContentLoaded", () => {
    const inputEl = document.getElementById("input-text");
    const runBtn = document.getElementById("run-btn");
    const spansContainer = document.getElementById("spans-container");

    runBtn.addEventListener("click", runAnalysis);
    inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            runAnalysis();
        }
    });

    async function runAnalysis() {
        const text = inputEl.value.trim();
        if (!text) return;

        runBtn.disabled = true;
        runBtn.textContent = "...";
        spansContainer.innerHTML = "";

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
            console.error("Error:", err);
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = "Enter";
        }
    }

    function renderResults(data) {
        const { spans } = data;
        if (!spans || spans.length === 0) return;

        spansContainer.innerHTML = "";
        spans.forEach(([spanText, lang]) => {
            const tag = document.createElement("span");
            tag.className = "span-tag";
            tag.innerHTML = `<span>${escapeHtml(spanText)}</span><span class="span-lang">[${escapeHtml(lang || "und")}]</span>`;
            spansContainer.appendChild(tag);
        });
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
    const btnTabMain = document.getElementById("btn-tab-main");
    const btnTabTech = document.getElementById("btn-tab-tech");
    const tabMain = document.getElementById("tab-main");
    const tabTech = document.getElementById("tab-tech");

    if (btnTabMain && btnTabTech && tabMain && tabTech) {
        btnTabMain.addEventListener("click", () => {
            btnTabMain.classList.add("active");
            btnTabTech.classList.remove("active");
            tabMain.style.display = "block";
            tabTech.style.display = "none";
        });

        btnTabTech.addEventListener("click", async () => {
            btnTabTech.classList.add("active");
            btnTabMain.classList.remove("active");
            tabTech.style.display = "block";
            tabMain.style.display = "none";

            if (window.mermaid && !tabTech.dataset.mermaidRendered) {
                tabTech.dataset.mermaidRendered = "true";
                try {
                    await window.mermaid.run({ querySelector: '.mermaid' });
                } catch (e) {
                    console.error("Mermaid run error:", e);
                }
            }
        });
    }

    // Example Buttons Logic
    const exampleBtns = document.querySelectorAll(".example-btn");
    exampleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (inputEl && runBtn) {
                inputEl.value = btn.getAttribute("data-text");
                runBtn.click();
            }
        });
    });
});
