"""Renders one piece of a week in the new style and prints what it made as JSON.

  python3 tools/studio/render.py weeks/2026-W47/pieces.json 2026-W47-E05 --media weeks/2026-W47/media --preview .previews/2026-W47

Formats: explainer and ad (narrated video), carousel (slides), carousel_reel (the carousel as a music reel),
story (one frame). A video whose narrator cannot run is made without a voice and says so in "notes".
"""
import argparse, hashlib, json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio, capture, slides, video

FPS = 30


def seed_of(pid):
    return int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16)


def disclaimer_for(piece):
    return any(not str(c).startswith("FD-") for c in piece.get("claims", []))


def prefix(piece):
    return "TEST-" if piece.get("test") else ""


def pad(s):
    s = dict(s)
    if s.get("num") is not None and len(str(s["num"])) == 1:
        s["num"] = "0" + str(s["num"])
    return s


def render_carousel(piece, media, preview, browser):
    sl = piece["content"]["slides"]
    files, problems = [], []
    for i, s in enumerate(sl):
        name = "%s%s_%02d.png" % (prefix(piece), piece["id"], i + 1)
        html = slides.carousel_slide(pad(s), i, len(sl), "post", disclaimer=disclaimer_for(piece))
        p = browser.still(html, 1080, 1350, os.path.join(media, name), name)
        if p:
            problems.append("slide %d: %s" % (i + 1, p))
        files.append(name)
    frames = [os.path.join(media, f) for f in files]
    return {"files": files, "frames": frames, "problems": problems}


def render_story(piece, media, preview, browser):
    s = piece["content"]["slides"][0]
    name = "%s%s_01.png" % (prefix(piece), piece["id"])
    p = browser.still(slides.story_frame(s, disclaimer=disclaimer_for(piece)), 1080, 1920, os.path.join(media, name), name)
    return {"files": [name], "frames": [os.path.join(media, name)], "problems": ["story: " + p] if p else []}


def slide_seconds(s):
    n = len(" ".join(str(s.get(k, "")) for k in ("kicker", "title", "body", "cta")))
    if s.get("layout") in ("COVER", "CLOSE"):
        return 4.2
    return max(4.2, min(6.8, 3.0 + n * 0.016 + (0.6 if s.get("visual") else 0)))


