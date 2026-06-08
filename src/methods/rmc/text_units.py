import json
import re
from typing import Sequence


def clean_blank_units(units: Sequence[str]) -> list[str]:
    return [unit for unit in units if unit.strip()]


def normalize_escaped_newlines(text: str) -> str:
    if "\n" in text or "\\n" not in text:
        return text
    return json.loads(f'"{text}"')


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    sentences = [
        match.group(0).strip()
        for match in re.finditer(r".+?(?:[.!?][\"']?|$)(?=\s+|$)", normalized)
        if match.group(0).strip()
    ]
    return sentences or [normalized]


def split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n+", normalized)
        if paragraph.strip()
    ]
    return paragraphs or ([re.sub(r"\s+", " ", normalized).strip()] if normalized else [])
