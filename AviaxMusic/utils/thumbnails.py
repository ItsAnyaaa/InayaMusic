import os
import re
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

# Function to pick dominant color (Aesthetic ke liye)
def get_dominant_color(img):
    img = img.copy().resize((1, 1), resample=Image.BICUBIC)
    return img.getpixel((0, 0))

async def gen_thumb(videoid: str, thumb_size=(1280, 720)):
    os.makedirs("cache", exist_ok=True)
    path = f"cache/{videoid}.png"

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        data = (await results.next())["result"][0]

        title = data.get("title", "Unsupported")
        duration = data.get("duration") or "05:00"
        channel = data.get("channel", {}).get("name", "Unknown Artist")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                content = await resp.read()

        temp_path = f"cache/temp_{videoid}.jpg"
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)

        # 1. Background Setup
        base = Image.open(temp_path).convert("RGBA")
        base = base.resize(thumb_size, Image.LANCZOS)
        
        # Dominant Color for Tint
        dom_color = get_dominant_color(base)
        
        # Blurred Background
        bg = base.filter(ImageFilter.GaussianBlur(50))
        bg = ImageEnhance.Brightness(bg).enhance(0.6)

        # 2. Glass Panel with Tint (Image se match karta hua color)
        # Hum card ko background se milta-julta color denge
        card_color = (dom_color[0], dom_color[1], dom_color[2], 100) # Semi-transparent tint
        
        overlay = Image.new("RGBA", thumb_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        card_box = (100, 100, 1180, 620)
        overlay_draw.rounded_rectangle(card_box, radius=50, fill=card_color)
        
        # Border for glass effect
        overlay_draw.rounded_rectangle(card_box, radius=50, outline=(255, 255, 255, 30), width=2)
        
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # 3. Text Styling
        font_title = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 65)
        font_artist = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 45)
        font_small = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 28)

        # Title & Artist (Left Aligned)
        display_title = title[:25] + "..." if len(title) > 25 else title
        draw.text((160, 220), "Spotify", font=font_small, fill=(255, 255, 255, 180))
        draw.text((160, 270), display_title, font=font_title, fill="white")
        draw.text((160, 360), channel, font=font_artist, fill=(255, 255, 255, 200))

        # 4. Improved Music Controls (Brownish/Match color)
        cx, cy = 640, 480
        accent_color = (dom_color[0], dom_color[1], dom_color[2], 255) # Deep color from image

        # Play/Pause Button (Rounded Box)
        draw.rounded_rectangle((cx-45, cy-55, cx+45, cy+55), radius=25, fill=accent_color)
        # Pause Lines
        draw.rectangle((cx-18, cy-35, cx-6, cy+35), fill="white")
        draw.rectangle((cx+6, cy-35, cx+18, cy+35), fill="white")

        # Skip Buttons (Triangles)
        draw.polygon([(cx+140, cy-30), (cx+140, cy+30), (cx+180, cy)], fill=accent_color) # Next
        draw.polygon([(cx-140, cy-30), (cx-140, cy+30), (cx-180, cy)], fill=accent_color) # Prev

        # 5. Progress Bar
        bar_x1, bar_y, bar_x2 = 160, 560, 1120
        draw.line((bar_x1, bar_y, bar_x2, bar_y), fill=(accent_color[0], accent_color[1], accent_color[2], 100), width=8)
        
        progress_end = bar_x1 + (bar_x2 - bar_x1) * 0.45
        draw.line((bar_x1, bar_y, progress_end, bar_y), fill=accent_color, width=8)
        draw.ellipse((progress_end-12, bar_y-12, progress_end+12, bar_y+12), fill=accent_color)

        # Time
        draw.text((160, 585), "01:24", font=font_small, fill="white")
        draw.text((bar_x2-80, 585), duration, font=font_small, fill="white")

        bg = bg.convert("RGB")
        bg.save(path)
        os.remove(temp_path)
        return path

    except Exception as e:
        print(f"Error: {e}")
        return YOUTUBE_IMG_URL
        
