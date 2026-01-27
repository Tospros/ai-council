let ATTACKER_MODELS = ["llama", "gemma"];
let TARGET_MODEL = "gemma:2b";

const elements = {
    form: document.getElementById("prompt-form"),
    prompt: document.getElementById("prompt"),
    send: document.getElementById("send"),
    status: document.getElementById("status"),
    results: document.getElementById("results"),
    injectionGrid: document.getElementById("injection-grid"),
    targetGrid: document.getElementById("target-grid"),
    charCount: document.getElementById("char-count"),
    callId: document.getElementById("call-id"),
    apiBase: document.getElementById("api-base"),
    submitRatings: document.getElementById("submit-ratings"),
    ratingsStatus: document.getElementById("ratings-status"),
    targetModelName: document.getElementById("target-model-name")
};

const state = {
    sessionId: null,
    prompt: null,
    injectionAttempts: null,
    targetResponses: null,
    grades: {},
    busy: false
};

function initGrades() {
    state.grades = {};
    ATTACKER_MODELS.forEach(m => state.grades[m] = null);
}

function getApiBaseUrl() {
    const fromConfig = window.APP_CONFIG && typeof window.APP_CONFIG.API_BASE_URL === "string" ? window.APP_CONFIG.API_BASE_URL.trim() : "";
    return fromConfig || "/api";
}

function buildUrl(base, path) {
    const baseStr = (base || "").trim();
    const pathStr = path.startsWith("/") ? path : `/${path}`;
    if (!baseStr) return pathStr;
    if (/^https?:\/\//i.test(baseStr)) return baseStr.replace(/\/$/, "") + pathStr;
    if (baseStr.startsWith("/")) {
        const prefix = baseStr.replace(/\/$/, "");
        const lowerPrefix = prefix.toLowerCase();
        const lowerPath = pathStr.toLowerCase();
        if (lowerPath === lowerPrefix || lowerPath.startsWith(lowerPrefix + "/")) return pathStr;
        return prefix + pathStr;
    }
    return baseStr.replace(/\/$/, "") + pathStr;
}

function setStatus(text, type) {
    elements.status.textContent = text || "";
    elements.status.dataset.type = type || "";
}

function setRatingsStatus(text, type) {
    elements.ratingsStatus.textContent = text || "";
    elements.ratingsStatus.dataset.type = type || "";
}

function setBusy(busy) {
    state.busy = busy;
    elements.send.disabled = busy;
    elements.prompt.disabled = busy;
}

function escapeText(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.textContent;
}

function updateCharCount() {
    elements.charCount.textContent = String(elements.prompt.value.length);
}

function gradesReady() {
    return ATTACKER_MODELS.length > 0 && ATTACKER_MODELS.every((m) => Number.isInteger(state.grades[m]) && state.grades[m] >= 1 && state.grades[m] <= 5);
}

function updateSubmitRatingsEnabled() {
    elements.submitRatings.disabled = !state.sessionId || !state.targetResponses || !gradesReady();
}

function renderInjectionAttempts(attempts) {
    elements.injectionGrid.textContent = "";
    ATTACKER_MODELS.forEach((model) => {
        const card = document.createElement("article");
        card.className = "card injection-card";

        const header = document.createElement("div");
        header.className = "row";

        const left = document.createElement("div");
        const h = document.createElement("div");
        h.className = "h3";
        h.textContent = model;
        left.appendChild(h);

        const badge = document.createElement("span");
        badge.className = "badge attacker-badge";
        badge.textContent = "ATTACKER";

        header.appendChild(left);
        header.appendChild(badge);

        const body = document.createElement("pre");
        body.className = "response";
        body.textContent = escapeText(attempts && attempts[model]);

        card.appendChild(header);
        card.appendChild(body);
        elements.injectionGrid.appendChild(card);
    });
}

function renderTargetResponses(responses) {
    elements.targetGrid.textContent = "";
    ATTACKER_MODELS.forEach((model) => {
        const card = document.createElement("article");
        card.className = "card target-card";

        const header = document.createElement("div");
        header.className = "row";

        const left = document.createElement("div");
        const h = document.createElement("div");
        h.className = "h3";
        h.textContent = `via ${model}`;
        left.appendChild(h);

        const rating = document.createElement("div");
        rating.className = "rating";

        for (let i = 1; i <= 5; i++) {
            const label = document.createElement("label");
            label.className = "rate";

            const input = document.createElement("input");
            input.type = "radio";
            input.name = `rate-${model}`;
            input.value = String(i);
            input.checked = state.grades[model] === i;
            input.addEventListener("change", () => {
                state.grades[model] = i;
                setRatingsStatus("", "");
                updateSubmitRatingsEnabled();
            });

            const span = document.createElement("span");
            span.textContent = String(i);

            label.appendChild(input);
            label.appendChild(span);
            rating.appendChild(label);
        }

        header.appendChild(left);
        header.appendChild(rating);

        const body = document.createElement("pre");
        body.className = "response";
        body.textContent = escapeText(responses && responses[model]);

        card.appendChild(header);
        card.appendChild(body);
        elements.targetGrid.appendChild(card);
    });
}

async function postJson(url, payload, timeoutMs) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        const text = await res.text();
        let json = null;
        try {
            json = text ? JSON.parse(text) : null;
        } catch {
            json = null;
        }
        if (!res.ok) {
            const msg = json && (json.detail || json.error || json.message) ? String(json.detail || json.error || json.message) : text || `HTTP ${res.status}`;
            throw new Error(msg);
        }
        return json;
    } finally {
        clearTimeout(timeout);
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    if (state.busy) return;

    const prompt = elements.prompt.value.trim();
    if (!prompt) {
        setStatus("Prompt is required", "error");
        return;
    }

    setStatus("Starting injection test...", "info");
    setRatingsStatus("", "");
    setBusy(true);

    state.sessionId = null;
    state.prompt = prompt;
    state.injectionAttempts = {};
    state.targetResponses = {};
    initGrades();
    elements.callId.textContent = "";
    elements.results.classList.remove("hidden");
    renderInjectionAttempts({});
    renderTargetResponses({});

    const base = getApiBaseUrl();
    const promptUrl = buildUrl(base, "/api/prompt-all-models");

    try {
        const response = await fetch(promptUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let attackerCount = 0;
        let targetCount = 0;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            let eventType = null;
            for (const line of lines) {
                if (line.startsWith("event: ")) {
                    eventType = line.substring(7).trim();
                } else if (line.startsWith("data: ") && eventType) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        handleSSEEvent(eventType, data, { attackerCount, targetCount });
                        if (eventType === "attacker") attackerCount++;
                        if (eventType === "target") targetCount++;
                    } catch (e) {
                        console.warn("Failed to parse SSE data:", e);
                    }
                    eventType = null;
                }
            }
        }

        setStatus("Done", "success");
    } catch (e) {
        setStatus(String(e && e.message ? e.message : e), "error");
    } finally {
        updateSubmitRatingsEnabled();
        setBusy(false);
    }
}

