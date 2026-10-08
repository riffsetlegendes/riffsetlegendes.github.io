"""Petit groove rock original, synthétisé (aucun échantillon, aucun droit tiers).
make(path, dur, seed) écrit un WAV stéréo 44,1 kHz."""
import math, random, wave
import numpy as np

SR = 44100
PROGS = [[0, 0, 3, 5], [0, 5, 3, 0], [0, -2, -5, -2], [0, 3, 5, 7], [0, 0, 5, 3]]  # demi-tons depuis la tonique
KEYS = [40, 42, 43, 45, 38]  # E2, F#2, G2, A2, D2 (MIDI)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.003, d=0.25, s=0.0, r=0.0):
    t = np.arange(n) / SR
    e = np.exp(-t / max(d, 1e-3)) * (1 - s) + s
    att = int(a * SR)
    if att:
        e[:att] *= np.linspace(0, 1, att)
    return e


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune)) % 1) - 1


def make(path, dur=15.0, seed=0):
    rng = random.Random(seed)
    bpm = rng.choice([112, 118, 124, 128])
    key = rng.choice(KEYS)
    prog = rng.choice(PROGS)
    beat = 60 / bpm
    n = int(dur * SR)
    L = np.zeros(n); R = np.zeros(n)
    noise = np.random.default_rng(seed).uniform(-1, 1, n)

    def add(sig, start, pan=0.0, gain=1.0):
        i = int(start * SR)
        if i >= n:
            return
        sig = sig[: n - i] * gain
        L[i:i + len(sig)] += sig * (1 - max(0, pan))
        R[i:i + len(sig)] += sig * (1 + min(0, pan))

    steps = int(dur / (beat / 2))
    end_hit = dur - 3.2
    for k in range(steps):
        t = k * beat / 2
        if t > end_hit:
            break
        bar = int(t // (beat * 4))
        root = key + prog[bar % 4]
        # batterie
        if k % 4 == 0:  # grosse caisse sur 1 et 3
            m = int(0.25 * SR); tt = np.arange(m) / SR
            add(np.sin(2 * math.pi * (55 + 90 * np.exp(-tt * 30)) * tt) * env(m, d=0.12), t, gain=0.9)
        if k % 4 == 2:  # caisse claire sur 2 et 4
            m = int(0.2 * SR)
            add((noise[:m] * 0.7 + np.sin(2 * math.pi * 190 * np.arange(m) / SR) * 0.4) * env(m, d=0.07), t, gain=0.55)
        if k % 8 == 7 and rng.random() < 0.5:  # petite relance
            add(np.sin(2 * math.pi * 55 * np.arange(int(0.2 * SR)) / SR) * env(int(0.2 * SR), d=0.1), t + beat / 4, gain=0.6)
        hh = int(0.05 * SR)
        hat = np.diff(noise[1000:1000 + hh + 1]) * env(hh, d=0.015)
        add(hat, t, pan=0.3, gain=0.18 if k % 2 else 0.12)
        # basse
        m = int(beat / 2 * SR * 0.9)
        b = np.sin(2 * math.pi * hz(root - 12) * np.arange(m) / SR) + 0.3 * saw(hz(root - 12), m)
        add(np.tanh(b * 1.5) * env(m, d=0.25, s=0.4), t, gain=0.35)
        # guitare : quinte saturée, étouffée en croches
        m = int(beat / 2 * SR * 0.85)
        g = sum(saw(hz(root + iv), m, dt) for iv, dt in ((12, 0), (19, 0.002), (24, -0.002)))
        g = np.tanh(g * 4) * env(m, d=0.09 if k % 8 != 0 else 0.3, s=0.15)
        add(g, t, pan=-0.35, gain=0.13)
        add(g, t + 0.012, pan=0.35, gain=0.11)
    # accord final qui sonne
    m = n - int(end_hit * SR)
    g = sum(saw(hz(key + iv), m, dt) for iv, dt in ((12, 0), (19, 0.003), (24, -0.003), (31, 0.001)))
    add(np.tanh(g * 4) * env(m, d=1.4, s=0.0), end_hit, gain=0.2)
    mm = int(0.4 * SR)
    add(np.sin(2 * math.pi * 55 * np.arange(mm) / SR) * env(mm, d=0.2), end_hit, gain=0.9)
    add(noise[:mm] * env(mm, d=0.6), end_hit, gain=0.35)
    mix = np.stack([L, R], 1)
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    mix /= max(1e-6, np.abs(mix).max()) / 0.89
    data = (mix * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data)
    return path
