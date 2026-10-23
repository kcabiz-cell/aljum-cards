#!/usr/bin/env python3
"""wow_pusan 카드뉴스 제작. 사진: Pixabay API(상업 이용 가능, 출처표기 불필요).
mode cands: busan/cands/<slug>/ 에 후보 썸네일 + sheet.jpg 생성
mode build: busan_photos.json 의 사진 ID로 busan/<slug>/01..N.jpg + caption.txt + meta.json 생성"""
import os, sys, json, glob, argparse
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
W, H = 1080, 1350
KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
FOOT = json.load(open(os.path.join(HERE, "busan_misc.json")))["foot"]

def font(bold, size):
    pats = ["NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc", "NotoSansCJK-Regular.ttc"]
    for p in pats:
        for f in glob.glob(f"/usr/share/fonts/**/{p}", recursive=True):
            for idx in (1, 0):
                try: return ImageFont.truetype(f, size, index=idx)
                except Exception: pass
    raise RuntimeError("font")

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for tok in text.split(" "):
        t = (cur + " " + tok).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = tok
            while d.textlength(cur, font=f) > maxw:  # 매우 긴 토큰은 글자 단위
                k = len(cur)
                while k > 1 and d.textlength(cur[:k], font=f) > maxw: k -= 1
                lines.append(cur[:k]); cur = cur[k:]
    if cur: lines.append(cur)
    return lines

def cover_fit(img, w, h):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))

def draw_block(d, x, y, maxw, text, bold, size, fill, gap=1.35, minsize=28):
    f = font(bold, size); ls = wrap(d, text, f, maxw)
    for ln in ls:
        d.text((x, y), ln, font=f, fill=fill); y += int(size * gap)
    return y

def gradient(img, top_a, bot_a, start=0.35):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); px = ov.load()
    for yy in range(img.height):
        t = yy / img.height
        a = top_a if t < start else int(top_a + (bot_a - top_a) * ((t - start) / (1 - start)) ** 1.2)
        for xx in range(0, img.width): px[xx, yy] = (8, 14, 24, a)
    return Image.alpha_composite(img.convert("RGBA"), ov)

def footer(d, n, total):
    f = font(False, 30)
    d.text((60, H - 70), "wow_pusan · Busan Guide 부산", font=f, fill=(255, 255, 255, 200))
    t = f"{n}/{total}"; d.text((W - 60 - d.textlength(t, font=f), H - 70), t, font=f, fill=(255, 255, 255, 200))

def make_cover(photo, c, total):
    base = gradient(cover_fit(photo, W, H), 20, 230, 0.30)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((60, 60, 420, 118), 28, fill=(255, 255, 255, 235))
    d.text((84, 70), "WOW PUSAN · BUSAN", font=font(True, 30), fill=(20, 40, 70))
    y = 700
    y = draw_block(d, 60, y, W - 120, c["t"], True, 92, (255, 255, 255), 1.15)
    y = draw_block(d, 60, y + 14, W - 120, c["k"], True, 56, (255, 214, 170))
    y = draw_block(d, 60, y + 10, W - 120, c["s"], False, 40, (235, 240, 245))
    d.text((W - 60 - d.textlength("swipe →", font=font(True, 36)), H - 120), "swipe →", font=font(True, 36), fill=(255, 255, 255))
    footer(d, 1, total); return base.convert("RGB")

def make_card(photo, card, n, total):
    bg = cover_fit(photo, W, H).filter(ImageFilter.GaussianBlur(10))
    base = Image.alpha_composite(bg.convert("RGBA"), Image.new("RGBA", (W, H), (10, 20, 34, 205)))
    d = ImageDraw.Draw(base)
    accent = (255, 190, 120) if card.get("route") else (140, 220, 235)
    if card.get("route"):
        cf = font(True, 26); cw = int(d.textlength("HOW TO GET THERE", font=cf)); d.rounded_rectangle((60, 90, 60 + cw + 48, 142), 24, fill=accent); d.text((84, 99), "HOW TO GET THERE", font=cf, fill=(30, 30, 40))
    y = 200
    y = draw_block(d, 60, y, W - 120, card["h"], True, 68, accent, 1.2)
    y += 36
    for i, ln in enumerate(card["lines"]):
        size = 48
        pre = f"{i + 1}.  " if card.get("route") and not card.get("nonum") and len(card["lines"]) > 2 and i < len(card["lines"]) - 1 else "•  "
        f = font(False, size); lines = wrap(d, ln, f, W - 120 - 80)
        d.text((60, y), pre.strip(), font=font(True, size), fill=accent)
        for l in lines:
            d.text((140, y), l, font=f, fill=(255, 255, 255)); y += int(size * 1.4)
        y += 30
    footer(d, n, total); return base.convert("RGB")

