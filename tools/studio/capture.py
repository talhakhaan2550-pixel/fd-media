"""Draws pages in headless Chromium: stills as PNG, and animated pages frame by frame (window.seek(t)) into an MP4.

Uses the Python Playwright and the Chromium that come with the workspace (PLAYWRIGHT_BROWSERS_PATH), so nothing is
installed. Frames are captured as JPEG through the DevTools protocol, which is the slow part (about 0.15 s a frame).
"""
import base64, os, shutil, subprocess, tempfile, time

_CHECK_JS = """() => {
  const c = document.querySelector('.content');
  if (!c) return null;
  const hidden = [...document.querySelectorAll('.deco,.loc,.heroshape,.zmap')];
  const old = hidden.map(e => e.style.display);
  hidden.forEach(e => e.style.display = 'none');
  const over = c.scrollHeight > c.clientHeight + 3 || c.scrollWidth > c.clientWidth + 3;
  const r = c.getBoundingClientRect();
  let worst = null;
  for (const e of c.querySelectorAll('h1,h2,p,.chip,.cta,.reply,.card,.val,.big,.label,.small,.xl,.kicker,.cal,.lic,.cred,.step,.ckr')) {
    if (e.closest('.deco,.loc,.heroshape,.zmap')) continue;
    const b = e.getBoundingClientRect();
    if (b.width === 0 && b.height === 0) continue;
    if (b.bottom > r.bottom + 3 || b.right > r.right + 3 || b.left < r.left - 3) { worst = (e.className || e.tagName) + ': ' + (e.textContent || '').trim().slice(0, 40); break; }
  }
  hidden.forEach((e, i) => e.style.display = old[i]);
  return over || worst ? (worst || 'content taller or wider than its box') : null;
}"""


class Browser:
    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        path = os.environ.get("CHROMIUM_PATH")
        args = ["--force-color-profile=srgb", "--hide-scrollbars", "--disable-lcd-text", "--font-render-hinting=none"]
        self.browser = self._pw.chromium.launch(executable_path=path or None, args=args)
        self.tmp = tempfile.mkdtemp(prefix="fd-studio-")

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()
            shutil.rmtree(self.tmp, ignore_errors=True)

    def _open(self, html, w, h, name):
        f = os.path.join(self.tmp, name + ".html")
        with open(f, "w") as fh:
            fh.write(html)
        page = self.browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.goto("file://" + f)
        ok = page.evaluate("""async () => {
          const want = ['400 40px SS4', '600 40px SS4', '700 40px SS4', '400 40px Plex', '500 40px Plex', '600 40px Plex'];
          await Promise.all(want.map(f => document.fonts.load(f)));
          await document.fonts.ready;
          return want.every(f => document.fonts.check(f));
        }""")
        if not ok:
            raise RuntimeError("the brand fonts did not load")
        page.evaluate("window.fitNow && window.fitNow()")
        page.wait_for_timeout(60)
        return page

    def still(self, html, w, h, out, name="still", check=True):
        """Draws the finished state of a page to a PNG. Returns a layout problem, or None."""
        page = self._open(html, w, h, name)
        try:
            page.evaluate("window.final && window.final()")
            page.wait_for_timeout(40)
            problem = page.evaluate(_CHECK_JS) if check else None
            page.screenshot(path=out, type="png")
            return problem
        finally:
            page.close()

    def frames(self, html, w, h, fps, seconds, out_dir, name="anim", quality=90, progress=None):
        """Draws every frame of an animated page into out_dir/f00000.jpg and so on. Returns seconds per frame."""
        os.makedirs(out_dir, exist_ok=True)
        page = self._open(html, w, h, name)
        cdp = page.context.new_cdp_session(page)
        n = int(round(seconds * fps))
        t0 = time.time()
        try:
            for i in range(n):
                page.evaluate("t => window.seek(t)", i / fps)
                shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": quality, "optimizeForSpeed": True})
                with open(os.path.join(out_dir, "f%05d.jpg" % i), "wb") as fh:
                    fh.write(base64.b64decode(shot["data"]))
                if progress and i % 150 == 0:
                    progress(i, n)
        finally:
            page.close()
        return (time.time() - t0) / max(1, n)


def encode(frames_dir, fps, out, audio=None, crf=19):
    """Frames (and an audio track) to an H.264 MP4 that Instagram, Facebook and YouTube accept."""
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%05d.jpg")]
    if audio:
        args += ["-i", audio]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(fps)]
    if audio:
        args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    args += ["-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    return out


def grab(video, t, out, width=540):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.2f" % t, "-i", video, "-frames:v", "1", "-vf", "scale=%d:-1" % width, out], check=True)
    return out


def sheet(images, out, width=360):
    """One preview image of several frames side by side, for the run to look at."""
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for f in images:
        args += ["-i", f]
    scaled = ";".join("[%d:v]scale=%d:-1[a%d]" % (i, width, i) for i in range(len(images)))
    if len(images) > 1:
        # different heights (4:5 slides and 9:16 frames) are padded to the tallest
        args += ["-filter_complex", scaled + ";" + "".join("[a%d]" % i for i in range(len(images))) + "xstack=inputs=%d:layout=%s:fill=0x222222[out]"
                 % (len(images), "|".join("%d_0" % (i * width) if i else "0_0" for i in range(len(images)))), "-map", "[out]"]
    else:
        args += ["-filter_complex", scaled, "-map", "[a0]"]
    args += ["-frames:v", "1", out]
    subprocess.run(args, check=True)
    return out
