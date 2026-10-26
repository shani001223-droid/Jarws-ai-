"""Hoshi backend ad studio: real downloadable creatives, no model/API key.

Creates feed + story PNGs, copy and a video storyboard from verified catalogue
details. This is intentionally template art, NOT fabricated product photography.
All artifacts live inside a returned ZIP; nothing is posted externally.
"""
from __future__ import annotations

import base64
from io import BytesIO
import math
import re
import textwrap
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw, ImageFont

CATALOG = {
    "gold_kit": {
        "brand": "FLORA BY M/S&Co.",
        "name": "24K GOLD",
        "subtitle": "FACIAL KIT",
        "type": "6 PRODUCT BEAUTY KIT",
        "price": "RS. 3,500",
        "details": ["6 products in one kit", "Premium gold & white collection"],
        "caption": "Flora 24K Gold Facial Kit — 6 products, Rs. 3,500. Premium gold & white collection. Message to order. #FloraBeauty #FacialCare #GoldFacial",
        "roman": "Flora 24K Gold Facial Kit: 6 products, sirf Rs. 3,500. Order ke liye message karein.",
        "theme": "ivory",
    },
    "shampoo": {
        "brand": "FLORA BY M/S&Co.",
        "name": "HERBAL",
        "subtitle": "SHAMPOO",
        "type": "500 ML BOTTLE",
        "price": "RS. 1,500",
        "details": ["Amla  /  Shikakai  /  Tulsi", "Curry leaf  /  Onion"],
        "caption": "Flora Herbal Shampoo — 500 ml, Rs. 1,500. Amla, Shikakai, Tulsi, Curry Leaf & Onion. Message to order. #FloraBeauty #HerbalShampoo #HairCare",
        "roman": "Flora Herbal Shampoo 500 ml, Rs. 1,500. Amla, Shikakai, Tulsi aur doosre herbal ingredients. Order ke liye message karein.",
        "theme": "dark",
    },
}

def choose_products(message: str) -> list[str]:
    """Select only known honest product data; never invent catalogue details."""
    text = str(message or "").casefold()
    kit = bool(re.search(r"\b(gold|24\s*k|facial|kit|scrub|face)\b", text))
    shampoo = bool(re.search(r"\b(shampoo|shampu|shampooing|hair)\b", text))
    if kit and not shampoo:
        return ["gold_kit"]
    if shampoo and not kit:
        return ["shampoo"]
    return ["gold_kit", "shampoo"]

