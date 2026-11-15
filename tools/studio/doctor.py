"""Checks that this workspace can make the studio's media, and with --setup installs what is missing.

  python3 tools/studio/doctor.py            # report only
  python3 tools/studio/doctor.py --setup    # also install kokoro-onnx (pip) and fetch the narrator's model files

Prints one JSON object: chromium, ffmpeg, python packages, the narrator and a short test render.
"""
import json, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PIP = ["kokoro-onnx==0.6.1"]


def main():
    setup = "--setup" in sys.argv
    out = {}
    out["ffmpeg"] = bool(shutil.which("ffmpeg"))
    for mod in ["numpy", "scipy", "PIL", "playwright"]:
        try:
            __import__(mod); out[mod] = True
        except Exception as e:
            out[mod] = "missing: %s" % e
    try:
        import kokoro_onnx  # noqa
        out["kokoro_onnx"] = True
    except Exception:
        if setup:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages"] + PIP, capture_output=True, text=True)
            out["pip"] = "ok" if r.returncode == 0 else r.stderr.strip()[-400:]
        try:
            import importlib; importlib.invalidate_caches(); import kokoro_onnx  # noqa
            out["kokoro_onnx"] = True
        except Exception as e:
            out["kokoro_onnx"] = "missing: %s" % e
    import audio
    ok, why = audio.voice_status(download=setup)
    out["narrator"] = True if ok else why
    try:
        import capture, brand
        b = capture.Browser()
        try:
            html = brand.shell('<div class="content"><h1>Test</h1></div>', 1080, 1350)
            f = os.path.join(tempfile.gettempdir(), "fd-doctor.png")
            b.still(html, 1080, 1350, f, "doctor")
            out["chromium"] = True
        finally:
            b.close()
    except Exception as e:
        out["chromium"] = "failed: %s" % str(e)[:300]
    if ok:
        try:
            r = audio.narrate("Finance Department.", os.path.join(tempfile.gettempdir(), "fd-doctor.wav"))
            out["narrator_test"] = "%.2f seconds" % r["dur"]
        except Exception as e:
            out["narrator_test"] = "failed: %s" % str(e)[:300]
    out["ready"] = all(v is True for k, v in out.items() if k in ("ffmpeg", "numpy", "scipy", "PIL", "playwright", "chromium"))
    out["voice_ready"] = out.get("narrator") is True
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
