/* global Plotly */
"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const appState = {
  page: "overview",
  liveStream: null,
  liveContext: null,
  liveTimer: null,
  audioContext: null,
  audioObjectUrl: null,
  uploadedSamples: null,
  uploadedRate: 0,
};

const PAGE_META = {
  overview: ["信号与系统实验", "通过交互图表直观理解信号、频谱、采样与滤波。所有数值计算均在浏览器本机执行。"],
  "time-frequency": ["时域与频域", "调整信号参数，观察固定时间轴上的波形运动及对应频谱变化。"],
  fourier: ["傅里叶级数合成", "逐项叠加谐波，观察周期信号的逼近过程与吉布斯现象。"],
  stft: ["短时傅里叶变换", "使用滑动分析窗观察线性调频信号的时频特征。"],
  sampling: ["采样与混叠", "改变采样率，比较连续信号、离散采样点与频谱折叠。"],
  phase: ["相位谱与窗函数", "观察信号相位，并比较矩形窗、汉宁窗和汉明窗的频谱影响。"],
  filter: ["滤波前后对比", "调整 FIR 滤波器类型和截止频率，查看信号与频谱变化。"],
  voice: ["语音频谱分析", "分析本机麦克风输入或导入音频，查看实时频谱及分帧时频图。"],
};

const WINDOW_NAMES = ["矩形窗", "汉宁窗", "汉明窗"];
const SIGNAL_NAMES = ["正弦波", "方波", "三角波", "矩形脉冲", "指数衰减"];

function esc(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function selectField(id, label, values, current) {
  return `<label class="field"><span>${esc(label)}</span><select id="${id}">${values.map((item) => {
    const value = typeof item === "object" ? item.value : item;
    const text = typeof item === "object" ? item.label : item;
    return `<option value="${esc(value)}" ${String(value) === String(current) ? "selected" : ""}>${esc(text)}</option>`;
  }).join("")}</select></label>`;
}

function rangeField(id, label, min, max, step, value, unit = "") {
  return `<label class="field"><span>${esc(label)}</span><div class="range-row">
    <input id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="${value}">
    <output for="${id}">${esc(value)}${esc(unit)}</output></div></label>`;
}

function checkField(id, label, checked) {
  return `<label><input id="${id}" type="checkbox" ${checked ? "checked" : ""}>${esc(label)}</label>`;
}

function fieldValue(id) {
  const element = document.getElementById(id);
  return element.type === "checkbox" ? element.checked : element.value;
}

function bindControls(onChange, ignore = []) {
  $("#controls").querySelectorAll("input, select").forEach((input) => {
    if (ignore.includes(input.id)) return;
    if (input.type === "range") {
      input.addEventListener("input", () => {
        const output = document.querySelector(`output[for="${input.id}"]`);
        if (output) output.value = `${input.value}${input.dataset.unit || ""}`;
      });
    }
    input.addEventListener("change", onChange);
  });
}

function showMessage(text, kind = "") {
  const message = $("#message");
  if (!message) return;
  message.textContent = text;
  message.className = `message${kind ? ` ${kind}` : ""}`;
  message.classList.remove("hidden");
}

function clearMessage() {
  const message = $("#message");
  if (message) message.classList.add("hidden");
}

function layoutBase(extra = {}) {
  return {
    template: "plotly_white",
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    font: { family: "Microsoft YaHei, Noto Sans SC, sans-serif", color: "#344258", size: 12 },
    margin: { l: 64, r: 28, t: 70, b: 55 },
    hovermode: "closest",
    ...extra,
  };
}

async function drawPlot(data, layout, frames = [], reuse = false) {
  const chart = $("#chart");
  if (!chart || !window.Plotly) throw new Error("Plotly 图表组件未加载，请检查本地 assets/plotly.min.js。");
  if (reuse) {
    await Plotly.react(chart, data, layout, { responsive: true, displaylogo: false });
  } else {
    Plotly.purge(chart);
    await Plotly.newPlot(chart, data, layout, { responsive: true, displaylogo: false });
  }
  if (frames.length) {
    await Plotly.addFrames(chart, frames);
  }
}

function animationControls(frames, sliderTitle = "帧") {
  return {
    updatemenus: [{
      type: "buttons",
      direction: "left",
      x: 0,
      y: 1.15,
      xanchor: "left",
      yanchor: "top",
      showactive: false,
      buttons: [
        {
          label: "▶ 播放",
          method: "animate",
          args: [null, {
            frame: { duration: 80, redraw: true },
            fromcurrent: true,
            transition: { duration: 0 },
          }],
        },
        {
          label: "Ⅱ 暂停",
          method: "animate",
          args: [[null], {
            mode: "immediate",
            frame: { duration: 0, redraw: false },
            transition: { duration: 0 },
          }],
        },
      ],
    }],
    sliders: [{
      active: 0,
      x: 0.21,
      y: 1.12,
      len: 0.77,
      currentvalue: { prefix: `${sliderTitle} ` },
      steps: frames.map((frame, index) => ({
        label: String(index + 1),
        method: "animate",
        args: [[frame.name], {
          mode: "immediate",
          frame: { duration: 0, redraw: true },
          transition: { duration: 0 },
        }],
      })),
    }],
  };
}

function linspace(start, stop, count, endpoint = true) {
  if (count < 1) return [];
  if (count === 1) return [start];
  const divisor = endpoint ? count - 1 : count;
  return Array.from({ length: count }, (_, index) => start + (stop - start) * index / divisor);
}

function makeWindow(length, name) {
  if (length === 1) return new Float64Array([1]);
  return Float64Array.from({ length }, (_, index) => {
    if (name === "汉宁窗") return 0.5 - 0.5 * Math.cos(2 * Math.PI * index / (length - 1));
    if (name === "汉明窗") return 0.54 - 0.46 * Math.cos(2 * Math.PI * index / (length - 1));
    return 1;
  });
}

function fftReal(input, fftPoints, windowName = "矩形窗") {
  const used = Math.min(input.length, fftPoints);
  const window = makeWindow(used, windowName);
  let gain = 0;
  const real = new Float64Array(fftPoints);
  const imag = new Float64Array(fftPoints);
  for (let index = 0; index < used; index += 1) {
    real[index] = input[index] * window[index];
    gain += window[index];
  }
  if (!gain) throw new Error("窗函数增益为零，无法计算频谱。");

  for (let i = 1, j = 0; i < fftPoints; i += 1) {
    let bit = fftPoints >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [real[i], real[j]] = [real[j], real[i]];
      [imag[i], imag[j]] = [imag[j], imag[i]];
    }
  }
  for (let size = 2; size <= fftPoints; size <<= 1) {
    const angle = -2 * Math.PI / size;
    const half = size >> 1;
    for (let start = 0; start < fftPoints; start += size) {
      for (let offset = 0; offset < half; offset += 1) {
        const cosine = Math.cos(angle * offset);
        const sine = Math.sin(angle * offset);
        const even = start + offset;
        const odd = even + half;
        const oddReal = real[odd] * cosine - imag[odd] * sine;
        const oddImag = real[odd] * sine + imag[odd] * cosine;
        real[odd] = real[even] - oddReal;
        imag[odd] = imag[even] - oddImag;
        real[even] += oddReal;
        imag[even] += oddImag;
      }
    }
  }
  const bins = Math.floor(fftPoints / 2) + 1;
  const magnitude = new Float64Array(bins);
  const phase = new Float64Array(bins);
  let maximum = 0;
  for (let index = 0; index < bins; index += 1) {
    magnitude[index] = Math.hypot(real[index], imag[index]) / gain;
    if ((fftPoints % 2 === 0 && index > 0 && index < bins - 1) ||
      (fftPoints % 2 !== 0 && index > 0)) magnitude[index] *= 2;
    phase[index] = Math.atan2(imag[index], real[index]);
    maximum = Math.max(maximum, magnitude[index]);
  }
  for (let index = 0; index < bins; index += 1) {
    if (magnitude[index] <= maximum * 1e-8) phase[index] = NaN;
  }
  return { magnitude, phase };
}

