"""Sound for the studio videos: the AI narrator, original music, sound effects and the final mix.

Narrator: Kokoro 82M (Apache 2.0), run locally through kokoro-onnx with the voice am_michael (US male, since 18 November 2026; af_heart before). Its two model files
come from the kokoro-onnx GitHub release and are kept in ~/.cache/fd-studio/voice (checked by SHA-256).
Music and sound effects are generated here from code, so they are original and free of any licence or claim.
The mix ducks the music under the voice and is normalised to -14 LUFS with ffmpeg's loudnorm.
"""
import hashlib, json, math, os, re, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

CACHE = os.path.expanduser(os.environ.get("FD_STUDIO_CACHE", "~/.cache/fd-studio"))
VOICE_DIR = os.path.join(CACHE, "voice")
RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = {
    "kokoro-v1.0.onnx": "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
    "voices-v1.0.bin": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
}
VOICE, SPEED = "am_michael", 1.06  # US male, since 18 November 2026 (Talha: a man's voice); af_heart before
SR = 48000


# ---------------------------------------------------------------- setup
def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def voice_status(download=False):
    """(True, "") when the narrator can run; else (False, the reason). download=True fetches missing model files."""
    try:
        import kokoro_onnx  # noqa: F401
    except Exception as e:
        return False, "kokoro-onnx is not installed (%s); run python3 tools/studio/doctor.py --setup" % e
    os.makedirs(VOICE_DIR, exist_ok=True)
    for name, sha in MODEL_FILES.items():
        p = os.path.join(VOICE_DIR, name)
        ok = os.path.exists(p) and os.path.exists(p + ".ok")
        if not ok and download:
            subprocess.run(["curl", "-sSL", "--fail", "--retry", "2", "--max-time", "900", "-o", p + ".part", RELEASE + name], check=False)
            if os.path.exists(p + ".part") and _sha(p + ".part") == sha:
                os.replace(p + ".part", p)
                open(p + ".ok", "w").write(sha)
                ok = True
            elif os.path.exists(p + ".part"):
                os.remove(p + ".part")
        if not ok:
            return False, "voice model file %s is missing; run python3 tools/studio/doctor.py --setup" % name
    return True, ""


_KOKORO = None


def _kokoro():
    global _KOKORO
    if _KOKORO is None:
        from kokoro_onnx import Kokoro
        _KOKORO = Kokoro(os.path.join(VOICE_DIR, "kokoro-v1.0.onnx"), os.path.join(VOICE_DIR, "voices-v1.0.bin"))
    return _KOKORO


