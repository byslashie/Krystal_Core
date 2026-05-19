#!/usr/bin/env python3
"""
export_slides_pdf.py
把 slides_20260530.html 的每一張投影片截成 PNG，再合成 PDF

安裝（第一次）：
    pip install playwright pillow
    playwright install chromium

執行：
    python 07-工具/export_slides_pdf.py
"""

import asyncio
import os
from pathlib import Path

SLIDES_HTML = Path(__file__).parent.parent / "11-自媒體專區/直播活動/2026-0530-AI量化策略/投影片/slides_20260530.html"
OUTPUT_DIR  = Path(__file__).parent.parent / "11-自媒體專區/直播活動/2026-0530-AI量化策略/投影片/export"
PDF_OUTPUT  = Path(__file__).parent.parent / "11-自媒體專區/直播活動/2026-0530-AI量化策略/投影片/slides_20260530_final.pdf"

WIDTH  = 1920
HEIGHT = 1080
TOTAL_SLIDES = 23


async def export():
    from playwright.async_api import async_playwright

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    url = SLIDES_HTML.resolve().as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        print(f"開啟：{url}")
        await page.goto(url, wait_until="networkidle")

        # 等字體載入
        await page.wait_for_timeout(2000)

        png_paths = []

        for i in range(TOTAL_SLIDES):
            slide_num = i + 1
            # 跳到第 i 張（透過 JS）
            await page.evaluate(f"go({i})")
            await page.wait_for_timeout(400)

            path = OUTPUT_DIR / f"slide_{slide_num:02d}.png"
            await page.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
            png_paths.append(path)
            print(f"  ✓ Slide {slide_num:02d} / {TOTAL_SLIDES}")

        await browser.close()

    # 合成 PDF
    print("\n合成 PDF...")
    try:
        from PIL import Image
        images = [Image.open(p).convert("RGB") for p in png_paths]
        images[0].save(
            str(PDF_OUTPUT),
            save_all=True,
            append_images=images[1:],
            resolution=150,
        )
        print(f"✅ PDF 輸出：{PDF_OUTPUT}")
    except ImportError:
        print("⚠️  Pillow 未安裝，PNG 已儲存在：")
        print(f"   {OUTPUT_DIR}")
        print("   請執行：pip install pillow  再重跑一次")


if __name__ == "__main__":
    asyncio.run(export())
