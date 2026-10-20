from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def test_dashboard_starts():
    # Catches startup crashes; works with or without trained weights
    at = AppTest.from_file(str(APP), default_timeout=120).run()

    assert not at.exception
    assert at.title[0].value == "🔥 MichaelAI"
