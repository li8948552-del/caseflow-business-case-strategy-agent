import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "benchmark_catalog.py"
SPEC = importlib.util.spec_from_file_location("benchmark_catalog", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
benchmark_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_catalog)


def test_catalog_is_valid() -> None:
    data = benchmark_catalog.load_catalog(benchmark_catalog.DEFAULT_CATALOG)
    assert benchmark_catalog.validate_catalog(data) == []
    assert len(data["decks"]) == 13


def test_blind_fields_cover_labels() -> None:
    assert {
        "placement",
        "placement_verified",
        "team",
        "learning_focus",
    } <= benchmark_catalog.BLIND_FIELDS


def test_ranked_evaluation_sets_are_complete() -> None:
    data = benchmark_catalog.load_catalog(benchmark_catalog.DEFAULT_CATALOG)
    calibration = benchmark_catalog.select(data, "calibration")
    holdout = benchmark_catalog.select(data, "holdout")
    assert {deck["placement"] for deck in calibration} == {1, 2, 3}
    assert {deck["placement"] for deck in holdout} == {1, 2, 3}
    assert len({deck["case_company"] for deck in calibration}) == 1
    assert len({deck["case_company"] for deck in holdout}) == 1

