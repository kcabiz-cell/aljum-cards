#!/usr/bin/env python3
"""12띠 한 장 카드(1080x1350). 사용: python3 -I make_card12.py tools/content12_DATE.json out.png"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_cards import W, H, BG, INK, SUB, load_font, center, tint

ORDER = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]


def render(d):
    img = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(img)
    dr.rounded_rectangle((40, 40, W - 40, H - 40), 44, outline="#E4D9C6", width=4)
    center(dr, 78, d["date_label"], load_font("Medium", 32), SUB)
    center(dr, 125, "오늘의 띠별 운세", load_font("Black", 70), INK)
    center(dr, 222, f"오늘의 일진  {d['ilgin']}  ({d['ilgin_ko']})", load_font("Medium", 34), "#B8892E")
    by = {c["animal"]: c for c in d["items"]}
    x0, y0, cw, ch = 70, 290, 470, 148
    for i, an in enumerate(ORDER):
        c = by[an]; col = c["color"]
        x = x0 + (i % 2) * cw; y = y0 + (i // 2) * (ch + 8)
        dr.rounded_rectangle((x, y, x + cw - 12, y + ch - 6), 26, fill=tint(col, 0.88))
        sd = os.path.join(HERE, "animals", d.get("animal_set", ""))
        ip = os.path.join(sd, f"{an}.png")
        if not os.path.exists(ip): ip = os.path.join(HERE, "animals", f"{an}.png")
        ic = Image.open(ip); ic.thumbnail((112, 112), Image.LANCZOS)
        img.paste(ic, (x + 16 + (112 - ic.width) // 2, y + (ch - 6 - ic.height) // 2), ic)
        dr.text((x + 148, y + 26), f"{an}띠", font=load_font("Black", 38), fill=INK)
        f = load_font("Medium", 27); t = c["line"]
        while dr.textlength(t, font=f) > cw - 12 - 148 - 12: f = load_font("Medium", f.size - 1)
        dr.text((x + 148, y + 82), t, font=f, fill="#43465C")
    center(dr, H - 135, "재미로 보는 오늘의 운세예요. 선택과 판단은 언제나 나의 몫이에요.", load_font("Regular", 25), SUB)
    center(dr, H - 95, "알아줌 · @arajum_saju", load_font("Medium", 28), SUB)
    return img


if __name__ == "__main__":
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
    render(d).save(sys.argv[2]); print(sys.argv[2])