# ---------------------------------------------------------------- words for the narrator
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
ORD = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def words(n):
    n = int(n)
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else "-" + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " and " + words(n % 100))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div:
            rest = n % div
            return words(n // div) + " " + name + ("" if rest == 0 else (" and " if rest < 100 else " ") + words(rest))
    return str(n)


def ordinal(n):
    w = words(n)
    last = w.split("-")[-1].split(" ")[-1]
    if last in ORD:
        new = ORD[last]
    elif last.endswith("y"):
        new = last[:-1] + "ieth"
    else:
        new = last + "th"
    return w[: len(w) - len(last)] + new


def year(n):
    n = int(n)
    if 2000 <= n <= 2009:
        return "two thousand" + ("" if n == 2000 else " and " + ONES[n - 2000])
    hi, lo = divmod(n, 100)
    return words(hi) + " " + ("hundred" if lo == 0 else ("oh " + ONES[lo] if lo < 10 else words(lo)))


SPOKEN_AS_WORDS = {"FIRE", "IRIS", "NASA", "SAFE", "SAFEs", "CALL", "ACCA", "ICAP"}


def speakable(text):
    """A plain spoken version of approved words, used when a piece gives no `say` text for a line."""
    s = " " + str(text) + " "
    s = s.replace("\u2019", "'").replace("&", " and ")
    s = re.sub(r"\b(\d{3})-(\d{3})-(\d{4})\b", lambda m: ", ".join(" ".join(ONES[int(c)] for c in g) for g in m.groups()), s)
    s = re.sub(r"\b(\d{4})-(NEC|MISC|K|INT|DIV)\b", lambda m: "%s %s" % (_formno(m.group(1)), " ".join(m.group(2))), s)
    s = re.sub(r"\b(\d{3,4})\(([a-z])\)", lambda m: "%s %s" % (_formno(m.group(1)), m.group(2)), s)
    s = re.sub(r"(?<!\$)\b(\d{3,4})([A-JL-Z])\b", lambda m: "%s %s" % (_formno(m.group(1)), m.group(2)) if m.group(2) not in "MB" else m.group(0), s)
    s = re.sub(r"\b(1099|1120|5472|7004|1065|8832|1040)s\b", lambda m: _formno(m.group(1)) + "s", s)
    s = re.sub(r"\bForm (\d{4})\b", lambda m: "Form " + _formno(m.group(1)), s)
    s = re.sub(r"\b(\d{1,2}) (%s)( \d{4})?" % "|".join(MONTHS), lambda m: "%s %s%s" % (m.group(2), ordinal(m.group(1)), (", " + year(m.group(3).strip())) if m.group(3) else ""), s)
    s = re.sub(r"\$(\d[\d,]*)(\.\d+)?(?:\s?(million|billion|M|K)\b)?\+?", _money, s)
    s = re.sub(r"(\d[\d,]*(?:\.\d+)?)%", lambda m: _num(m.group(1)) + " percent", s)
    s = re.sub(r"\b(1[0-9]|20)(\d{2})\b(?![,.]\d)", lambda m: year(m.group(0)) if 1900 <= int(m.group(0)) <= 2099 else m.group(0), s)
    s = re.sub(r"\b(\d{3,4})\b", lambda m: _formno(m.group(1)) if m.group(1) in ("1099", "1120", "5472", "7004", "1065", "8832") else m.group(1), s)
    s = re.sub(r"(\d[\d,]*(?:\.\d+)?)\+", lambda m: "more than " + _num(m.group(1)), s)
    s = re.sub(r"\d[\d,]*(?:\.\d+)?", lambda m: _num(m.group(0)), s)
    s = re.sub(r"\b([ap])\.m\.", lambda m: m.group(1).upper() + " M", s)
    s = re.sub(r"\b([A-Z]{2,5})(s?)\b", lambda m: m.group(0) if m.group(0) in SPOKEN_AS_WORDS else " ".join(m.group(1)) + m.group(2), s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _formno(d):
    d = str(d)
    if len(d) == 3:
        a, b = int(d[0]), int(d[1:])
        return ONES[a] + " " + ("hundred" if b == 0 else ("oh " + ONES[b] if b < 10 else words(b)))
    if len(d) == 4:
        a, b = int(d[:2]), int(d[2:])
        return words(a) + " " + ("hundred" if b == 0 else ("oh " + ONES[b] if b < 10 else words(b)))
    return words(int(d))


def _num(x):
    x = x.replace(",", "")
    if "." in x:
        a, b = x.split(".", 1)
        return words(int(a or 0)) + " point " + " ".join(ONES[int(c)] for c in b)
    return words(int(x))


def _money(m):
    whole, frac, unit = m.group(1).replace(",", ""), m.group(2), m.group(3)
    unitw = {"M": "million", "K": "thousand"}.get(unit, unit)
    if unitw:
        base = _num(whole + (frac or "")) + " " + unitw
    elif frac and len(frac) == 3 and int(whole) == 0:
        return "%s cents" % words(int(frac[1:]))
    elif frac and len(frac) > 3:
        base = _num(whole + frac)
    else:
        base = words(int(whole))
        if frac and int(frac[1:]):
            return base + " dollars and " + words(int(frac[1:])) + " cents"
    return base + " dollars"


# ---------------------------------------------------------------- narration and word timings
def _syl(w):
    w = w.lower().strip(".,?!;:'\u2019\"")
    if not w:
        return 0
    if len(w) == 1:
        return 1
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def _gaps(x, sr, thr_ratio=0.03, min_gap=0.085):
    hop = int(sr * 0.01)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x), hop)])
    silent = env < thr_ratio * env.max()
    out, i = [], 0
    while i < len(silent):
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]:
                j += 1
            if i > 0 and j < len(silent) and (j - i) * 0.01 >= min_gap:
                out.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return out


