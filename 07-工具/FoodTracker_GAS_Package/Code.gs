// ╔══════════════════════════════════════════════════════╗
// ║  FoodTracker — Google Apps Script                    ║
// ║  v3.0  |  通用版（個人設定由 App 內設定頁填寫）      ║
// ╚══════════════════════════════════════════════════════╝
// 部署前請在 Script Properties 設定：
//   SPREADSHEET_ID  → 你的 Google Sheets ID
//   GEMINI_API_KEY  → Gemini API Key
//   DRIVE_FOLDER_ID → 儲存食物圖片的 Drive 資料夾 ID

// ── 系統常數（預設值，可被使用者設定覆寫）────────────────
function getProp(key) {
  return PropertiesService.getScriptProperties().getProperty(key) || '';
}

const GEMINI_MODEL = 'gemini-2.5-flash';

// 預設熱量目標（使用者未設定時的參考值）
const DEFAULT_TARGETS = {
  '重訓日': { emoji: '🏋️', label: '高碳日', kcal: 1600, p: 130, c: 200, f: 42 },
  '有氧日': { emoji: '🏃', label: '中碳日', kcal: 1550, p: 125, c: 145, f: 47 },
  '休息日': { emoji: '💤', label: '低碳日', kcal: 1500, p: 127, c: 65,  f: 55 },
};

const EXERCISES = {
  '上半身重訓 (B日)': '重訓日', '下半身重訓 (A日)': '重訓日', '全身複合 (C日)': '重訓日',
  '飛輪': '有氧日', '跑步 Zone 2': '有氧日', '30分鐘滑步機': '有氧日',
  '瑜珈': '休息日', '完全休息': '休息日',
};

const EXERCISE_BURN = {
  '上半身重訓 (B日)': 280, '下半身重訓 (A日)': 350, '全身複合 (C日)': 430,
  '飛輪': 450, '跑步 Zone 2': 350, '30分鐘滑步機': 250,
  '瑜珈': 180, '完全休息': 0,
};

// 預設基礎代謝（使用者可在設定頁修改）
const DEFAULT_BMR = 1450;

// ── 動態設定：從 settings 表讀取，建立當前用戶的 TARGETS ─
function buildTargets(s) {
  if (!s) return DEFAULT_TARGETS;
  return {
    '重訓日': { emoji: '🏋️', label: '高碳日',
      kcal: +s.training_kcal || 1600, p: +s.training_p || 130,
      c: +s.training_c || 200,        f: +s.training_f || 42 },
    '有氧日': { emoji: '🏃', label: '中碳日',
      kcal: +s.cardio_kcal || 1550, p: +s.cardio_p || 125,
      c: +s.cardio_c || 145,          f: +s.cardio_f || 47 },
    '休息日': { emoji: '💤', label: '低碳日',
      kcal: +s.rest_kcal || 1500, p: +s.rest_p || 127,
      c: +s.rest_c || 65,              f: +s.rest_f || 55 },
  };
}

// ── 里程碑：從 settings 動態組成 ──────────────────────────
function buildMilestones(s) {
  if (!s || !s.program_start || !s.target_date) return [];
  const start = s.program_start;
  const end   = s.target_date;
  const startBf = +(s.current_bf) || 30;
  const endBf   = +(s.target_bf)  || 22;
  return [
    { date: start, label: '計畫啟動', icon: '🚀', bf: startBf, note: '計畫開始' },
    { date: end,   label: '最終目標', icon: '🏆', bf: endBf,   note: `目標體脂 ${endBf}%` },
  ];
}

function getActiveMilestone(milestones) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const ms = milestones || [];
  for (let i = 0; i < ms.length; i++) {
    const d = new Date(ms[i].date + 'T00:00:00');
    if (d >= today) return { milestone: ms[i], idx: i };
  }
  return ms.length > 0
    ? { milestone: ms[ms.length - 1], idx: ms.length - 1 }
    : { milestone: null, idx: -1 };
}

// 向下相容用（訓練計畫週次計算）
const PROGRAM_START_DEFAULT = new Date();
PROGRAM_START_DEFAULT.setHours(0,0,0,0);

