
const CONFIG = {
    API_ENDPOINT: 'https://python-backend.matra.cc',
    TIMEOUT: 120000, 
    DEBOUNCE_DELAY: 300,
    MAX_CHARS: 5000,
    MODELS: [
        { id: 1, name: 'GPT-4', icon: '🔵' },
        { id: 2, name: 'Claude', icon: '🟣' },
        { id: 3, name: 'Gemini', icon: '🟢' }
    ]
};


const state = {
    isProcessing: false,
    abortController: null,
    history: [],
    currentRequest: null
};


const elements = {
    promptInput: document.getElementById('prompt-input'),
    submitBtn: document.getElementById('submit-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    charCount: document.getElementById('char-count'),
    resultsSection: document.getElementById('results-section'),
    arbiterSection: document.getElementById('arbiter-section'),
    historySection: document.getElementById('history-section'),
    historyList: document.getElementById('history-list'),
    historyCount: document.getElementById('history-count'),
    toastContainer: document.getElementById('toast-container')
};




function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}


function formatTime(milliseconds) {
    const seconds = (milliseconds / 1000).toFixed(2);
    return `${seconds}s`;
}


function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}




function updateCharCount() {
    const length = elements.promptInput.value.length;
    elements.charCount.textContent = `${length} / ${CONFIG.MAX_CHARS}`;
    
    if (length > CONFIG.MAX_CHARS * 0.9) {
        elements.charCount.style.color = 'var(--error-color)';
    } else {
        elements.charCount.style.color = 'var(--text-tertiary)';
    }
}


function updateLLMStatus(llmId, status, time = null) {
    const statusElement = document.getElementById(`status-${llmId}`);
    const statusText = statusElement.querySelector('.status-text');
    const timeElement = document.getElementById(`time-${llmId}`);
    
    const statusMessages = {
        waiting: 'Oczekiwanie...',
        loading: 'Przetwarzanie...',
        success: 'Gotowe',
        error: 'Błąd'
    };
    
    statusText.textContent = statusMessages[status] || status;
    
    if (time !== null) {
        timeElement.textContent = formatTime(time);
        timeElement.classList.remove('hidden');
    }
}


function toggleLoadingSkeleton(llmId, show) {
    const loading = document.getElementById(`loading-${llmId}`);
    const response = document.getElementById(`response-${llmId}`);
    const error = document.getElementById(`error-${llmId}`);
    
    if (show) {
        loading.classList.remove('hidden');
        response.classList.add('hidden');
        error.classList.add('hidden');
    } else {
        loading.classList.add('hidden');
    }
}


function displayLLMResponse(llmId, text, isError = false) {
    const responseElement = document.getElementById(`response-${llmId}`);
    const errorElement = document.getElementById(`error-${llmId}`);
    
    toggleLoadingSkeleton(llmId, false);
    
    if (isError) {
        errorElement.textContent = text;
        errorElement.classList.remove('hidden');
        responseElement.classList.add('hidden');
    } else {
        responseElement.textContent = text;
        responseElement.classList.remove('hidden');
        errorElement.classList.add('hidden');
    }
}


function resetUI() {
    
    elements.resultsSection.classList.add('hidden');
    elements.arbiterSection.classList.add('hidden');
    
    
    for (let i = 1; i <= 3; i++) {
        updateLLMStatus(i, 'waiting');
        toggleLoadingSkeleton(i, false);
        document.getElementById(`response-${i}`).classList.add('hidden');
        document.getElementById(`error-${i}`).classList.add('hidden');
        document.getElementById(`time-${i}`).classList.add('hidden');
    }
    
    
    updateLLMStatus('arbiter', 'waiting');
    toggleLoadingSkeleton('arbiter', false);
    document.getElementById('response-arbiter').classList.add('hidden');
    document.getElementById('error-arbiter').classList.add('hidden');
    document.getElementById('time-arbiter').classList.add('hidden');
}


function updateButtonStates(isProcessing) {
    const btnText = elements.submitBtn.querySelector('.btn-text');
    const btnLoader = elements.submitBtn.querySelector('.btn-loader');
    
    if (isProcessing) {
        elements.submitBtn.disabled = true;
        elements.cancelBtn.disabled = false;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
    } else {
        elements.submitBtn.disabled = false;
        elements.cancelBtn.disabled = true;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
    }
}




async function callLLM(llmId, prompt, signal) {
    const startTime = Date.now();
    
    try {
        
        
        const response = await fetch(CONFIG.API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                llm_id: llmId,
                prompt: prompt
            }),
            signal: signal
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const endTime = Date.now();
        
        return {
            success: true,
            response: data.response,
            time: endTime - startTime
        };
        
        
        /*
        await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
        
        if (signal.aborted) {
            throw new Error('Request aborted');
        }
        
        const endTime = Date.now();
        
        
        if (Math.random() < 0.1) {
            throw new Error('Simulated API error');
        }
        
        return {
            success: true,
            response: `To jest odpowiedź od modelu ${CONFIG.MODELS[llmId - 1].name} na pytanie: "${prompt}". Lorem ipsum dolor sit amet, consectetur adipiscing elit.`,
            time: endTime - startTime
        };
        */
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Request cancelled');
        }
        throw error;
    }
}


