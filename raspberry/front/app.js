(function() {
    "use strict";

    // State
    const state = {
        sessionId: null,
        prompt: null,
        attackerModels: [],
        targetModel: "",
        injectionAttempts: {},
        targetResponses: {},
        grades: {},
        loading: false
    };

    // DOM elements
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const dom = {
        form: $("#prompt-form"),
        prompt: $("#prompt"),
        send: $("#send"),
        status: $("#status"),
        results: $("#results"),
        injectionGrid: $("#injection-grid"),
        targetGrid: $("#target-grid"),
        charCount: $("#char-count"),
        callId: $("#call-id"),
        apiBase: $("#api-base"),
        submitRatings: $("#submit-ratings"),
        ratingsStatus: $("#ratings-status"),
        targetModelName: $("#target-model-name")
    };

    // Config
    function getApiBase() {
        if (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) {
            return window.APP_CONFIG.API_BASE_URL.replace(/\/$/, "");
        }
        return "";
    }

    // UI helpers
    function setStatus(msg, type) {
        dom.status.textContent = msg;
        dom.status.dataset.type = type || "";
    }

    function setRatingsStatus(msg, type) {
        dom.ratingsStatus.textContent = msg;
        dom.ratingsStatus.dataset.type = type || "";
    }

    function setLoading(loading) {
        state.loading = loading;
        dom.send.disabled = loading;
        dom.prompt.disabled = loading;
    }

    function updateCharCount() {
        dom.charCount.textContent = dom.prompt.value.length;
    }

    // Initialize grades for current attacker models
    function initGrades() {
        state.grades = {};
        state.attackerModels.forEach(m => { state.grades[m] = null; });
    }

    // Check if all grades are set
    function allGradesSet() {
        return state.attackerModels.length > 0 &&
            state.attackerModels.every(m => state.grades[m] >= 1 && state.grades[m] <= 5);
    }

    function updateSubmitButton() {
        dom.submitRatings.disabled = !state.sessionId || !allGradesSet();
    }

    // Render injection attempts cards
    function renderInjectionAttempts() {
        dom.injectionGrid.innerHTML = "";
        state.attackerModels.forEach(model => {
            const response = state.injectionAttempts[model] || "";
            const card = document.createElement("article");
            card.className = "card injection-card";
            card.innerHTML = `
                <div class="row">
                    <div class="h3">${escapeHtml(model)}</div>
                    <span class="badge attacker-badge">ATTACKER</span>
                </div>
                <pre class="response">${escapeHtml(response)}</pre>
            `;
            dom.injectionGrid.appendChild(card);
        });
    }

    // Render target responses cards with rating inputs
    function renderTargetResponses() {
        dom.targetGrid.innerHTML = "";
        state.attackerModels.forEach(model => {
            const response = state.targetResponses[model] || "";
            const card = document.createElement("article");
            card.className = "card target-card";

            const ratingHtml = [1, 2, 3, 4, 5].map(i => {
                const checked = state.grades[model] === i ? "checked" : "";
                return `
                    <label class="rate">
                        <input type="radio" name="rate-${model}" value="${i}" ${checked}>
                        <span>${i}</span>
                    </label>
                `;
            }).join("");

            card.innerHTML = `
                <div class="row">
                    <div class="h3">via ${escapeHtml(model)}</div>
                    <div class="rating">${ratingHtml}</div>
                </div>
                <pre class="response">${escapeHtml(response)}</pre>
            `;

            // Add rating change listeners
            card.querySelectorAll('input[type="radio"]').forEach(input => {
                input.addEventListener("change", () => {
                    state.grades[model] = parseInt(input.value, 10);
                    setRatingsStatus("", "");
                    updateSubmitButton();
                });
            });

            dom.targetGrid.appendChild(card);
        });
    }

    function escapeHtml(str) {
        if (str == null) return "";
        const div = document.createElement("div");
        div.textContent = String(str);
        return div.innerHTML;
    }

    // Fetch available models from API
    async function fetchModels() {
        try {
            const res = await fetch(getApiBase() + "/api/models");
            if (!res.ok) throw new Error("Failed to fetch models");
            const data = await res.json();
            if (Array.isArray(data.attacker_models)) {
                state.attackerModels = data.attacker_models;
            }
            if (data.target_model) {
                state.targetModel = data.target_model;
                if (dom.targetModelName) {
                    dom.targetModelName.textContent = data.target_model;
                }
            }
            initGrades();
        } catch (e) {
            console.warn("Could not fetch models:", e);
            // Default fallback
            state.attackerModels = ["llama", "gemma"];
            initGrades();
        }
    }

    // Parse SSE stream manually (more reliable than EventSource for POST)
    async function streamSSE(url, body, handlers) {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || `HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete events (separated by double newline)
            const events = buffer.split("\n\n");
            buffer = events.pop(); // Keep incomplete event in buffer

            for (const eventBlock of events) {
                if (!eventBlock.trim()) continue;

                const lines = eventBlock.split("\n");
                let eventType = null;
                let eventData = null;

                for (const line of lines) {
                    if (line.startsWith("event:")) {
                        eventType = line.slice(6).trim();
                    } else if (line.startsWith("data:")) {
                        eventData = line.slice(5).trim();
                    }
                }

                if (eventType && eventData) {
                    try {
                        const parsed = JSON.parse(eventData);
                        if (handlers[eventType]) {
                            handlers[eventType](parsed);
                        }
                    } catch (e) {
                        console.warn("Failed to parse SSE data:", eventData, e);
                    }
                }
            }
        }

        // Process any remaining data
        if (buffer.trim()) {
            const lines = buffer.split("\n");
            let eventType = null;
            let eventData = null;
            for (const line of lines) {
                if (line.startsWith("event:")) {
                    eventType = line.slice(6).trim();
                } else if (line.startsWith("data:")) {
                    eventData = line.slice(5).trim();
                }
            }
            if (eventType && eventData) {
                try {
                    const parsed = JSON.parse(eventData);
                    if (handlers[eventType]) {
                        handlers[eventType](parsed);
                    }
                } catch (e) {
                    console.warn("Failed to parse final SSE data:", e);
                }
            }
        }
    }

    // Main form submission
    async function handleSubmit(e) {
        e.preventDefault();
        if (state.loading) return;

        const prompt = dom.prompt.value.trim();
        if (!prompt) {
            setStatus("Please enter a prompt", "error");
            return;
        }

        // Reset state
        state.sessionId = null;
        state.prompt = prompt;
        state.injectionAttempts = {};
        state.targetResponses = {};
        initGrades();

        // Show results section
        dom.results.classList.remove("hidden");
        dom.callId.textContent = "";
        renderInjectionAttempts();
        renderTargetResponses();

        setStatus("Connecting...", "info");
        setRatingsStatus("", "");
        setLoading(true);

        let attackerCount = 0;
        let targetCount = 0;

        try {
            await streamSSE(getApiBase() + "/api/prompt-all-models", { prompt }, {
                session: (data) => {
                    state.sessionId = data.session_id;
                    dom.callId.textContent = `Session: ${data.session_id.slice(0, 8)}...`;
                    setStatus("Session started", "info");
                },

                attacker: (data) => {
                    attackerCount++;
                    state.injectionAttempts[data.model] = data.response;
                    renderInjectionAttempts();
                    setStatus(`Generating injections... (${attackerCount}/${state.attackerModels.length})`, "info");
                },

                target: (data) => {
                    targetCount++;
                    state.targetResponses[data.model] = data.response;
                    renderTargetResponses();
                    setStatus(`Getting target responses... (${targetCount}/${state.attackerModels.length})`, "info");
                },

                done: (data) => {
                    state.injectionAttempts = data.injection_attempts || state.injectionAttempts;
                    state.targetResponses = data.target_responses || state.targetResponses;
                    renderInjectionAttempts();
                    renderTargetResponses();
                    setStatus("Complete", "success");
                },

                error: (data) => {
                    setStatus(`Error: ${data.message}`, "error");
                }
            });

            if (!dom.status.textContent.startsWith("Error")) {
                setStatus("Complete", "success");
            }
        } catch (err) {
            console.error("Stream error:", err);
            setStatus(err.message || "Connection failed", "error");
        } finally {
            setLoading(false);
            updateSubmitButton();
        }
    }

    // Submit ratings
    async function handleSubmitRatings() {
        if (state.loading) return;
        if (!state.sessionId) {
            setRatingsStatus("No session to rate", "error");
            return;
        }
        if (!allGradesSet()) {
            setRatingsStatus("Please rate all responses (1-5)", "error");
            return;
        }

        setRatingsStatus("Submitting...", "info");
        dom.submitRatings.disabled = true;

        try {
            const res = await fetch(getApiBase() + "/api/answers", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: state.sessionId,
                    prompt: state.prompt,
                    injection_attempts: state.injectionAttempts,
                    target_responses: state.targetResponses,
                    grades: state.grades
                })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || data.message || `HTTP ${res.status}`);
            }

            setRatingsStatus("Ratings saved!", "success");
        } catch (err) {
            console.error("Rating error:", err);
            setRatingsStatus(err.message || "Failed to save ratings", "error");
        } finally {
            updateSubmitButton();
        }
    }

    // Initialize
    function init() {
        dom.apiBase.textContent = getApiBase() || "(same origin)";
        dom.prompt.addEventListener("input", updateCharCount);
        dom.form.addEventListener("submit", handleSubmit);
        dom.submitRatings.addEventListener("click", handleSubmitRatings);
        updateCharCount();
        fetchModels();
    }

    // Start
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