// ── 重量訓練菜單 2026 Q2 ────────────────────────────────
const WORKOUT_PLANS = {
  A1: {
    label: 'A1 臀腿主導',
    dayType: '重訓日',
    warmup: ['滾筒放鬆臀腿 × 2–3 分鐘', '單腿 RDL（徒手）× 10下/邊 × 2組（啟動後側鏈）'],
    exercises: [
      { name: '硬舉',               m1: '40kg×6×4',  m2: '45kg×6×4',      m3: '47.5–50kg×6×4 ⏸頂部停1秒', note: '鉸鏈動作，臀部主導，背打直' },
      { name: '臀推（槓鈴）',        m1: '20kg×8×3',  m2: '25kg×8–9×3',    m3: '27.5–30kg×8–9×3 ⏸頂部停2秒', note: '頂部停1–2秒' },
      { name: '史密斯保加利亞分腿蹲', m1: '10kg×8×3',  m2: '12.5kg×8×3',    m3: '15kg×8×3', note: '前腳踩穩，重心在前腳跟' },
      { name: '坐姿髖外展',          m1: '25kg×12×3', m2: '30kg×12×3',     m3: '30kg×15×3', note: '收尾，感受外側臀' },
    ]
  },
  A2: {
    label: 'A2 深蹲主導',
    dayType: '重訓日',
    warmup: ['深蹲徒手 × 10下 × 2組', 'Cat-Cow 脊椎活動 × 10下'],
    exercises: [
      { name: '深蹲（槓鈴）',  m1: '27.5kg×8×4',  m2: '30kg×8×4',       m3: '32.5–35kg×8×4', note: '膝蓋對腳尖方向' },
      { name: 'RDL',          m1: '27.5kg×8×3',  m2: '30kg×8–10×3',    m3: '32.5kg×8–10×3 ⏸降速3秒離心', note: '脊椎中立，感受後側大腿拉伸' },
      { name: '分腿蹲（啞鈴）', m1: '5kg×10×3',    m2: '7.5kg×10×3',     m3: '10kg×10×3', note: '單側穩定，核心收緊' },
      { name: '坐姿器械髖外展', m1: '25kg×12×3',   m2: '30kg×12×3',      m3: '30kg×15×3', note: '收尾，感受外側臀' },
    ]
  },
  B1: {
    label: 'B1 上半身推',
    dayType: '重訓日',
    warmup: ['彈力帶肩膀繞環 × 15下 × 2組', '空手臥推動作練習 × 10下'],
    exercises: [
      { name: '槓鈴臥推',             m1: '20kg×8×4',    m2: '22.5kg×8–10×4',  m3: '25kg×8–10×4', note: '胸部發力為主' },
      { name: '啞鈴臥推',             m1: '7.5kg×8×3',   m2: '8.75kg×6–8×3',   m3: '10kg×6–8×3', note: '加大活動範圍' },
      { name: 'Cable 站姿上提',        m1: '20kg×12×3',   m2: '20kg×12×3',      m3: '22.5kg×12×3', note: '胸下緣，斜向推' },
      { name: '站姿胸飛鳥（Cable）',   m1: '20kg×10×3',   m2: '20kg×10×3',      m3: '22.5kg×10×3', note: '感受夾胸' },
      { name: '三頭下壓（Cable）',     m1: '15kg×10×3',   m2: '15kg×10×3',      m3: '15kg×10×3', note: '三頭收尾' },
    ]
  },
  B2: {
    label: 'B2 上半身拉',
    dayType: '重訓日',
    warmup: ['滾筒放鬆背部 2 分鐘', '架上划船（輕重量）× 8下 × 2組'],
    exercises: [
      { name: '架上划船',       m1: '22.5kg×8×3',  m2: '25kg×8×3',      m3: '27.5kg×8×3', note: '拉至腰部不是胸口' },
      { name: '滑輪下拉',       m1: '20kg×12×4',   m2: '22.5kg×12×4',   m3: '25kg×10–12×4', note: '肩胛骨下收，感受背闊' },
      { name: '單臂坐姿划船',   m1: '5kg×8×3',     m2: '5kg×8–10×3',    m3: '6kg×8–10×3', note: '確認左右平衡' },
      { name: '直立划船',       m1: '4kg×12×3',    m2: '4–5kg×12–15×4', m3: '5kg×12–15×4', note: '手肘高於手腕' },
      { name: '側平舉',         m1: '2kg×15×3',    m2: '2kg×15×3',      m3: '2.5kg×15×3', note: '手肘微彎' },
    ]
  },
  C: {
    label: 'C 全身複合',
    dayType: '重訓日',
    warmup: ['開合跳 × 20下', '徒手深蹲 × 10下 × 2組'],
    exercises: [
      { name: '硬舉（主項）',        m1: '依當日調整×6×4',   m2: '依當日調整×6×4',   m3: '依當日調整×6×4',   note: '主項（結構式訓練），臀部主導，背打直' },
      { name: '腿推',                m1: '20kg×12×4',        m2: '重量×12×4',         m3: '重量×12×4',         note: '輔助，增加訓練總量，組間30–45秒' },
      { name: '臀推（槓鈴/史密斯）', m1: '依當日調整×8×3',   m2: '依當日調整×8×3',   m3: '依當日調整×8×3',   note: '臀部必要動作，頂部停1–2秒' },
      { name: '啞鈴臥推/器械胸推',   m1: '依當日調整×次×組', m2: '依當日調整×次×組', m3: '依當日調整×次×組', note: '水平推，胸部發力' },
      { name: '滑輪下拉',            m1: '20kg×12×4',        m2: '重量×12×4',         m3: '重量×10–12×4',     note: '垂直拉，肩胛骨下收，感受背闊' },
      { name: '啞鈴肩推',            m1: '依當日調整×次×組', m2: '依當日調整×次×組', m3: '依當日調整×次×組', note: '垂直推，肩部發力' },
      { name: '腹肌',                m1: '30秒×3',           m2: '40秒×3',            m3: '45秒×3',           note: '棒式/捲腹/死蟲式擇一' },
    ]
  }
};

