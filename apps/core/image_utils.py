import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ImageCompressor:

    @staticmethod
    def compress_image(
        image_path: str,
        output_path: Optional[str] = None,
        quality: int = 85,
        max_size: Optional[Tuple[int, int]] = None,
        format: str = "JPEG",
    ) -> str:
        """
        Compress an image file.
        """
        try:
            image = Image.open(image_path)

            if max_size:
                image = ImageCompressor._resize_image(image, max_size)

            if image.mode in ("RGBA", "P") and format == "JPEG":
                image = image.convert("RGB")

            output = output_path or image_path
            image.save(output, format=format, quality=quality, optimize=True)

            logger.info(f"Image compressed: {image_path} -> {output}")
            return output

        except Exception as e:
            logger.error(f"Error compressing image {image_path}: {e}")
            raise

    @staticmethod
    def compress_from_memory(
        image_data: bytes, quality: int = 85, max_size: Optional[Tuple[int, int]] = None, format: str = "JPEG"
    ) -> bytes:
        """
        Compress image from bytes in memory.
        """
        try:
            image = Image.open(BytesIO(image_data))

            if max_size:
                image = ImageCompressor._resize_image(image, max_size)

            if image.mode in ("RGBA", "P") and format == "JPEG":
                image = image.convert("RGB")

            output = BytesIO()
            image.save(output, format=format, quality=quality, optimize=True)
            output.seek(0)

            return output.read()

        except Exception as e:
            logger.error(f"Error compressing image from memory: {e}")
            raise

    @staticmethod
    def _resize_image(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """
        Resize image maintaining aspect ratio.
        """
        max_width, max_height = max_size

        if image.width <= max_width and image.height <= max_height:
            return image

        ratio = min(max_width / image.width, max_height / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))

        return image.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def get_image_info(image_path: str) -> dict:
        """
        Get image metadata.
        """
        try:
            image = Image.open(image_path)
            file_size = Path(image_path).stat().st_size

            return {
                "format": image.format,
                "mode": image.mode,
                "size": file_size,
                "width": image.width,
                "height": image.height,
                "dimensions": f"{image.width}x{image.height}",
            }
        except Exception as e:
            logger.error(f"Error getting image info {image_path}: {e}")
            raise

    @staticmethod
    def create_thumbnail(
        image_path: str, output_path: str, size: Tuple[int, int] = (150, 150), format: str = "JPEG"
    ) -> str:
        """
        Create a thumbnail image."""
        try:
            image = Image.open(image_path)
            image.thumbnail(size, Image.Resampling.LANCZOS)

            if image.mode in ("RGBA", "P") and format == "JPEG":
                image = image.convert("RGB")

            image.save(output_path, format=format, quality=85, optimize=True)

            logger.info(f"Thumbnail created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise
