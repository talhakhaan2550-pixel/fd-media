"""Renders a motion v2 piece (content.motion, see motion.py) and prints what it made as JSON.

  python3 tools/studio/render_motion.py samples/motion-v2/pieces.json MV2-MID-5472 --out samples/motion-v2/media
  python3 tools/studio/render_motion.py samples/motion-v2/pieces.json MV2-MID-5472 --peek 0,3.5,9   # stills only

--peek draws only the frames at those seconds (fast, for checking layout); without it the whole reel is made:
narration (Kokoro, the generic af_heart voice), frames at 30 fps, original music, sound effects, -14 LUFS.
"""
import argparse, hashlib, json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio, capture, motion

FPS = 30


def seed_of(pid):
    return int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16)


def disclaimer_for(piece):
    return any(not str(c).startswith("FD-") for c in piece.get("claims", []))


def narrate(beats, work):
    ok, why = audio.voice_status(download=True)
    if not ok:
        raise RuntimeError("narrator unavailable: " + why)
    for b in beats:
        text = b.say or audio.speakable(b.text)
        b.say = text
        wav = os.path.join(work, "vo_%s.wav" % b.key)
        r = audio.narrate(text, wav)
        b.dur, b.words, b.wav = r["dur"], r["words"], wav


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("piece_id")
    ap.add_argument("--out", default="samples/motion-v2/media")
    ap.add_argument("--peek", help="comma separated seconds: draw only these frames")
    a = ap.parse_args()
    data = json.load(open(a.file))
    piece = [p for p in data["pieces"] if p["id"] == a.piece_id][0]
    os.makedirs(a.out, exist_ok=True)
    work = tempfile.mkdtemp(prefix="fd-motion-")
    t0 = time.time()
    b = capture.Browser()
    try:
        beats, stations = motion.make_beats(piece)
        narrate(beats, work)
        html, total, cues, looks = motion.build(piece, beats, stations, disclaimer=disclaimer_for(piece))
        with open(os.path.join(work, "page.html"), "w") as f:
            f.write(html)
        timing = [{"beat": x.key, "station": x.station, "start": round(x.start, 2), "end": round(x.end, 2)} for x in beats]
        if a.peek:
            times = [float(x) for x in a.peek.split(",")]
            page = b._open(html, 1080, 1920, "peek")
            files = []
            try:
                for t in times:
                    page.evaluate("t => window.seek(t)", t)
                    f = os.path.join(a.out, "%s_peek_%05.2f.png" % (piece["id"], t))
                    page.screenshot(path=f, type="png")
                    files.append(f)
            finally:
                page.close()
            sheet = os.path.join(a.out, "%s_peek.png" % piece["id"])
            capture.sheet(files, sheet, width=300)
            print(json.dumps({"id": piece["id"], "seconds": total, "timing": timing, "sheet": sheet}, indent=1))
            return
        d = os.path.join(work, "frames")
        spf = b.frames(html, 1080, 1920, FPS, total, d, "reel")
        mus = audio.music(os.path.join(work, "music.wav"), total + 0.5, seed=seed_of(piece["id"]), preset=seed_of(piece["id"]) % 4)
        voice = [(x.wav, x.start) for x in beats if x.wav]
        wav = audio.mix(os.path.join(work, "mix.wav"), total, voice=voice, music_wav=mus, cues=cues)
        out = os.path.join(a.out, "%s.mp4" % piece["id"])
        capture.encode(d, FPS, out, audio=wav)
        frames = [capture.grab(out, t, os.path.join(a.out, "%s_%02d.png" % (piece["id"], i)), width=540) for i, t in enumerate(looks)]
        sheet = os.path.join(a.out, "%s_sheet.png" % piece["id"])
        capture.sheet(frames[:9], sheet, width=300)
        for f in frames:
            os.remove(f)
        print(json.dumps({"id": piece["id"], "file": out, "seconds": total, "seconds_per_frame": round(spf, 3), "loudness": audio.loudness(wav),
                          "elapsed": round(time.time() - t0, 1), "timing": timing, "sheet": sheet}, indent=1))
    finally:
        b.close()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
