"""OCR service — extracts Arabic text from camera images."""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from config import OCR_ENGINE

logger = logging.getLogger(__name__)


class OcrService:
    """OCR abstraction that uses either EasyOCR or Tesseract."""

    def __init__(self):
        self._reader = None
        self._engine = OCR_ENGINE

    # ── Public API ──────────────────────────────────────────────────

    def extract_text(self, image_data: bytes | str) -> str:
        """Extract Arabic text from an image.

        Accepts raw bytes or a base64-encoded string.
        Returns concatenated detected text lines.
        """
        img_array = self._decode_image(image_data)
        img_array = self._preprocess(img_array)

        if self._engine == "easyocr":
            return self._easyocr_extract(img_array)
        elif self._engine == "tesseract":
            return self._tesseract_extract(img_array)
        else:
            raise ValueError(f"Unknown OCR engine: {self._engine}")

    def extract_text_with_boxes(
        self, image_data: bytes | str
    ) -> tuple[str, list[dict]]:
        """Return (text, boxes) where each box is
        { 'bbox': [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], 'text': str }."""
        img_array = self._decode_image(image_data)
        img_array = self._preprocess(img_array)

        if self._engine == "easyocr":
            return self._easyocr_extract_with_boxes(img_array)
        elif self._engine == "tesseract":
            return self._tesseract_extract_with_boxes(img_array)
        else:
            raise ValueError(f"Unknown OCR engine: {self._engine}")

    # ── Decoding ────────────────────────────────────────────────────

    @staticmethod
    def _decode_image(data: bytes | str) -> np.ndarray:
        """Convert base64 string or raw bytes to OpenCV BGR array."""
        if isinstance(data, str):
            # Base64 string
            try:
                raw = base64.b64decode(data)
            except Exception:
                raw = data.encode("utf-8")
        else:
            raw = data

        pil_img = Image.open(BytesIO(raw)).convert("RGB")
        # PIL RGB → OpenCV BGR
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # ── Preprocessing ───────────────────────────────────────────────

    @staticmethod
    def _preprocess(img: np.ndarray) -> np.ndarray:
        """Quran-optimised preprocessing: denoise, adaptive threshold,
        invert (dark text on light background for EasyOCR).

        Mirrors ai/ocr/arabic_ocr.py::ArabicOcrPipeline._preprocess.
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray, h=20)
            binary = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                block_size=15,
                C=10,
            )
            inverted = cv2.bitwise_not(binary)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            return cv2.dilate(inverted, kernel, iterations=1)
        except Exception as e:
            logger.warning("Preprocessing failed (%s); using raw image.", e)
            return img

    # ── EasyOCR ─────────────────────────────────────────────────────

    def _get_easyocr(self):
        """Lazy-load EasyOCR reader (takes ~2 s first time)."""
        if self._reader is None:
            try:
                import easyocr

                logger.info("Loading EasyOCR (Arabic) …")
                self._reader = easyocr.Reader(
                    ["ar"], gpu=self._gpu_available()
                )
            except ImportError:
                logger.error(
                    "EasyOCR not installed. "
                    "Run: pip install easyocr"
                )
                raise
        return self._reader

    def _easyocr_extract(self, img: np.ndarray) -> str:
        try:
            reader = self._get_easyocr()
            results = reader.readtext(img)
            return " ".join(text for _, text, conf in results if conf > 0.3)
        except Exception as e:
            logger.warning("EasyOCR failed: %s. Trying Tesseract fallback.", e)
            return self._tesseract_extract(img)

    def _easyocr_extract_with_boxes(
        self, img: np.ndarray
    ) -> tuple[str, list[dict]]:
        try:
            reader = self._get_easyocr()
            results = reader.readtext(img)
            texts = []
            boxes = []
            for bbox, text, conf in results:
                if conf > 0.3:
                    texts.append(text)
                    boxes.append(
                        {
                            "bbox": bbox.tolist()
                            if hasattr(bbox, "tolist")
                            else bbox,
                            "text": text,
                            "confidence": round(float(conf), 4),
                        }
                    )
            return " ".join(texts), boxes
        except Exception as e:
            logger.warning("EasyOCR failed: %s. Trying Tesseract.", e)
            return self._tesseract_extract_with_boxes(img)

    # ── Tesseract ───────────────────────────────────────────────────

    def _tesseract_extract(self, img: np.ndarray) -> str:
        try:
            import pytesseract
            from pytesseract import Output

            custom_config = (
                r"--oem 3 --psm 6 "
                r"-c tessedit_char_whitelist="
                r"ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي"
                r"۝۞\ufdfd\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652"
                r" "
            )
            data = pytesseract.image_to_data(
                img, lang="ara", config=custom_config, output_type=Output.DICT
            )
            lines = []
            for i, text in enumerate(data["text"]):
                if text.strip() and int(data["conf"][i]) > 30:
                    lines.append(text.strip())
            return " ".join(lines)
        except ImportError:
            logger.warning(
                "pytesseract not installed; falling back to EasyOCR"
            )
            return self._easyocr_extract(img)

    def _tesseract_extract_with_boxes(
        self, img: np.ndarray
    ) -> tuple[str, list[dict]]:
        try:
            import pytesseract
            from pytesseract import Output

            custom_config = (
                r"--oem 3 --psm 6 "
                r"-c tessedit_char_whitelist="
                r"ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي"
                r"۝۞\ufdfd\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652"
                r" "
            )
            data = pytesseract.image_to_data(
                img, lang="ara", config=custom_config, output_type=Output.DICT
            )
            texts = []
            boxes = []
            for i, text in enumerate(data["text"]):
                if text.strip() and int(data["conf"][i]) > 30:
                    x, y, w, h = (
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    )
                    texts.append(text.strip())
                    boxes.append(
                        {
                            "bbox": [
                                [x, y],
                                [x + w, y],
                                [x + w, y + h],
                                [x, y + h],
                            ],
                            "text": text.strip(),
                            "confidence": round(data["conf"][i] / 100.0, 4),
                        }
                    )
            return " ".join(texts), boxes
        except ImportError:
            return self._easyocr_extract_with_boxes(img)

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _gpu_available() -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def is_loaded(self) -> bool:
        """Return True if the OCR engine can actually run.

        We attempt a quick import check; if the engine's dependencies are
        broken (e.g. numpy/pandas incompatibility) we return False so the
        caller can fall back to text-only input.
        """
        if self._engine == "easyocr":
            try:
                import easyocr  # noqa: F401
                return True
            except Exception:
                return False
        elif self._engine == "tesseract":
            try:
                import pytesseract  # noqa: F401
                return True
            except Exception:
                return False
        return False
