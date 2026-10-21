#!/usr/bin/env python3
"""알아줌 일일 띠별 운세 카드뉴스 생성기.
사용법: python3 make_cards.py content_YYYY-MM-DD.json
출력: out/YYYY-MM-DD/01_cover.png ... 08_closing.png
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = "#FBF6EE"
INK = "#2B2D42"
SUB = "#6B6F85"
FONT_DIR = "/usr/share/fonts/opentype/noto/"


def load_font(weight, size):
    path = FONT_DIR + f"NotoSansCJK-{weight}.ttc"
    for idx in range(5):
        try:
            f = ImageFont.truetype(path, size, index=idx)
            if "KR" in f.getname()[0]:
                return f
        except Exception:
            continue
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def center(draw, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(color, amt=0.88):
    r, g, b = hex_rgb(color)
    return tuple(int(c + (255 - c) * amt) for c in (r, g, b))


def footer(draw, page, total, brand, y=None):
    f = load_font("Medium", 30)
    y = H - 125 if y is None else y
    draw.text((100, y), brand, font=f, fill=SUB)
    t = f"{page} / {total}"
    draw.text((W - 100 - draw.textlength(t, font=f), y), t, font=f, fill=SUB)


def cover(d, total):
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((50, 50, W - 50, H - 50), 48, outline="#E4D9C6", width=4)
    center(dr, 150, d["date_label"], load_font("Medium", 44), SUB)
    center(dr, 290, d["today_title"], load_font("Black", 96), INK)
    center(dr, 430, f"오늘의 일진  {d['ilgin']}  ({d['ilgin_ko']})", load_font("Medium", 46), "#B8892E")
    # 6 hanja circles (3x2)
    cx0, cy0, gap, r = 270, 640, 270, 90
    for i, c in enumerate(d["cards"]):
        cx = cx0 + (i % 3) * gap
        cy = cy0 + (i // 3) * 250
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tint(c["color"], 0.78), outline=c["color"], width=5)
        fh = load_font("Bold", 84)
        w = dr.textlength(c["hanja"], font=fh)
        dr.text((cx - w / 2, cy - 62), c["hanja"], font=fh, fill=c["color"])
        fa = load_font("Medium", 38)
        w = dr.textlength(c["animal"], font=fa)
        dr.text((cx - w / 2, cy + r + 14), c["animal"], font=fa, fill=INK)
    center(dr, 1120, "오늘은 이 6개 띠의 운세예요", load_font("Medium", 44), INK)
    center(dr, 1190, "옆으로 넘겨서 내 띠를 확인해 보세요  →", load_font("Regular", 36), SUB)
    footer(dr, 1, total, d["brand"])
    return img


def card(d, c, page, total):
    col = c["color"]
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    # top accent band
    dr.rectangle((0, 0, W, 24), fill=col)
    dr.text((70, 80), d["date_label"], font=load_font("Medium", 34), fill=SUB)
    t = f"{d['ilgin']}日"
    fw = load_font("Medium", 34)
    dr.text((W - 70 - dr.textlength(t, font=fw), 80), t, font=fw, fill=SUB)
    # hanja circle
    cx, cy, r = W // 2, 330, 150
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tint(col, 0.78), outline=col, width=6)
    fh = load_font("Bold", 150)
    w = dr.textlength(c["hanja"], font=fh)
    dr.text((cx - w / 2, cy - 105), c["hanja"], font=fh, fill=col)
    # animal name + years
    center(dr, 510, f"{c['animal']}띠", load_font("Black", 92), INK)
    center(dr, 628, c["years"], load_font("Regular", 32), SUB)
    # keyword chip
    kf = load_font("Bold", 38)
    kw = dr.textlength(c["keyword"], font=kf)
    x0 = (W - kw) / 2 - 36
    dr.rounded_rectangle((x0, 700, x0 + kw + 72, 770), 35, fill=col)
    dr.text((x0 + 36, 708), c["keyword"], font=kf, fill="white")
    # summary
    sf = load_font("Bold", 50)
    y = 800
    for ln in wrap(dr, c["summary"], sf, W - 160):
        center(dr, y, ln, sf, INK)
        y += 74
    # body
    bf = load_font("Regular", 37)
    y += 10
    for ln in wrap(dr, c["body"], bf, W - 180):
        center(dr, y, ln, bf, "#43465C")
        y += 58
    # tip box
    ty = H - 215
    dr.rounded_rectangle((90, ty, W - 90, ty + 110), 28, fill=tint(col, 0.86))
    tf = load_font("Medium", 36)
    tl = wrap(dr, "“" + c["tip"] + "”", tf, W - 260)
    yy = ty + (110 - 50 * len(tl)) / 2
    for ln in tl:
        center(dr, yy, ln, tf, col)
        yy += 50
    footer(dr, page, total, d["brand"], y=H - 70)
    return img


def closing(d, total):
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((50, 50, W - 50, H - 50), 48, outline="#E4D9C6", width=4)
    center(dr, 230, "내일은", load_font("Medium", 50), SUB)
    center(dr, 330, "나머지 6개 띠의 차례예요", load_font("Black", 70), INK)
    names = "  ".join(d["tomorrow_animals"][:3]) + "\n" + "  ".join(d["tomorrow_animals"][3:])
    f = load_font("Bold", 64)
    y = 520
    for ln in names.split("\n"):
        center(dr, y, ln, f, "#B8892E")
        y += 100
    center(dr, 790, "저장해 두고 내일 다시 만나요", load_font("Medium", 44), INK)
    center(dr, 870, "프로필 링크에서 더 자세한 풀이도 볼 수 있어요", load_font("Regular", 34), SUB)
    center(dr, 1040, d["brand"], load_font("Black", 84), INK)
    for i, ln in enumerate(wrap(dr, d["disclaimer"], load_font("Regular", 30), W - 200)):
        center(dr, 1180 + i * 44, ln, load_font("Regular", 30), SUB)
    footer(dr, total, total, d["brand"])
    return img


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    out = os.path.join(os.path.dirname(os.path.abspath(path)), "out", d["date"])
    os.makedirs(out, exist_ok=True)
    total = len(d["cards"]) + 2
    cover(d, total).save(os.path.join(out, "01_cover.png"))
    for i, c in enumerate(d["cards"], start=2):
        card(d, c, i, total).save(os.path.join(out, f"{i:02d}_{c['hanja']}.png"))
    closing(d, total).save(os.path.join(out, f"{total:02d}_closing.png"))
    print("saved to", out)


if __name__ == "__main__":
    main(sys.argv[1])
