const $ = (id) => document.getElementById(id);

const exprDisplay = $('exprDisplay');
const resultDisplay = $('resultDisplay');
const historyBtn = $('historyBtn');
const historyLabel = $('historyLabel');
const clockEl = $('clock');

const modeBackendBtn = $('modeBackend');
const modeKeyBtn = $('modeKey');
const connectBtn = $('connectBtn');
const apiKeyInput = $('apiKey');
const aiStatusDot = $('aiStatusDot');
const aiStatusText = $('aiStatusText');
const aiRemaining = $('aiRemaining');
const aiChat = $('aiChat');
const hintText = $('hintText');

const updateHint = (text) => {
  hintText.textContent = text || 'Hover or click a key to see what it does.';
};

const questionInput = $('question');
const aiBtn = $('aiBtn');

const aiKeyRow = $('aiKeyRow');

const tabs = Array.from(document.querySelectorAll('.tab'));
const padStandard = $('padStandard');
const padScientific = $('padScientific');
const aiPanel = $('aiPanel');

const state = {
  expr: '',
  result: '0',
  history: [],
  mode: 'standard',
  busy: false,
  aiMode: 'backend', // backend | key
  apiKey: '',
  remaining: null,
  units: 'deg', // deg | rad
  aiHistory: [], // Array of {role, content}
};

const formatHistoryLabel = () => {
  if (!state.history.length) return '—';
  const last = state.history[state.history.length - 1];
  return `${last.expr} = ${last.result}`;
};

const updateDisplay = () => {
  exprDisplay.textContent = state.expr || '';
  
  // Dynamic font scaling for result
  const len = state.result.length;
  let fontSize = window.innerWidth < 480 ? '2.5rem' : '3rem';
  
  if (len > 8) fontSize = window.innerWidth < 480 ? '2rem' : '2.5rem';
  if (len > 12) fontSize = window.innerWidth < 480 ? '1.5rem' : '2rem';
  if (len > 16) fontSize = window.innerWidth < 480 ? '1.2rem' : '1.5rem';
  if (len > 20) fontSize = '1rem';

  resultDisplay.style.fontSize = fontSize;
  resultDisplay.textContent = state.result;
  historyBtn.textContent = formatHistoryLabel();
};

const setBusy = (busy) => {
  state.busy = busy;
  const allButtons = document.querySelectorAll('.pad button, .ai-panel button');
  allButtons.forEach((btn) => (btn.disabled = busy));

  if (busy && state.mode !== 'ai') {
    resultDisplay.textContent = '…';
  }
};

const jsonRequest = async (url, body) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText || 'Request failed');
  }

  return res.json();
};

const showError = (msg) => {
  state.result = `Error: ${msg}`;
  updateDisplay();
};

const setAiStatus = ({ text, dotColor, remaining, remainingClass }) => {
  aiStatusText.textContent = text;
  aiStatusDot.style.color = dotColor;

  if (remaining != null) {
    aiRemaining.textContent = `Remaining: ${remaining}`;
    aiRemaining.className = `ai-remaining ${remainingClass}`;
    aiRemaining.style.display = 'inline-block';
  } else {
    aiRemaining.textContent = '';
    aiRemaining.className = 'ai-remaining';
    aiRemaining.style.display = 'none';
  }
};

const formatRemaining = (raw) => {
  const max = 14400;
  const num = Number(raw);
  if (!Number.isFinite(num)) return { text: String(raw), cls: 'grey' };

  const pct = Math.min(1, Math.max(0, num / max));
  const percent = Math.round(pct * 100);
  let cls = 'grey';
  if (num === 0) cls = 'grey';
  else if (pct <= 0.25) cls = 'red';
  else if (pct <= 0.5) cls = 'yellow';
  else cls = 'green';

  return { text: `${num} (${percent}%)`, cls };
};