def make_cta(total, title="Save this for your Busan trip"):
    base = Image.new("RGBA", (W, H), (14, 62, 84, 255)); d = ImageDraw.Draw(base)
    for yy in range(H):
        a = int(160 * yy / H); d.line((0, yy, W, yy), fill=(8, 24, 48, a))
    y = 330
    y = draw_block(d, 60, y, W - 120, title, True, 80, (255, 255, 255), 1.2)
    y = draw_block(d, 60, y + 20, W - 120, "여행 전에 저장해 두세요 🔖".replace(" 🔖", ""), True, 52, (255, 214, 170))
    y = draw_block(d, 60, y + 50, W - 120, "Share with your travel buddy.", False, 44, (235, 240, 245))
    y = draw_block(d, 60, y + 10, W - 120, "Follow @wow_pusan for Busan food, spots, routes & Giants news.", False, 44, (235, 240, 245))
    draw_block(d, 60, H - 330, W - 120, FOOT, False, 30, (200, 215, 225), 1.4)
    footer(d, total, total); return base.convert("RGB")

def search(q, n=8):
    r = requests.get("https://pixabay.com/api/", params=dict(key=KEY, q=q, image_type="photo", safesearch="true", per_page=20, order="popular", min_width=1000), timeout=30)
    r.raise_for_status(); return r.json().get("hits", [])[:n]

def cands(posts):
    out = os.path.join(ROOT, "busan", "cands"); os.makedirs(out, exist_ok=True)
    for p in posts:
        seen, items = set(), []
        for q in p["q"]:
            try: hits = search(q, 6)
            except Exception as e: print("err", q, str(e).replace(KEY, "***")[:100]); continue
            for h in hits:
                if h["id"] not in seen: seen.add(h["id"]); items.append((q, h))
        items = items[:12]
        cols, tw, th = 4, 400, 300; rows = (len(items) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + 40)), (30, 30, 30)); d = ImageDraw.Draw(sheet)
        for i, (q, h) in enumerate(items):
            try:
                im = Image.open(BytesIO(requests.get(h["webformatURL"], timeout=40).content)).convert("RGB")
            except Exception: continue
            im = cover_fit(im, tw, th); x, y = (i % cols) * tw, (i // cols) * (th + 40)
            sheet.paste(im, (x, y)); d.text((x + 6, y + th + 6), f'{h["id"]}  {h.get("tags","")[:34]}', font=font(False, 18), fill=(255, 255, 255))
        sheet.save(os.path.join(out, p["slug"] + ".jpg"), quality=80); print(p["slug"], len(items))

def build(posts, photos):
    for p in posts:
        ids = photos.get(p["slug"])
        if not ids: print("skip", p["slug"]); continue
        imgs, credits = [], []
        for pid in ids:
            h = requests.get("https://pixabay.com/api/", params=dict(key=KEY, id=pid), timeout=30).json()["hits"][0]
            imgs.append(Image.open(BytesIO(requests.get(h["largeImageURL"], timeout=60).content)).convert("RGB"))
            credits.append({"id": pid, "user": h.get("user"), "page": h.get("pageURL")})
        total = 2 + len(p["cards"]); od = os.path.join(ROOT, "busan", p["slug"]); os.makedirs(od, exist_ok=True)
        make_cover(imgs[0], p["cover"], total).save(os.path.join(od, "01.jpg"), quality=92)
        for i, c in enumerate(p["cards"]):
            make_card(imgs[(i + 1) % len(imgs)], c, i + 2, total).save(os.path.join(od, f"{i + 2:02d}.jpg"), quality=92)
        make_cta(total).save(os.path.join(od, f"{total:02d}.jpg"), quality=92)
        cap = f'{p["en"]}\n\n{p["kr"]}\n\n💾 Save for your trip · 🔁 Share with your travel buddy · ➕ Follow @wow_pusan\n📷 Photos: Pixabay (free license)\nℹ️ {FOOT}\n\n{p["tags"]}'
        open(os.path.join(od, "caption.txt"), "w", encoding="utf-8").write(cap)
        json.dump({"slug": p["slug"], "date": p["date"], "time": p["time"], "images": total, "photos": credits}, open(os.path.join(od, "meta.json"), "w"), ensure_ascii=False, indent=1)
        print("built", p["slug"], total)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode"); a = ap.parse_args()
    posts = json.load(open(os.path.join(HERE, "busan_posts.json"), encoding="utf-8"))
    if a.mode == "cands": cands(posts)
    else: build(posts, json.load(open(os.path.join(HERE, "busan_photos.json"))))