// 12週排程
const WEEK_SCHEDULE = [
  { week: 1,  parity: 'odd',  date: '3/24', phase: 'm1', A: 'A1', B: 'B1' },
  { week: 2,  parity: 'even', date: '3/31', phase: 'm1', A: 'A2', B: 'B2' },
  { week: 3,  parity: 'odd',  date: '4/7',  phase: 'm1', A: 'A1', B: 'B1' },
  { week: 4,  parity: 'even', date: '4/14', phase: 'm1', A: 'A2', B: 'B2' },
  { week: 5,  parity: 'odd',  date: '4/21', phase: 'm2', A: 'A1', B: 'B1' },
  { week: 6,  parity: 'even', date: '4/28', phase: 'm2', A: 'A2', B: 'B2' },
  { week: 7,  parity: 'odd',  date: '5/5',  phase: 'm2', A: 'A1', B: 'B1' },
  { week: 8,  parity: 'even', date: '5/12', phase: 'm2', A: 'A2', B: 'B2' },
  { week: 9,  parity: 'odd',  date: '5/19', phase: 'm3', A: 'A1', B: 'B1' },
  { week: 10, parity: 'even', date: '5/26', phase: 'm3', A: 'A2', B: 'B2' },
  { week: 11, parity: 'odd',  date: '6/2',  phase: 'm3', A: 'A1', B: 'B1' },
  { week: 12, parity: 'even', date: '6/9',  phase: 'm3', A: 'A2', B: 'B2' },
];

// ── Web App 入口 ─────────────────────────────────────────
function doGet() {
  const s = getSettings();
  const appName = (s && s.user_name) ? s.user_name + ' 的飲食追蹤' : 'FoodTracker';
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle(appName)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ── Sheet 工具 ───────────────────────────────────────────
function getSpreadsheet() {
  return SpreadsheetApp.openById(getProp('SPREADSHEET_ID'));
}

function getSheet(name) {
  const ss = getSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    const headers = {
      meals:        ['id','date','meal_type','description','calories','protein','carbs','fat','image_url','created_at'],
      daily_log:    ['date','exercise','day_type'],
      workout_log:  ['id','date','day_label','exercise','planned','actual_weight','reps','sets','feeling','notes'],
      aerobic_log:  ['id','date','activity','minutes','created_at'],
      settings:     ['key','value'],
    };
    if (headers[name]) sh.appendRow(headers[name]);
  }
  return sh;
}

function sheetToObjects(sh) {
  const data = sh.getDataRange().getValues();
  if (data.length < 2) return [];
  const headers = data[0];
  return data.slice(1).map(row => {
    const obj = {};
    headers.forEach((h, i) => {
      let v = row[i];
      // Sheets 會把日期格式的儲存格自動轉成 Date 物件，需統一轉回字串
      if (v instanceof Date) v = Utilities.formatDate(v, 'Asia/Taipei', 'yyyy-MM-dd');
      obj[h] = v;
    });
    return obj;
  });
}

