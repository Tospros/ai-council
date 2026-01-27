// API Configuration
const API_BASE = window.location.origin;

// State
let currentSessionId = null;
let injectionAttempts = {};
let targetResponses = {};
let currentPrompt = '';
let historyOffset = 0;
const historyLimit = 10;
let totalHistoryItems = 0;

// DOM Elements
const elements = {
    // Tabs
    tabs: document.querySelectorAll('.tab'),
    tabContents: document.querySelectorAll('.tab-content'),

    // Health
    healthStatus: document.getElementById('health-status'),
    statusText: document.querySelector('.status-text'),

    // Test form
    promptInput: document.getElementById('prompt-input'),
    charCount: document.getElementById('char-count'),
    submitBtn: document.getElementById('submit-btn'),

    // Results
    resultsSection: document.getElementById('results-section'),
    sessionId: document.getElementById('session-id'),
    resultsContainer: document.getElementById('results-container'),
    ratingSection: document.getElementById('rating-section'),
    ratingInputs: document.getElementById('rating-inputs'),
    submitRatingsBtn: document.getElementById('submit-ratings-btn'),

    // History
    filterModel: document.getElementById('filter-model'),
    refreshHistory: document.getElementById('refresh-history'),
    historyContainer: document.getElementById('history-container'),
    pagination: document.getElementById('pagination'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageInfo: document.getElementById('page-info'),

    // Toast
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initForm();
    initHistory();
    checkHealth();

    // Check health every 30 seconds
    setInterval(checkHealth, 30000);
});

// Tab Navigation
function initTabs() {
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;

            elements.tabs.forEach(t => t.classList.remove('active'));
            elements.tabContents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');

            if (tabId === 'history') {
                loadHistory();
            }
        });
    });
}

// Health Check
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        elements.healthStatus.classList.remove('healthy', 'unhealthy');

        if (data.status === 'healthy') {
            elements.healthStatus.classList.add('healthy');
            elements.statusText.textContent = `Healthy | ${data.attacker_models.length} attackers | Target: ${data.target_model}`;
        } else {
            elements.healthStatus.classList.add('unhealthy');
            elements.statusText.textContent = 'Unhealthy';
        }
    } catch (error) {
        elements.healthStatus.classList.remove('healthy');
        elements.healthStatus.classList.add('unhealthy');
        elements.statusText.textContent = 'Connection failed';
    }
}

// Form Handling
function initForm() {
    // Character count
    elements.promptInput.addEventListener('input', () => {
        const count = elements.promptInput.value.length;
        elements.charCount.textContent = count;

        if (count > 10000) {
            elements.charCount.style.color = 'var(--accent-red)';
        } else {
            elements.charCount.style.color = '';
        }
    });

    // Submit button
    elements.submitBtn.addEventListener('click', runTest);

    // Submit ratings button
    elements.submitRatingsBtn.addEventListener('click', submitRatings);

    // Enter key to submit
    elements.promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            runTest();
        }
    });
}

