"""
Uses LangChain's RecursiveCharacterTextSplitter: splits on the coarsest natural
boundary (paragraph -> line -> sentence -> word) that keeps chunks under the
size limit, only hard-cutting as a last resort.
"""

import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.utils.logger import setup_logger
from src.utils.schema import Chunk, make_chunk_id

logger = setup_logger(__name__)

PROCESSED_DIR = Path("data/processed")
CONFIG_NAMES = [
    "regulatory-guidance",
    "legal",
    "clinical-guidelines",
]
OUTPUT_PATH = PROCESSED_DIR / "chunks.jsonl"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

SEGMENT_THRESHOLD = 200_000   # records longer than this get pre-split
SEGMENT_SIZE = 100_000        # size of each segment (citation granularity unit)


def segment_record(text: str, source_md5: str) -> list[tuple[str, str]]:
    """
    Turn one record into a list of (doc_id, text) segments.
    Small records -> one segment, doc_id = source_md5 (unchanged).
    Giant records  -> many segments, doc_id = '{source_md5}_seg{N}'.
    """
    if len(text) <= SEGMENT_THRESHOLD:
        return [(source_md5, text)]

    segments = []
    for i in range(0, len(text), SEGMENT_SIZE):
        seg_index = i // SEGMENT_SIZE
        seg_text = text[i:i + SEGMENT_SIZE]
        seg_doc_id = f"{source_md5}_seg{seg_index}"
        segments.append((seg_doc_id, seg_text))
    return segments


def chunk_category(config_name: str, out_file) -> None:
    """ read one category'ss jsonl, split inro a chunks and write chunk objects and return chunk count"""
    in_path = PROCESSED_DIR / f"{config_name}.jsonl"
    logger.info(f"chunking category: {config_name}")

    record_count = 0
    chunk_written = 0

    with open (in_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            record_count += 1

            for doc_id, seg_text in segment_record(record["text"], record["source_md5"]):
                pieces = splitter.split_text(seg_text)


                for index, piece in enumerate(pieces):
                    chunk = Chunk(
                        chunk_id=make_chunk_id(doc_id, index),
                        doc_id=doc_id,
                        chunk_index=index,
                        text=piece,
                        category=record["category"],
                        source_url=record["source_url"],
                        section=None,  # to be filled in by the chunker when it reads section headings
                        tags=record["tags"],
                        relative_path=record["relative_path"],
                        source_md5=record["source_md5"],
                    )
                    out_file.write(json.dumps(chunk.to_payload()) + "\n")
                    chunk_written += 1

    logger.info(f"done: {config_name} | {record_count} records -> {chunk_written} chunks")
    return chunk_written

def chunk_all() -> None:
    total = 0
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        for config_name in CONFIG_NAMES:
            total += chunk_category(config_name, out_file)
    logger.info(f"All categories chunked: {total} total chunks -> {OUTPUT_PATH}")

if __name__ == "__main__":
    chunk_all()