import io
import json
import logging
import random
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("mikubot.image")


class MikuImageService:
    def __init__(
        self,
        image_dir: str | None,
        image_api_url: str | None,
        font_path: str | None,
    ) -> None:
        self.image_dir = Path(image_dir) if image_dir else None
        self.image_api_url = image_api_url
        self.font_path = font_path
        self.supported_exts = {".png", ".jpg", ".jpeg", ".webp"}

    def _list_local_images(self) -> list[Path]:
        if not self.image_dir or not self.image_dir.exists():
            return []
        return [
            path
            for path in self.image_dir.iterdir()
            if path.is_file() and path.suffix.lower() in self.supported_exts
        ]

    def _pick_local_image(self) -> Path | None:
        candidates = self._list_local_images()
        if not candidates:
            return None
        return random.choice(candidates)

    async def _fetch_remote_image_bytes(self) -> bytes:
        if not self.image_api_url:
            raise ValueError("Missing image API URL")

        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.image_api_url) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                payload = await response.read()

            data = None
            if "application/json" in content_type or payload[:1] in {b"{", b"["}:
                try:
                    data = json.loads(payload.decode("utf-8"))
                except Exception:
                    data = None

            if data is not None:
                image_url = self._extract_image_url(data)
                if not image_url:
                    raise ValueError("No image URL found in API response")
                async with session.get(image_url) as image_response:
                    image_response.raise_for_status()
                    return await image_response.read()

            return payload

    async def _fetch_image_bytes(self) -> bytes:
        local_image = self._pick_local_image()
        if local_image:
            return local_image.read_bytes()
        return await self._fetch_remote_image_bytes()

    def _extract_image_url(self, data: object) -> str | None:
        if isinstance(data, dict):
            for key in ("url", "image", "image_url", "file", "file_url"):
                value = data.get(key)
                if isinstance(value, str):
                    return value
            images = data.get("images")
            if isinstance(images, list) and images:
                return self._extract_image_url(images[0])
        elif isinstance(data, list) and data:
            return self._extract_image_url(random.choice(data))
        return None

    def _load_font(self, size: int) -> tuple[ImageFont.ImageFont, bool]:
        font_candidates = [
            self.font_path,
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for candidate in font_candidates:
            if not candidate:
                continue
            try:
                return ImageFont.truetype(candidate, size=size), True
            except OSError:
                continue
        return ImageFont.load_default(), False

    def _wrap_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
        stroke_width: int,
    ) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font, stroke_width=stroke_width)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _truncate_lines(
        self,
        lines: list[str],
        max_lines: int,
    ) -> list[str]:
        if max_lines <= 0 or len(lines) <= max_lines:
            return lines
        clipped = lines[:max_lines]
        last = clipped[-1].rstrip()
        if len(last) > 3:
            clipped[-1] = f"{last[:-3]}..."
        else:
            clipped[-1] = f"{last}..."
        return clipped

    def _fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        image_width: int,
        image_height: int,
    ) -> tuple[str, ImageFont.ImageFont]:
        stroke_width = max(2, image_width // 300)
        max_width = int(image_width * 0.9)
        max_height = int(image_height * 0.35)
        spacing = 4
        base_size = max(18, image_width // 18)

        font, scalable = self._load_font(base_size)
        sizes = [base_size] if not scalable else range(base_size, 12, -2)

        last_text = text
        last_font = font

        for size in sizes:
            font, _ = self._load_font(size)
            lines = self._wrap_text(draw, text, font, max_width, stroke_width)
            line_bbox = draw.textbbox((0, 0), "Ag", font=font, stroke_width=stroke_width)
            line_height = line_bbox[3] - line_bbox[1]
            max_lines = max(
                1,
                int((max_height + spacing) / max(1, line_height + spacing)),
            )
            lines = self._truncate_lines(lines, max_lines)
            candidate_text = "\n".join(lines)
            bbox = draw.multiline_textbbox(
                (0, 0),
                candidate_text,
                font=font,
                spacing=spacing,
                align="center",
                stroke_width=stroke_width,
            )
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            last_text = candidate_text
            last_font = font
            if text_width <= max_width and text_height <= max_height:
                break
            if not scalable:
                break

        return last_text, last_font

    async def generate(self, text: str) -> io.BytesIO:
        image_bytes = await self._fetch_image_bytes()

        with Image.open(io.BytesIO(image_bytes)) as image:
            image = image.convert("RGBA")
            draw = ImageDraw.Draw(image)
            wrapped_text, font = self._fit_text(draw, text, image.width, image.height)

            stroke_width = max(2, image.width // 300)
            spacing = 4
            bbox = draw.multiline_textbbox(
                (0, 0),
                wrapped_text,
                font=font,
                spacing=spacing,
                align="center",
                stroke_width=stroke_width,
            )
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            margin = int(max(12, image.height * 0.06))
            x = (image.width - text_width) / 2
            y = image.height - text_height - margin
            if y < margin:
                y = margin

            padding = max(8, int(max(image.width, image.height) * 0.015))
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                (
                    x - padding,
                    y - padding,
                    x + text_width + padding,
                    y + text_height + padding,
                ),
                fill=(0, 0, 0, 150),
            )
            image = Image.alpha_composite(image, overlay)
            draw = ImageDraw.Draw(image)
            draw.multiline_text(
                (x, y),
                wrapped_text,
                font=font,
                fill=(255, 255, 255, 255),
                spacing=spacing,
                align="center",
                stroke_width=stroke_width,
                stroke_fill=(0, 0, 0, 255),
            )

            output = io.BytesIO()
            image.save(output, format="PNG")
            output.seek(0)
            return output
