import os
import re
import random
import aiofiles
import aiohttp

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch

from config import YOUTUBE_IMG_URL


def truncate(text, max_len=28):
    words = text.split()
    lines = ["", ""]
    i = 0
    for word in words:
        if len(lines[i]) + len(word) + 1 <= max_len:
            lines[i] += (" " if lines[i] else "") + word
        elif i == 0:
            i = 1
    return lines


def circular_crop(img, size, border, color):
    inner = size - 2 * border
    img = img.resize((inner, inner), Image.LANCZOS)

    mask = Image.new("L", (inner, inner), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, inner, inner), 255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg = Image.new("RGBA", (size, size), color)
    output.paste(bg, (0, 0))

    output.paste(img, (border, border), mask)
    return output


def draw_text(draw, pos, text, font, fill):
    x, y = pos
    draw.text((x + 2, y + 2), text, font=font, fill="black")
    draw.text(pos, text, font=font, fill=fill)


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

        # 🎬 Cinematic Background
        bg = base.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        overlay = Image.new("RGBA", thumb_size, (0, 0, 0, 160))
        bg = Image.alpha_composite(bg, overlay)

        draw = ImageDraw.Draw(bg)

        font_title = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 55)
        font_small = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 32)
        font_badge = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 28)

        # 💿 Album Circle
        cover = Image.open(temp_path).convert("RGBA")
        circle = circular_crop(cover, 420, 15, (255, 255, 255))

        glow = circle.filter(ImageFilter.GaussianBlur(30))
        bg.paste(glow, (100, 140), glow)
        bg.paste(circle, (120, 160), circle)

        # 🏷 NOW PLAYING Badge
        draw.rounded_rectangle(
            (90, 70, 320, 120),
            radius=18,
            fill=(255, 0, 90)
        )
        draw_text(draw, (120, 82), "NOW PLAYING", font_badge, "white")

        # 📝 Text Layout
        x = 620
        t1, t2 = truncate(title)

        draw_text(draw, (x, 200), t1, font_title, "white")
        draw_text(draw, (x, 265), t2, font_title, "white")

        draw_text(draw, (x, 340), f"🎵 {channel}", font_small, "#cccccc")
        draw_text(draw, (x, 380), f"👁 {views}", font_small, "#aaaaaa")

        # 🎧 Progress Bar
        bar_x = x
        bar_y = 460
        bar_width = 600
        bar_height = 16

        progress = random.uniform(0.2, 0.8)
        fill_width = int(bar_width * progress)

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
            radius=10,
            fill=(70, 70, 70)
        )

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + fill_width, bar_y + bar_height),
            radius=10,
            fill=(255, 0, 90)
        )

        # ⏱ Time
        draw_text(draw, (bar_x, bar_y + 35), "00:00", font_small, "white")
        draw_text(draw, (bar_x + bar_width - 100, bar_y + 35), duration, font_small, "white")

        bg.save(path)
        os.remove(temp_path)

        return path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