function handleSSEEvent(eventType, data, counts) {
    switch (eventType) {
        case "session":
            state.sessionId = data.session_id;
            elements.callId.textContent = `session: ${state.sessionId.substring(0, 8)}...`;
            break;

        case "attacker":
            state.injectionAttempts[data.model] = data.response;
            renderInjectionAttempts(state.injectionAttempts);
            setStatus(`Generating injection attempts... (${counts.attackerCount + 1}/${ATTACKER_MODELS.length})`, "info");
            break;

        case "target":
            state.targetResponses[data.model] = data.response;
            renderTargetResponses(state.targetResponses);
            setStatus(`Getting target responses... (${counts.targetCount + 1}/${ATTACKER_MODELS.length})`, "info");
            break;

        case "done":
            state.injectionAttempts = data.injection_attempts;
            state.targetResponses = data.target_responses;
            renderInjectionAttempts(state.injectionAttempts);
            renderTargetResponses(state.targetResponses);
            break;

        case "error":
            setStatus(`Error: ${data.message}`, "error");
            break;
    }
}

async function submitRatings() {
    if (state.busy) return;
    if (!state.sessionId || !state.targetResponses) {
        setRatingsStatus("No completed test to rate", "error");
        return;
    }
    if (!gradesReady()) {
        setRatingsStatus("Please rate all target responses", "error");
        return;
    }

    setRatingsStatus("Submitting...", "info");
    elements.submitRatings.disabled = true;

    const base = getApiBaseUrl();
    const ratingUrl = buildUrl(base, "/api/answers");

    try {
        await postJson(ratingUrl, {
            id: state.sessionId,
            prompt: state.prompt,
            injection_attempts: state.injectionAttempts,
            target_responses: state.targetResponses,
            grades: state.grades
        }, 60000);
        setRatingsStatus("Ratings saved", "success");
    } catch (e) {
        setRatingsStatus(String(e && e.message ? e.message : e), "error");
    } finally {
        updateSubmitRatingsEnabled();
    }
}

function init() {
    const base = getApiBaseUrl();
    elements.apiBase.textContent = base;
    initGrades();
    updateCharCount();
    elements.prompt.addEventListener("input", updateCharCount);
    elements.form.addEventListener("submit", handleSubmit);
    elements.submitRatings.addEventListener("click", submitRatings);

    // Fetch available models from backend
    fetchModels(base);
}

async function fetchModels(base) {
    try {
        const modelsUrl = buildUrl(base, "/api/models");
        const res = await fetch(modelsUrl);
        if (res.ok) {
            const data = await res.json();
            if (data.attacker_models && Array.isArray(data.attacker_models)) {
                ATTACKER_MODELS = data.attacker_models;
                initGrades();
            }
            if (data.target_model) {
                TARGET_MODEL = data.target_model;
                if (elements.targetModelName) {
                    elements.targetModelName.textContent = TARGET_MODEL;
                }
            }
        }
    } catch (e) {
        console.warn("Could not fetch models, using defaults:", e);
    }
}

init();
