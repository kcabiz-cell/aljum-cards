"""저작권 없는 자체 생성 배경 장면 (구름 하늘, 노을 바다, 산 능선, 숲, 달밤 하늘, 별 우주). 전부 코드로 직접 그림."""
import numpy as np
from PIL import Image, ImageFilter

def _lerp(c1, c2, t):
    return np.array(c1, np.float32) * (1 - t)[..., None] + np.array(c2, np.float32) * t[..., None]

def _noise(w, h, scale, seed, octaves=5):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gw, gh = max(2, int(w / scale * 2 ** o)), max(2, int(h / scale * 2 ** o))
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        tot += amp; amp *= 0.5
    return out / tot

def _grad(w, h, stops):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
    img = np.zeros((h, w, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (y >= p0) & (y <= p1)
        t = np.clip((y - p0) / (p1 - p0), 0, 1)
        img[m] = _lerp(c0, c1, t)[m]
    return img

def _glow(w, h, cx, cy, r, color, strength):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return (np.exp(-d * d * 2.2) * strength)[..., None] * np.array(color, np.float32)

def _ridge(w, h, base, amp, seed, scale=420):
    n = _noise(w, 8, scale, seed, 4)[0]
    n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return (base + (n - 0.5) * amp).astype(np.float32)

def _mountains(img, w, h, cols, bases, amp, seed, haze=(255, 235, 225)):
    yy = np.arange(h, dtype=np.float32)[:, None]
    for i, (c, b) in enumerate(zip(cols, bases)):
        top = _ridge(w, h, b * h, amp * h, seed + i * 7)[None, :]
        m = (yy >= top)[..., None]
        fade = np.clip((yy - top) / (0.25 * h), 0, 1)[..., None]
        col = np.array(c, np.float32) * (1 - 0.35 * fade) + np.array(haze, np.float32) * 0.35 * fade
        img = np.where(m, col, img)
    return img

def _stars(img, w, h, seed, n=420, maxy=1.0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, w), int(rng.random() * h * maxy)
        b = rng.random() ** 3 * 200 + 40; r = 1 if rng.random() < 0.85 else 2
        img[max(0, y - r):y + r, max(0, x - r):x + r] = np.minimum(255, img[max(0, y - r):y + r, max(0, x - r):x + r] + b)
    return img

def _clouds(img, w, h, seed, color=(255, 255, 255), cover=0.55, soft=0.22, ymax=0.7):
    n = _noise(w, h, 380, seed, 6)
    a = np.clip((n - cover) / soft, 0, 1) * np.clip(1 - np.linspace(0, 1, h)[:, None] / ymax, 0, 1) ** 0.5
    return img * (1 - a[..., None] * 0.85) + np.array(color, np.float32) * a[..., None] * 0.85

def scene(name, w, h, seed=3):
    """returns (PIL RGB image, text color)"""
    if name == "sky":      # 맑은 아침 하늘 + 구름
        img = _grad(w, h, [(0, (150, 196, 235)), (0.65, (214, 232, 248)), (1, (255, 236, 214))])
        img = _clouds(img, w, h, seed, (255, 255, 255), 0.50, 0.25, 0.95); txt = (52, 66, 92)
    elif name == "sunset_sea":  # 노을 바다
        hz = 0.60
        img = _grad(w, h, [(0, (120, 130, 190)), (0.35, (246, 170, 160)), (hz, (255, 214, 160)), (hz, (255, 200, 150)), (1, (150, 150, 190))])
        img += _glow(w, h, w * 0.5, h * hz, w * 0.45, (255, 214, 160), 0.30)
        sea = np.arange(h)[:, None] > h * hz
        ripple = (_noise(w, h, 90, seed, 3) - 0.5) * 14
        refl = np.exp(-((np.arange(w)[None, :] - w * 0.5) / (w * 0.10)) ** 2) * np.clip((np.arange(h)[:, None] - h * hz) / (h * 0.3), 0, 1) ** 0.4 * 70
        img = np.where(sea[..., None], img + (ripple + refl)[..., None], img)
        img = _clouds(img, w, h, seed + 1, (255, 224, 214), 0.56, 0.2, hz); txt = (84, 52, 66)
    elif name == "mountains":   # 새벽 산 능선
        img = _grad(w, h, [(0, (176, 190, 232)), (0.4, (250, 204, 196)), (0.62, (255, 232, 204)), (1, (255, 240, 222))])
        img += _glow(w, h, w * 0.62, h * 0.52, w * 0.5, (255, 236, 190), 0.5)
        img = _clouds(img, w, h, seed, (255, 240, 236), 0.58, 0.2, 0.55)
        img = _mountains(img, w, h, [(214, 196, 220), (188, 176, 208), (158, 154, 192), (126, 128, 170)], [0.62, 0.70, 0.79, 0.89], 0.10, seed)
        txt = (62, 52, 84)
    elif name == "forest":      # 안개 낀 숲
        img = _grad(w, h, [(0, (214, 236, 226)), (0.5, (236, 246, 232)), (1, (200, 226, 210))])
        img += _glow(w, h, w * 0.5, h * 0.25, w * 0.6, (255, 250, 214), 0.12)
        yy = np.arange(h, dtype=np.float32)[:, None]; xx = np.arange(w, dtype=np.float32)[None, :]
        rng = np.random.default_rng(seed)
        for layer, (col, base, sz) in enumerate([((170, 205, 188), 0.66, 120), ((130, 176, 152), 0.76, 170), ((92, 146, 120), 0.88, 230)]):
            tops = np.full(w, h * 2, np.float32)
            for _ in range(int(w / sz * 2.2)):
                cx = rng.uniform(-50, w + 50); th = sz * rng.uniform(2.2, 3.4); bw = sz * rng.uniform(0.55, 0.8); by = base * h + rng.uniform(-30, 30)
                t = np.clip(1 - np.abs(xx[0] - cx) / bw, 0, 1)
                tops = np.minimum(tops, by - th * t)
            m = (yy >= tops[None, :])[..., None]
            fade = np.clip((yy - tops[None, :]) / (0.3 * h), 0, 1)[..., None]
            c = np.array(col, np.float32) * (1 - 0.3 * fade) + np.array((236, 246, 236), np.float32) * 0.3 * fade
            img = np.where(m, c, img)
        txt = (36, 70, 56)
    elif name == "moon":        # 달빛 하늘 (어둡지 않은 보랏빛 새벽)
        img = _grad(w, h, [(0, (96, 100, 168)), (0.55, (170, 156, 208)), (1, (236, 196, 206))])
        img = _stars(img, w, h, seed, 300, 0.6)
        mx, my = w * 0.70, h * 0.2
        img += _glow(w, h, mx, my, w * 0.45, (255, 246, 214), 0.6)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        disk = np.clip((w * 0.075 - np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)) / 3, 0, 1)
        img = img * (1 - disk[..., None]) + np.array((255, 250, 232), np.float32) * disk[..., None]
        img = _clouds(img, w, h, seed + 2, (236, 220, 240), 0.60, 0.2, 0.9); txt = (255, 252, 244)
    elif name == "space":       # 별 가득한 우주 (성운 + 은하수 결)
        base = _grad(w, h, [(0, (58, 62, 128)), (0.5, (104, 84, 156)), (1, (176, 116, 160))])
        n1 = _noise(w, h, 300, seed, 5); n2 = _noise(w, h, 220, seed + 5, 5)
        band = np.exp(-(((np.linspace(0, 1, w)[None, :] * 0.6 + np.linspace(0, 1, h)[:, None] * 0.4) - 0.55) / 0.16) ** 2)
        neb = np.clip((n1 - 0.4) * 2.2, 0, 1) * band
        img = base + neb[..., None] * np.array((150, 90, 140), np.float32) * 0.9 + (np.clip((n2 - 0.45) * 2.4, 0, 1) * band)[..., None] * np.array((60, 120, 170), np.float32) * 0.8
        img = _stars(img, w, h, seed, 900, 1.0); txt = (255, 250, 240)
    else:
        raise ValueError(name)
    img = np.clip(img + np.random.default_rng(seed).normal(0, 2.2, (h, w, 1)), 0, 255).astype(np.uint8)
    return Image.fromarray(img), txt
