from pathlib import Path
from datasets import load_dataset
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATASET_ID = "Persius/hicric"
DATASET_REVISION = "main"
RAW_DIR = Path("data/raw/hicric")
CONFIG_NAME = "regulatory-guidance"

def download_corpus() -> object:
    logger.info(f"Starting download of {DATASET_ID}/{CONFIG_NAME} (revision: {DATASET_REVISION})")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(
        DATASET_ID,
        CONFIG_NAME,
        revision=DATASET_REVISION,
        cache_dir=str(RAW_DIR),
    )

    logger.info(f"Download complete. Dataset structure: {dataset}")
    return dataset

if __name__ == "__main__":
    download_corpus()