// Sheets getValues() 直接取得的 Date 物件轉換輔助
function rowDateStr(val) {
  if (val instanceof Date) return Utilities.formatDate(val, 'Asia/Taipei', 'yyyy-MM-dd');
  return String(val);
}

function nextId(sh) {
  const data = sh.getDataRange().getValues();
  if (data.length < 2) return 1;
  const ids = data.slice(1).map(r => parseInt(r[0]) || 0);
  return Math.max(...ids) + 1;
}

// ── 使用者設定管理 ────────────────────────────────────────
function getSettings() {
  const sh   = getSheet('settings');
  const rows = sheetToObjects(sh);
  if (rows.length === 0) return null;
  const s = {};
  rows.forEach(r => { if (r.key) s[r.key] = String(r.value); });
  return Object.keys(s).length > 0 ? s : null;
}

function saveSettings(data) {
  const sh      = getSheet('settings');
  const lastRow = sh.getLastRow();
  if (lastRow > 1) sh.getRange(2, 1, lastRow - 1, 2).clearContent();
  Object.entries(data).forEach(([k, v]) => sh.appendRow([k, String(v)]));
  return { ok: true };
}

// ── 日期工具 ─────────────────────────────────────────────
function todayStr() {
  return Utilities.formatDate(new Date(), 'Asia/Taipei', 'yyyy-MM-dd');
}

function getWeekInfo(dateStr) {
  const s = getSettings();
  const programStart = (s && s.program_start)
    ? new Date(s.program_start + 'T00:00:00')
    : PROGRAM_START_DEFAULT;
  const d = dateStr ? new Date(dateStr) : new Date();
  const msPerDay  = 1000 * 60 * 60 * 24;
  const msPerWeek = msPerDay * 7;
  const diff = d - programStart;
  if (diff < 0) return null;
  const weekIdx = Math.floor(diff / msPerWeek);         // 0-based
  return weekIdx < WEEK_SCHEDULE.length ? WEEK_SCHEDULE[weekIdx] : null;
}

function getWorkoutDayKey(dateStr) {
  const d = dateStr ? new Date(dateStr + 'T00:00:00') : new Date();
  const dow = d.getDay(); // 0=Sun,1=Mon,...
  const info = getWeekInfo(dateStr);
  if (!info) return null;
  if (dow === 1) return info.A;   // 週一
  if (dow === 3) return info.B;   // 週三
  if (dow === 5) return 'C';      // 週五
  return null;
}

// ── API：飲食資料 ─────────────────────────────────────────
function getPageData(dateStr) {
  dateStr = dateStr || todayStr();
  const today    = todayStr();
  const settings = getSettings();
  const targets  = buildTargets(settings);
  const ms       = buildMilestones(settings);

  const mealsSh = getSheet('meals');
  const logSh   = getSheet('daily_log');

  const allMeals = sheetToObjects(mealsSh).filter(r => r.date === dateStr);
  const logRow   = sheetToObjects(logSh).find(r => r.date === dateStr) || {};

  const totals = allMeals.reduce((acc, m) => {
    acc.kcal += Number(m.calories) || 0;
    acc.p    += Number(m.protein)  || 0;
    acc.c    += Number(m.carbs)    || 0;
    acc.f    += Number(m.fat)      || 0;
    return acc;
  }, { kcal: 0, p: 0, c: 0, f: 0 });

  const dayType = logRow.day_type || null;
  const target  = dayType ? targets[dayType] : null;

  const activeMs = getActiveMilestone(ms);
  let daysLeft = 0;
  if (activeMs.milestone) {
    const msDate = new Date(activeMs.milestone.date + 'T00:00:00');
    daysLeft = Math.max(0, Math.ceil((msDate - new Date()) / (1000 * 60 * 60 * 24)));
  }

  return {
    date: dateStr,
    isToday: dateStr === today,
    meals: allMeals,
    exercise: logRow.exercise || null,
    dayType,
    target,
    totals,
    targets,
    exercises: Object.keys(EXERCISES),
    daysLeft,
    milestones: ms,
    activeMilestoneIdx: activeMs.idx,
    settingsReady: !!settings,
    userName: settings ? (settings.user_name || '') : '',
  };
}