def narrate(text, out_wav):
    """Speaks text into out_wav (48 kHz mono). Returns its length and the estimated time of each word."""
    samples, sr = _kokoro().create(text, voice=VOICE, speed=SPEED, lang="en-us")
    x = np.asarray(samples, np.float32)
    idx = np.where(np.abs(x) > 0.01)[0]
    if len(idx):
        x = x[max(0, idx[0] - int(0.02 * sr)): idx[-1] + int(0.06 * sr)]
    dur = len(x) / sr
    ws = text.split()
    sy = [_syl(w) for w in ws]
    cum = np.cumsum([0] + sy) / max(1, sum(sy))
    cand = [i for i, w in enumerate(ws[:-1]) if w[-1] in ",.?;:!"]
    g = _gaps(x, sr)
    exp_t = {i: cum[i + 1] * dur for i in cand}
    pairs = sorted(((abs((a + b) / 2 - exp_t[i]), i, (a, b)) for i in cand for (a, b) in g), key=lambda z: z[0])
    used_i, used_g, anchors = set(), set(), {}
    for dist, i, gg in pairs:
        if i in used_i or gg in used_g or dist > 1.2:
            continue
        used_i.add(i); used_g.add(gg); anchors[i] = gg
    out, start_w, t_start = [], 0, 0.0
    for i, (ga, gb) in sorted(anchors.items()) + [(len(ws) - 1, (dur, dur))]:
        idxs = list(range(start_w, i + 1))
        tot = sum(sy[j] for j in idxs) or 1
        t = t_start
        for j in idxs:
            d = (ga - t_start) * sy[j] / tot
            out.append({"w": ws[j], "t0": round(t, 3), "t1": round(t + d, 3)})
            t += d
        start_w, t_start = i + 1, gb
    y = resample_poly(x, 2, 1).astype(np.float32)  # 24 kHz to 48 kHz
    wavfile.write(out_wav, SR, y)
    return {"dur": round(dur, 3), "words": out}


# ---------------------------------------------------------------- music
PRESETS = [
    dict(bpm=96, prog=[[50, 53, 57, 62], [46, 50, 53, 58], [41, 45, 48, 53], [48, 52, 55, 60]], roots=[38, 34, 41, 36], pat=(0, 1, 2, 3, 2, 1, 2, 3), bright=1.0),
    dict(bpm=104, prog=[[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 60], [55, 59, 62, 67]], roots=[45, 41, 48, 43], pat=(0, 2, 1, 3, 0, 2, 3, 1), bright=1.25),
    dict(bpm=100, prog=[[52, 55, 59, 64], [48, 52, 55, 60], [43, 47, 50, 55], [50, 54, 57, 62]], roots=[40, 36, 43, 38], pat=(0, 1, 3, 2, 0, 1, 3, 2), bright=1.1),
    dict(bpm=92, prog=[[55, 58, 62, 67], [51, 55, 58, 63], [46, 50, 53, 58], [53, 57, 60, 65]], roots=[43, 39, 46, 41], pat=(0, 2, 3, 2, 1, 2, 3, 2), bright=0.95),
]
MSR = 44100