const addAiMessage = (role, text) => {
  if (state.mode !== 'ai') return;

  const wrapper = document.createElement('div');
  wrapper.className = `ai-msg ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  aiChat.appendChild(wrapper);
  aiChat.scrollTop = aiChat.scrollHeight;
};

const setAiMode = (mode) => {
  state.aiMode = mode;
  modeBackendBtn.classList.toggle('active', mode === 'backend');
  modeKeyBtn.classList.toggle('active', mode === 'key');
  aiKeyRow.style.display = mode === 'key' ? 'flex' : 'none';

  if (mode === 'backend') {
    setAiStatus({
      text: 'Using backend API',
      dotColor: 'var(--green)',
      remaining: state.remaining ? formatRemaining(state.remaining).text : null,
      remainingClass: state.remaining ? formatRemaining(state.remaining).cls : '',
    });
  } else {
    setAiStatus({
      text: state.apiKey ? 'Using own API key' : 'No key set',
      dotColor: state.apiKey ? 'var(--green)' : 'var(--red)',
      remaining: state.remaining ? formatRemaining(state.remaining).text : null,
      remainingClass: state.remaining ? formatRemaining(state.remaining).cls : '',
    });
  }
};

const connectKey = () => {
  const key = apiKeyInput.value.trim();
  state.apiKey = key;

  if (key) {
    setAiStatus({
      text: 'Using own API key',
      dotColor: 'var(--green)',
      remaining: state.remaining ? formatRemaining(state.remaining).text : null,
      remainingClass: state.remaining ? formatRemaining(state.remaining).cls : '',
    });
    setAiMode('key');
  } else {
    setAiStatus({
      text: 'No API key set',
      dotColor: 'var(--red)',
      remaining: null,
      remainingClass: '',
    });
  }
};

const pushHistory = (expr, result) => {
  state.history.push({ expr, result });
  if (state.history.length > 12) state.history.shift();
  updateDisplay();
};

const compute = async () => {
  const expr = state.expr.trim();
  if (!expr) return;

  setBusy(true);

  try {
    const data = await jsonRequest('/api/calc', { expr, mode: state.units });
    state.result = String(data.result);
    pushHistory(expr, state.result);
  } catch (err) {
    showError(err.message);
  } finally {
    setBusy(false);
  }
};

const insert = (value) => {
  if (state.justEvaled && /[0-9.]/.test(value)) {
    state.expr = '';
  }

  state.expr += value;
  state.justEvaled = false;
  updateDisplay();
};

const actions = {
  ac: () => {
    state.expr = '';
    state.result = '0';
    state.justEvaled = false;
    updateDisplay();
  },
  del: () => {
    state.expr = state.expr.slice(0, -1);
    updateDisplay();
  },
  eval: async () => {
    await compute();
    state.justEvaled = true;
  },
  prev: () => {
    if (!state.history.length) return;
    const last = state.history[state.history.length - 1];
    state.expr = last.expr;
    state.result = last.result;
    updateDisplay();
  },
  toggleHistory: () => {
    if (!state.history.length) return;
    const last = state.history[state.history.length - 1];
    state.expr = last.expr;
    state.result = last.result;
    updateDisplay();
  },
};

const handlePadClick = (event) => {
  const btn = event.target.closest('button');
  if (!btn || state.busy) return;

  const action = btn.dataset.action;
  const value = btn.dataset.value;
  const fn = btn.dataset.function;

  if (fn && typeof actions[fn] === 'function') {
    actions[fn]();
    return;
  }

  if (action && typeof actions[action] === 'function') {
    actions[action]();
    return;
  }

  if (value) {
    insert(value);
  }
};

const switchMode = (mode) => {
  state.mode = mode;
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.mode === mode));

  // Use classes instead of inline styles so CSS can handle layout (e.g. flex on desktop)
  padStandard.classList.toggle('visible', mode === 'standard');
  padScientific.classList.toggle('visible', mode === 'scientific');
  aiPanel.classList.toggle('visible', mode === 'ai');

  if (mode !== 'ai') {
    // Clear the AI chat and status when leaving AI mode
    aiChat.innerHTML = '';
    setAiStatus({ text: 'Not connected', dotColor: 'var(--red)', remaining: null, remainingClass: '' });
  }
};

const startClock = () => {
  const tick = () => {
    const now = new Date();
    const mins = String(now.getMinutes()).padStart(2, '0');
    const hrs = String(now.getHours()).padStart(2, '0');
    clockEl.textContent = `${hrs}:${mins}`;
  };
  tick();
  setInterval(tick, 10_000);
};

const askAi = async () => {
  if (state.mode !== 'ai') return;

  const question = questionInput.value.trim();
  if (!question) return;

  if (state.aiMode === 'key' && !state.apiKey) {
    setAiStatus({
      text: 'No API key set (switch to Backend or paste key)',
      dotColor: 'var(--red)',
      remaining: null,
      remainingClass: '',
    });
    return;
  }

  setBusy(true);
  addAiMessage('user', question);
  questionInput.value = ''; // Clear textarea after sending

  try {
    let data;
    let remaining = null;

    if (state.aiMode === 'key') {
      const SYSTEM =
        "You are an expert mathematician with advanced logical thinking and problem-solving skills. " +
        "When users ask questions, provide precise, logically structured answers. " +
        "Use formal mathematical notation and step-by-step reasoning where appropriate. " +
        "Be concise but thorough. Focus on providing the most accurate and elegant solution possible. " +
        "Keep answers short (≤6 lines). Use plain text (no markdown headers).";

      const resp = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${state.apiKey}`,
        },
        body: JSON.stringify({
          model: "llama-3.3-70b-versatile",
          messages: [
            { role: "system", content: SYSTEM },
            ...state.aiHistory,
            { role: "user", content: question },
          ],
          max_tokens: 400,
          temperature: 0.3,
        }),
      });

      if (!resp.ok) {
        const errBody = await resp.json().catch(() => null);
        const msg = errBody?.error?.message || resp.statusText || "Request failed";
        throw new Error(msg);
      }

      data = await resp.json();
      remaining =
        resp.headers.get("x-ratelimit-remaining-requests-today") ||
        resp.headers.get("x-ratelimit-remaining-requests");

      data.answer = data.choices?.[0]?.message?.content?.trim() ?? "(no response)";
    } else {
      const backendData = await jsonRequest("/api/ai", {
        question,
        history: state.aiHistory,
      });
      data = backendData;
      remaining = backendData.remaining_requests ?? backendData.remaining ?? null;
    }

    state.remaining = remaining;
    const remainingInfo = formatRemaining(remaining);

    setAiStatus({
      text: state.aiMode === 'key' ? 'Using own API key' : 'Using backend API',
      dotColor: 'var(--green)',
      remaining: remainingInfo.text,
      remainingClass: remainingInfo.cls,
    });

    addAiMessage('bot', data.answer);
    
    // Update memory
    state.aiHistory.push({ role: 'user', content: question });
    state.aiHistory.push({ role: 'assistant', content: data.answer });
    
    // Limit history length to avoid huge payloads (keep last 10 messages)
    if (state.aiHistory.length > 10) {
       state.aiHistory = state.aiHistory.slice(-10);
    }
  } catch (err) {
    addAiMessage('bot', `Error: ${err.message}`);
    setAiStatus({
      text: 'Error contacting AI',
      dotColor: 'var(--red)',
      remaining: null,
      remainingClass: '',
    });
  } finally {
    setBusy(false);
  }
};