function addMeal(data) {
  const sh = getSheet('meals');
  const id = nextId(sh);
  sh.appendRow([
    id,
    data.date || todayStr(),
    data.meal_type   || '',
    data.description || '',
    parseInt(data.calories) || 0,
    parseFloat(data.protein) || 0,
    parseFloat(data.carbs)   || 0,
    parseFloat(data.fat)     || 0,
    data.image_url || '',
    Utilities.formatDate(new Date(), 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss'),
  ]);
  return { ok: true, id };
}

function deleteMeal(mealId) {
  const sh   = getSheet('meals');
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(mealId)) {
      sh.deleteRow(i + 1);
      return { ok: true };
    }
  }
  return { ok: false };
}

function updateMeal(mealId, data) {
  const sh   = getSheet('meals');
  const rows = sh.getDataRange().getValues();
  for (let i = 1; i < rows.length; i++) {
    if (String(rows[i][0]) === String(mealId)) {
      sh.getRange(i + 1, 4).setValue(data.description || '');
      sh.getRange(i + 1, 3).setValue(data.meal_type   || '');
      sh.getRange(i + 1, 5).setValue(parseInt(data.calories)  || 0);
      sh.getRange(i + 1, 6).setValue(parseFloat(data.protein) || 0);
      sh.getRange(i + 1, 7).setValue(parseFloat(data.carbs)   || 0);
      sh.getRange(i + 1, 8).setValue(parseFloat(data.fat)     || 0);
      return { ok: true };
    }
  }
  return { ok: false };
}

function setExercise(dateStr, exercise) {
  dateStr = dateStr || todayStr();
  const sh      = getSheet('daily_log');
  const rows    = sh.getDataRange().getValues();
  const dayType = EXERCISES[exercise] || '休息日';

  for (let i = 1; i < rows.length; i++) {
    if (rowDateStr(rows[i][0]) === dateStr) {
      sh.getRange(i + 1, 2).setValue(exercise);
      sh.getRange(i + 1, 3).setValue(dayType);
      return { ok: true };
    }
  }
  sh.appendRow([dateStr, exercise, dayType]);
  return { ok: true };
}

// ── API：Gemini 飲食建議 ─────────────────────────────────
function getSuggestion(dateStr) {
  dateStr = dateStr || todayStr();
  const settings = getSettings();
  const targets  = buildTargets(settings);
  const logSh    = getSheet('daily_log');
  const mealsSh  = getSheet('meals');

  const logRow = sheetToObjects(logSh).find(r => r.date === dateStr) || {};
  const meals  = sheetToObjects(mealsSh).filter(r => r.date === dateStr);

  const dayType  = logRow.day_type || '休息日';
  const exercise = logRow.exercise || '';
  const target   = targets[dayType];

  const eaten = meals.reduce((a, m) => {
    a.kcal += Number(m.calories)||0; a.p += Number(m.protein)||0;
    a.c    += Number(m.carbs)  ||0; a.f += Number(m.fat)    ||0;
    return a;
  }, { kcal:0, p:0, c:0, f:0 });

  const rem = { kcal: target.kcal - eaten.kcal, p: target.p - eaten.p, c: target.c - eaten.c, f: target.f - eaten.f };

  const prompt = `我今天是${dayType}（${target.label}）${exercise ? `，運動：${exercise}` : ''}，目標 ${target.kcal} kcal。\n` +
    `已攝取：${Math.round(eaten.kcal)} kcal｜蛋白質 ${Math.round(eaten.p)}g｜碳水 ${Math.round(eaten.c)}g｜脂肪 ${Math.round(eaten.f)}g\n` +
    `還剩：${Math.round(rem.kcal)} kcal｜蛋白質 ${Math.round(rem.p)}g｜碳水 ${Math.round(rem.c)}g｜脂肪 ${Math.round(rem.f)}g\n\n` +
    '請建議接下來可以吃什麼（2–3 個實際選項），要簡短具體、繁體中文。';

  const key = getProp('GEMINI_API_KEY');
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${key}`;
  try {
    const resp = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
      muteHttpExceptions: true,
    });
    const json = JSON.parse(resp.getContentText());
    const text = json.candidates?.[0]?.content?.parts?.[0]?.text || '無法取得建議';
    return { ok: true, suggestion: text, remaining: rem };
  } catch(e) {
    return { ok: false, suggestion: '建議失敗：' + e.message, remaining: rem };
  }
}

// ── API：Gemini 食物辨識 ─────────────────────────────────
function analyzeFood(b64, mimeType) {
  const key    = getProp('GEMINI_API_KEY');
  const url    = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${key}`;
  const prompt = '請分析這張食物照片，估算熱量與營養素。只回傳以下 JSON，不要任何其他文字：{"description":"食物中文描述","calories":數字,"protein":數字,"carbs":數字,"fat":數字,"notes":"份量假設等備註"}';

  const payload = {
    contents: [{
      parts: [
        { inline_data: { mime_type: mimeType || 'image/jpeg', data: b64 } },
        { text: prompt }
      ]
    }]
  };

  try {
    const resp = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
    });
    const json = JSON.parse(resp.getContentText());
    const text = json.candidates?.[0]?.content?.parts?.[0]?.text || '';
    const m    = text.match(/\{[\s\S]*\}/);
    if (m) return JSON.parse(m[0]);
    return { description: text.slice(0, 80), calories: 0, protein: 0, carbs: 0, fat: 0, notes: '請手動修正' };
  } catch(e) {
    return { description: 'AI辨識失敗：' + e.message, calories: 0, protein: 0, carbs: 0, fat: 0, notes: '' };
  }
}

