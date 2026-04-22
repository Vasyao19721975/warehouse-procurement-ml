import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
RAW_STOCKS_DIR = os.path.join(RAW_DATA_DIR, "stocks")
RAW_SUPPLIES_DIR = os.path.join(RAW_DATA_DIR, "supplies")

PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

ALL_STOCKS_RAW_FILE = os.path.join(PROCESSED_DATA_DIR, "all_stocks_raw.csv")
ALL_SUPPLIES_FILE = os.path.join(PROCESSED_DATA_DIR, "all_supplies.csv")
ALL_STOCKS_MAIN_FILE = os.path.join(PROCESSED_DATA_DIR, "all_stocks_main.csv")
FINAL_DATASET_FILE = os.path.join(PROCESSED_DATA_DIR, "final_dataset.csv")
FINAL_OUTPUT_FILE = os.path.join(OUTPUTS_DIR, "final_recommendations.csv")

TARGET_DAYS = 7

MODEL_RANDOM_STATE = 42
MODEL_N_ESTIMATORS = 50
TEST_SIZE = 0.2