function frequencyAxis(fftPoints, samplingRate) {
  return Array.from({ length: Math.floor(fftPoints / 2) + 1 },
    (_, index) => index * samplingRate / fftPoints);
}

function generateSignal(type, time, options, offset = 0) {
  const { amplitude, frequency, phase, duty, pulseWidth, decay } = options;
  const center = (time[0] + time[time.length - 1]) / 2;
  return time.map((value) => {
    const shifted = value + offset;
    if (type === "正弦波" || type === "方波" || type === "三角波") {
      const cycles = ((frequency * shifted + phase / 360) % 1 + 1) % 1;
      if (type === "正弦波") return amplitude * Math.sin(2 * Math.PI * cycles);
      if (type === "方波") return amplitude * (cycles < duty ? 1 : -1);
      return amplitude * (1 - 4 * Math.abs(cycles - 0.5));
    }
    if (type === "矩形脉冲") return Math.abs(shifted - center) < pulseWidth / 2 ? amplitude : 0;
    return amplitude * Math.exp(-decay * Math.max(shifted, 0));
  });
}

function fieldPanel(markup) {
  $("#page-body").innerHTML = `<div id="message" class="message hidden"></div>
    <section class="panel"><div class="controls-grid" id="controls">${markup}</div></section>
    <section class="panel chart-panel"><div id="chart"></div></section><div id="note"></div>`;
}

function setNote(text) {
  $("#note").innerHTML = `<p class="note">${esc(text)}</p>`;
}

function renderOverview() {
  const modules = [
    ["01", "time-frequency", "时域与频域", "五种信号、幅度频谱和函数自身运动动画"],
    ["02", "fourier", "傅里叶级数合成", "逐项增加谐波并观察吉布斯现象"],
    ["03", "stft", "短时傅里叶变换", "滑动分析窗与线性调频信号时频图"],
    ["04", "sampling", "采样与混叠", "奈奎斯特判定、离散采样和频谱折叠"],
    ["05", "phase", "相位谱与窗函数", "三种常用窗函数对幅度和相位的影响"],
    ["06", "filter", "滤波前后对比", "低通、高通、带通和带阻 FIR 滤波器"],
    ["07", "voice", "语音频谱分析", "本机麦克风、WAV 导入与分帧时频回放"],
  ];
  $("#page-body").innerHTML = `
    <section class="hero-card"><div><h2>从波形看见信号</h2>
      <p>通过可调参数和动态频谱图，探索傅里叶变换、采样、滤波与语音分析。<br>
      本页面是纯 HTML/JavaScript 应用，计算和麦克风采集均在本机浏览器中进行。</p></div>
      <div class="hero-mark">∿</div></section>
    <section class="panel"><h2>实验模块</h2><div class="module-grid">${modules.map((item) => `
      <article class="module-card" data-open-page="${item[1]}">
        <span class="module-index">MODULE ${item[0]}</span><h3>${item[2]}</h3><p>${item[3]}</p>
      </article>`).join("")}</div></section>
    <div class="stats-row"><div class="stat-card"><strong>7</strong><span>基础与拓展实验</span></div>
      <div class="stat-card"><strong>本机</strong><span>数据不上传到服务器</span></div>
      <div class="stat-card"><strong>离线</strong><span>Plotly 图表资源已随项目打包</span></div></div>`;
  $("#page-body").querySelectorAll("[data-open-page]").forEach((card) =>
    card.addEventListener("click", () => navigate(card.dataset.openPage)));
}

function renderTimeFrequency() {
  fieldPanel(
    selectField("signal", "信号类型", SIGNAL_NAMES, "正弦波") +
    selectField("fs", "采样率 (Hz)", [500, 1000, 2000, 4000, 8000], 2000) +
    selectField("duration", "显示时长 (s)", [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2], 1) +
    rangeField("amplitude", "幅值", 0.1, 5, 0.1, 1) +
    rangeField("frequency", "频率 (Hz)", 0.5, 100, 0.5, 5) +
    rangeField("phase", "相位 (°)", -180, 180, 1, 0) +
    rangeField("duty", "方波占空比", 5, 95, 1, 50, "%") +
    rangeField("pulse-width", "脉冲宽度 (s)", 0.01, 0.5, 0.01, 0.1) +
    rangeField("decay", "指数衰减系数 (1/s)", 0.1, 10, 0.1, 2) +
    selectField("fft-points", "FFT 点数", [256, 512, 1024, 2048, 4096], 1024) +
    selectField("window", "窗函数", WINDOW_NAMES, "矩形窗"),
  );
  const update = () => {
    try { clearMessage(); drawTimeFrequency(); } catch (error) { showMessage(error.message, "error"); }
  };
  bindControls(update);
  drawTimeFrequency();
}