def music(out_wav, seconds, seed=7, preset=0, intro_bars=1, outro_bars=1):
    """An original music bed of at least `seconds`: pads, then plucks and bass, drums in the middle, a soft ending."""
    P = PRESETS[preset % len(PRESETS)]
    rng = np.random.default_rng(seed)
    BEAT = 60 / P["bpm"]; BAR = 4 * BEAT
    nbars = int(math.ceil((seconds + 1.0) / BAR))
    N = int(MSR * (nbars * BAR + 4))
    lp = lambda x, f, o=4: sosfilt(butter(o, f, "low", fs=MSR, output="sos"), x)
    hp = lambda x, f, o=2: sosfilt(butter(o, f, "high", fs=MSR, output="sos"), x)
    bp = lambda x, lo, hi, o=2: sosfilt(butter(o, [lo, hi], "band", fs=MSR, output="sos"), x)
    midi = lambda n: 440 * 2 ** ((n - 69) / 12)

    def add(buf, start, sig):
        sig = sig.copy(); fo = min(len(sig), int(MSR * 0.035)); sig[-fo:] *= np.linspace(1, 0, fo)
        i = int(start * MSR); j = min(len(buf), i + len(sig))
        if j > i:
            buf[i:j] += sig[: j - i]

    def saw(f, n, c):
        ff = f * 2 ** (c / 1200); ph = (np.arange(n) * ff / MSR + rng.random()) % 1.0
        return 2 * ph - 1

    padL, padR, pl, plR, bass, kick, clap, hats = (np.zeros(N) for _ in range(8))
    drums_from, drums_to = min(intro_bars + 1, nbars), max(nbars - outro_bars - 1, 0)
    for b in range(nbars):
        t0 = b * BAR; ch = P["prog"][b % 4]; L = int(MSR * (BAR + 1.6)); t = np.arange(L) / MSR
        env = np.minimum(t / 0.7, 1.0) * np.where(t < BAR, 1.0, np.exp(-(t - BAR) / 0.5))
        sL, sR = np.zeros(L), np.zeros(L)
        for n in ch:
            f = midi(n + 12); sL += saw(f, L, -9) + saw(f, L, 4); sR += saw(f, L, 9) + saw(f, L, -4)
        add(padL, t0, lp(sL, 1500 * P["bright"]) * env * 0.05); add(padR, t0, lp(sR, 1500 * P["bright"]) * env * 0.05)
        if intro_bars <= b < nbars - outro_bars:
            tones = [x + 24 for x in ch]
            for k, p in enumerate(P["pat"]):
                f = midi(tones[p % 4]); n = int(MSR * 0.9); tt = np.arange(n) / MSR
                s = (np.sin(2 * np.pi * f * tt) + 0.45 * np.sin(4 * np.pi * f * tt) + 0.18 * P["bright"] * np.sin(6 * np.pi * f * tt))
                s *= np.minimum(tt / 0.003, 1) * np.exp(-tt / 0.22) * 0.06 * (1.0 if k % 2 == 0 else 0.75)
                pan = 0.35 if k % 2 else -0.35
                add(pl, t0 + k * BEAT / 2, s * (1 - pan)); add(plR, t0 + k * BEAT / 2, s * (1 + pan))
            for beat in (0, 2):
                f = midi(P["roots"][b % 4]); n = int(MSR * BEAT * 2); tt = np.arange(n) / MSR
                add(bass, t0 + beat * BEAT, (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * np.minimum(tt / 0.01, 1) * np.exp(-tt / 1.2) * 0.22)
        if drums_from <= b < drums_to:
            for beat in (0, 2):
                n = int(MSR * 0.5); tt = np.arange(n) / MSR; fr = 45 + 80 * np.exp(-tt / 0.045); ph = 2 * np.pi * np.cumsum(fr) / MSR
                s = np.sin(ph) * np.exp(-tt / 0.22) * 0.55; s[:60] += rng.normal(0, 0.15, 60); add(kick, t0 + beat * BEAT, s)
            for beat in (1, 3):
                n = int(MSR * 0.35); s = np.zeros(n)
                for dd in (0, 0.011, 0.022):
                    i = int(dd * MSR); m = n - i; s[i:] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / MSR / 0.06)
                add(clap, t0 + beat * BEAT, bp(s, 900, 5000) * 0.12)
            for k in range(8):
                n = int(MSR * 0.08); tt = np.arange(n) / MSR
                add(hats, t0 + k * BEAT / 2, hp(rng.normal(0, 1, n), 7000) * np.exp(-tt / 0.025) * (0.05 if k % 2 else 0.03))
    pump = np.ones(N)
    for b in range(drums_from, drums_to):
        for beat in (0, 2):
            i = int((b * BAR + beat * BEAT) * MSR); n = int(MSR * 0.45); tt = np.arange(n) / MSR; j = min(N, i + n)
            pump[i:j] *= (1 - 0.45 * np.exp(-tt / 0.16))[: j - i]
    padL *= pump; padR *= pump
    irn = int(MSR * 2.6); ti = np.arange(irn) / MSR
    irL = lp(rng.normal(0, 1, irn), 6000) * np.exp(-ti / 0.55); irR = lp(rng.normal(0, 1, irn), 6000) * np.exp(-ti / 0.55)
    irL /= np.sqrt(np.sum(irL ** 2)); irR /= np.sqrt(np.sum(irR ** 2))
    revL = fftconvolve(padL * 0.5 + pl * 0.6 + clap * 0.6, irL)[:N] * 0.35
    revR = fftconvolve(padR * 0.5 + plR * 0.6 + clap * 0.6, irR)[:N] * 0.35
    d = int(MSR * BEAT * 0.75); dl, dr = np.zeros(N), np.zeros(N); dl[d:] += plR[:-d] * 0.35; dr[2 * d:] += pl[: -2 * d] * 0.25
    Lc = padL + pl + dl + bass + kick + clap + hats + revL
    Rc = padR + plR + dr + bass + kick + clap + hats * 0.8 + revR
    mix = hp(np.stack([Lc, Rc], 1).T, 28).T
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    mix /= np.max(np.abs(mix)) / 0.89
    end = int(MSR * (seconds + 0.5))
    mix = mix[:end]
    fo = int(MSR * 2.5); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    y = resample_poly(mix, 160, 147, axis=0).astype(np.float32)  # 44.1 kHz to 48 kHz
    wavfile.write(out_wav, SR, y)
    return out_wav