// Run Injection Test
async function runTest() {
    const prompt = elements.promptInput.value.trim();

    if (!prompt) {
        showToast('Please enter a prompt', 'error');
        return;
    }

    if (prompt.length > 10000) {
        showToast('Prompt is too long (max 10000 characters)', 'error');
        return;
    }

    // Reset state
    currentSessionId = null;
    injectionAttempts = {};
    targetResponses = {};
    currentPrompt = prompt;

    // Update UI
    setButtonLoading(elements.submitBtn, true);
    elements.resultsSection.classList.remove('hidden');
    elements.resultsContainer.innerHTML = '<div class="stream-loading"><span>Waiting for results</span><span class="dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span></div>';
    elements.ratingSection.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/prompt-all-models`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Handle SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        elements.resultsContainer.innerHTML = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete events
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('event:')) {
                    const eventType = line.replace('event:', '').trim();
                    continue;
                }

                if (line.startsWith('data:')) {
                    const data = line.replace('data:', '').trim();
                    if (data) {
                        try {
                            const parsed = JSON.parse(data);
                            handleStreamEvent(parsed);
                        } catch (e) {
                            console.error('Failed to parse SSE data:', e);
                        }
                    }
                }
            }
        }

        // Show rating section after completion
        if (Object.keys(injectionAttempts).length > 0) {
            showRatingSection();
        }

    } catch (error) {
        console.error('Test failed:', error);
        elements.resultsContainer.innerHTML = `<div class="history-empty">Error: ${error.message}</div>`;
        showToast('Test failed: ' + error.message, 'error');
    } finally {
        setButtonLoading(elements.submitBtn, false);
    }
}

// Handle SSE Stream Events
function handleStreamEvent(data) {
    if (data.session_id) {
        currentSessionId = data.session_id;
        elements.sessionId.textContent = `Session: ${data.session_id.slice(0, 8)}...`;
        return;
    }

    if (data.model && data.response !== undefined) {
        // Determine if this is an attacker or target response based on context
        // The API sends attacker events first, then target events
        const modelKey = data.model;

        if (!injectionAttempts[modelKey]) {
            // First response for this model is the attacker response
            injectionAttempts[modelKey] = data.response;
            addResultCard(modelKey, 'attacker', data.response);
        } else if (!targetResponses[modelKey]) {
            // Second response for this model is the target response
            targetResponses[modelKey] = data.response;
            addResultCard(modelKey, 'target', data.response);
        }
        return;
    }

    if (data.error) {
        showToast('Error: ' + data.error, 'error');
        return;
    }

    // Handle 'done' event with complete results
    if (data.injection_attempts) {
        injectionAttempts = data.injection_attempts;
    }
    if (data.target_responses) {
        targetResponses = data.target_responses;
    }
}

// Add Result Card to UI
function addResultCard(model, type, content) {
    // Check if we already have a card for this model
    let modelContainer = document.getElementById(`result-${model}`);

    if (!modelContainer) {
        modelContainer = document.createElement('div');
        modelContainer.id = `result-${model}`;
        modelContainer.className = 'result-card';
        modelContainer.innerHTML = `
            <div class="result-card-header">
                <span class="model-badge attacker">${model}</span>
                <span class="result-label">Injection Test</span>
            </div>
            <div class="result-sections"></div>
        `;
        elements.resultsContainer.appendChild(modelContainer);
    }

    const sectionsContainer = modelContainer.querySelector('.result-sections');

    const section = document.createElement('div');
    section.className = 'result-section';
    section.innerHTML = `
        <div class="result-section-title">${type === 'attacker' ? 'Injection Attempt' : 'Target Response'}</div>
        <div class="result-content">${escapeHtml(content)}</div>
    `;

    sectionsContainer.appendChild(section);
}

// Show Rating Section
function showRatingSection() {
    elements.ratingSection.classList.remove('hidden');
    elements.ratingInputs.innerHTML = '';

    Object.keys(injectionAttempts).forEach(model => {
        const ratingItem = document.createElement('div');
        ratingItem.className = 'rating-item';
        ratingItem.innerHTML = `
            <label>${model} Injection</label>
            <div class="rating-stars" data-model="${model}">
                ${[5, 4, 3, 2, 1].map(i => `
                    <input type="radio" name="rating-${model}" id="rating-${model}-${i}" value="${i}">
                    <label for="rating-${model}-${i}" title="${i} stars">&#9733;</label>
                `).join('')}
            </div>
        `;
        elements.ratingInputs.appendChild(ratingItem);
    });
}

// Submit Ratings
async function submitRatings() {
    const grades = {};
    let allRated = true;

    Object.keys(injectionAttempts).forEach(model => {
        const selected = document.querySelector(`input[name="rating-${model}"]:checked`);
        if (selected) {
            grades[model] = parseInt(selected.value);
        } else {
            allRated = false;
        }
    });

    if (!allRated) {
        showToast('Please rate all injection attempts', 'error');
        return;
    }

    setButtonLoading(elements.submitRatingsBtn, true);

    try {
        const response = await fetch(`${API_BASE}/api/answers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: currentSessionId,
                prompt: currentPrompt,
                injection_attempts: injectionAttempts,
                target_responses: targetResponses,
                grades
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast(`Ratings saved successfully (${data.saved_count} records)`, 'success');
            elements.ratingSection.classList.add('hidden');
        } else {
            throw new Error(data.message || 'Failed to save ratings');
        }
    } catch (error) {
        console.error('Failed to submit ratings:', error);
        showToast('Failed to submit ratings: ' + error.message, 'error');
    } finally {
        setButtonLoading(elements.submitRatingsBtn, false);
    }
}

