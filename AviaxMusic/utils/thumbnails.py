import os
import re
import random
import aiofiles
import aiohttp

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch

from config import YOUTUBE_IMG_URL


def truncate(text, max_len=30):
    words = text.split()
    lines = ["", ""]
    i = 0
    for word in words:
        if len(lines[i]) + len(word) + 1 <= max_len:
            lines[i] += (" " if lines[i] else "") + word
        elif i == 0:
            i = 1
    return lines


def circular_crop(img, size, border):
    inner = size - 2 * border
    img = img.resize((inner, inner), Image.LANCZOS)

    mask = Image.new("L", (inner, inner), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, inner, inner), 255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (border, border), mask)
    return output


def draw_text(draw, pos, text, font, fill):
    x, y = pos
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 180))
    draw.text(pos, text, font=font, fill=fill)


def create_glass_panel(base, box, radius=30):
    x1, y1, x2, y2 = box

    panel = base.crop(box).filter(ImageFilter.GaussianBlur(25))

    overlay = Image.new("RGBA", (x2 - x1, y2 - y1), (255, 255, 255, 60))
    panel = Image.alpha_composite(panel.convert("RGBA"), overlay)

    mask = Image.new("L", (x2 - x1, y2 - y1), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, x2 - x1, y2 - y1),
        radius=radius,
        fill=255
    )

    base.paste(panel, (x1, y1), mask)

    border_draw = ImageDraw.Draw(base)
    border_draw.rounded_rectangle(
        box,
        radius=radius,
        outline=(255, 255, 255, 120),
        width=2
    )


async def gen_thumb(videoid: str, thumb_size=(1280, 720)):
    os.makedirs("cache", exist_ok=True)
    path = f"cache/{videoid}.png"

    if os.path.isfile(path):
        return path

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        data = (await results.next())["result"][0]

        title = re.sub(r"\W+", " ", data.get("title", "Unsupported")).title()
        duration = data.get("duration") or "00:00"
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "Unknown Channel")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                content = await resp.read()

        temp_path = f"cache/temp_{videoid}.jpg"
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)

        base = Image.open(temp_path).convert("RGBA")
        base = base.resize(thumb_size, Image.LANCZOS)

        # 🎬 Background Blur
        bg = base.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.5)

        dark_overlay = Image.new("RGBA", thumb_size, (0, 0, 0, 120))
        bg = Image.alpha_composite(bg, dark_overlay)

        draw = ImageDraw.Draw(bg)

        font_title = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 55)
        font_small = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 32)

        # 💿 Album Cover Left
        cover = Image.open(temp_path).convert("RGBA")
        circle = circular_crop(cover, 420, 10)

        glow = circle.filter(ImageFilter.GaussianBlur(25))
        bg.paste(glow, (110, 150), glow)
        bg.paste(circle, (130, 170), circle)

        # 💎 Glass Panel Right
        panel_box = (550, 150, 1180, 570)
        create_glass_panel(bg, panel_box)

        # 📝 Text inside panel
        x = 600
        t1, t2 = truncate(title)

        draw_text(draw, (x, 220), t1, font_title, "white")
        draw_text(draw, (x, 285), t2, font_title, "white")

        draw_text(draw, (x, 360), f"{channel}", font_small, "#dddddd")
        draw_text(draw, (x, 400), f"{views}", font_small, "#bbbbbb")

        # 🎧 Thin Premium Progress Line
        bar_x = x
        bar_y = 470
        bar_width = 520

        progress = random.uniform(0.2, 0.8)
        fill_width = int(bar_width * progress)

        draw.line(
            (bar_x, bar_y, bar_x + bar_width, bar_y),
            fill=(200, 200, 200, 120),
            width=4
        )

        draw.line(
            (bar_x, bar_y, bar_x + fill_width, bar_y),
            fill=(255, 255, 255),
            width=4
        )

        draw_text(draw, (bar_x, bar_y + 20), "00:00", font_small, "white")
        draw_text(draw, (bar_x + bar_width - 100, bar_y + 20), duration, font_small, "white")

        bg.save(path)
        os.remove(temp_path)

        return path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
