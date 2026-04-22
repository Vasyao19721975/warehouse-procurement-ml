from src import config


def test_config_constants_exist():
    assert config.TARGET_DAYS == 7
    assert isinstance(config.PROCESSED_DATA_DIR, str)
    assert isinstance(config.FINAL_OUTPUT_FILE, str)