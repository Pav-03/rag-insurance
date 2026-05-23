from datasets import load_dataset
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATASET_ID = "Persius/hicric"
DATASET_REVISION = "main"
RAW_DIR = "data/raw/hicric"