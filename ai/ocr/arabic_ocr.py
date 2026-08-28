"""Arabic-specific OCR pipeline optimized for Quranic text.

This module provides Quran-specific image preprocessing and OCR
configuration to maximise accuracy on printed Mushaf pages.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ArabicOcrPipeline:
    """End-to-end pipeline for Arabic Quranic text extraction.

    Steps:
        1. Preprocess image (grayscale, denoise, binarize)
        2. Detect text regions / lines
        3. Extract text via OCR engine
        4. Post-process (remove spurious characters)
    """

    def __init__(self, engine: str = "easyocr"):
        self.engine = engine
        self._reader = None

    # ── Public API ──────────────────────────────────────────────────

    def extract(self, image: np.ndarray) -> str:
        """Run the full pipeline on an OpenCV BGR image."""
        processed = self._preprocess(image)
        return self._ocr(processed)

    def extract_with_regions(self, image: np.ndarray) -> list[dict]:
        """Return detected text regions with bounding boxes."""
        processed = self._preprocess(image)
        return self._ocr_with_regions(processed)

    # ── Image preprocessing ─────────────────────────────────────────

    @staticmethod
    def _preprocess(img: np.ndarray) -> np.ndarray:
        """Apply Quran-optimised preprocessing."""
        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Denoise (removes printing artefacts)
        denoised = cv2.fastNlMeansDenoising(gray, h=30)

        # 3. Adaptive thresholding (handles lighting variation)
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size=15,
            C=10,
        )

        # 4. Invert so text is white on black (EasyOCR expects this)
        inverted = cv2.bitwise_not(binary)

        # 5. Slight dilation to thicken thin diacritics
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(inverted, kernel, iterations=1)

        return dilated

    # ── Line detection ──────────────────────────────────────────────

    @staticmethod
    def detect_text_lines(
        img: np.ndarray,
    ) -> list[tuple[int, int, int, int]]:
        """Detect horizontal text lines and return (x, y, w, h) boxes."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]

        # Horizontal kernel to merge characters into lines
        h_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (150, 1)
        )
        connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, h_kernel)

        contours, _ = cv2.findContours(
            connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        lines = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter very small regions (noise)
            if w > 100 and h > 10:
                lines.append((x, y, w, h))

        # Sort top-to-bottom
        lines.sort(key=lambda b: b[1])
        return lines

    # ── OCR ─────────────────────────────────────────────────────────

    def _get_reader(self):
        if self._reader is None:
            if self.engine == "easyocr":
                import easyocr

                self._reader = easyocr.Reader(
                    ["ar"], gpu=False
                )
            else:
                import pytesseract

                self._reader = pytesseract
        return self._reader

    def _ocr(self, img: np.ndarray) -> str:
        reader = self._get_reader()
        if self.engine == "easyocr":
            results = reader.readtext(img)
            texts = [t for _, t, c in results if c > 0.4]
            return " ".join(texts)
        else:
            import pytesseract

            custom_config = r"--oem 3 --psm 6 -l ara"
            return pytesseract.image_to_string(
                img, config=custom_config
            ).strip()

    def _ocr_with_regions(self, img: np.ndarray) -> list[dict]:
        reader = self._get_reader()
        regions = []

        if self.engine == "easyocr":
            results = reader.readtext(img)
            for bbox, text, conf in results:
                if conf > 0.4:
                    regions.append(
                        {
                            "bbox": [
                                [int(bbox[0][0]), int(bbox[0][1])],
                                [int(bbox[1][0]), int(bbox[1][1])],
                                [int(bbox[2][0]), int(bbox[2][1])],
                                [int(bbox[3][0]), int(bbox[3][1])],
                            ],
                            "text": text,
                            "confidence": round(float(conf), 4),
                        }
                    )
        else:
            import pytesseract
            from pytesseract import Output

            custom_config = r"--oem 3 --psm 6 -l ara"
            data = pytesseract.image_to_data(
                img, config=custom_config, output_type=Output.DICT
            )
            for i, t in enumerate(data["text"]):
                if t.strip() and int(data["conf"][i]) > 30:
                    x, y, w, h = (
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    )
                    regions.append(
                        {
                            "bbox": [
                                [x, y],
                                [x + w, y],
                                [x + w, y + h],
                                [x, y + h],
                            ],
                            "text": t.strip(),
                            "confidence": round(data["conf"][i] / 100.0, 4),
                        }
                    )

        return regions
