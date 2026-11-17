# -*- coding: utf-8 -*-
"""
相似度函数篇 · 配图生成脚本
只依赖 Pillow，无 matplotlib / 无网络。
所有尺寸按最终像素设计，绘制时乘 SS 超采样，最后 LANCZOS 缩回，得到抗锯齿效果。

用法: python make_figs.py
输出: ./img/fig1..fig4*.png
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

SS = 3
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
os.makedirs(OUT, exist_ok=True)

BG      = "#FFFFFF"
INK     = "#1F2328"
MUTED   = "#6E7781"
GRID    = "#E6E8EB"
BLUE    = "#2563EB"
BLUE_L  = "#DBEAFE"
ORANGE  = "#EA580C"
ORANGE_L= "#FFEDD5"
TEAL    = "#0D9488"
TEAL_L  = "#CCFBF1"
PURPLE  = "#7C3AED"
PURPLE_L= "#EDE9FE"
GRAY_B  = "#C3C9D1"
GREEN   = "#15803D"
GREEN_L = "#F0FDF4"
GREEN_D = "#86EFAC"

FONT_REG = next((p for p in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"] if os.path.exists(p)), None)
FONT_BOLD = next((p for p in [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"] if os.path.exists(p)), FONT_REG)
if FONT_REG is None:
    raise SystemExit("找不到中文字体")


def F(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, int(size * SS))


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (int(w * SS), int(h * SS)), (255, 255, 255, 255))
        self.d = ImageDraw.Draw(self.im)

    def s(self, v):
        return v * SS

    def line(self, xy, fill=INK, width=2, dash=None):
        pts = [(self.s(x), self.s(y)) for x, y in xy]
        if dash:
            for a, b in zip(pts[:-1], pts[1:]):
                self._dash(a, b, fill, width, dash)
        else:
            self.d.line(pts, fill=fill, width=max(1, int(width * SS)), joint="curve")

    def _dash(self, a, b, fill, width, dash):
        (x1, y1), (x2, y2) = a, b
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            return
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        on, off = dash[0] * SS, dash[1] * SS
        t = 0.0
        while t < L:
            t2 = min(t + on, L)
            self.d.line([(x1 + ux * t, y1 + uy * t), (x1 + ux * t2, y1 + uy * t2)],
                        fill=fill, width=max(1, int(width * SS)))
            t = t2 + off

    def circle(self, c, r, fill=None, outline=None, width=2):
        self.d.ellipse([self.s(c[0] - r), self.s(c[1] - r), self.s(c[0] + r), self.s(c[1] + r)],
                       fill=fill, outline=outline, width=int(width * SS))

    def poly(self, pts, fill=None, outline=None, width=2):
        pp = [(self.s(x), self.s(y)) for x, y in pts]
        self.d.polygon(pp, fill=fill)
        if outline:
            self.d.line(pp + [pp[0]], fill=outline, width=int(width * SS), joint="curve")

    def rect(self, box, radius=10, fill=None, outline=None, width=2, dash=None):
        x1, y1, x2, y2 = [self.s(v) for v in box]
        if dash:
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
            for a, b in zip(pts[:-1], pts[1:]):
                self._dash(a, b, outline, width, dash)
        else:
            self.d.rounded_rectangle([x1, y1, x2, y2], radius=self.s(radius),
                                     fill=fill, outline=outline, width=int(width * SS))

    def text(self, xy, s, size=22, fill=INK, anchor="la", bold=False):
        self.d.text((self.s(xy[0]), self.s(xy[1])), s, font=F(size, bold), fill=fill, anchor=anchor)

    def text_rot(self, center, s, size=21, fill=MUTED, bold=False):
        """竖排旋转文字，中心定位"""
        f = F(size, bold)
        bb = self.d.textbbox((0, 0), s, font=f)
        pad = 12 * SS
        tmp = Image.new("RGBA", (int(bb[2] - bb[0] + pad * 2), int(bb[3] - bb[1] + pad * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((pad - bb[0], pad - bb[1]), s, font=f, fill=fill)
        tmp = tmp.rotate(90, expand=True, resample=Image.BICUBIC)
        self.im.alpha_composite(tmp, (int(center[0] * SS - tmp.width / 2), int(center[1] * SS - tmp.height / 2)))

    def arrow(self, p1, p2, fill=INK, width=2, head=12, dash=None):
        (x1, y1), (x2, y2) = p1, p2
        ang = math.atan2(y2 - y1, x2 - x1)
        sx, sy = x2 - math.cos(ang) * head, y2 - math.sin(ang) * head
        self.line([(x1, y1), (sx, sy)], fill=fill, width=width, dash=dash)
        l = (sx - math.sin(ang) * head * 0.6, sy + math.cos(ang) * head * 0.6)
        r = (sx + math.sin(ang) * head * 0.6, sy - math.cos(ang) * head * 0.6)
        self.poly([(x2, y2), l, r], fill=fill)

    def save(self, name):
        p = os.path.join(OUT, name)
        self.im.convert("RGB").resize((int(self.w), int(self.h)), Image.LANCZOS).save(p, quality=95)
        print("saved", p)


def title(c, txt, sub):
    c.text((54, 38), txt, 33, INK, bold=True)
    c.text((54, 84), sub, 20, MUTED)


# ============================================================
# 图 1
# ============================================================
def fig_metric():
    c = Canvas(1400, 740)
    title(c, "归一化之后，余弦相似度与 L2 距离严格单调对应",
          "左边是几何事实，右边是工程后果：换度量不改变排序，只改变数值")

    cx, cy, r = 380, 420, 205
    c.circle((cx, cy), r, outline=GRID, width=2)
    c.line([(cx - r - 40, cy), (cx + r + 40, cy)], GRID, 1.2)
    c.line([(cx, cy - r - 40), (cx, cy + r + 40)], GRID, 1.2)

    aA, bA = 12, 67
    ax, ay = cx + r * math.cos(math.radians(aA)), cy - r * math.sin(math.radians(aA))
    bx, by = cx + r * math.cos(math.radians(bA)), cy - r * math.sin(math.radians(bA))

    rr = 96
    c.d.arc([c.s(cx - rr), c.s(cy - rr), c.s(cx + rr), c.s(cy + rr)], -bA, -aA,
            fill=TEAL, width=int(2.6 * SS))
    mid = math.radians((aA + bA) / 2)
    c.text((cx + 142 * math.cos(mid), cy - 142 * math.sin(mid)), "θ", 25, TEAL, anchor="mm", bold=True)

    c.line([(ax, ay), (bx, by)], ORANGE, 3)

    c.arrow((cx, cy), (ax, ay), BLUE, 3.5, head=13)
    c.arrow((cx, cy), (bx, by), BLUE, 3.5, head=13)

    # 弦标签放在弦的外法线方向，避开端点与角度弧
    mx, my = (ax + bx) / 2, (ay + by) / 2
    nx, ny = (mx - cx) / math.hypot(mx - cx, my - cy), (my - cy) / math.hypot(mx - cx, my - cy)
    c.text((mx + nx * 52, my + ny * 52), "‖a−b‖", 20, ORANGE, anchor="lm", bold=True)
    c.circle((ax, ay), 5, BLUE)
    c.circle((bx, by), 5, BLUE)
    c.text((ax + 14, ay + 8), "a", 23, BLUE, anchor="lm", bold=True)
    c.text((bx - 22, by - 18), "b", 23, BLUE, anchor="rm", bold=True)
    c.text((cx - 18, cy + 14), "O", 19, MUTED, anchor="rm")
    c.text((72, 668), "‖a‖ = ‖b‖ = 1，两个端点都落在单位圆上", 19, MUTED)

    ox, oy, pw, ph = 880, 590, 370, 380

    def X(t):
        return ox + (t + 1) / 2 * pw

    def Y(v):
        return oy - v / 4.3 * ph

    c.line([(ox, oy), (ox + pw + 20, oy)], INK, 2)
    c.line([(ox, oy), (ox, oy - ph - 20)], INK, 2)
    c.text((ox + pw / 2, oy + 52), "cos(a, b)", 20, INK, anchor="mm")
    c.text((ox + 6, oy - ph - 44), "‖a−b‖²", 20, INK, anchor="lm")

    c.line([(X(-1), Y(4)), (X(1), Y(0))], PURPLE, 3.5)
    for t in (-1, 0, 1):
        c.circle((X(t), Y(2 - 2 * t)), 5, PURPLE)
        c.text((X(t), oy + 24), f"{t}", 18, MUTED, anchor="mm")
    for v in (0, 2, 4):
        c.text((ox - 14, Y(v)), f"{v}", 18, MUTED, anchor="rm")

    cv = math.cos(math.radians(55))
    px, py = X(cv), Y(2 - 2 * cv)
    c.line([(px, oy), (px, py)], ORANGE, 1.4, dash=(5, 5))
    c.line([(ox, py), (px, py)], ORANGE, 1.4, dash=(5, 5))
    c.circle((px, py), 6, ORANGE)
    # 注释放绘图区右上方空白，用引线连到点，避免压住曲线
    c.line([(1018, 330), (px - 6, py - 8)], MUTED, 1.2, dash=(4, 4))
    c.text((1032, 292), f"cos 55° = {cv:.3f}", 18, ORANGE, anchor="la", bold=True)
    c.text((1032, 314), f"‖a−b‖² = {2 - 2 * cv:.3f}", 18, ORANGE, anchor="la", bold=True)

    c.text((880, 674), "斜率恒为 −2，不存在交叉或排序反转", 19, MUTED)
    c.save("fig1_metric_equivalence.png")


# ============================================================
# 图 2
# ============================================================
def fig_temperature():
    c = Canvas(1400, 720)
    title(c, "温度 τ 决定梯度落在谁身上",
          "同一个正样本、同一批负样本，只改 τ，负样本分到的权重完全不同")

    scores = [0.62, 0.58, 0.51, 0.47, 0.40, 0.33, 0.28, 0.20]
    labels = ["正", "n1", "n2", "n3", "n4", "n5", "n6", "n7"]
    taus = [0.07, 0.20, 1.00]
    panel_w, gap, left0 = 396, 56, 62
    top, bot, ymax = 236, 556, 0.60

    for pi, tau in enumerate(taus):
        x0 = left0 + pi * (panel_w + gap)
        ex = [math.exp(s / tau) for s in scores]
        Z = sum(ex)
        p = [e / Z for e in ex]

        c.line([(x0, bot), (x0 + panel_w, bot)], INK, 2)
        c.line([(x0, top), (x0, bot)], GRID, 2)
        yv = bot - 0.5 / ymax * (bot - top)
        c.line([(x0, yv), (x0 + panel_w, yv)], GRID, 1, dash=(4, 6))
        c.text((x0 - 10, yv), "0.5", 15, MUTED, anchor="rm")

        step = panel_w / len(scores)
        bw = step * 0.58
        for i, pv in enumerate(p):
            bx = x0 + step * i + step / 2
            hgt = pv / ymax * (bot - top)
            color = BLUE if i == 0 else (ORANGE if i == 1 else GRAY_B)
            c.rect([bx - bw / 2, bot - hgt, bx + bw / 2, bot], radius=4, fill=color)
            if i <= 1:
                c.text((bx, bot - hgt - 15), f"{pv:.2f}", 16, color, anchor="mm", bold=True)
            c.text((bx, bot + 24), labels[i], 16, MUTED, anchor="mm")

        c.text((x0 + panel_w / 2, top - 52), f"τ = {tau}", 23, INK, anchor="mm", bold=True)
        c.text((x0 + panel_w / 2, top - 22), f"最难负样本权重 {p[1]:.2f}", 16, MUTED, anchor="mm")

    c.text((62, 636), "τ 小 → 梯度几乎只推最像的那条负样本，模型被迫分辨细节，但训练容易抖", 20, ORANGE)
    c.text((62, 674), "τ 大 → 所有负样本被均匀地推，表示更均匀更稳，但难样本被淹没", 20, TEAL)

    lx = 1150
    c.rect([lx, 40, lx + 22, 62], radius=4, fill=BLUE)
    c.text((lx + 32, 40), "正样本", 18, MUTED)
    c.rect([lx, 74, lx + 22, 96], radius=4, fill=ORANGE)
    c.text((lx + 32, 74), "最难负样本", 18, MUTED)
    c.save("fig3_temperature.png")


# ============================================================
# 图 3
# ============================================================
def fig_negatives():
    c = Canvas(1200, 780)
    title(c, "负样本不是越贵越好，是越干净越好",
          "气泡大小 = 假负样本风险。成本几乎为零的地方，风险恰好最高")

    ox, oy, pw, ph = 170, 620, 800, 430

    def X(v):
        return ox + v * pw

    def Y(v):
        return oy - v * ph

    c.line([(ox, oy), (ox + pw + 30, oy)], INK, 2)
    c.line([(ox, oy), (ox, oy - ph - 26)], INK, 2)
    c.text((ox + pw / 2, oy + 56), "构造成本 →", 20, INK, anchor="mm")
    c.text_rot((ox - 40, oy - ph / 2), "负样本难度 →", 18)

    c.rect([X(0.30), Y(0.90), X(0.70), Y(0.66)], radius=14, fill="#ECFDF5")
    c.text((X(0.305), 204), "性价比区间", 18, GREEN, anchor="la", bold=True)

    pts = [
        ("batch 内负样本",  0.08, 0.34, 0.92, BLUE,   "right"),
        ("随机负样本",      0.15, 0.10, 0.22, BLUE,   "right"),
        ("MoCo 队列",       0.24, 0.44, 0.78, BLUE,   "right"),
        ("BM25 top-k",      0.34, 0.80, 0.52, ORANGE, "right"),
        ("BM25 + 重排过滤", 0.62, 0.73, 0.14, ORANGE, "right"),
        ("ANCE 异步索引",   0.80, 0.93, 0.40, TEAL,   "right"),
        ("LLM 改写生成",    0.88, 0.56, 0.34, PURPLE, "right"),
    ]
    for name, xv, yv, risk, col, side in pts:
        px, py = X(xv), Y(yv)
        r = 15 + risk * 32
        c.circle((px, py), r, outline=col, width=3)
        c.circle((px, py), r * 0.32, fill=col)
        c.text((px + r + 12, py - 9), name, 18, INK, anchor="la")

    # 气泡大小图例
    lx, ly = 800, 500
    c.circle((lx, ly), 12, outline=MUTED, width=2)
    c.text((lx + 24, ly - 9), "低", 16, MUTED)
    c.circle((lx + 96, ly), 26, outline=MUTED, width=2)
    c.text((lx + 128, ly - 9), "高", 16, MUTED)
    c.text((lx - 6, ly - 56), "假负样本风险", 16, MUTED)

    c.text((170, 706), "零成本那端的风险来自语料重复：同一篇文档被切成两个 chunk，会被当成负样本推远", 18, MUTED)
    c.save("fig4_negative_sources.png")


# ============================================================
# 图 4
# ============================================================
def fig_pipeline():
    c = Canvas(1600, 700)
    title(c, "检索链路上，相似度函数落在哪几个位置",
          "双路召回 + 融合 + 重排，每一层用的度量并不相同")

    def box(x, y, w, h, label, sub=None, color=INK, fill="#F6F8FA"):
        c.rect([x, y, x + w, y + h], radius=12, fill=fill, outline=color, width=2)
        cy = y + h / 2
        if sub:
            c.text((x + w / 2, cy - 13), label, 20, color, anchor="mm", bold=True)
            c.text((x + w / 2, cy + 15), sub, 15, MUTED, anchor="mm")
        else:
            c.text((x + w / 2, cy), label, 20, color, anchor="mm", bold=True)

    y1, h1 = 300, 84
    box(60, y1, 150, h1, "Query")
    box(280, y1, 200, h1, "Encoder", "双塔 / bi-encoder", BLUE, BLUE_L)
    box(550, y1, 220, h1, "L2 归一化", "除以模长", BLUE, BLUE_L)
    box(840, y1, 240, h1, "向量库 IP 检索", "faiss / milvus", BLUE, BLUE_L)
    for x1, x2 in [(212, 278), (482, 548), (772, 838)]:
        c.arrow((x1, y1 + h1 / 2), (x2, y1 + h1 / 2), INK, 2)

    y2 = 500
    box(550, y2, 220, h1, "BM25 倒排", "词法精确匹配", ORANGE, ORANGE_L)
    box(840, y2, 240, h1, "RRF 融合", "按名次加权，k=60", TEAL, TEAL_L)
    box(1150, y2, 220, h1, "Cross-encoder", "重排，精度换延迟", PURPLE, PURPLE_L)
    box(1430, y2, 150, h1, "Top-k")

    # Query 到 BM25 的支路
    c.line([(135, y1 + h1), (135, y2 + h1 / 2)], ORANGE, 2, dash=(6, 5))
    c.arrow((135, y2 + h1 / 2), (546, y2 + h1 / 2), ORANGE, 2, dash=(6, 5))

    # 向量库 -> RRF
    c.arrow((960, y1 + h1 + 4), (960, y2 - 4), TEAL, 2)
    # BM25 -> RRF
    c.arrow((772, y2 + h1 / 2), (838, y2 + h1 / 2), INK, 2)
    # RRF -> CE -> Top-k
    c.arrow((1082, y2 + h1 / 2), (1148, y2 + h1 / 2), INK, 2)
    c.arrow((1372, y2 + h1 / 2), (1428, y2 + h1 / 2), INK, 2)

    # 一致性提示
    c.rect([266, y1 - 44, 784, y1 + h1 + 18], radius=14, outline="#F87171", width=2, dash=(7, 6))
    c.text((525, y1 - 78), "训练与推理必须一致：同一个 encoder、同一套归一化", 18, "#B91C1C", anchor="mm")

    c.text((60, 636), "稠密通道管语义泛化（手机 / iPhone），稀疏通道管精确命中（型号、专有名词）",
           19, MUTED)
    c.text((60, 672), "两路分数量纲不同，不能直接相加，所以用 RRF 按名次融合", 19, MUTED)
    c.save("fig2_retrieval_pipeline.png")


if __name__ == "__main__":
    from PIL import __version__ as v
    print("Pillow", v, "| font:", os.path.basename(FONT_REG))
    fig_metric()       # 图 1
    fig_pipeline()     # 图 2
    fig_temperature()  # 图 3
    fig_negatives()    # 图 4
