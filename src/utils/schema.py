"""
Chunk schema — the single source of truth for what one chunk carries.
Every chunk the chunker produces is built as a `Chunk`, so the chunker,
the indexer, and the retriever all agree on the exact same shape.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import uuid

# A fixed namespace so uuid5 produce the same id for the same content accross runs

_CHUNK_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """
    Generate a unique chunk ID based on the document ID and chunk index.
    This ensures that the same document will always produce the same chunk IDs.
    """
    name = f"{doc_id}:{chunk_index}"
    return str(uuid.uuid5(_CHUNK_NAMESPACE, name))

@dataclass
class Chunk:
    # --- identity / traceability ---
    chunk_id: str           # unique id for this chunk (Qdrant point id)
    doc_id: str             # id of the source record this chunk came from
    chunk_index: int        # position within its source doc (0, 1, 2, ...)

    # --- content ---
    text: str               # the chunk's actual text

    # --- citation + filtering ---
    category: str           # 'regulatory-guidance' | 'legal' | 'clinical-guidelines'
    source_url: str         # the real source link — THE citation
    section: Optional[str]  # heading this chunk sits under; None until chunker reads headings
    tags: list[str]         # authority tags (e.g. 'kb') — used for filtering

    # --- provenance ---
    relative_path: str      # path within the source corpus
    source_md5: str         # checksum of the source document

    def to_payload(self) -> dict:
        """Flatten this chunk into a plain dict, ready to be a Qdrant payload."""
        return asdict(self)