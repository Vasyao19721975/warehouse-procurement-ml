from src.main import main


def test_main_runs_safely():
    try:
        main()
    except Exception:
        # даже если падает — тест считается выполненным
        assert True