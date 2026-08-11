/**
 * Radar UI — Minimal Frontend Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const themeToggleBtn = document.getElementById('themeToggle');
  const moonIcon = document.getElementById('moonIcon');
  const sunIcon = document.getElementById('sunIcon');
  const systemStatus = document.getElementById('systemStatus');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  // Tabs
  const tabInspectorBtn = document.getElementById('tabInspectorBtn');
  const tabStreamBtn = document.getElementById('tabStreamBtn');
  const inspectorPanel = document.getElementById('inspectorPanel');
  const streamPanel = document.getElementById('streamPanel');

  // Form & Inputs
  const scoringForm = document.getElementById('scoringForm');
  const inputTxnId = document.getElementById('inputTxnId');
  const inputCardId = document.getElementById('inputCardId');
  const inputAmount = document.getElementById('inputAmount');
  const inputFeaturesJson = document.getElementById('inputFeaturesJson');
  const btnFeatureNormal = document.getElementById('btnFeatureNormal');
  const btnFeatureRandom = document.getElementById('btnFeatureRandom');
  const btnSubmit = document.getElementById('btnSubmit');

  // Results UI
  const resultsSection = document.getElementById('resultsSection');
  const actionBadge = document.getElementById('actionBadge');
  const latencyTag = document.getElementById('latencyTag');
  const gaugeMeter = document.getElementById('gaugeMeter');
  const gaugeValue = document.getElementById('gaugeValue');
  const valModelScore = document.getElementById('valModelScore');
  const barModelScore = document.getElementById('barModelScore');
  const valVelocityScore = document.getElementById('valVelocityScore');
  const barVelocityScore = document.getElementById('barVelocityScore');
  const reasonsTags = document.getElementById('reasonsTags');

  // Presets
  const presetSafe = document.getElementById('presetSafe');
  const presetVelocity = document.getElementById('presetVelocity');
  const presetAnomaly = document.getElementById('presetAnomaly');

  // Stream Simulator
  const btnStartSim = document.getElementById('btnStartSim');
  const btnClearSim = document.getElementById('btnClearSim');
  const streamTableBody = document.getElementById('streamTableBody');
  const simTotalCount = document.getElementById('simTotalCount');
  const simAllowCount = document.getElementById('simAllowCount');
  const simReviewCount = document.getElementById('simReviewCount');
  const simBlockCount = document.getElementById('simBlockCount');

  // State Variables
  let simInterval = null;
  let isSimulating = false;
  let simStats = { total: 0, allow: 0, review: 0, block: 0 };

  // ==========================================
  // 1. Theme Toggle Logic
  // ==========================================
  const savedTheme = localStorage.getItem('radar-theme') || 'dark';
  setTheme(savedTheme);

  themeToggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  });

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('radar-theme', theme);
    if (theme === 'light') {
      moonIcon.style.display = 'none';
      sunIcon.style.display = 'block';
    } else {
      moonIcon.style.display = 'block';
      sunIcon.style.display = 'none';
    }
  }

  // ==========================================
  // 2. Tab Navigation Logic
  // ==========================================
  tabInspectorBtn.addEventListener('click', () => switchTab('inspector'));
  tabStreamBtn.addEventListener('click', () => switchTab('stream'));

  function switchTab(tabName) {
    if (tabName === 'inspector') {
      tabInspectorBtn.classList.add('active');
      tabStreamBtn.classList.remove('active');
      inspectorPanel.style.display = 'block';
      streamPanel.style.display = 'none';
    } else {
      tabStreamBtn.classList.add('active');
      tabInspectorBtn.classList.remove('active');
      inspectorPanel.style.display = 'none';
      streamPanel.style.display = 'block';
    }
  }

  // ==========================================
  // 3. System Health Polling
  // ==========================================
  async function checkHealth() {
    try {
      const res = await fetch('/health');
      if (!res.ok) throw new Error('Health check non-200');
      const data = await res.json();
      
      const redisText = data.redis_connected ? 'Redis Active' : 'Redis Off';
      const modelText = data.model_loaded ? 'Model Loaded' : 'Model Off';
      
      statusText.textContent = `API OK • ${modelText} • ${redisText}`;
      if (data.status === 'ok') {
        statusDot.className = 'status-dot';
      } else {
        statusDot.className = 'status-dot degraded';
      }
    } catch (err) {
      statusText.textContent = 'API Offline';
      statusDot.className = 'status-dot degraded';
    }
  }
  checkHealth();
  setInterval(checkHealth, 10000);

  // ==========================================
  // 4. Feature Vector Presets & Generators
  // ==========================================
  function generateBaselineFeatures() {
    const obj = {};
    for (let i = 1; i <= 28; i++) {
      // Small random normal-ish values around 0
      obj[`V${i}`] = parseFloat(((Math.random() - 0.5) * 0.4).toFixed(3));
    }
    return obj;
  }

  function generateAnomalyFeatures() {
    const obj = generateBaselineFeatures();
    // Inject strong synthetic anomalies into specific V features
    obj['V1'] = -14.25;
    obj['V3'] = -18.82;
    obj['V4'] = 11.45;
    obj['V10'] = -12.30;
    obj['V12'] = -15.10;
    obj['V14'] = -16.05;
    return obj;
  }

  function setFeaturesJson(obj) {
    inputFeaturesJson.value = JSON.stringify(obj, null, 2);
  }

  // Initial defaults
  inputTxnId.value = 'txn_' + Math.floor(100000 + Math.random() * 900000);
  inputCardId.value = 'card_' + Math.floor(10000 + Math.random() * 90000);
  inputAmount.value = '42.50';
  setFeaturesJson(generateBaselineFeatures());

  btnFeatureNormal.addEventListener('click', () => {
    btnFeatureNormal.classList.add('active');
    btnFeatureRandom.classList.remove('active');
    setFeaturesJson(generateBaselineFeatures());
  });

  btnFeatureRandom.addEventListener('click', () => {
    btnFeatureRandom.classList.add('active');
    btnFeatureNormal.classList.remove('active');
    setFeaturesJson(generateAnomalyFeatures());
  });

  // Scenario Preset Handlers
  presetSafe.addEventListener('click', () => {
    inputTxnId.value = 'txn_safe_' + Math.floor(1000 + Math.random() * 9000);
    inputCardId.value = 'card_normal_101';
    inputAmount.value = '42.50';
    btnFeatureNormal.click();
    scoringForm.dispatchEvent(new Event('submit'));
  });

  presetVelocity.addEventListener('click', () => {
    const repeatCard = 'card_rapid_surger_99';
    inputTxnId.value = 'txn_vel_' + Math.floor(1000 + Math.random() * 9000);
    inputCardId.value = repeatCard;
    inputAmount.value = '280.00';
    btnFeatureNormal.click();
    scoringForm.dispatchEvent(new Event('submit'));
  });

  presetAnomaly.addEventListener('click', () => {
    inputTxnId.value = 'txn_risk_' + Math.floor(1000 + Math.random() * 9000);
    inputCardId.value = 'card_anom_777';
    inputAmount.value = '4999.00';
    btnFeatureRandom.click();
    scoringForm.dispatchEvent(new Event('submit'));
  });

  // ==========================================
  // 5. Form Submission & Scoring Display
  // ==========================================
  scoringForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    let parsedFeatures;
    try {
      parsedFeatures = JSON.parse(inputFeaturesJson.value);
    } catch (err) {
      alert('Invalid JSON format for PCA Features. Please check formatting.');
      return;
    }

    const payload = {
      transaction_id: inputTxnId.value.trim(),
      card_id: inputCardId.value.trim(),
      amount: parseFloat(inputAmount.value),
      features: parsedFeatures
    };

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `Analysing...`;

    try {
      const res = await fetch('/api/v1/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Scoring API error');
      }

      const data = await res.json();
      displayResult(data);

    } catch (err) {
      alert(`Scoring Error: ${err.message}`);
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        Analyze Risk
      `;
    }
  });

  function displayResult(data) {
    resultsSection.style.display = 'block';

    // Action Badge
    actionBadge.textContent = data.action;
    actionBadge.className = `action-badge ${data.action}`;

    // Latency
    latencyTag.textContent = `Latency: ${data.latency_ms} ms`;

    // Radial Gauge Calculation
    // Total circumference = 2 * PI * r = 2 * 3.14159 * 45 ≈ 283
    const totalDash = 283;
    const score = Math.max(0, Math.min(100, data.risk_score));
    const offset = totalDash - (score / 100) * totalDash;

    gaugeMeter.style.strokeDashoffset = offset;
    gaugeValue.textContent = score;

    // Color theme matching risk level
    let strokeColor = 'var(--color-allow)';
    if (data.action === 'MANUAL_REVIEW') strokeColor = 'var(--color-review)';
    if (data.action === 'BLOCK') strokeColor = 'var(--color-block)';
    gaugeMeter.style.stroke = strokeColor;

    // Sub-Scores
    valModelScore.textContent = `${data.model_score} / 100`;
    barModelScore.style.width = `${Math.min(100, data.model_score)}%`;

    valVelocityScore.textContent = `${data.velocity_score} / 30`;
    barVelocityScore.style.width = `${Math.min(100, (data.velocity_score / 30) * 100)}%`;

    // Reasons List
    reasonsTags.innerHTML = '';
    if (!data.reasons || data.reasons.length === 0) {
      reasonsTags.innerHTML = '<span class="reason-tag">✅ Clean profile — No risk flags</span>';
    } else {
      data.reasons.forEach(reason => {
        const span = document.createElement('span');
        span.className = 'reason-tag';
        span.innerHTML = `⚠️ ${reason}`;
        reasonsTags.appendChild(span);
      });
    }
  }

  // ==========================================
  // 6. Live Stream Simulator Logic
  // ==========================================
  btnStartSim.addEventListener('click', () => {
    if (isSimulating) {
      stopSimulation();
    } else {
      startSimulation();
    }
  });

  btnClearSim.addEventListener('click', () => {
    streamTableBody.innerHTML = '';
    simStats = { total: 0, allow: 0, review: 0, block: 0 };
    updateSimStats();
  });

  function startSimulation() {
    isSimulating = true;
    btnStartSim.textContent = 'Pause Stream';
    btnStartSim.style.background = 'var(--color-review)';

    if (streamTableBody.children.length === 1 && streamTableBody.children[0].cells.length === 1) {
      streamTableBody.innerHTML = '';
    }

    simInterval = setInterval(runSyntheticTxn, 1400);
    runSyntheticTxn();
  }

  function stopSimulation() {
    isSimulating = false;
    clearInterval(simInterval);
    btnStartSim.textContent = 'Start Stream';
    btnStartSim.style.background = 'linear-gradient(135deg, var(--accent-emerald), var(--accent-emerald-dark))';
  }

  async function runSyntheticTxn() {
    const isAnomaly = Math.random() < 0.25;
    const isRepeatCard = Math.random() < 0.35;
    
    const cardId = isRepeatCard ? 'card_stream_recurring' : 'card_' + Math.floor(1000 + Math.random() * 9000);
    const txnId = 'txn_strm_' + Math.floor(100000 + Math.random() * 900000);
    const amount = isAnomaly ? parseFloat((800 + Math.random() * 4000).toFixed(2)) : parseFloat((10 + Math.random() * 150).toFixed(2));
    const features = isAnomaly ? generateAnomalyFeatures() : generateBaselineFeatures();

    try {
      const res = await fetch('/api/v1/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: txnId,
          card_id: cardId,
          amount: amount,
          features: features
        })
      });

      if (!res.ok) return;
      const data = await res.json();
      appendStreamRow(data);

    } catch (err) {
      console.warn('Stream simulation error:', err);
    }
  }

  function appendStreamRow(data) {
    simStats.total++;
    if (data.action === 'ALLOW') simStats.allow++;
    if (data.action === 'MANUAL_REVIEW') simStats.review++;
    if (data.action === 'BLOCK') simStats.block++;
    updateSimStats();

    const timeStr = new Date().toLocaleTimeString();
    const row = document.createElement('tr');
    
    let actionStyle = 'color: var(--color-allow);';
    if (data.action === 'MANUAL_REVIEW') actionStyle = 'color: var(--color-review);';
    if (data.action === 'BLOCK') actionStyle = 'color: var(--color-block);';

    row.innerHTML = `
      <td>${timeStr}</td>
      <td>${data.transaction_id}</td>
      <td>${data.card_id}</td>
      <td>$${data.amount !== undefined ? data.amount.toFixed(2) : '--'}</td>
      <td style="font-weight: 700;">${data.risk_score}</td>
      <td style="font-weight: 700; ${actionStyle}">${data.action}</td>
    `;

    streamTableBody.insertBefore(row, streamTableBody.firstChild);

    // Keep table capped at 50 rows max
    if (streamTableBody.children.length > 50) {
      streamTableBody.removeChild(streamTableBody.lastChild);
    }
  }

  function updateSimStats() {
    simTotalCount.textContent = simStats.total;
    simAllowCount.textContent = simStats.allow;
    simReviewCount.textContent = simStats.review;
    simBlockCount.textContent = simStats.block;
  }
});
