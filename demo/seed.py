"""
Demo seed script — submits and classifies a set of sample RF signals.

Usage:
    python3 demo/seed.py <base_url>

Example:
    python3 demo/seed.py http://127.0.0.1:51234
"""

import sys
import json
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Sample signals — each one is designed to produce a clear classification
# result so the dashboard looks interesting during a demo.
# ---------------------------------------------------------------------------
SIGNALS = [
    {
        "label": "GPS L1 (Washington DC area)",
        "frequency_mhz": 1575.42,
        "bandwidth_mhz": 2.0,
        "signal_strength_dbm": -128.0,
        "modulation": "BPSK",
        "latitude": 38.8977,
        "longitude": -77.0365,
    },
    {
        "label": "GPS L2 (Washington DC area)",
        "frequency_mhz": 1227.60,
        "bandwidth_mhz": 1.0,
        "signal_strength_dbm": -131.0,
        "modulation": "BPSK",
        "latitude": 38.8977,
        "longitude": -77.0365,
    },
    {
        "label": "X-band Radar (Atlantic coast)",
        "frequency_mhz": 9450.0,
        "bandwidth_mhz": 22.0,
        "signal_strength_dbm": -32.0,
        "modulation": "PULSE",
        "pulse_rate_pps": 1400.0,
        "latitude": 36.8508,
        "longitude": -75.9779,
    },
    {
        "label": "L-band Radar (Mid-Atlantic)",
        "frequency_mhz": 1280.0,
        "bandwidth_mhz": 4.5,
        "signal_strength_dbm": -42.0,
        "modulation": "PULSE",
        "pulse_rate_pps": 950.0,
        "latitude": 39.0458,
        "longitude": -76.6413,
    },
    {
        "label": "VHF Military Comms (Fort Meade area)",
        "frequency_mhz": 148.5,
        "bandwidth_mhz": 0.022,
        "signal_strength_dbm": -78.0,
        "modulation": "FM",
        "latitude": 39.1137,
        "longitude": -76.7741,
    },
    {
        "label": "UHF SATCOM (Eastern seaboard)",
        "frequency_mhz": 355.0,
        "bandwidth_mhz": 0.45,
        "signal_strength_dbm": -98.0,
        "modulation": "PSK",
        "latitude": 38.5976,
        "longitude": -75.0816,
    },
    {
        "label": "FM Radio Broadcast (DC)",
        "frequency_mhz": 99.5,
        "bandwidth_mhz": 145.0,
        "signal_strength_dbm": -55.0,
        "modulation": "WBFM",
        "latitude": 38.9072,
        "longitude": -77.0369,
    },
    {
        "label": "S-band Radar (Chesapeake Bay)",
        "frequency_mhz": 2950.0,
        "bandwidth_mhz": 9.0,
        "signal_strength_dbm": -38.0,
        "modulation": "PULSE",
        "pulse_rate_pps": 480.0,
        "latitude": 38.7784,
        "longitude": -76.0726,
    },
    {
        "label": "Unknown signal (anomalous)",
        "frequency_mhz": 4800.0,
        "bandwidth_mhz": 60.0,
        "signal_strength_dbm": -15.0,
        "modulation": "OFDM",
        "latitude": 37.4316,
        "longitude": -78.6569,
    },
]


def post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 demo/seed.py <base_url>")
        print("Example: python3 demo/seed.py http://127.0.0.1:51234")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    print(f"\nSeeding demo signals to {base}\n")
    print(f"{'#':<4} {'Signal':<42} {'Classification':<22} {'Confidence'}")
    print("-" * 85)

    for i, signal in enumerate(SIGNALS, 1):
        label = signal.pop("label")           # remove display label before sending
        payload = {k: v for k, v in signal.items()}

        # Submit the signal
        created = post(f"{base}/signals", payload)
        signal_id = created["id"]

        # Immediately classify it
        result = post(f"{base}/signals/{signal_id}/classify", {})

        classification = result.get("classification", "UNKNOWN")
        confidence = result.get("confidence_score", 0)
        status = result.get("status", "")

        print(f"{signal_id:<4} {label:<42} {classification:<22} {confidence}%  {status}")

    print(f"\nDone. {len(SIGNALS)} signals loaded. Open the dashboard to view them.\n")


if __name__ == "__main__":
    main()
