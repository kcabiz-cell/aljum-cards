#!/usr/bin/env python3
"""알아줌 위로 콘텐츠 자동 제작기.
- 배경: Pixabay API(무료, 상업 이용 가능) 사진 / 실패·키 없음 시 자체 생성 장면(scenes.py)
- 문구: tools/comfort_lines.json (해요체, 위로·다독임)
- 음악: 직접 합성(저작권 없음) → 릴스에 삽입
사용: python3 comfort_assets.py [--start YYYY-MM-DD] [--days 7] [--out comfort] [--no-net] [--force-type reel|image]
요일 규칙(KST): 월·금·일=이미지, 수·토=릴스, 화·목=띠별 카드(별도 파이프라인이므로 건너뜀)
"""
import os, sys, json, glob, random, subprocess, wave, argparse, datetime as dt, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
W, H = 1080, 1920
TYPE_BY_WEEKDAY = {0: "image", 2: "reel", 4: "image", 5: "reel", 6: "image"}  # Mon=0
QUERIES = ["sky clouds pastel", "sunrise mountains mist", "calm sea sunset", "green forest sunlight", "starry night sky",
           "soft clouds sky", "meadow flowers field", "lake reflection morning", "milky way stars", "autumn leaves forest path"]
BAD_TAGS = {"woman", "man", "girl", "boy", "people", "person", "portrait", "child", "children", "face", "couple", "baby",
            "model", "men", "women", "lady", "bride", "groom", "hand", "hands", "fashion", "logo", "text", "sign", "advertising",
            "car", "city", "building", "street", "crowd", "tourist", "selfie"}


def find_font(kind):
    pats = {"serif": ["NotoSerifCJK-SemiBold.ttc", "NotoSerifCJK-Bold.ttc", "NotoSerifCJK-Regular.ttc"],
            "sans": ["NotoSansCJK-Regular.ttc", "NotoSansCJK-Medium.ttc"]}[kind]
    for p in pats:
        for f in glob.glob(f"/usr/share/fonts/**/{p}", recursive=True):
            return f
    for f in glob.glob("/usr/share/fonts/**/*CJK*.ttc", recursive=True):
        return f
    raise RuntimeError("Korean font not found")


def load_font(path, size):
    for idx in (1, 0, 3):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.truetype(path, size)


# ---------------- 배경 ----------------
def cover(img, w, h):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def pixabay_pick(key, query, used):
    import requests
    params = dict(key=key, q=query, image_type="photo", orientation="vertical", safesearch="true", min_width=1000,
                  min_height=1500, per_page=100, order="popular", lang="en")
    r = requests.get("https://pixabay.com/api/", params=params, timeout=30)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    ok = []
    for h in hits:
        tags = {t.strip().lower() for t in h.get("tags", "").split(",")}
        words = {w for t in tags for w in t.split()}
        if (tags | words) & BAD_TAGS or h["id"] in used:
            continue
        ok.append(h)
    if not ok:
        return None
    h = random.choice(ok[:30])
    data = requests.get(h["largeImageURL"], timeout=60).content
    from io import BytesIO
    return Image.open(BytesIO(data)).convert("RGB"), {"id": h["id"], "page": h["pageURL"], "user": h.get("user"), "query": query}


def get_background(date, outdir, used, no_net, seed):
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if key and not no_net:
        for attempt in range(3):
            q = QUERIES[(date.toordinal() + attempt) % len(QUERIES)]
            try:
                res = pixabay_pick(key, q, used)
                if res:
                    img, meta = res
                    meta["source"] = "pixabay"
                    return cover(img, int(W * 1.12), int(H * 1.12)), meta
            except Exception as e:  # 네트워크/한도 문제는 폴백
                print("pixabay error:", e, file=sys.stderr)
    import scenes
    names = ["sky", "sunset_sea", "mountains", "forest", "moon", "space"]
    name = names[date.toordinal() % len(names)]
    img, _ = scenes.scene(name, int(W * 1.12), int(H * 1.12), seed=seed)
    return img, {"source": "procedural", "scene": name}


