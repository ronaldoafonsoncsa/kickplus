const translations = {
  pt: {
    pageTitle:      "KickPlus — Análise de Fundamentos",
    tagline:        "Análise Técnica de Fundamentos",
    uploadTitle:    "Enviar Vídeo para Análise",
    uploadSubtitle: "Filme a execução do fundamento e envie para receber feedback técnico detalhado.",
    skillLabel:     "Fundamento praticado",
    skillShot:      "Chute",
    skillPass:      "Passe",
    skillControl:   "Domínio",
    videoLabel:     "Vídeo do treino",
    dropText:       "Clique ou arraste o vídeo aqui",
    dropHint:       "MP4, MOV, AVI, WebM — máx. 100MB",
    btnAnalyze:     "Analisar Vídeo",
    btnAnalyzing:   "Analisando...",
    btnRemove:      "✕ Remover",
    resultsTitle:   "Resultado da Análise",
    scoreLabel:     "/ 10",
    mainTipLabel:   "💡 Dica principal para o próximo treino",
    positivesTitle:    "✅ Pontos Positivos",
    improvementsTitle: "🔧 Pontos a Melhorar",
    exercisePrefix: "🏃 Exercício: ",
    btnNewAnalysis: "Nova Análise",
    errSelectSkill: "Selecione o fundamento praticado.",
    errSelectVideo: "Selecione um vídeo.",
    errConnection:  "Erro de conexão. Verifique se o servidor está rodando.",
    errGeneric:     "Erro ao processar o vídeo.",
  },
  en: {
    pageTitle:      "KickPlus — Fundamentals Analysis",
    tagline:        "Technical Fundamentals Analysis",
    uploadTitle:    "Submit Video for Analysis",
    uploadSubtitle: "Record the skill execution and submit to receive detailed technical feedback.",
    skillLabel:     "Skill being practiced",
    skillShot:      "Shot",
    skillPass:      "Pass",
    skillControl:   "Ball Control",
    videoLabel:     "Training video",
    dropText:       "Click or drag video here",
    dropHint:       "MP4, MOV, AVI, WebM — max. 100MB",
    btnAnalyze:     "Analyze Video",
    btnAnalyzing:   "Analyzing...",
    btnRemove:      "✕ Remove",
    resultsTitle:   "Analysis Result",
    scoreLabel:     "/ 10",
    mainTipLabel:   "💡 Main tip for the next training session",
    positivesTitle:    "✅ Positive Points",
    improvementsTitle: "🔧 Areas to Improve",
    exercisePrefix: "🏃 Exercise: ",
    btnNewAnalysis: "New Analysis",
    errSelectSkill: "Please select the skill being practiced.",
    errSelectVideo: "Please select a video.",
    errConnection:  "Connection error. Make sure the server is running.",
    errGeneric:     "Error processing the video.",
  },
};

let currentLang = localStorage.getItem('kickplus-lang')
  || (navigator.language.startsWith('pt') ? 'pt' : 'en');

function t(key) {
  return translations[currentLang]?.[key] ?? translations.pt[key] ?? key;
}

function applyTranslations() {
  document.documentElement.lang = currentLang === 'pt' ? 'pt-BR' : 'en';
  document.title = t('pageTitle');
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === currentLang);
  });
}

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentLang = btn.dataset.lang;
    localStorage.setItem('kickplus-lang', currentLang);
    applyTranslations();
  });
});

applyTranslations();

const form = document.getElementById('analyzeForm');
const videoInput = document.getElementById('videoInput');
const dropZone = document.getElementById('dropZone');
const dropZoneContent = document.getElementById('dropZoneContent');
const videoPreviewContainer = document.getElementById('videoPreviewContainer');
const videoPreview = document.getElementById('videoPreview');
const removeVideoBtn = document.getElementById('removeVideo');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');
const resultsSection = document.getElementById('resultsSection');
const errorBox = document.getElementById('errorBox');
const errorMessage = document.getElementById('errorMessage');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

videoInput.addEventListener('change', () => {
  if (videoInput.files[0]) showVideoPreview(videoInput.files[0]);
});

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('video/')) {
    videoInput.files = e.dataTransfer.files;
    showVideoPreview(file);
  }
});

removeVideoBtn.addEventListener('click', () => {
  videoInput.value = '';
  videoPreview.src = '';
  videoPreviewContainer.classList.add('hidden');
  dropZoneContent.classList.remove('hidden');
  dropZone.style.display = '';
});

function showVideoPreview(file) {
  const url = URL.createObjectURL(file);
  videoPreview.src = url;
  videoPreviewContainer.classList.remove('hidden');
  dropZoneContent.classList.add('hidden');
  dropZone.style.display = 'none';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const skill = form.querySelector('input[name="skill"]:checked')?.value;
  const file = videoInput.files[0];

  if (!skill) { showError(t('errSelectSkill')); return; }
  if (!file)  { showError(t('errSelectVideo')); return; }

  hideError();
  setLoading(true);
  resultsSection.classList.add('hidden');

  const formData = new FormData();
  formData.append('video', file);
  formData.append('skill', skill);
  formData.append('language', currentLang);

  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || t('errGeneric'));
      return;
    }

    renderResults(data.analysis);
  } catch {
    showError(t('errConnection'));
  } finally {
    setLoading(false);
  }
});

function renderResults(analysis) {
  document.getElementById('scoreValue').textContent = analysis.overall_score ?? '—';
  document.getElementById('resultSummary').textContent = analysis.summary ?? '';
  document.getElementById('mainTip').textContent = analysis.main_tip ?? '';

  document.getElementById('scoreBadge').style.background = scoreToColor(analysis.overall_score);

  const posList = document.getElementById('positivesList');
  posList.innerHTML = '';
  (analysis.positive_points || []).forEach(p => {
    const li = document.createElement('li');
    li.textContent = p;
    posList.appendChild(li);
  });

  const impList = document.getElementById('improvementsList');
  impList.innerHTML = '';
  (analysis.areas_to_improve || []).forEach(item => {
    const div = document.createElement('div');
    div.className = 'improvement-item';
    div.innerHTML = `
      <div class="improvement-problem">${escHtml(item.problem)}</div>
      <div class="improvement-correction">${escHtml(item.correction)}</div>
      <div class="improvement-exercise">
        <span class="exercise-label">${escHtml(t('exercisePrefix'))}</span>${escHtml(item.exercise)}
      </div>
    `;
    impList.appendChild(div);
  });

  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function scoreToColor(score) {
  if (score >= 8) return '#1a7f3c';
  if (score >= 6) return '#4a8f20';
  if (score >= 4) return '#c07010';
  return '#c03030';
}

newAnalysisBtn.addEventListener('click', () => {
  resultsSection.classList.add('hidden');
  form.reset();
  videoInput.value = '';
  videoPreview.src = '';
  videoPreviewContainer.classList.add('hidden');
  dropZoneContent.classList.remove('hidden');
  dropZone.style.display = '';
  hideError();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

function setLoading(on) {
  submitBtn.disabled = on;
  btnText.classList.toggle('hidden', on);
  btnLoader.classList.toggle('hidden', !on);
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBox.classList.remove('hidden');
  errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
  errorBox.classList.add('hidden');
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