def render_carousel_reel(piece, week, media, preview, browser):
    src = piece["content"].get("slides")
    if not src:
        ref = piece["content"].get("from")
        found = [p for p in week["pieces"] if p["id"] == ref]
        if not found:
            raise ValueError("carousel_reel needs content.slides or content.from naming a carousel in this week")
        src = found[0]["content"]["slides"]
        disc = disclaimer_for(found[0]) or disclaimer_for(piece)
    else:
        disc = disclaimer_for(piece)
    T = 0.5
    durs = [slide_seconds(s) for s in src]
    work = tempfile.mkdtemp(prefix="fd-reel-")
    problems = []
    try:
        dirs = []
        for i, s in enumerate(src):
            html = slides.carousel_slide(pad(s), i, len(src), "reel", disclaimer=disc)
            p = browser.still(html, 1080, 1920, os.path.join(work, "check%d.png" % i), "chk%d" % i)
            if p:
                problems.append("slide %d: %s" % (i + 1, p))
            d = os.path.join(work, "s%02d" % i)
            browser.frames(html, 1080, 1920, FPS, durs[i], d, "reel%d" % i)
            dirs.append(d)
        total = sum(durs) - T * (len(durs) - 1)
        silent = os.path.join(work, "video.mp4")
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for d in dirs:
            args += ["-framerate", str(FPS), "-i", os.path.join(d, "f%05d.jpg")]
        fc = ";".join("[%d]settb=AVTB,fps=%d,format=yuv420p[a%d]" % (i, FPS, i) for i in range(len(dirs)))
        prev, off, cues = "a0", 0.0, []
        for i in range(1, len(dirs)):
            off += durs[i - 1] - T
            fc += ";[%s][a%d]xfade=transition=slideleft:duration=%.2f:offset=%.3f[v%d]" % (prev, i, T, off, i)
            prev = "v%d" % i
            cues.append(("whoosh", off - 0.12, 0.3))
        args += ["-filter_complex", fc, "-map", "[%s]" % prev, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), silent]
        import subprocess
        subprocess.run(args, check=True)
        mus = audio.music(os.path.join(work, "music.wav"), total + 0.5, seed=seed_of(piece["id"]), preset=seed_of(piece["id"]) % 4, intro_bars=0, outro_bars=1)
        wav = audio.mix(os.path.join(work, "mix.wav"), total, music_wav=mus, cues=cues)
        name = "%s%s.mp4" % (prefix(piece), piece["id"])
        out = os.path.join(media, name)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        os.makedirs(preview, exist_ok=True)
        frames, t = [], 0.0
        for i, dd in enumerate(durs):
            frames.append(capture.grab(out, min(total - 0.2, t + dd - T - 0.3), os.path.join(preview, "%s_%02d.png" % (piece["id"], i))))
            t += dd - T
        return {"files": [name], "frames": frames, "seconds": round(total, 2), "problems": problems, "loudness": audio.loudness(wav)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def render_video(piece, media, preview, browser, allow_silent=True):
    beats = video.make_beats(piece)
    ok, why = audio.voice_status(download=True)
    notes = []
    work = tempfile.mkdtemp(prefix="fd-video-")
    try:
        if ok:
            for b in beats:
                text = b.say or audio.speakable(b.text)
                b.say = text
                r = audio.narrate(text, os.path.join(work, "vo_%s.wav" % b.key))
                b.dur, b.words, b.wav = r["dur"], r["words"], os.path.join(work, "vo_%s.wav" % b.key)
        elif not allow_silent:
            raise RuntimeError("narrator unavailable: " + why)
        else:
            notes.append("made without the AI voice: " + why)
        html, total, cues, dips, looks = video.build(piece, beats, voiced=ok, disclaimer=disclaimer_for(piece))
        d = os.path.join(work, "frames")
        spf = browser.frames(html, 1080, 1920, FPS, total, d, "video")
        mus = audio.music(os.path.join(work, "music.wav"), total + 0.5, seed=seed_of(piece["id"]), preset=seed_of(piece["id"]) % 4)
        voice = [(b.wav, b.start) for b in beats if b.wav]
        wav = audio.mix(os.path.join(work, "mix.wav"), total, voice=voice, music_wav=mus, cues=cues, dips=dips)
        name = "%s%s.mp4" % (prefix(piece), piece["id"])
        out = os.path.join(media, name)
        capture.encode(d, FPS, out, audio=wav)
        os.makedirs(preview, exist_ok=True)
        frames = [capture.grab(out, t, os.path.join(preview, "%s_%02d.png" % (piece["id"], i))) for i, t in enumerate(looks)]
        timing = [{"beat": b.key, "start": round(b.start, 2), "end": round(b.end, 2), "say": b.say} for b in beats]
        return {"files": [name], "frames": frames, "seconds": total, "notes": notes, "voiced": ok, "loudness": audio.loudness(wav),
                "seconds_per_frame": round(spf, 3), "timing": timing, "problems": []}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("week_file")
    ap.add_argument("piece_id")
    ap.add_argument("--media")
    ap.add_argument("--preview")
    ap.add_argument("--no-silent", action="store_true", help="fail instead of making a video without the voice")
    a = ap.parse_args()
    week = json.load(open(a.week_file))
    piece = [p for p in week["pieces"] if p["id"] == a.piece_id]
    if not piece:
        sys.exit("no piece %s" % a.piece_id)
    piece = piece[0]
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    media = a.media or os.path.join(root, "weeks", week["week"], "media")
    preview = a.preview or os.path.join(root, ".previews", week["week"])
    os.makedirs(media, exist_ok=True); os.makedirs(preview, exist_ok=True)
    t0 = time.time()
    b = capture.Browser()
    try:
        f = piece["format"]
        if f == "carousel":
            r = render_carousel(piece, media, preview, b)
        elif f == "story":
            r = render_story(piece, media, preview, b)
        elif f in ("explainer", "ad"):
            r = render_video(piece, media, preview, b, allow_silent=not a.no_silent)
        elif f == "carousel_reel":
            r = render_carousel_reel(piece, week, media, preview, b)
        else:
            sys.exit("format %s is not made by the studio" % f)
    finally:
        b.close()
    sheet = os.path.join(preview, "%s.png" % piece["id"])
    try:
        capture.sheet(r["frames"][:8], sheet)
        r["preview"] = sheet
    except Exception as e:
        r["preview_error"] = str(e)[:200]
    r["id"] = piece["id"]
    r["elapsed"] = round(time.time() - t0, 1)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