async function callArbiter(prompt, responses, signal) {
    const startTime = Date.now();
    
    try {
        
        const response = await fetch(`${CONFIG.API_ENDPOINT}/arbiter`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                original_prompt: prompt,
                llm_responses: responses
            }),
            signal: signal
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const endTime = Date.now();
        
        return {
            success: true,
            response: data.synthesis,
            time: endTime - startTime
        };
        
        
        /*
        await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 2000));
        
        if (signal.aborted) {
            throw new Error('Request aborted');
        }
        
        const endTime = Date.now();
        
        return {
            success: true,
            response: `Synteza odpowiedzi od wszystkich modeli AI:\n\nPo przeanalizowaniu odpowiedzi od GPT-4, Claude i Gemini, mogę przedstawić następującą zbiorczą syntezę...\n\n${responses.map((r, i) => `Model ${i + 1}: ${r.substring(0, 50)}...`).join('\n')}`,
            time: endTime - startTime
        };
        */
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Request cancelled');
        }
        throw error;
    }
}




async function processLLMs(prompt, signal) {
    const results = [];
    
    
    const promises = CONFIG.MODELS.map(async (model) => {
        const llmId = model.id;
        
        try {
            updateLLMStatus(llmId, 'loading');
            toggleLoadingSkeleton(llmId, true);
            
            const result = await callLLM(llmId, prompt, signal);
            
            displayLLMResponse(llmId, result.response);
            updateLLMStatus(llmId, 'success', result.time);
            
            return result.response;
        } catch (error) {
            console.error(`LLM ${llmId} error:`, error);
            displayLLMResponse(llmId, error.message, true);
            updateLLMStatus(llmId, 'error');
            throw error;
        }
    });
    
    
    try {
        const responses = await Promise.all(promises);
        return responses;
    } catch (error) {
        
        
        throw error;
    }
}


async function processArbiter(prompt, llmResponses, signal) {
    try {
        elements.arbiterSection.classList.remove('hidden');
        updateLLMStatus('arbiter', 'loading');
        toggleLoadingSkeleton('arbiter', true);
        
        const result = await callArbiter(prompt, llmResponses, signal);
        
        displayLLMResponse('arbiter', result.response);
        updateLLMStatus('arbiter', 'success', result.time);
        
        return result.response;
    } catch (error) {
        console.error('Arbiter error:', error);
        displayLLMResponse('arbiter', error.message, true);
        updateLLMStatus('arbiter', 'error');
        throw error;
    }
}


async function handleSubmit() {
    const prompt = elements.promptInput.value.trim();
    
    
    if (!prompt) {
        showToast('Proszę wprowadzić pytanie', 'warning');
        return;
    }
    
    if (prompt.length > CONFIG.MAX_CHARS) {
        showToast(`Pytanie jest za długie (max ${CONFIG.MAX_CHARS} znaków)`, 'error');
        return;
    }
    
    if (state.isProcessing) {
        return;
    }
    
    
    state.isProcessing = true;
    state.abortController = new AbortController();
    resetUI();
    updateButtonStates(true);
    elements.resultsSection.classList.remove('hidden');
    
    try {
        
        const llmResponses = await processLLMs(prompt, state.abortController.signal);
        
        
        const arbiterResponse = await processArbiter(prompt, llmResponses, state.abortController.signal);
        
        
        addToHistory(prompt, llmResponses, arbiterResponse);
        
        showToast('Proces zakończony pomyślnie!', 'success');
        
    } catch (error) {
        console.error('Processing error:', error);
        
        if (error.message === 'Request cancelled') {
            showToast('Żądanie zostało anulowane', 'warning');
        } else {
            showToast('Wystąpił błąd podczas przetwarzania', 'error');
        }
    } finally {
        state.isProcessing = false;
        state.abortController = null;
        updateButtonStates(false);
    }
}


function handleCancel() {
    if (state.abortController) {
        state.abortController.abort();
        showToast('Anulowanie żądania...', 'warning');
    }
}




function addToHistory(prompt, llmResponses, arbiterResponse) {
    const entry = {
        id: Date.now(),
        timestamp: new Date(),
        prompt: prompt,
        llmResponses: llmResponses,
        arbiterResponse: arbiterResponse
    };
    
    state.history.unshift(entry);
    
    
    if (state.history.length > 10) {
        state.history = state.history.slice(0, 10);
    }
    
    updateHistoryDisplay();
}


function updateHistoryDisplay() {
    if (state.history.length === 0) {
        elements.historySection.classList.add('hidden');
        return;
    }
    
    elements.historySection.classList.remove('hidden');
    elements.historyCount.textContent = `${state.history.length} ${state.history.length === 1 ? 'zapytanie' : 'zapytań'}`;
    
    elements.historyList.innerHTML = state.history.map(entry => `
        <div class="history-item">
            <div class="history-question">${escapeHtml(entry.prompt.substring(0, 100))}${entry.prompt.length > 100 ? '...' : ''}</div>
            <div class="history-timestamp">${entry.timestamp.toLocaleString('pl-PL')}</div>
        </div>
    `).join('');
}




elements.promptInput.addEventListener('input', debounce(updateCharCount, 100));


elements.promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        handleSubmit();
    }
});


elements.submitBtn.addEventListener('click', handleSubmit);


elements.cancelBtn.addEventListener('click', handleCancel);


document.addEventListener('DOMContentLoaded', () => {
    console.log('AI Council initialized');
    updateCharCount();
    updateHistoryDisplay();
});
