"""Calibration, time handling, sequence validation, and device isolation."""

from backend.ingestion.processor import IngestionProcessor
from backend.processing.signal_processor import SignalProcessor
from backend.thermal.engine import ThermalEngine


def payload(**changes):
    return dict(
        device_id="Sensor-A",
        food_type="tomato",
        temperature_c=25,
        humidity_pct=60,
        voc_raw=31800,
        nox_raw=16800,
        **changes,
    )


def test_calibration_requires_the_configured_sample_window(tmp_path):
    ingestor, signal = IngestionProcessor(tmp_path), SignalProcessor(baseline_window=5)
    readings = [signal.process(ingestor.process(payload())) for _ in range(5)]
    assert [r.baseline_established for r in readings] == [False, False, False, False, True]


def test_duplicate_and_reordered_packets_are_not_stored(tmp_path):
    ingestor = IngestionProcessor(tmp_path)
    assert ingestor.process(payload(sequence_number=2)) is not None
    assert ingestor.process(payload(sequence_number=2)) is None
    assert ingestor.process(payload(sequence_number=1)) is None
    assert ingestor.process(payload(sequence_number=3)) is not None
    assert len(next(tmp_path.rglob("*.jsonl")).read_text().splitlines()) == 2


def test_zero_elapsed_time_does_not_add_thermal_exposure(tmp_path):
    ingestor, signal = IngestionProcessor(tmp_path), SignalProcessor()
    thermal = ThermalEngine()
    for _ in range(2):
        reading = signal.process(ingestor.process(payload(), received_at="2026-11-04T12:00:00Z"))
        state = thermal.calculate_risk(reading)
    assert state["thermal_exposure"] == 0
