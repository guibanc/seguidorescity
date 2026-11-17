// =====================================================================
//  SONS: tudo sintetizado aqui (Web Audio), sem arquivos de áudio.
//  Sons.tocar('nome')  ·  Sons.ambiente(lugar, noite)  ·  Sons.alternar()
//  Botão 🔊: tudo ligado → 🔉 só efeitos (sem música) → 🔇 mudo
// =====================================================================
(function () {
'use strict';
let ac = null, mestre = null, busMusica = null, ruidoBuf = null;
const ler = () => { try { return localStorage.getItem('vila_som') || 'tudo'; } catch { return 'tudo'; } };
let estado = ler();                                   // 'tudo' | 'efeitos' | 'mudo'

function iniciar() {
  if (ac) { if (ac.state === 'suspended') ac.resume(); return ac; }
  const C = window.AudioContext || window.webkitAudioContext; if (!C) return null;
  ac = new C();
  mestre = ac.createGain(); mestre.gain.value = estado === 'mudo' ? 0 : 0.55;
  const comp = ac.createDynamicsCompressor(); mestre.connect(comp); comp.connect(ac.destination);
  busMusica = ac.createGain(); busMusica.gain.value = estado === 'tudo' ? 1 : 0; busMusica.connect(mestre);
  ruidoBuf = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
  const d = ruidoBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  return ac;
}
// o navegador só deixa tocar depois de um toque/tecla
const destrava = () => { iniciar(); };
addEventListener('pointerdown', destrava, { passive: true }); addEventListener('keydown', destrava);

function tom(f, dur, o = {}) {
  if (!ac || estado === 'mudo') return;
  const t = ac.currentTime + (o.atraso || 0), osc = ac.createOscillator(), g = ac.createGain();
  osc.type = o.tipo || 'square'; osc.frequency.setValueAtTime(f, t);
  if (o.ate) osc.frequency.exponentialRampToValueAtTime(Math.max(20, o.ate), t + dur);
  const v = (o.vol || 0.15);
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + Math.min(0.012, dur / 4));
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  osc.connect(g); g.connect(o.bus || mestre); osc.start(t); osc.stop(t + dur + 0.02);
}
function ruido(dur, o = {}) {
  if (!ac || estado === 'mudo') return;
  const t = ac.currentTime + (o.atraso || 0), s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
  s.buffer = ruidoBuf; s.playbackRate.value = o.taxa || 1;
  f.type = o.filtro || 'lowpass'; f.frequency.value = o.freq || 1000; f.Q.value = o.q || 1;
  const v = o.vol || 0.2;
  g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(f); f.connect(g); g.connect(o.bus || mestre); s.start(t, Math.random() * 0.5); s.stop(t + dur + 0.02);
}
const var_ = (x, p = 0.08) => x * (1 + (Math.random() * 2 - 1) * p);    // cada batida soa um pouco diferente

const EFEITOS = {
  madeira: () => { ruido(0.07, { filtro: 'bandpass', freq: var_(700), q: 2, vol: 0.35 }); tom(var_(170), 0.09, { tipo: 'triangle', ate: 90, vol: 0.25 }); },
  pedra:   () => { tom(var_(1900), 0.035, { ate: 1300, vol: 0.07 }); ruido(0.06, { filtro: 'highpass', freq: 2200, vol: 0.22 }); tom(var_(320), 0.05, { tipo: 'triangle', vol: 0.12 }); },
  terra:   () => { ruido(0.09, { freq: var_(450), vol: 0.35 }); },
  folha:   () => { ruido(0.12, { filtro: 'bandpass', freq: var_(3200), q: 0.8, vol: 0.18 }); },
  quebrou: () => { ruido(0.18, { freq: 1400, vol: 0.35 }); tom(320, 0.16, { tipo: 'triangle', ate: 70, vol: 0.22 }); },
  pegar:   () => { tom(660, 0.05, { vol: 0.07 }); tom(990, 0.09, { vol: 0.07, atraso: 0.05 }); },
  moeda:   () => { tom(988, 0.07, { vol: 0.09 }); tom(1319, 0.22, { vol: 0.09, atraso: 0.07 }); },
  criar:   () => { ruido(0.05, { filtro: 'bandpass', freq: 900, vol: 0.2 }); tom(523, 0.07, { tipo: 'triangle', vol: 0.15, atraso: 0.05 }); tom(784, 0.14, { tipo: 'triangle', vol: 0.15, atraso: 0.12 }); },
  rankup:  () => { [523, 659, 784, 1047].forEach((f, i) => tom(f, 0.16, { vol: 0.09, atraso: i * 0.1 })); [523, 659, 784].forEach(f => tom(f * 2, 0.6, { tipo: 'triangle', vol: 0.06, atraso: 0.42 })); },
  dano:    () => { tom(240, 0.16, { tipo: 'sawtooth', ate: 110, vol: 0.12 }); ruido(0.08, { freq: 800, vol: 0.15 }); },
  golpe:   () => { ruido(0.05, { freq: 1600, vol: 0.3 }); tom(var_(150), 0.07, { tipo: 'triangle', ate: 80, vol: 0.2 }); },
  morre:   () => { tom(420, 0.3, { tipo: 'square', ate: 90, vol: 0.08 }); ruido(0.2, { freq: 900, vol: 0.18, atraso: 0.05 }); },
  comer:   () => { for (let i = 0; i < 3; i++) ruido(0.06, { filtro: 'bandpass', freq: var_(1200, 0.2), q: 3, vol: 0.3, atraso: i * 0.11 }); },
  passo:   () => { ruido(0.04, { freq: var_(380, 0.2), vol: 0.09 }); },
  passo_pedra: () => { ruido(0.035, { filtro: 'bandpass', freq: var_(1500, 0.2), q: 2, vol: 0.08 }); },
  portal:  () => { tom(180, 0.7, { tipo: 'sine', ate: 900, vol: 0.14 }); tom(270, 0.7, { tipo: 'triangle', ate: 1350, vol: 0.06, atraso: 0.05 }); ruido(0.6, { filtro: 'bandpass', freq: 2500, vol: 0.06 }); },
  descer:  () => { tom(330, 0.22, { tipo: 'triangle', ate: 140, vol: 0.18 }); ruido(0.2, { freq: 500, vol: 0.2 }); },
  subir:   () => { tom(150, 0.22, { tipo: 'triangle', ate: 330, vol: 0.18 }); },
  colocar: () => { tom(var_(210), 0.06, { tipo: 'square', vol: 0.06 }); ruido(0.06, { freq: 900, vol: 0.28 }); },
  erro:    () => { tom(170, 0.12, { vol: 0.07 }); tom(130, 0.16, { vol: 0.07, atraso: 0.1 }); },
  clique:  () => { tom(1300, 0.025, { vol: 0.05 }); },
  abrir:   () => { tom(500, 0.05, { tipo: 'triangle', vol: 0.1 }); tom(750, 0.07, { tipo: 'triangle', vol: 0.1, atraso: 0.04 }); },
  regenera:() => { [392, 523, 659].forEach((f, i) => tom(f, 0.3, { tipo: 'sine', vol: 0.08, atraso: i * 0.12 })); },
};
let ultimoPasso = 0;
function tocar(nome) {
  if (estado === 'mudo' || !iniciar() || ac.state !== 'running') return;
  if (nome.startsWith('passo')) { const t = performance.now(); if (t - ultimoPasso < 300) return; ultimoPasso = t; }
  const f = EFEITOS[nome]; if (f) try { f(); } catch {}
}

// ---------------------------------------------------------------------
// AMBIENTE: passarinhos de dia, grilos de noite, gotas na mina,
// e uma música calminha (escala pentatônica) que muda com o lugar
// ---------------------------------------------------------------------
let lugar = 'cidade', noite = false, timerAmb = null, timerMus = null, passoMus = 0;
const ESCALAS = { dia: [261.6, 293.7, 329.6, 392, 440, 523.3, 587.3, 659.3], mina: [110, 130.8, 146.8, 164.8, 196, 220, 261.6, 293.7], noite: [220, 246.9, 261.6, 329.6, 349.2, 440, 493.9, 523.3] };
function ambiente(l, n) { lugar = l; noite = !!n; if (!timerAmb) { timerAmb = setTimeout(somAmbiente, 2500); timerMus = setInterval(compasso, 450); } }
function somAmbiente() {
  timerAmb = setTimeout(somAmbiente, 1800 + Math.random() * 4500);
  if (!ac || ac.state !== 'running' || estado === 'mudo' || document.hidden) return;
  if (lugar === 'mina') {                                  // gota com eco
    const f = 900 + Math.random() * 700; tom(f, 0.09, { tipo: 'sine', ate: f / 2, vol: 0.05 }); tom(f, 0.09, { tipo: 'sine', ate: f / 2, vol: 0.02, atraso: 0.25 });
  } else if (noite) {                                      // grilos
    const f = 4200 + Math.random() * 600; for (let i = 0; i < 6; i++) tom(f, 0.025, { tipo: 'sine', vol: 0.012, atraso: i * 0.06 });
  } else {                                                 // passarinho
    const b = 2200 + Math.random() * 1400, n = 2 + Math.floor(Math.random() * 3);
    for (let i = 0; i < n; i++) tom(b * (1 + Math.random() * 0.2), 0.07, { tipo: 'sine', ate: b * 1.4, vol: 0.022, atraso: i * 0.11 });
  }
}
function compasso() {
  if (!ac || ac.state !== 'running' || estado !== 'tudo' || document.hidden) return;
  passoMus++;
  const esc = ESCALAS[lugar === 'mina' ? 'mina' : noite ? 'noite' : 'dia'], lento = lugar === 'mina' || noite;
  if (passoMus % 8 === 0) {                                // acorde no começo do compasso
    const raiz = esc[[0, 3, 4, 2][(passoMus / 8) % 4 | 0]] / 2;
    [1, 1.25, 1.5].forEach(m => tom(raiz * m, 3.2, { tipo: 'sine', vol: 0.018, bus: busMusica }));
  }
  if (Math.random() < (lento ? 0.25 : 0.4)) tom(esc[Math.floor(Math.random() * esc.length)], lento ? 1.1 : 0.6, { tipo: 'triangle', vol: 0.03, bus: busMusica });
}

function alternar() {
  estado = estado === 'tudo' ? 'efeitos' : estado === 'efeitos' ? 'mudo' : 'tudo';
  try { localStorage.setItem('vila_som', estado); } catch {}
  iniciar();
  if (ac) { mestre.gain.value = estado === 'mudo' ? 0 : 0.55; busMusica.gain.value = estado === 'tudo' ? 1 : 0; }
  if (estado !== 'mudo') tocar('clique');
  desenharBotao(); return estado;
}
function desenharBotao() {
  const b = document.querySelector('#btnSom'); if (!b) return;
  b.textContent = { tudo: '🔊', efeitos: '🔉', mudo: '🔇' }[estado];
  b.title = { tudo: 'Som e música ligados', efeitos: 'Só efeitos (sem música)', mudo: 'Sem som' }[estado];
}
document.addEventListener('DOMContentLoaded', () => { const b = document.querySelector('#btnSom'); if (b) { b.onclick = alternar; desenharBotao(); } });
if (document.readyState !== 'loading') { const b = document.querySelector('#btnSom'); if (b) { b.onclick = alternar; desenharBotao(); } }

window.Sons = { tocar, ambiente, alternar, estado: () => estado };
})();