# ---------------------------------------------------------------- sound effects
def sfx_bank():
    d = os.path.join(CACHE, "sfx")
    names = ["whoosh", "impact", "tick", "riser", "chime", "boom"]
    if all(os.path.exists(os.path.join(d, n + ".wav")) for n in names):
        return {n: os.path.join(d, n + ".wav") for n in names}
    os.makedirs(d, exist_ok=True)
    rng = np.random.default_rng(7)
    bp = lambda x, lo, hi, o=2: sosfilt(butter(o, [lo, min(hi, SR / 2 - 100)], "band", fs=SR, output="sos"), x)
    lp = lambda x, f, o=4: sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
    hp = lambda x, f, o=2: sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)

    def save(n, x):
        x = x / np.max(np.abs(x)) * 0.9
        if x.ndim == 1:
            x = np.stack([x, x], 1)
        wavfile.write(os.path.join(d, n + ".wav"), SR, x.astype(np.float32))

    n = int(SR * 0.75); tt = np.arange(n) / SR; ns = rng.normal(0, 1, n); out = np.zeros(n); seg = 512
    for i in range(0, n, seg):
        c = 400 + 4200 * (i / n) ** 1.5
        chunk = bp(ns[max(0, i - 2048): i + seg], c * 0.6, min(c * 1.6, 20000))[-(min(seg, n - i)):]
        out[i: i + len(chunk)] = chunk
    env = np.sin(np.pi * np.clip(tt / 0.75, 0, 1)) ** 2
    save("whoosh", np.stack([out * env * np.linspace(1.2, 0.6, n), out * env * np.linspace(0.6, 1.2, n)], 1))
    n = int(SR * 1.2); tt = np.arange(n) / SR; fr = 40 + 70 * np.exp(-tt / 0.05); ph = 2 * np.pi * np.cumsum(fr) / SR
    save("impact", np.sin(ph) * np.exp(-tt / 0.35) + lp(rng.normal(0, 1, n), 1800) * np.exp(-tt / 0.07) * 0.8 + bp(rng.normal(0, 1, n), 2000, 6000) * np.exp(-tt / 0.012) * 0.6)
    n = int(SR * 0.06); tt = np.arange(n) / SR
    save("tick", (np.sin(2 * np.pi * 2100 * tt) * np.exp(-tt / 0.008) + bp(rng.normal(0, 1, n), 3000, 8000) * np.exp(-tt / 0.004) * 0.5) * 0.5)
    n = int(SR * 1.6); tt = np.arange(n) / SR; f = 180 * 2 ** (tt * 2.2); ph = 2 * np.pi * np.cumsum(f) / SR
    save("riser", (np.sin(ph) * 0.3 + hp(rng.normal(0, 1, n), 2500) * 0.5 * (tt / 1.6) ** 2) * (tt / 1.6) ** 1.6)
    n = int(SR * 1.8); tt = np.arange(n) / SR
    save("chime", sum(a * np.sin(2 * np.pi * fq * tt) * np.exp(-tt / dd) for fq, a, dd in [(1318.5, 1, 0.9), (1975.5, 0.5, 0.6), (2637, 0.3, 0.4), (659.3, 0.4, 1.2)]) * np.minimum(tt / 0.004, 1))
    n = int(SR * 2.2); tt = np.arange(n) / SR
    save("boom", np.sin(2 * np.pi * (38 + 12 * np.exp(-tt / 0.3)) * tt) * np.exp(-tt / 0.9) + lp(rng.normal(0, 1, n), 400) * np.exp(-tt / 0.5) * 0.5)
    return {n: os.path.join(d, n + ".wav") for n in names}


