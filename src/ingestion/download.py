from pathlib import Path
from datasets import load_dataset
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATASET_ID = "Persius/hicric"
DATASET_REVISION = "main"
RAW_DIR = Path("data/raw/hicric")
CONFIG_NAMES = [
    "regulatory-guidance",
    "legal",
    "clinical-guidelines",
    ]

def download_corpus() -> None:

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for config_name in CONFIG_NAMES:
        logger.info(f"Starting download of {DATASET_ID}/{config_name} (revision: {DATASET_REVISION})")

        dataset = load_dataset(
            DATASET_ID,
            config_name,
            revision=DATASET_REVISION,
            cache_dir=str(RAW_DIR),
        )

        logger.info(f"Done: {config_name} | {dataset['train'].num_rows} records downaloaded")
    
    logger.info("All conffigured categories downloaded successfully.")

if __name__ == "__main__":
    download_corpus()