def style_for(bg):
    """사진 가운데 영역 밝기에 맞춰 글자색과 반투명 막(가독성 확보) 결정"""
    g = np.asarray(bg.convert("L").crop((bg.width // 8, bg.height // 4, bg.width * 7 // 8, bg.height * 3 // 4)), np.float32).mean()
    if g > 135:
        return (58, 46, 60), (255, 255, 255)   # 어두운 글자 + 밝은 막
    return (255, 252, 246), (20, 20, 40)        # 밝은 글자 + 어두운 막


def veil(bg, veil_rgb, strength=0.38):
    arr = np.asarray(bg.convert("RGB"), np.float32)
    h, w = arr.shape[:2]
    y = np.linspace(-1, 1, h)[:, None]
    band = np.exp(-(y / 0.55) ** 2)  # 가운데가 더 진하게
    a = (strength * (0.45 + 0.55 * band))[..., None]
    arr = arr * (1 - a) + np.array(veil_rgb, np.float32) * a
    return Image.fromarray(arr.astype(np.uint8))


# ---------------- 글자/음악 ----------------
def text_layer(groups, color, size=66, w=W, h=H, shadow=None):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = load_font(find_font("serif"), size)
    lh = int(size * 1.65)
    lines = [x for g in groups for x in g]
    y = (h - lh * len(lines)) // 2 - 30
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((w - tw) / 2, y), ln, font=f, fill=color + (255,))
        y += lh
    return lay


def brand_layer(color, w=W, h=H):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = load_font(find_font("sans"), 34)
    t = "알아줌 · @arajum_saju"
    d.text(((w - d.textlength(t, font=f)) / 2, h - 210), t, font=f, fill=color + (190,))
    return lay


def synth_music(path, seconds, seed=1):
    sr = 44100
    n = int(sr * seconds)
    t = np.arange(n) / sr
    rnd = random.Random(seed)
    prog = rnd.choice([
        [[261.63, 329.63, 392.00], [220.00, 261.63, 329.63], [174.61, 220.00, 261.63], [196.00, 246.94, 293.66]],
        [[293.66, 369.99, 440.00], [246.94, 293.66, 369.99], [196.00, 246.94, 293.66], [220.00, 277.18, 329.63]],
        [[246.94, 311.13, 369.99], [220.00, 277.18, 329.63], [164.81, 207.65, 246.94], [185.00, 233.08, 277.18]]])
    out = np.zeros(n)
    seg = seconds / len(prog)
    for i, ch in enumerate(prog):
        s0, s1 = int(i * seg * sr), int(min(n, (i + 1) * seg * sr + sr * 2))
        tt = t[s0:s1] - t[s0]
        env = np.minimum(1, tt / 2.5) * np.minimum(1, np.maximum(0, (len(tt) / sr - tt)) / 2.5)
        for f in ch:
            for det in (0.997, 1.0, 1.003):
                out[s0:s1] += 0.05 * np.sin(2 * np.pi * f * det * tt) * env
            out[s0:s1] += 0.02 * np.sin(2 * np.pi * f * 2 * tt) * env
    pent = [523.25, 587.33, 659.25, 783.99, 880.00]
    tpos = 1.5
    while tpos < seconds - 3:
        f = rnd.choice(pent)
        i0 = int(tpos * sr)
        tt = np.arange(int(sr * 3.0)) / sr
        note = 0.07 * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.01)
        end = min(n, i0 + len(note))
        out[i0:end] += note[: end - i0]
        tpos += rnd.choice([1.6, 2.4, 3.2])
    out = out / max(1e-6, np.abs(out).max()) * 0.8
    out *= np.minimum(1, t / 2.0) * np.minimum(1, (seconds - t) / 3.0)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------------- 제작 ----------------
def make_reel(bg, groups, color, vrgb, outdir, seed, per=4.0):
    secs = per * len(groups) + 3.0
    bgv = veil(bg, vrgb)
    bgp = os.path.join(outdir, "_bg.png"); bgv.save(bgp)
    wav = os.path.join(outdir, "_music.wav"); synth_music(wav, secs, seed)
    ins = ["-loop", "1", "-t", f"{secs}", "-i", bgp]
    fc = [f"[0:v]zoompan=z='1.0+0.0004*on':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s={W}x{H}:fps=30,format=yuv420p[v0]"]
    last = "v0"
    for i, g in enumerate(groups):
        p = os.path.join(outdir, f"_t{i}.png"); text_layer([g], color).save(p)
        ins += ["-loop", "1", "-t", f"{secs}", "-i", p]
        st = 0.8 + i * per
        fo = f",fade=t=out:st={st + per - 0.8}:d=0.8:alpha=1" if i < len(groups) - 1 else ""
        fc.append(f"[{i + 1}:v]format=rgba,fade=t=in:st={st}:d=1.2:alpha=1{fo}[tx{i}]")
        fc.append(f"[{last}][tx{i}]overlay=0:0:format=auto[o{i}]"); last = f"o{i}"
    bp = os.path.join(outdir, "_brand.png"); brand_layer(color).save(bp)
    ins += ["-loop", "1", "-t", f"{secs}", "-i", bp]
    fc.append(f"[{len(groups) + 1}:v]format=rgba,fade=t=in:st=1:d=1.5:alpha=1[br]")
    fc.append(f"[{last}][br]overlay=0:0:format=auto,format=yuv420p[vout]")
    mp4 = os.path.join(outdir, "reel.mp4")
    cmd = ["ffmpeg", "-y", *ins, "-i", wav, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{len(groups) + 2}:a",
           "-t", f"{secs}", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-c:a", "aac", "-b:a", "128k",
           "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in glob.glob(os.path.join(outdir, "_*")):
        os.remove(f)
    return mp4


def make_image(bg, groups, color, vrgb, outdir):
    base = cover(veil(bg, vrgb), 1080, 1350)  # 피드용 4:5
    lay = text_layer(groups[:2], color, size=62, w=1080, h=1350)
    img = base.convert("RGBA"); img.alpha_composite(lay)
    b = brand_layer(color, 1080, 1350)
    img.alpha_composite(b.transform(b.size, Image.AFFINE, (1, 0, 0, 0, 1, 130)))  # 하단 여백 조정
    p = os.path.join(outdir, "01.jpg"); img.convert("RGB").save(p, quality=92)
    return p


def caption(entry, kind):
    tail = "소리를 켜고 보면 더 좋아요 🎧\n" if kind == "reel" else ""
    return (f"{entry['cap']}\n\n{tail}마음에 남는 한마디가 있다면 저장해 두고, 힘이 필요할 때 꺼내 보세요 🤍\n"
            "알아줌은 오늘도 따뜻한 한마디를 건네요.\n\n"
            "#오늘의한마디 #위로 #따뜻한말 #마음챙김 #힐링 #글귀 #알아줌 #arajum_saju")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start"); ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "comfort"))
    ap.add_argument("--no-net", action="store_true"); ap.add_argument("--force-type")
    a = ap.parse_args()
    kst = dt.timezone(dt.timedelta(hours=9))
    start = dt.date.fromisoformat(a.start) if a.start else (dt.datetime.now(kst).date() + dt.timedelta(days=1))
    lines = json.load(open(os.path.join(HERE, "comfort_lines.json"), encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    used_path = os.path.join(a.out, "used.json")
    used = json.load(open(used_path)) if os.path.exists(used_path) else {"photos": [], "lines": []}
    for i in range(a.days):
        d = start + dt.timedelta(days=i)
        kind = a.force_type or TYPE_BY_WEEKDAY.get(d.weekday())
        if not kind:
            continue
        od = os.path.join(a.out, d.isoformat())
        if os.path.exists(os.path.join(od, "meta.json")):
            continue
        os.makedirs(od, exist_ok=True)
        pool = [k for k in range(len(lines)) if k not in used["lines"]] or list(range(len(lines)))
        if len(pool) == len(lines):
            used["lines"] = []
        li = pool[d.toordinal() % len(pool)]
        entry = lines[li]
        groups = [g.split("|") for g in entry["g"]]
        bg, meta = get_background(d, od, set(used["photos"]), a.no_net, seed=d.toordinal())
        color, vrgb = style_for(bg)
        if kind == "reel":
            make_reel(bg, groups, color, vrgb, od, seed=d.toordinal())
            files = ["reel.mp4"]
        else:
            make_image(bg, groups, color, vrgb, od); files = ["01.jpg"]
        open(os.path.join(od, "caption.txt"), "w", encoding="utf-8").write(caption(entry, kind))
        json.dump({"date": d.isoformat(), "type": kind, "files": files, "line_set": li, "background": meta},
                  open(os.path.join(od, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        used["lines"].append(li)
        if meta.get("id"):
            used["photos"].append(meta["id"])
        print(d, kind, meta.get("source"), files)
    json.dump(used, open(used_path, "w"))


if __name__ == "__main__":
    main()
