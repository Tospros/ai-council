const MODELS = ["llama", "mistral", "gemma"];

const elements = {
    form: document.getElementById("prompt-form"),
    prompt: document.getElementById("prompt"),
    send: document.getElementById("send"),
    status: document.getElementById("status"),
    results: document.getElementById("results"),
    grid: document.getElementById("responses-grid"),
    charCount: document.getElementById("char-count"),
    callId: document.getElementById("call-id"),
    apiBase: document.getElementById("api-base"),
    submitRatings: document.getElementById("submit-ratings"),
    ratingsStatus: document.getElementById("ratings-status")
};

const state = {
    callId: null,
    responses: null,
    grades: { llama: null, mistral: null, gemma: null },
    busy: false
};

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

function newCallId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
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
    return MODELS.every((m) => Number.isInteger(state.grades[m]) && state.grades[m] >= 1 && state.grades[m] <= 5);
}

function updateSubmitRatingsEnabled() {
    elements.submitRatings.disabled = !state.callId || !state.responses || !gradesReady();
}

function renderResponses(responses) {
    elements.grid.textContent = "";
    MODELS.forEach((model) => {
        const card = document.createElement("article");
        card.className = "card";

        const header = document.createElement("div");
        header.className = "row";

        const left = document.createElement("div");
        const h = document.createElement("div");
        h.className = "h3";
        h.textContent = model;
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
        elements.grid.appendChild(card);
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

    setStatus("Sending...", "info");
    setRatingsStatus("", "");
    setBusy(true);

    state.callId = newCallId();
    state.responses = null;
    state.grades = { llama: null, mistral: null, gemma: null };
    elements.callId.textContent = `call id: ${state.callId}`;

    const base = getApiBaseUrl();
    const promptUrl = buildUrl(base, "/api/prompt-all-models");

    try {
        const data = await postJson(promptUrl, { prompt }, 180000);
        if (!data || typeof data !== "object") throw new Error("Invalid response");
        state.responses = data;
        elements.results.classList.remove("hidden");
        renderResponses(state.responses);
        setStatus("Done", "success");
    } catch (e) {
        setStatus(String(e && e.message ? e.message : e), "error");
    } finally {
        updateSubmitRatingsEnabled();
        setBusy(false);
    }
}

async function submitRatings() {
    if (state.busy) return;
    if (!state.callId || !state.responses) {
        setRatingsStatus("No completed call to rate", "error");
        return;
    }
    if (!gradesReady()) {
        setRatingsStatus("Please rate all three answers", "error");
        return;
    }

    setRatingsStatus("Submitting...", "info");
    elements.submitRatings.disabled = true;

    const base = getApiBaseUrl();
    const ratingUrl = buildUrl(base, "/api/answers");

    try {
        await postJson(ratingUrl, { id: state.callId, grades: state.grades }, 60000);
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
    updateCharCount();
    elements.prompt.addEventListener("input", updateCharCount);
    elements.form.addEventListener("submit", handleSubmit);
    elements.submitRatings.addEventListener("click", submitRatings);
}

init();
