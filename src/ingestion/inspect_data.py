from datasets import load_dataset
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATASET_ID = "Persius/hicric"
CONFIG_NAME = "clinical-guidelines"
RAW_DIR = "data/raw/hicric"

def inspect_corpus() -> None:

    logger.info(f"Loading {CONFIG_NAME} from local cache for inpection")

    dataset = load_dataset(
        DATASET_ID,
        CONFIG_NAME,
        cache_dir=RAW_DIR,
    )

    data = dataset["train"]

    logger.info(f"Total records in dataset: {len(data)}")

    first_record = data[0]
    logger.info(" ------- Inpecting first record -------")
    logger.info(f"Available fields: {list(first_record.keys())}")
    logger.info(f"Tags: {first_record['tags']}")
    logger.info(f"source URL: {first_record['source_url']}")
    logger.info(f"Date Accessed: {first_record['date_accessed']}")

    text = first_record['text']

    logger.info(f"Text length: {len(text)} characters")
    logger.info(f"Text preview: {text[:300]}")

    all_length = [len(record['text']) for record in data ]

    shortest = min(all_length)
    longest = max(all_length)
    average = sum(all_length) / len(all_length)

    logger.info("------- text length statistics")
    logger.info(f"shortest document: {shortest} characters")
    logger.info(f"longest document: {longest} characters")
    logger.info(f"average document length: {average:.2f} characters")

if __name__ == "__main__":
    inspect_corpus()
