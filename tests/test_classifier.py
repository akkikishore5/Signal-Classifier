import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

from classifier import classify

GPS_L1_SIGNAL = {
    "frequency_mhz": 1575.42,
    "bandwidth_mhz": 2.0,
    "signal_strength_dbm": -128.0,
    "modulation": "BPSK",
    "pulse_rate_pps": None,
}

XBAND_RADAR_SIGNAL = {
    "frequency_mhz": 9500.0,
    "bandwidth_mhz": 25.0,
    "signal_strength_dbm": -30.0,
    "modulation": "PULSE",
    "pulse_rate_pps": 1500.0,
}

UNKNOWN_SIGNAL = {
    "frequency_mhz": 5000.0,
    "bandwidth_mhz": 50.0,
    "signal_strength_dbm": -10.0,
    "modulation": "QAM",
    "pulse_rate_pps": None,
}


def test_gps_l1_high_confidence():
    result = classify(GPS_L1_SIGNAL)
    assert result["classification"] == "GPS L1"
    assert result["confidence_score"] >= 70.0
    assert result["status"] == "HIGH CONFIDENCE"


def test_xband_radar_high_confidence():
    result = classify(XBAND_RADAR_SIGNAL)
    assert result["classification"] == "X-band Radar"
    assert result["confidence_score"] >= 70.0
    assert result["status"] == "HIGH CONFIDENCE"


def test_unknown_signal_returns_unknown_status():
    result = classify(UNKNOWN_SIGNAL)
    assert result["status"] == "UNKNOWN"
    assert result["confidence_score"] < 40.0


def test_result_contains_top3_in_notes():
    result = classify(GPS_L1_SIGNAL)
    assert "Top 3:" in result["classification_notes"]


def test_classification_notes_contains_top_match():
    result = classify(GPS_L1_SIGNAL)
    assert "GPS L1" in result["classification_notes"]


def test_pulse_rate_mismatch_lowers_confidence():
    # GPS L1 is a continuous wave signal — adding a pulse rate should lower confidence
    signal_with_pulses = {**GPS_L1_SIGNAL, "pulse_rate_pps": 1000.0}
    result_clean = classify(GPS_L1_SIGNAL)
    result_with_pulses = classify(signal_with_pulses)
    assert result_with_pulses["confidence_score"] < result_clean["confidence_score"]