const init = () => {
  padStandard.addEventListener('click', handlePadClick);
  padScientific.addEventListener('click', handlePadClick);
  historyBtn.addEventListener('click', () => {
    if (state.history.length) {
      const last = state.history[state.history.length - 1];
      state.expr = last.expr;
      state.result = last.result;
      updateDisplay();
    }
  });

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => switchMode(tab.dataset.mode));
  });

  // Hint bar logic
  [padStandard, padScientific].forEach(pad => {
    pad.addEventListener('mouseover', (e) => {
      const btn = e.target.closest('button');
      if (btn && btn.dataset.hint) updateHint(btn.dataset.hint);
    });
    pad.addEventListener('mouseout', (e) => {
      updateHint();
    });
  });

  aiBtn.addEventListener('click', askAi);
  connectBtn.addEventListener('click', connectKey);
  modeBackendBtn.addEventListener('click', () => setAiMode('backend'));
  modeKeyBtn.addEventListener('click', () => setAiMode('key'));

  const unitDegBtn = $('unitDeg');
  const unitRadBtn = $('unitRad');

  const setUnits = (u) => {
    state.units = u;
    unitDegBtn.classList.toggle('active', u === 'deg');
    unitRadBtn.classList.toggle('active', u === 'rad');
  };

  unitDegBtn.addEventListener('click', () => setUnits('deg'));
  unitRadBtn.addEventListener('click', () => setUnits('rad'));

  const resetAiBtn = $('aiResetBtn');
  const resetAiChat = () => {
    state.aiHistory = [];
    aiChat.innerHTML = '';
    updateHint('AI Chat has been reset.');
  };
  resetAiBtn.addEventListener('click', resetAiChat);

  document.addEventListener('keydown', (event) => {
    // Ignore when typing in AI input fields
    const active = document.activeElement;
    if (active === apiKeyInput || active === questionInput) return;

    if (event.key === 'Enter') {
      event.preventDefault();
      actions.eval();
      return;
    }

    if (event.key === 'Backspace') {
      event.preventDefault();
      actions.del();
      return;
    }

    if (event.key === 'Escape') {
      event.preventDefault();
      actions.ac();
      return;
    }

    const keyMap = {
      '*': '×',
      '/': '÷',
      '^': '^',
      '(': '(',
      ')': ')',
      ',': ',',
      '.': '.',
      '+': '+',
      '-': '−',
    };

    if (/[0-9]/.test(event.key)) {
      insert(event.key);
      return;
    }

    if (keyMap[event.key]) {
      insert(keyMap[event.key]);
      return;
    }
  });

  // Initial state
  switchMode(state.mode); // ensure correct panel visibility
  setAiMode('backend');
  addAiMessage('bot', "🤖 AI is ready! Switch to 'Own API' to use your key, or keep 'Backend' for .env key.");

  updateDisplay();
  startClock();
};

init();