// History
function initHistory() {
    elements.refreshHistory.addEventListener('click', () => {
        historyOffset = 0;
        loadHistory();
    });

    elements.filterModel.addEventListener('change', () => {
        historyOffset = 0;
        loadHistory();
    });

    elements.prevPage.addEventListener('click', () => {
        if (historyOffset >= historyLimit) {
            historyOffset -= historyLimit;
            loadHistory();
        }
    });

    elements.nextPage.addEventListener('click', () => {
        if (historyOffset + historyLimit < totalHistoryItems) {
            historyOffset += historyLimit;
            loadHistory();
        }
    });

    // Load models for filter
    loadModels();
}

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/models`);
        const data = await response.json();

        // Add attacker models to filter
        data.attacker_models.forEach(model => {
            const option = document.createElement('option');
            option.value = `target_via_${model}`;
            option.textContent = `Target via ${model}`;
            elements.filterModel.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

async function loadHistory() {
    elements.historyContainer.innerHTML = '<div class="loading-placeholder"><span class="spinner"></span> Loading history...</div>';

    try {
        let url = `${API_BASE}/api/history?limit=${historyLimit}&offset=${historyOffset}`;

        const modelFilter = elements.filterModel.value;
        if (modelFilter) {
            url += `&llm_name=${encodeURIComponent(modelFilter)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        totalHistoryItems = data.total;

        if (data.items.length === 0) {
            elements.historyContainer.innerHTML = '<div class="history-empty">No history found</div>';
            elements.pagination.classList.add('hidden');
            return;
        }

        elements.historyContainer.innerHTML = data.items.map(item => `
            <div class="history-item">
                <div class="history-item-header">
                    <div class="history-item-meta">
                        <span class="history-model">${escapeHtml(item.llm_name)}</span>
                        <span class="history-date">${formatDate(item.created_at)}</span>
                    </div>
                    <div class="history-rating">
                        ${renderStars(item.rating)}
                    </div>
                </div>
                <div class="history-prompt"><strong>Prompt:</strong> ${escapeHtml(item.prompt || 'N/A')}</div>
                ${item.response ? `<div class="history-response">${escapeHtml(item.response)}</div>` : ''}
            </div>
        `).join('');

        // Update pagination
        updatePagination();

    } catch (error) {
        console.error('Failed to load history:', error);
        elements.historyContainer.innerHTML = `<div class="history-empty">Failed to load history: ${error.message}</div>`;
    }
}

function updatePagination() {
    const currentPage = Math.floor(historyOffset / historyLimit) + 1;
    const totalPages = Math.ceil(totalHistoryItems / historyLimit);

    if (totalPages <= 1) {
        elements.pagination.classList.add('hidden');
        return;
    }

    elements.pagination.classList.remove('hidden');
    elements.pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    elements.prevPage.disabled = currentPage <= 1;
    elements.nextPage.disabled = currentPage >= totalPages;
}

// Utility Functions
function setButtonLoading(button, loading) {
    const textEl = button.querySelector('.btn-text');
    const loadingEl = button.querySelector('.btn-loading');

    if (loading) {
        textEl.classList.add('hidden');
        loadingEl.classList.remove('hidden');
        button.disabled = true;
    } else {
        textEl.classList.remove('hidden');
        loadingEl.classList.add('hidden');
        button.disabled = false;
    }
}

function showToast(message, type = 'info') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.add('show');

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderStars(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        stars += `<span class="star ${i <= rating ? '' : 'empty'}">&#9733;</span>`;
    }
    return stars;
}
