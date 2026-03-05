import os
import re
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

# --- Helper functions (Same as yours but modified layout) ---

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

        # 1. Background Setup (Blurred Image)
        base = Image.open(temp_path).convert("RGBA")
        base = base.resize(thumb_size, Image.LANCZOS)
        bg = base.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.7)

        # 2. Main Card Setup (The Spotify-like Panel)
        draw = ImageDraw.Draw(bg)
        card_x1, card_y1, card_x2, card_y2 = 100, 100, 1180, 620
        
        # Create Semi-Transparent Glass Effect
        overlay = Image.new("RGBA", thumb_size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=40, fill=(255, 255, 255, 40))
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg) # Redefine draw for new bg

        # 3. Fonts
        # Note: Make sure these paths are correct or use default fonts
        font_title = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 60)
        font_artist = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 40)
        font_time = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 25)

        # 4. Text (Left Aligned)
        draw.text((150, 180), "Spotify", font=font_artist, fill=(255, 255, 255, 200))
        
        # Title (Truncate if too long)
        display_title = title[:30] + "..." if len(title) > 30 else title
        draw.text((150, 240), display_title, font=font_title, fill="white")
        draw.text((150, 320), channel, font=font_artist, fill=(255, 255, 255, 180))

        # 5. Icons/Controls (Draw simple shapes for Play/Pause)
        cx, cy = 640, 480 # Center of controls
        
        # Play/Pause Circle (Center)
        draw.rounded_rectangle((cx-40, cy-50, cx+40, cy+50), radius=15, fill="white") # Simplified Pause
        draw.rounded_rectangle((cx-15, cy-40, cx-5, cy+40), radius=2, fill="black") # Pause lines
        draw.rounded_rectangle((cx+5, cy-40, cx+15, cy+40), radius=2, fill="black")

        # Skip Buttons (Triangles)
        draw.polygon([(cx+120, cy-25), (cx+120, cy+25), (cx+150, cy)], fill="white") # Next
        draw.polygon([(cx-120, cy-25), (cx-120, cy+25), (cx-150, cy)], fill="white") # Prev

        # 6. Progress Bar (Bottom of Card)
        bar_x1, bar_y = 150, 560
        bar_x2 = 1130
        draw.line((bar_x1, bar_y, bar_x2, bar_y), fill=(255, 255, 255, 80), width=6) # Background bar
        
        # Current Progress (Random for aesthetic)
        progress_end = bar_x1 + (bar_x2 - bar_x1) * 0.4 
        draw.line((bar_x1, bar_y, progress_end, bar_y), fill="white", width=6)
        draw.ellipse((progress_end-8, bar_y-8, progress_end+8, bar_y+8), fill="white") # The Dot

        # Time Stamps
        draw.text((150, 580), "01:24", font=font_time, fill="white")
        draw.text((bar_x2-70, 580), duration, font=font_time, fill="white")

        bg = bg.convert("RGB")
        bg.save(path)
        os.remove(temp_path)
        return path

    except Exception as e:
        print(f"Error: {e}")
        return YOUTUBE_IMG_URL
        
