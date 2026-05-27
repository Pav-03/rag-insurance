"""
Cleaning step —> read raw HICRIC records one at a time, drop junk, apply
safe whitespace fixes, and write the survivors to data/processed/ as JSONL.

Streaming by design: one record in memory at a time (the legal category has a
~39M-char record; accumulating would blow the 8GB machine's memory).
"""
import json
import re
from pathlib import Path
from datasets import load_dataset
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATASET_ID = "Persius/hicric"
RAW_DIR = Path("data/raw/hicric")
PROCESSED_DIR = Path("data/processed")
CONFIG_NAMES = [
    "regulatory-guidance",
    "legal",
    "clinical-guidelines",
]

MIN_CHARS = 200
_WHITESPACE = re.compile(r"\s+")

def clean_text(text: str) -> str:
    """ Apply safe whitepace fixes: collapse multiple spaces, newlines, tabs into a single spaces"""
    return _WHITESPACE.sub(" ", text).strip()

def clean_category(config_name: str) -> str:
    """ read the category, drop junks, clean space, stream survivors to a .jsonl file"""

    logger.info(f"Cleaning category: {config_name}")
    dataset = load_dataset(
        DATASET_ID,
        config_name,
        cache_dir=str(RAW_DIR),
    )
    data = dataset["train"]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{config_name}.jsonl"

    kept = 0
    dropped = 0

    with open(out_path, "w", encoding="utf-8") as f:
        for record in data:
            text = record["text"]

            if len(text) < MIN_CHARS:
                dropped += 1
                continue

            cleaned = clean_text(text)

            output_record = {
                "text": cleaned,
                "category": config_name,
                "tags": record["tags"],
                "source_url": record["source_url"],
                "source_md5": record["source_md5"],
                "relative_path": record["relative_path"],
            }

            f.write(json.dumps(output_record) + "\n")
            kept += 1

    logger.info(f"Done {config_name}: kept {kept}, dropped {dropped} -> {out_path}")

def clean_all() -> None:
    for config_name in CONFIG_NAMES:
        clean_category(config_name)

if __name__ == "__main__":
    clean_all()