def _font(size: int, bold: bool = False):
    # Pillow's packaged DejaVu fonts are available on many Linux hosts;
    # fallback remains available on slim Python hosts.
    names = (
        ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else
        ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()

def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def _title_fit(draw, text, max_width, starting):
    for size in range(starting, 27, -3):
        font = _font(size, bold=True)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
    return _font(27, bold=True)

def draw_creative(product: dict, width=1080, height=1350) -> bytes:
    """Make an actual PNG (not merely text describing an ad)."""
    if (width, height) not in ((1080, 1350), (1080, 1920)):
        raise ValueError("Unsupported export format")
    dark = product["theme"] == "dark"
    paper = (12, 20, 24) if dark else (251, 247, 237)
    far = (28, 36, 40) if dark else (238, 226, 201)
    gold = (223, 178, 94) if dark else (153, 106, 45)
    accent = (252, 234, 192) if dark else (70, 49, 27)
    sub = (216, 202, 174) if dark else (100, 84, 65)
    img = Image.new("RGB", (width, height), paper)
    dr = ImageDraw.Draw(img)
    # Elegant banded light-to-dark gradient, no fabricated actual product photo.
    for y in range(height):
        t = min(1, y / height)
        dr.line([(0, y), (width, y)], fill=_mix(paper, far, .35 * t), width=1)

    margin = 86
    dr.rounded_rectangle((margin-28, margin-28, width-margin+28, height-margin+28),
                         radius=35, outline=gold, width=3)
    dr.line([(margin, 207), (width-margin, 207)], fill=gold, width=2)
    dr.text((margin, 120), product["brand"], font=_font(33, True), fill=accent)
    dr.text((width-margin, 120), "EST. 2026", font=_font(24), fill=sub, anchor="ra")

    # Abstract gold rings are graphic decoration, NOT a depiction of the kit.
    cy = 480 if height==1350 else 730
    cx = width//2
    for radius in (235, 205, 166):
        dr.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=gold, width=3)
    for j in range(11):
        angle = (j/11)*2*math.pi
        px = cx + math.cos(angle)*248
        py = cy + math.sin(angle)*248
        dr.ellipse((px-5,py-5,px+5,py+5), fill=gold)
    dr.ellipse((cx-125,cy-125,cx+125,cy+125), outline=gold, width=2)
    dr.text((cx, cy-31), "FLORA", font=_font(52, True), fill=accent, anchor="mm")
    dr.text((cx, cy+31), "P R E M I U M", font=_font(19), fill=sub, anchor="mm")

    name_top = 753 if height==1350 else 1050
    dr.text((cx,name_top),product["name"],
            font=_title_fit(dr,product["name"],width-2*margin,91),
            fill=accent,anchor="mm")
    dr.text((cx,name_top+81),product["subtitle"],
            font=_title_fit(dr,product["subtitle"],width-2*margin,70),
            fill=gold,anchor="mm")
    dr.text((cx,name_top+145),product["type"],font=_font(27,True),fill=sub,anchor="mm")
    dr.line([(margin+85,name_top+199),(width-margin-85,name_top+199)], fill=gold,width=2)
    dr.text((cx,name_top+244),product["price"],font=_font(62,True),fill=accent,anchor="mm")

    features_y = name_top+321
    for i,feature in enumerate(product["details"]):
        dr.text((cx,features_y + i*46),feature,font=_font(26),fill=sub,anchor="mm")
    button_y = height-196
    dr.rounded_rectangle((margin+90,button_y,width-margin-90,button_y+83),
                         radius=33, fill=gold)
    button_text = "MESSAGE TO ORDER"
    dr.text((cx,button_y+40),button_text,font=_font(31,True),
            fill=(20,22,27) if dark else (255,251,243),anchor="mm")
    dr.text((cx,height-103),"FLORA  •  PRODUCT CREATIVE  •  IMAGE-ONLY TEMPLATE",
            font=_font(18),fill=sub,anchor="mm")
    data=BytesIO()
    img.save(data,format="PNG",optimize=True)
    return data.getvalue()

def _storyboard(product: dict):
    return (
        "15-second video ad storyboard (not a rendered video)\n\n"
        "0-3s: Show genuine product pack photo with logo and soft fade.\n"
        "3-7s: Highlight " + product["name"] + " " + product["subtitle"] + ".\n"
        "7-11s: Show verified details: " + " / ".join(product["details"]) + ".\n"
        "11-15s: Display " + product["price"] + " and Message to Order.\n"
        "Use actual user-supplied product photography; this file is a script only.\n"
    )

def create_ad_pack(message: str):
    """Return compact, zero-disk, ready-to-download ZIP and first image preview."""
    keys = choose_products(message)
    contents=BytesIO()
    outputs=[]
    preview=None
    with ZipFile(contents,"w",compression=ZIP_DEFLATED,compresslevel=6) as archive:
        for key in keys:
            item=CATALOG[key]
            feed=draw_creative(item,1080,1350)
            story=draw_creative(item,1080,1920)
            archive.writestr(key+"_feed_1080x1350.png",feed)
            archive.writestr(key+"_story_1080x1920.png",story)
            archive.writestr(key+"_caption.txt",
                             item["caption"]+"\n\nRoman Urdu:\n"+item["roman"]+"\n")
            archive.writestr(key+"_video_storyboard.txt",_storyboard(item))
            if preview is None:
                preview=base64.b64encode(feed).decode("ascii")
            outputs.append({
                "product":item["name"]+" "+item["subtitle"],
                "price":item["price"],
                "caption":item["caption"],
                "sizes":["1080x1350 feed PNG","1080x1920 story PNG"],
                "image_note":"Illustrated template, not a product photo.",
            })
    payload=contents.getvalue()
    if len(payload)>5_000_000:
        raise ValueError("Ad output exceeded safe size limit.")
    return {
        "ok":True,
        "task":"create_product_ads",
        "completed":True,
        "products":outputs,
        "filename":"Flora_Product_Ads.zip",
        "mime_type":"application/zip",
        "zip_base64":base64.b64encode(payload).decode("ascii"),
        "preview_base64":preview,
        "note":"Real PNG images, captions and a video storyboard. No rendered video or fabricated product photos.",
    }
