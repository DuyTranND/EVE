from src.utility.friendship import load_friendliness, save_friendliness


def test_round_trip(tmp_path):
    path = tmp_path / "friendly.txt"
    save_friendliness(path, 42.5)
    assert load_friendliness(path) == 42.5


def test_invalid_value_uses_default(tmp_path):
    path = tmp_path / "friendly.txt"
    path.write_text("not a number", encoding="utf-8")
    assert load_friendliness(path, default=70.0) == 70.0


def test_values_are_clamped(tmp_path):
    path = tmp_path / "friendly.txt"
    save_friendliness(path, 150)
    assert load_friendliness(path) == 100.0
