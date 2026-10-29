#!/usr/bin/env python3
"""生成应用图标 v2：靛蓝→紫罗兰渐变底 + 白色闪电（4x 超采样抗锯齿）。
输出: assets/icon/icon.png, assets/icon/icon_fg.png（安卓自适应前景），
以及 iOS 启动图 LaunchImage{,@2x,@3x}.png。"""
from PIL import Image, ImageDraw, ImageFont

S = 4096          # 超采样画布
OUT = 1024        # 输出尺寸
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"

C_TOP = (79, 70, 229)     # indigo-600
C_BOT = (139, 92, 246)    # violet-500
C_DEEP = (30, 27, 75)     # indigo-950（阴影/装饰）


def gradient(size, top, bottom):
    g = Image.new("RGB", (size, size))
    gd = ImageDraw.Draw(g)
    for y in range(size):
        t = y / (size - 1)
        gd.line([(0, y), (size, y)],
                fill=(int(top[0] + (bottom[0] - top[0]) * t),
                      int(top[1] + (bottom[1] - top[1]) * t),
                      int(top[2] + (bottom[2] - top[2]) * t)))
    return g


BOLT = [(0.585, 0.045), (0.235, 0.565), (0.455, 0.565),
        (0.375, 0.955), (0.775, 0.425), (0.545, 0.425)]


def bolt_draw(d, size, fill, offset=(0, 0), scale=1.0, center=(0.5, 0.5)):
    # BOLT 归一化框约 0.40x0.91，按 scale 缩放并平移到 center
    pts = []
    for x, y in BOLT:
        bx = (x - 0.5) * 0.40 * scale * size + center[0] * size + offset[0]
        by = (y - 0.5) * 0.91 * scale * size + center[1] * size + offset[1]
        pts.append((bx, by))
    d.polygon(pts, fill=fill)


def braces_draw(d, size, fill, center_x, glyph, font):
    bbox = d.textbbox((0, 0), glyph, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((center_x - w / 2 - bbox[0], (size - h) / 2 - bbox[3] - h * 0.04), glyph, font=font, fill=fill)


def make_icon():
    img = gradient(S, C_TOP, C_BOT).convert("RGBA")

    # 极淡的大圆光晕，避免生硬边缘
    halo = Image.new("L", (S, S), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([S * 0.35, -S * 0.45, S * 1.65, S * 0.8], fill=20)
    white = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    img.paste(white, (0, 0), halo)

    d = ImageDraw.Draw(img)
    # 白色花括号 { }（代码意象），垂直居中环抱
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", int(S * 0.34))
    braces_draw(d, S, (250, 251, 255, 240), S * 0.20, "{", font)
    braces_draw(d, S, (250, 251, 255, 240), S * 0.80, "}", font)
    # 闪电：深靛投影 + 白色主体，居中偏右让视觉平衡
    bolt_draw(d, S, (30, 27, 75, 255), offset=(S * 0.008, S * 0.014), scale=0.72, center=(0.515, 0.5))
    bolt_draw(d, S, (250, 251, 255, 255), scale=0.72, center=(0.5, 0.5))

    return img.resize((OUT, OUT), Image.LANCZOS)


def make_foreground():
    img = Image.new("RGBA", (OUT, OUT), (0, 0, 0, 0))
    bolt_draw(ImageDraw.Draw(img), OUT, (255, 255, 255, 255))
    return img


def make_launch(scale):
    size = 300 * scale
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # 渐变圆底
    grad = gradient(size, C_TOP, C_BOT)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([size * 0.04, size * 0.04, size * 0.96, size * 0.96], fill=255)
    img.paste(grad, (0, 0), mask)
    bolt_draw(ImageDraw.Draw(img), size, (255, 255, 255, 255))
    return img


if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_dir = os.path.join(root, "assets", "icon")
    os.makedirs(icon_dir, exist_ok=True)
    make_icon().save(os.path.join(icon_dir, "icon.png"))
    make_foreground().save(os.path.join(icon_dir, "icon_fg.png"))
    launch_set = os.path.join(root, "ios", "Runner", "Assets.xcassets", "LaunchImage.imageset")
    for scale in (1, 2, 3):
        name = f"LaunchImage{'@%dx' % scale if scale > 1 else ''}.png"
        make_launch(scale).save(os.path.join(launch_set, name))
    print("图标 v2 与启动图已生成 ✓")