# ---------------------------------------------------------------- mix
def _load(path):
    sr, x0 = wavfile.read(path)
    x = x0.astype(np.float32)
    if x0.dtype == np.int16:
        x /= 32768.0
    elif x0.dtype == np.int32:
        x /= 2147483648.0
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    if sr != SR:
        g = math.gcd(SR, sr); x = resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    return x


def mix(out_wav, total, voice=(), music_wav=None, cues=(), dips=(), music_level=0.18, duck=0.36, fade_out=2.6):
    """voice: [(wav, start)]; cues: [(sfx name, time, gain)]; dips: [(start, end, depth)] for drama.
    Writes a 48 kHz stereo WAV normalised to -14 LUFS (true peak -1.5 dB)."""
    N = int(SR * total)
    vo = np.zeros((N, 2), np.float32)

    def place(buf, x, t, g=1.0):
        i = int(t * SR); j = min(len(buf), i + len(x))
        if j > i and i >= 0:
            buf[i:j] += x[: j - i] * g
    for wav, t in voice:
        place(vo, _load(wav), t)
    if len(voice):
        vo = sosfilt(butter(2, 75, "high", fs=SR, output="sos"), vo, axis=0).astype(np.float32)
    mus = np.zeros((N, 2), np.float32)
    if music_wav:
        m = _load(music_wav)[:N]
        mus[: len(m)] = m
        t = np.arange(N) / SR
        g = np.ones(N, np.float32)
        if len(voice):
            env = np.convolve(np.abs(vo[:, 0]), np.ones(int(SR * 0.05)) / int(SR * 0.05), mode="same")
            k = int(SR * 0.15)
            active = np.convolve((env > 0.004).astype(np.float32), np.ones(2 * k + 1), mode="same") > 0
            g = np.where(active, duck, 1.0).astype(np.float32)
            sm = int(SR * 0.12); g = np.convolve(g, np.ones(sm) / sm, mode="same")
        for a, b, depth in dips:
            g *= 1 - depth * np.clip((t - a) / 0.25, 0, 1) * np.clip(1 - (t - b) / 0.9, 0, 1)
        g *= np.clip((total - t) / fade_out, 0, 1)
        mus *= (g * music_level)[:, None]
    fx = np.zeros((N, 2), np.float32)
    bank = sfx_bank() if cues else {}
    cache = {}
    for name, t, gain in cues:
        if name not in cache:
            cache[name] = _load(bank[name])
        place(fx, cache[name], t, gain)
    out = vo + mus * (1 if len(voice) else 4.2) + fx * 0.9
    tmp = out_wav + ".pre.wav"
    wavfile.write(tmp, SR, out.astype(np.float32))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), out_wav], check=True)
    os.remove(tmp)
    return out_wav


def loudness(wav):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m.group(1)) if m else None