// ── API：圖片上傳到 Drive ────────────────────────────────
function uploadImage(b64, mimeType, filename) {
  try {
    const folderId = getProp('DRIVE_FOLDER_ID');
    const folder   = folderId ? DriveApp.getFolderById(folderId) : DriveApp.getRootFolder();
    const blob     = Utilities.newBlob(Utilities.base64Decode(b64), mimeType || 'image/jpeg', filename || 'food.jpg');
    const file     = folder.createFile(blob);
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    return { ok: true, url: `https://drive.google.com/uc?id=${file.getId()}` };
  } catch(e) {
    return { ok: false, url: '', error: e.message };
  }
}

// ── API：訓練計畫（一週三個，不綁定星期）────────────────────
function getWeekWorkoutPlan(dateStr) {
  dateStr = dateStr || todayStr();
  const weekInfo = getWeekInfo(dateStr);
  if (!weekInfo) return { noProgram: true };

  const phase = weekInfo.phase;
  const keys  = [weekInfo.A, weekInfo.B, 'C'];

  const plans = keys.map(key => {
    const plan = WORKOUT_PLANS[key];
    return {
      key,
      label:     plan.label,
      warmup:    plan.warmup,
      exercises: plan.exercises.map(ex => ({
        name:    ex.name,
        planned: ex[phase] || ex.m1,
        note:    ex.note,
      })),
    };
  });

  const daysLeft = Math.ceil((TARGET_DATE - new Date()) / (1000 * 60 * 60 * 24));
  return { weekInfo, plans, phase, daysLeft };
}

function getWeekWorkoutLog(dateStr) {
  dateStr = dateStr || todayStr();
  const d   = new Date(dateStr + 'T00:00:00');
  const dow = d.getDay();
  const mon = new Date(d);
  mon.setDate(d.getDate() - (dow === 0 ? 6 : dow - 1));

  const days = [];
  for (let i = 0; i < 7; i++) {
    const dd = new Date(mon);
    dd.setDate(mon.getDate() + i);
    days.push(Utilities.formatDate(dd, 'Asia/Taipei', 'yyyy-MM-dd'));
  }
  return sheetToObjects(getSheet('workout_log')).filter(r => days.includes(String(r.date)));
}

function logWorkout(data) {
  const sh = getSheet('workout_log');
  const id = nextId(sh);
  sh.appendRow([
    id,
    data.date      || todayStr(),
    data.day_label || '',
    data.exercise  || '',
    data.planned   || '',
    parseFloat(data.actual_weight) || 0,
    parseInt(data.reps)    || 0,
    parseInt(data.sets)    || 0,
    parseInt(data.feeling) || 3,
    data.notes || '',
  ]);
  return { ok: true, id };
}

// ── API：有氧記錄 ─────────────────────────────────────────
const AEROBIC_GOAL = 150; // 預設每週有氧目標分鐘（用戶可在設定頁修改）

function logAerobic(data) {
  const sh = getSheet('aerobic_log');
  const id = nextId(sh);
  sh.appendRow([
    id,
    data.date     || todayStr(),
    data.activity || '',
    parseInt(data.minutes) || 0,
    Utilities.formatDate(new Date(), 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss'),
  ]);
  return { ok: true, id };
}

function deleteAerobic(aeroId) {
  const sh   = getSheet('aerobic_log');
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(aeroId)) {
      sh.deleteRow(i + 1);
      return { ok: true };
    }
  }
  return { ok: false };
}