async function drawTimeFrequency() {
  const fs = Number(fieldValue("fs"));
  const duration = Number(fieldValue("duration"));
  const fftPoints = Number(fieldValue("fft-points"));
  const count = Math.round(fs * duration);
  const fullTime = Array.from({ length: count }, (_, index) => index / fs);
  const step = Math.max(1, Math.ceil(count / 1200));
  const time = fullTime.filter((_, index) => index % step === 0);
  const type = fieldValue("signal");
  const options = {
    amplitude: Number(fieldValue("amplitude")),
    frequency: Number(fieldValue("frequency")),
    phase: Number(fieldValue("phase")),
    duty: Number(fieldValue("duty")) / 100,
    pulseWidth: Number(fieldValue("pulse-width")),
    decay: Number(fieldValue("decay")),
  };
  const windowName = fieldValue("window");
  const frameCount = 60;
  const frequenciesFull = frequencyAxis(fftPoints, fs);
  const frequencyStep = Math.max(1, Math.ceil(frequenciesFull.length / 512));
  const frequencies = frequenciesFull.filter((_, index) => index % frequencyStep === 0);
  const waveFrames = [];
  const spectrumFrames = [];
  for (let frameIndex = 0; frameIndex < frameCount; frameIndex += 1) {
    const offset = frameIndex * 0.05;
    const fullSamples = generateSignal(type, fullTime, options, offset);
    const displaySamples = time.map((value) => {
      const originalIndex = Math.min(count - 1, Math.round(value * fs));
      return fullSamples[originalIndex];
    });
    const spectrum = fftReal(fullSamples, fftPoints, windowName).magnitude;
    waveFrames.push(displaySamples);
    spectrumFrames.push(Array.from(spectrum).filter((_, index) => index % frequencyStep === 0));
  }
  const frames = waveFrames.map((wave, index) => ({
    name: String(index),
    data: [{ y: wave }, { y: spectrumFrames[index] }],
    traces: [0, 1],
    layout: {
      xaxis: { range: [time[0], time[time.length - 1]] },
      xaxis2: { range: [0, fs / 2] },
    },
  }));
  const values = waveFrames.flat();
  const low = Math.min(...values);
  const high = Math.max(...values);
  const padding = Math.max((high - low) * 0.08, 0.05);
  const layout = layoutBase({
    height: 690,
    margin: { l: 66, r: 28, t: 132, b: 48 },
    grid: { rows: 2, columns: 1, pattern: "independent" },
    annotations: [
      { text: "时域波形", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false, font: { size: 14 } },
      { text: `单边幅度谱（${windowName}）`, x: 0.5, y: 0.47, xref: "paper", yref: "paper", showarrow: false, font: { size: 14 } },
    ],
    xaxis: { title: "时间 (s)", range: [time[0], time[time.length - 1]], fixedrange: true, domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", range: [low - padding, high + padding], domain: [0.57, 0.94], anchor: "x" },
    xaxis2: { title: "频率 (Hz)", range: [0, fs / 2], fixedrange: true, domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "幅度", domain: [0.05, 0.42], anchor: "x2" },
    title: { text: `采样率 ${fs} Hz · FFT ${fftPoints} 点 · 频率栅格 ${formatNumber(fs / fftPoints)} Hz`, x: 0.02, y: 0.99 },
    ...animationControls(frames),
  });
  await drawPlot([
    { type: "scatter", mode: "lines", x: time, y: waveFrames[0], name: "信号", line: { color: "#1769aa", width: 2 }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "lines", x: frequencies, y: spectrumFrames[0], name: "幅度谱", line: { color: "#d1495b", width: 1.5 }, xaxis: "x2", yaxis: "y2" },
  ], layout, frames);
  const descriptions = {
    正弦波: "理想正弦波的频谱集中在基频；有限时长截取和加窗会影响谱线外观。",
    方波: "周期方波包含基波和奇次谐波；占空比变化会改变谐波幅值。",
    三角波: "对称三角波主要包含奇次谐波，谐波幅值比方波衰减更快。",
    矩形脉冲: "单个矩形脉冲的频谱具有 sinc 形状；脉宽越窄，频谱主瓣越宽。",
    指数衰减: "指数衰减信号的能量集中在起始时刻，频谱呈连续展宽的形态。",
  };
  setNote(`${descriptions[type]} 每帧频谱均根据该帧真实信号重新计算；动画在浏览器中播放，不会触发服务器重绘。`);
}

function harmonicData(type, maxOrder, amplitude) {
  const orders = [];
  const coeffs = [];
  for (let n = 1; n <= maxOrder; n += 1) {
    if (n % 2 === 0) continue;
    orders.push(n);
    coeffs.push(type === "方波"
      ? 4 * amplitude / (Math.PI * n)
      : 8 * amplitude * ((-1) ** ((n - 1) / 2)) / (Math.PI ** 2 * n ** 2));
  }
  return { orders, coeffs };
}

function seriesPartial(time, type, frequency, maxOrder, amplitude) {
  const { orders, coeffs } = harmonicData(type, maxOrder, amplitude);
  return time.map((t) => orders.reduce(
    (sum, order, index) => sum + coeffs[index] * Math.sin(2 * Math.PI * order * frequency * t),
    0,
  ));
}

function renderFourier() {
  fieldPanel(
    selectField("series-type", "目标信号", ["方波", "三角波"], "方波") +
    rangeField("series-amplitude", "目标峰值幅度", 0.2, 3, 0.1, 1) +
    rangeField("fundamental", "基波频率 (Hz)", 1, 20, 1, 2) +
    selectField("max-harmonic", "最高谐波次数", [1, 3, 5, 7, 9, 11, 15, 21, 31, 41, 51], 15),
  );
  bindControls(() => drawFourier());
  drawFourier();
}

async function drawFourier() {
  const type = fieldValue("series-type");
  const amplitude = Number(fieldValue("series-amplitude"));
  const frequency = Number(fieldValue("fundamental"));
  const maxOrder = Number(fieldValue("max-harmonic"));
  const time = linspace(0, 2 / frequency, 1200, false);
  const phase = time.map((t) => 2 * Math.PI * frequency * t);
  const reference = phase.map((value) => type === "方波"
    ? amplitude * Math.sign(Math.sin(value))
    : amplitude * (2 / Math.PI) * Math.asin(Math.sin(value)));
  const approximations = [];
  const frames = [];
  const allHarmonics = harmonicData(type, maxOrder, amplitude);
  for (let count = 1; count <= maxOrder; count += 1) {
    const wave = seriesPartial(time, type, frequency, count, amplitude);
    approximations.push(wave);
    frames.push({
      name: String(count - 1),
      data: [
        { y: wave },
        { y: allHarmonics.orders.map((order, index) => order <= count ? Math.abs(allHarmonics.coeffs[index]) : 0) },
      ],
      traces: [1, 2],
      layout: { xaxis: { range: [time[0], time[time.length - 1]] } },
    });
  }
  const harmonics = allHarmonics;
  const allValues = reference.concat(...approximations);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const layout = layoutBase({
    height: 680,
    margin: { l: 65, r: 25, t: 128, b: 50 },
    grid: { rows: 2, columns: 1, pattern: "independent" },
    annotations: [
      { text: `${type}傅里叶级数合成`, x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
      { text: "当前谐波幅值", x: 0.5, y: 0.47, xref: "paper", yref: "paper", showarrow: false },
    ],
    xaxis: { title: "时间 (s)", range: [time[0], time[time.length - 1]], fixedrange: true, domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", range: [min - 0.15, max + 0.15], domain: [0.57, 0.94], anchor: "x" },
    xaxis2: { title: "谐波序号", range: [0, maxOrder + 1], domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "峰值幅度", domain: [0.05, 0.42], anchor: "x2" },
    ...animationControls(frames, "谐波"),
  });
  await drawPlot([
    { type: "scatter", mode: "lines", x: time, y: reference, name: "目标波形", line: { color: "#888888", dash: "dot" }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "lines", x: time, y: approximations[0], name: "合成波形", line: { color: "#1769aa", width: 2 }, xaxis: "x", yaxis: "y" },
    { type: "bar", x: harmonics.orders, y: harmonics.orders.map((order, index) => order === 1 ? Math.abs(harmonics.coeffs[index]) : 0), name: "谐波幅值", marker: { color: "#d1495b" }, xaxis: "x2", yaxis: "y2" },
  ], layout, frames);
  setNote("方波理想频谱只包含奇次谐波，幅度约按 1/n 衰减；三角波奇次谐波约按 1/n² 衰减。跳变附近的过冲是吉布斯现象。");
}

function computeSTFT(samples, samplingRate, windowLength, hopLength, fftPoints, windowName) {
  const window = makeWindow(windowLength, windowName);
  const starts = [];
  const magnitudes = [];
  const frameTimes = [];
  for (let start = 0; start < samples.length; start += hopLength) {
    const frame = new Float64Array(windowLength);
    const validLength = Math.min(windowLength, samples.length - start);
    for (let index = 0; index < validLength; index += 1) frame[index] = samples[start + index];
    starts.push(start);
    frameTimes.push((start + Math.max(0, validLength - 1) / 2) / samplingRate);
    magnitudes.push(Array.from(fftReal(frame, fftPoints, windowName).magnitude));
  }
  return { starts, frameTimes, magnitudes, frequencies: frequencyAxis(fftPoints, samplingRate), window };
}

function heatmapData(frameTimes, frequencies, magnitudes) {
  const z = frequencies.map((_, frequencyIndex) =>
    magnitudes.map((frame) => 20 * Math.log10(Math.max(frame[frequencyIndex], 1e-8))));
  return z;
}

function currentWindowShapes(time, frameTime, windowLength, samplingRate, frequencies, xRef = "x", yRef = "y domain", spectrumX = "x2", spectrumY = "y2") {
  const half = windowLength / (2 * samplingRate);
  return [
    {
      type: "rect", xref: xRef, yref: yRef,
      x0: Math.max(time[0], frameTime - half), x1: Math.min(time[time.length - 1], frameTime + half),
      y0: 0, y1: 1, fillcolor: "rgba(244,162,97,.25)", line: { width: 0 }, layer: "above",
    },
    {
      type: "line", xref: spectrumX, yref: spectrumY,
      x0: frameTime, x1: frameTime, y0: frequencies[0], y1: frequencies[frequencies.length - 1],
      line: { color: "#d1495b", width: 2 },
    },
  ];
}

function makeStftFrames(time, frameTimes, frequencies, windowLength, samplingRate) {
  return frameTimes.map((frameTime, index) => ({
    name: String(index),
    layout: {
      shapes: currentWindowShapes(time, frameTime, windowLength, samplingRate, frequencies),
      xaxis: { range: [time[0], time[time.length - 1]] },
    },
  }));
}

function stftLayout(time, frameTimes, frequencies, frameTimesForFrames, windowLength, samplingRate) {
  const frames = makeStftFrames(time, frameTimesForFrames, frequencies, windowLength, samplingRate);
  const shapes = currentWindowShapes(time, frameTimes[0], windowLength, samplingRate, frequencies);
  const layout = layoutBase({
    height: 700,
    margin: { l: 68, r: 35, t: 128, b: 50 },
    grid: { rows: 2, columns: 1, pattern: "independent" },
    annotations: [
      { text: "信号与当前分析窗", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
      { text: "STFT 时频图（相对幅度 dB）", x: 0.5, y: 0.48, xref: "paper", yref: "paper", showarrow: false },
    ],
    xaxis: { title: "时间 (s)", range: [time[0], time[time.length - 1]], fixedrange: true, domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", domain: [0.61, 0.94], anchor: "x" },
    xaxis2: { title: "时间 (s)", range: [frameTimes[0], frameTimes[frameTimes.length - 1]], fixedrange: true, domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "频率 (Hz)", range: [frequencies[0], frequencies[frequencies.length - 1]], domain: [0.05, 0.4], anchor: "x2" },
    shapes,
    ...animationControls(frames),
  });
  return { layout, frames };
}

function renderStft() {
  fieldPanel(
    rangeField("chirp-start", "起始频率 (Hz)", 2, 100, 1, 10) +
    rangeField("chirp-end", "结束频率 (Hz)", 20, 400, 1, 180) +
    selectField("window-ms", "窗长 (ms)", [32, 48, 64, 80, 96, 112, 128, 160, 192, 256, 320, 400, 500], 128) +
    selectField("stft-window", "分析窗", WINDOW_NAMES, "汉宁窗"),
  );
  bindControls(() => {
    clearMessage();
    if (Number(fieldValue("chirp-end")) <= Number(fieldValue("chirp-start"))) {
      showMessage("结束频率必须大于起始频率。", "error");
      return;
    }
    drawStft();
  });
  drawStft();
}

async function drawStft() {
  const samplingRate = 1000;
  const duration = 2;
  const sampleCount = samplingRate * duration;
  const time = Array.from({ length: sampleCount }, (_, index) => index / samplingRate);
  const startFrequency = Number(fieldValue("chirp-start"));
  const endFrequency = Number(fieldValue("chirp-end"));
  const chirpRate = (endFrequency - startFrequency) / duration;
  const samples = time.map((t) => Math.sin(2 * Math.PI * (startFrequency * t + 0.5 * chirpRate * t * t)));
  const windowLength = Math.max(32, Math.round(Number(fieldValue("window-ms")) * samplingRate / 1000));
  const hopLength = Math.max(1, Math.floor(windowLength / 8));
  const fftPoints = 2 ** Math.ceil(Math.log2(windowLength));
  const stft = computeSTFT(samples, samplingRate, windowLength, hopLength, fftPoints, fieldValue("stft-window"));
  const { layout, frames } = stftLayout(time, stft.frameTimes, stft.frequencies, stft.frameTimes, windowLength, samplingRate);
  await drawPlot([
    { type: "scatter", mode: "lines", x: time, y: samples, name: "线性调频信号", line: { color: "#1769aa", width: 1.4 }, xaxis: "x", yaxis: "y" },
    { type: "heatmap", x: stft.frameTimes, y: stft.frequencies, z: heatmapData(stft.frameTimes, stft.frequencies, stft.magnitudes), colorscale: "Magma", colorbar: { title: "幅度 (dB)" }, name: "STFT", xaxis: "x2", yaxis: "y2" },
  ], layout, frames);
  setNote(`窗长 ${windowLength} 点（${formatNumber(windowLength / samplingRate * 1000)} ms），FFT 栅格 ${formatNumber(samplingRate / fftPoints)} Hz。缩短窗长可提高时间定位能力，但会降低频率分辨能力。`);
}

function formatNumber(value, digits = 3) {
  return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: digits });
}

function renderSampling() {
  fieldPanel(
    rangeField("low-tone", "低频分量 (Hz)", 5, 80, 1, 18) +
    rangeField("high-tone", "高频分量 (Hz)", 20, 200, 1, 65) +
    rangeField("sample-rate", "采样率 fs (Hz)", 20, 500, 5, 100),
  );
  bindControls(() => {
    clearMessage();
    if (Number(fieldValue("high-tone")) <= Number(fieldValue("low-tone"))) {
      showMessage("高频分量必须大于低频分量。", "error");
      return;
    }
    drawSampling();
  });
  drawSampling();
}

function interpolate(x, xp, fp) {
  if (x <= xp[0]) return fp[0];
  if (x >= xp[xp.length - 1]) return fp[fp.length - 1];
  const pos = x * (xp.length - 1) / (xp[xp.length - 1] - xp[0]);
  const index = Math.min(xp.length - 2, Math.floor(pos));
  const weight = (x - xp[index]) / (xp[index + 1] - xp[index]);
  return fp[index] * (1 - weight) + fp[index + 1] * weight;
}

async function drawSampling() {
  const lowFrequency = Number(fieldValue("low-tone"));
  const highFrequency = Number(fieldValue("high-tone"));
  const samplingRate = Number(fieldValue("sample-rate"));
  const referenceRate = 4000;
  const time = Array.from({ length: referenceRate }, (_, index) => index / referenceRate);
  const samples = time.map((t) => Math.sin(2 * Math.PI * lowFrequency * t) + 0.7 * Math.sin(2 * Math.PI * highFrequency * t));
  const sampleTimes = [];
  for (let t = 0; t < 1; t += 1 / samplingRate) sampleTimes.push(t);
  const sampleValues = sampleTimes.map((t) => interpolate(t, time, samples));
  const fftPoints = 4096;
  const referenceSpectrum = fftReal(samples, fftPoints, "汉宁窗").magnitude;
  const sampledSpectrum = fftReal(sampleValues, fftPoints, "汉宁窗").magnitude;
  const frequencies = frequencyAxis(fftPoints, samplingRate);
  const referenceFrequencies = frequencyAxis(fftPoints, referenceRate);
  const originalDisplay = frequencies.map((f) => interpolate(f, referenceFrequencies, Array.from(referenceSpectrum)));
  const displayOriginal = originalDisplay.map((value, index) => frequencies[index] <= samplingRate / 2 ? value : null);
  const displaySampled = Array.from(sampledSpectrum, (value, index) => frequencies[index] <= samplingRate / 2 ? value : null);
  const folded = ((highFrequency % samplingRate) + samplingRate) % samplingRate;
  const alias = Math.min(folded, samplingRate - folded);
  const aliased = highFrequency > samplingRate / 2;
  const statusText = aliased
    ? `发生混叠：最高频率 ${highFrequency} Hz 折叠至 ${formatNumber(alias)} Hz；奈奎斯特频率为 ${samplingRate / 2} Hz。`
    : `当前设置满足奈奎斯特采样条件；奈奎斯特频率为 ${samplingRate / 2} Hz。`;
  showMessage(statusText, aliased ? "error" : "success");
  const layout = layoutBase({
    height: 650,
    margin: { t: 65, b: 55 },
    grid: { rows: 2, columns: 1, pattern: "independent" },
    annotations: [
      { text: "连续信号与离散采样", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
      { text: "频谱对比", x: 0.5, y: 0.48, xref: "paper", yref: "paper", showarrow: false },
    ],
    xaxis: { title: "时间 (s)", domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", domain: [0.57, 0.94], anchor: "x" },
    xaxis2: { title: "频率 (Hz)", range: [0, samplingRate / 2], domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "归一化幅度", domain: [0.05, 0.42], anchor: "x2" },
    shapes: [{ type: "line", xref: "x2", yref: "y2 domain", x0: samplingRate / 2, x1: samplingRate / 2, y0: 0, y1: 1, line: { color: "#d1495b", dash: "dash" } }],
  });
  await drawPlot([
    { type: "scatter", mode: "lines", x: time.filter((_, index) => index % 4 === 0), y: samples.filter((_, index) => index % 4 === 0), name: "连续参考信号", line: { color: "#1769aa" }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "markers", x: sampleTimes, y: sampleValues, name: "离散采样点", marker: { color: "#d1495b", size: 6 }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "lines", x: frequencies, y: displayOriginal, name: "原信号频谱", line: { color: "#1769aa" }, xaxis: "x2", yaxis: "y2" },
    { type: "scatter", mode: "lines", x: frequencies, y: displaySampled, name: "采样序列频谱", line: { color: "#d1495b" }, xaxis: "x2", yaxis: "y2" },
  ], layout);
  setNote(`高频分量折叠频率：${formatNumber(alias)} Hz。频率显示范围限制在当前奈奎斯特区间。`);
}

function renderPhase() {
  fieldPanel(
    selectField("phase-rate", "采样率 (Hz)", [512, 1024, 2048], 1024) +
    selectField("phase-duration", "记录时长 (s)", [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2], 1) +
    selectField("phase-fft", "FFT 点数", [512, 1024, 2048, 4096], 1024) +
    rangeField("tone-frequency", "信号频率 (Hz)", 1, 500, 0.5, 37.5) +
    rangeField("tone-phase", "相位 (°)", -180, 180, 1, 35) +
    `<div class="field"><span>对比窗函数</span><div class="check-options">
      ${checkField("win-rect", "矩形窗", true)}${checkField("win-hann", "汉宁窗", true)}${checkField("win-hamming", "汉明窗", true)}
    </div></div>`,
  );
  bindControls(() => {
    clearMessage();
    if (!["win-rect", "win-hann", "win-hamming"].some((id) => fieldValue(id))) {
      showMessage("请至少选择一种窗函数。", "error");
      return;
    }
    drawPhase();
  });
  drawPhase();
}

async function drawPhase() {
  const samplingRate = Number(fieldValue("phase-rate"));
  const duration = Number(fieldValue("phase-duration"));
  const fftPoints = Number(fieldValue("phase-fft"));
  const frequency = Number(fieldValue("tone-frequency"));
  const phaseDegrees = Number(fieldValue("tone-phase"));
  const count = Math.round(samplingRate * duration);
  const time = Array.from({ length: count }, (_, index) => index / samplingRate);
  const samples = time.map((t) => Math.sin(2 * Math.PI * frequency * t + phaseDegrees * Math.PI / 180));
  const frequencies = frequencyAxis(fftPoints, samplingRate);
  const checked = [
    ["win-rect", "矩形窗"],
    ["win-hann", "汉宁窗"],
    ["win-hamming", "汉明窗"],
  ].filter(([id]) => fieldValue(id));
  const colors = { 矩形窗: "#1769aa", 汉宁窗: "#d1495b", 汉明窗: "#36866f" };
  const data = [
    { type: "scatter", mode: "lines", x: time, y: samples, name: "信号", line: { color: "#1769aa" }, xaxis: "x", yaxis: "y" },
  ];
  checked.forEach(([, name]) => {
    const result = fftReal(samples, fftPoints, name);
    data.push({ type: "scatter", mode: "lines", x: frequencies, y: Array.from(result.magnitude), name, line: { color: colors[name] }, xaxis: "x2", yaxis: "y2" });
    data.push({ type: "scatter", mode: "lines", x: frequencies, y: Array.from(result.phase, (value) => Number.isFinite(value) ? value * 180 / Math.PI : null), name: `${name}相位`, showlegend: false, line: { color: colors[name], dash: "dot" }, xaxis: "x3", yaxis: "y3" });
  });
  await drawPlot(data, layoutBase({
    height: 760,
    margin: { l: 70, r: 30, t: 62, b: 55 },
    xaxis: { title: "时间 (s)", domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", domain: [0.71, 0.98], anchor: "x" },
    xaxis2: { title: "频率 (Hz)", domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "幅度", domain: [0.38, 0.64], anchor: "x2" },
    xaxis3: { title: "频率 (Hz)", range: [0, samplingRate / 2], domain: [0, 1], anchor: "y3" },
    yaxis3: { title: "相位 (°)", range: [-180, 180], domain: [0.05, 0.31], anchor: "x3" },
    annotations: [
      { text: "时域信号", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
      { text: "单边幅度谱", x: 0.5, y: 0.66, xref: "paper", yref: "paper", showarrow: false },
      { text: "相位谱", x: 0.5, y: 0.33, xref: "paper", yref: "paper", showarrow: false },
    ],
  }));
  setNote("非整周期截断会造成频谱泄漏。汉宁/汉明窗通常降低旁瓣，但会加宽主瓣；幅度接近零的频率点不显示相位。");
}

function designFir(type, samplingRate, cutoffLow, cutoffHigh, tapCount) {
  const nyquist = samplingRate / 2;
  const lowpass = (cutoff) => {
    const normalized = cutoff / nyquist;
    const center = (tapCount - 1) / 2;
    const result = Array.from({ length: tapCount }, (_, index) => {
      const offset = index - center;
      const sinc = offset === 0 ? normalized : Math.sin(Math.PI * normalized * offset) / (Math.PI * offset);
      return sinc * (0.54 - 0.46 * Math.cos(2 * Math.PI * index / (tapCount - 1)));
    });
    const sum = result.reduce((acc, value) => acc + value, 0);
    return result.map((value) => value / sum);
  };
  const lp = lowpass(cutoffLow);
  if (type === "低通") return lp;
  if (type === "高通") return lp.map((value, index) => (index === (tapCount - 1) / 2 ? 1 : 0) - value);
  const hp = lowpass(cutoffHigh);
  const band = hp.map((value, index) => value - lp[index]);
  if (type === "带通") {
    const centerFrequency = (cutoffLow + cutoffHigh) / 2;
    let real = 0;
    let imag = 0;
    band.forEach((value, index) => {
      real += value * Math.cos(2 * Math.PI * centerFrequency * index / samplingRate);
      imag -= value * Math.sin(2 * Math.PI * centerFrequency * index / samplingRate);
    });
    const gain = Math.hypot(real, imag) || 1;
    return band.map((value) => value / gain);
  }
  return band.map((value, index) => (index === (tapCount - 1) / 2 ? 1 : 0) - value);
}

function applyFir(samples, coefficients) {
  const padding = Math.floor(coefficients.length / 2);
  return samples.map((_, index) => {
    let sum = 0;
    for (let tap = 0; tap < coefficients.length; tap += 1) {
      const sourceIndex = Math.max(0, Math.min(samples.length - 1, index + tap - padding));
      sum += samples[sourceIndex] * coefficients[tap];
    }
    return sum;
  });
}

function seededNoise(seed) {
  let value = seed >>> 0;
  return () => {
    value = (1664525 * value + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function renderFilter() {
  fieldPanel(
    selectField("filter-type", "滤波器", ["低通", "高通", "带通", "带阻"], "低通") +
    rangeField("cutoff-low", "截止频率 / 下限 (Hz)", 10, 450, 5, 120) +
    rangeField("cutoff-high", "上限频率 (Hz)", 20, 490, 5, 260) +
    selectField("tap-count", "滤波器抽头", [31, 51, 101, 151], 101),
  );
  bindControls(() => {
    clearMessage();
    if (["带通", "带阻"].includes(fieldValue("filter-type")) &&
      Number(fieldValue("cutoff-high")) <= Number(fieldValue("cutoff-low"))) {
      showMessage("带通/带阻的上限频率必须大于下限频率。", "error");
      return;
    }
    drawFilter();
  });
  drawFilter();
}

async function drawFilter() {
  const samplingRate = 1000;
  const count = 2000;
  const time = Array.from({ length: count }, (_, index) => index / samplingRate);
  const random = seededNoise(42);
  const original = time.map((t) => Math.sin(2 * Math.PI * 35 * t) +
    0.7 * Math.sin(2 * Math.PI * 180 * t) + 0.4 * Math.sin(2 * Math.PI * 330 * t) +
    0.12 * (random() * 2 - 1));
  const type = fieldValue("filter-type");
  const cutoffLow = Number(fieldValue("cutoff-low"));
  const cutoffHigh = Number(fieldValue("cutoff-high"));
  const coefficients = designFir(type, samplingRate, cutoffLow, cutoffHigh, Number(fieldValue("tap-count")));
  const filtered = applyFir(original, coefficients);
  const fftPoints = 2048;
  const frequencies = frequencyAxis(fftPoints, samplingRate);
  const originalSpectrum = fftReal(original, fftPoints, "汉宁窗").magnitude;
  const filteredSpectrum = fftReal(filtered, fftPoints, "汉宁窗").magnitude;
  await drawPlot([
    { type: "scatter", mode: "lines", x: time, y: original, name: "滤波前", line: { color: "#1769aa", width: 1 }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "lines", x: time, y: filtered, name: "滤波后", line: { color: "#d1495b", width: 1.4 }, xaxis: "x", yaxis: "y" },
    { type: "scatter", mode: "lines", x: frequencies, y: Array.from(originalSpectrum), name: "滤波前频谱", line: { color: "#1769aa" }, xaxis: "x2", yaxis: "y2" },
    { type: "scatter", mode: "lines", x: frequencies, y: Array.from(filteredSpectrum), name: "滤波后频谱", line: { color: "#d1495b" }, xaxis: "x2", yaxis: "y2" },
  ], layoutBase({
    height: 640,
    margin: { t: 65, b: 55 },
    grid: { rows: 2, columns: 1, pattern: "independent" },
    annotations: [
      { text: "时域波形", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
      { text: "幅度频谱（汉宁窗）", x: 0.5, y: 0.48, xref: "paper", yref: "paper", showarrow: false },
    ],
    xaxis: { title: "时间 (s)", domain: [0, 1], anchor: "y" },
    yaxis: { title: "幅值", domain: [0.57, 0.94], anchor: "x" },
    xaxis2: { title: "频率 (Hz)", range: [0, samplingRate / 2], domain: [0, 1], anchor: "y2" },
    yaxis2: { title: "幅度", domain: [0.05, 0.42], anchor: "x2" },
  }));
  setNote(`窗函数法 FIR ${type}滤波器，共 ${coefficients.length} 个抽头。增加阶数通常使过渡带更窄，但会增加运算量和边界瞬态。`);
}

function stopLiveMicrophone() {
  if (appState.liveTimer) clearInterval(appState.liveTimer);
  appState.liveTimer = null;
  if (appState.liveStream) appState.liveStream.getTracks().forEach((track) => track.stop());
  appState.liveStream = null;
  if (appState.liveContext) appState.liveContext.close().catch(() => {});
  appState.liveContext = null;
}

async function startLiveMicrophone() {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("当前浏览器不支持麦克风采集。请使用新版 Chrome/Edge，或通过 localhost 打开页面。");
    }
    stopLiveMicrophone();
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const context = new AudioContextClass();
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 4096;
    source.connect(analyser);
    appState.liveStream = stream;
    appState.liveContext = context;
    const samples = new Float32Array(analyser.fftSize);
    const chart = $("#chart");
    const update = async () => {
      if (!appState.liveContext || !chart) return;
      analyser.getFloatTimeDomainData(samples);
      const clean = Array.from(samples);
      const result = fftReal(clean, analyser.fftSize, "汉宁窗");
      const frequencies = frequencyAxis(analyser.fftSize, context.sampleRate);
      const time = clean.map((_, index) => (index - clean.length) / context.sampleRate);
      await Plotly.react(chart, [
        { type: "scatter", mode: "lines", x: time, y: clean, name: "实时波形", line: { color: "#1769aa", width: 1 } },
        { type: "scatter", mode: "lines", x: frequencies, y: Array.from(result.magnitude), name: "幅度谱", line: { color: "#d1495b", width: 1.5 }, xaxis: "x2", yaxis: "y2" },
      ], layoutBase({
        height: 490,
        grid: { rows: 2, columns: 1, pattern: "independent" },
        annotations: [
          { text: "最近一段麦克风波形", x: 0.5, y: 1, xref: "paper", yref: "paper", showarrow: false },
          { text: "实时单边幅度谱", x: 0.5, y: 0.48, xref: "paper", yref: "paper", showarrow: false },
        ],
        xaxis: { title: "时间 (s)", domain: [0, 1], anchor: "y" },
        yaxis: { title: "幅值", domain: [0.57, 0.94], anchor: "x" },
        xaxis2: { title: "频率 (Hz)", range: [0, context.sampleRate / 2], domain: [0, 1], anchor: "y2" },
        yaxis2: { title: "幅度", domain: [0.05, 0.42], anchor: "x2" },
      }), { responsive: true, displaylogo: false });
    };
    await update();
    appState.liveTimer = setInterval(() => update().catch((error) => showMessage(error.message, "error")), 250);
    showMessage(`麦克风已启动，采样率 ${context.sampleRate} Hz。音频仅在本机浏览器处理。`, "success");
    $("#live-start").disabled = true;
    $("#live-stop").disabled = false;
  } catch (error) {
    stopLiveMicrophone();
    showMessage(`无法启动麦克风：${error.message}`, "error");
  }
}

function stopLiveButton() {
  stopLiveMicrophone();
  const start = $("#live-start");
  const stop = $("#live-stop");
  if (start) start.disabled = false;
  if (stop) stop.disabled = true;
  showMessage("麦克风已停止。");
}

async function decodeAudioFile(file) {
  if (!file) return;
  clearMessage();
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) throw new Error("当前浏览器不支持 Web Audio API。");
    if (!appState.audioContext) appState.audioContext = new AudioContextClass();
    const buffer = await appState.audioContext.decodeAudioData(await file.arrayBuffer());
    const samplingRate = buffer.sampleRate;
    const maxLength = Math.min(buffer.length, Math.floor(30 * samplingRate));
    const channels = Array.from({ length: buffer.numberOfChannels }, (_, index) => buffer.getChannelData(index));
    const samples = Array.from({ length: maxLength }, (_, index) =>
      channels.reduce((sum, channel) => sum + channel[index], 0) / channels.length);
    appState.uploadedSamples = samples;
    appState.uploadedRate = samplingRate;
    if (appState.audioObjectUrl) URL.revokeObjectURL(appState.audioObjectUrl);
    appState.audioObjectUrl = URL.createObjectURL(file);
    $("#audio-player").src = appState.audioObjectUrl;
    $("#audio-player").classList.remove("hidden");
    if (buffer.length > maxLength) showMessage("音频超过 30 秒，仅分析前 30 秒。");
    drawUploadedAudio();
  } catch (error) {
    showMessage(`音频解码失败：${error.message}`, "error");
  }
}

async function drawUploadedAudio() {
  if (!appState.uploadedSamples || !appState.uploadedSamples.length) return;
  try {
    clearMessage();
    const samples = appState.uploadedSamples;
    const samplingRate = appState.uploadedRate;
    const frameLength = Math.max(2, Math.round(samplingRate * Number(fieldValue("voice-frame")) / 1000));
    const hopLength = Math.max(1, Math.round(samplingRate * Number(fieldValue("voice-hop")) / 1000));
    const fftPoints = 2 ** Math.ceil(Math.log2(frameLength));
    const totalFrames = Math.ceil(samples.length / hopLength);
    const displayStep = Math.max(1, Math.ceil(totalFrames / 300));
    const times = [];
    const magnitudes = [];
    for (let frameIndex = 0; frameIndex < totalFrames; frameIndex += displayStep) {
      const start = frameIndex * hopLength;
      const valid = Math.min(frameLength, samples.length - start);
      const frame = new Float64Array(frameLength);
      frame.set(samples.slice(start, start + valid));
      magnitudes.push(Array.from(fftReal(frame, fftPoints, "汉宁窗").magnitude));
      times.push((start + Math.max(0, valid - 1) / 2) / samplingRate);
    }
    const frequencies = frequencyAxis(fftPoints, samplingRate);
    const displayTime = linspace(0, (samples.length - 1) / samplingRate, Math.min(1200, samples.length));
    const displaySamples = displayTime.map((t) => samples[Math.min(samples.length - 1, Math.round(t * samplingRate))]);
    const { layout, frames } = stftLayout(
      displayTime,
      times,
      frequencies,
      times,
      frameLength,
      samplingRate,
    );
    const duration = samples.length / samplingRate;
    const chartLayout = {
      ...layout,
      xaxis2: { ...layout.xaxis2, range: [times[0], times[times.length - 1]] },
    };
    await drawPlot([
      { type: "scatter", mode: "lines", x: displayTime, y: displaySamples, name: "录音信号", line: { color: "#1769aa", width: 1 }, xaxis: "x", yaxis: "y" },
      { type: "heatmap", x: times, y: frequencies, z: heatmapData(times, frequencies, magnitudes), colorscale: "Magma", colorbar: { title: "幅度 (dB)" }, name: "语音 STFT", xaxis: "x2", yaxis: "y2" },
    ], chartLayout, frames);
    setNote(`采样率 ${samplingRate} Hz · 音频时长 ${formatNumber(duration, 2)} s · 显示 ${times.length} 个分析帧。音频文件和计算结果不会上传。`);
  } catch (error) {
    showMessage(`音频分析失败：${error.message}`, "error");
  }
}

function renderVoice() {
  fieldPanel(
    `<div class="field"><span>本机麦克风</span><div class="button-row">
      <button id="live-start" class="action-button">开始实时分析</button>
      <button id="live-stop" class="action-button danger" disabled>停止</button>
    </div></div>
    <label class="field"><span>导入音频（浏览器可解码的音频格式）</span><input id="audio-file" type="file" accept="audio/*,.wav"></label>
    ${selectField("voice-frame", "分析帧长 (ms)", [16, 20, 25, 32, 40], 25)}
    ${selectField("voice-hop", "帧移 (ms)", [5, 10, 15, 20], 10)}
    <div class="field"><span>录音播放</span><audio id="audio-player" class="audio-player hidden" controls></audio></div>`,
  );
  $("#live-start").addEventListener("click", startLiveMicrophone);
  $("#live-stop").addEventListener("click", stopLiveButton);
  $("#audio-file").addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (file) decodeAudioFile(file);
  });
  $("#voice-frame").addEventListener("change", drawUploadedAudio);
  $("#voice-hop").addEventListener("change", drawUploadedAudio);
  drawPlot([], layoutBase({ height: 490 })).catch((error) => showMessage(error.message, "error"));
  setNote("允许浏览器使用麦克风后可查看实时频谱；也可导入 WAV 或其他浏览器支持的音频文件进行分帧分析。");
}

function navigate(page) {
  if (appState.page === "voice" && page !== "voice") stopLiveMicrophone();
  appState.page = page;
  document.querySelectorAll(".nav-item").forEach((button) =>
    button.classList.toggle("active", button.dataset.page === page));
  const [title, description] = PAGE_META[page];
  $("#page-header").innerHTML = `<h1>${esc(title)}</h1><p>${esc(description)}</p>`;
  if (page === "overview") renderOverview();
  else if (page === "time-frequency") renderTimeFrequency();
  else if (page === "fourier") renderFourier();
  else if (page === "stft") renderStft();
  else if (page === "sampling") renderSampling();
  else if (page === "phase") renderPhase();
  else if (page === "filter") renderFilter();
  else if (page === "voice") renderVoice();
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".nav-item").forEach((button) =>
    button.addEventListener("click", () => navigate(button.dataset.page)));
  navigate("overview");
});