function getWeeklyAerobic(dateStr) {
  dateStr = dateStr || todayStr();
  const d   = new Date(dateStr + 'T00:00:00');
  const dow = d.getDay();
  const mon = new Date(d);
  mon.setDate(d.getDate() - (dow === 0 ? 6 : dow - 1));

  const days = [];
  for (let i = 0; i < 7; i++) {
    const dd = new Date(mon);
    dd.setDate(mon.getDate() + i);
    days.push(Utilities.formatDate(dd, 'Asia/Taipei', 'yyyy-MM-dd'));
  }

  const logs  = sheetToObjects(getSheet('aerobic_log')).filter(r => days.includes(String(r.date)));
  const total = logs.reduce((sum, r) => sum + (parseInt(r.minutes) || 0), 0);

  const s    = getSettings();
  const goal = s && s.aerobic_goal ? +s.aerobic_goal : AEROBIC_GOAL;
  return {
    logs,
    total,
    goal,
    pct:  Math.min(100, Math.round(total / goal * 100)),
    rem:  Math.max(0, goal - total),
  };
}

// ── API：週報 ─────────────────────────────────────────────
function getWeeklyData(weekOffset) {
  weekOffset = weekOffset || 0;
  const today = new Date();
  const dow   = today.getDay();
  const monday = new Date(today);
  monday.setDate(today.getDate() - (dow === 0 ? 6 : dow - 1) + weekOffset * 7);

  const days = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    days.push(Utilities.formatDate(d, 'Asia/Taipei', 'yyyy-MM-dd'));
  }

  const mealsSh    = getSheet('meals');
  const logSh      = getSheet('daily_log');
  const workoutSh  = getSheet('workout_log');
  const allMeals   = sheetToObjects(mealsSh);
  const allLogs    = sheetToObjects(logSh);
  const allWorkouts = sheetToObjects(workoutSh);

  const settings = getSettings();
  const targets  = buildTargets(settings);
  const bmr      = settings && settings.bmr ? +settings.bmr : DEFAULT_BMR;
  const ms       = buildMilestones(settings);
  const activeMs = getActiveMilestone(ms);
  let daysLeft = 0;
  if (activeMs.milestone) {
    const msDate = new Date(activeMs.milestone.date + 'T00:00:00');
    daysLeft = Math.max(0, Math.ceil((msDate - today) / (1000*60*60*24)));
  }

  let weekEaten = 0, weekBurned = 0;
  const dayData = days.map(d => {
    const meals   = allMeals.filter(m => m.date === d);
    const logRow  = allLogs.find(r => r.date === d) || {};
    const totals  = meals.reduce((a, m) => {
      a.kcal += Number(m.calories)||0; a.p += Number(m.protein)||0;
      a.c += Number(m.carbs)||0; a.f += Number(m.fat)||0;
      return a;
    }, { kcal:0, p:0, c:0, f:0 });

    const exercise  = logRow.exercise || null;
    const dayType   = logRow.day_type || null;
    const extraBurn = EXERCISE_BURN[exercise] || 0;
    const burned    = bmr + extraBurn;
    if (totals.kcal > 0) { weekEaten += totals.kcal; weekBurned += burned; }

    const workouts = allWorkouts
      .filter(w => String(w.date) === d)
      .map(w => ({
        exercise: w.exercise || '',
        weight:   Number(w.actual_weight) || 0,
        reps:     Number(w.reps) || 0,
        sets:     Number(w.sets) || 0,
        feeling:  Number(w.feeling) || 3,
      }));

    return { date: d, exercise, dayType, totals, burned, target: dayType ? targets[dayType] : null, workouts };
  });

  const deficit = weekBurned - weekEaten;

  return {
    days: dayData,
    weekEaten:  Math.round(weekEaten),
    weekBurned: Math.round(weekBurned),
    deficit:    Math.round(deficit),
    fatLostG:   Math.round(deficit / 7.7),
    daysLeft,
    weekOffset,
    weekLabel:  formatDateShort(monday) + ' – ' + formatDateShort(new Date(monday.getTime() + 6*24*60*60*1000)),
  };
}

function formatDateShort(d) {
  return Utilities.formatDate(d, 'Asia/Taipei', 'M/d');
}
