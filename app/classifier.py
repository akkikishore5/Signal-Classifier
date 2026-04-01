# Library of known signal profiles with expected ranges. 
# Classifier will score incoming signals against each profile and returns the best matches.
PROFILES = [
    {
        "name": "GPS L1",
        # frequency and tolerance in mhz
        "frequency_mhz": 1575.42, "freq_tol": 2.0,
        # bandwidth and tolerance in mhz
        "bandwidth_mhz": 2.0,     "bw_tol": 1.0,
        # Binary Phase Shift Keying/ Phase Shift Keying
        "modulation": "BPSK",     "mod_family": ["BPSK", "PSK"],
        # None refers to continuous wave 
        "pulse_rate_pps": None,
        #strength and tolerance in decibel-miliwatts
        "signal_strength_dbm": -130.0, "ss_tol": 20.0,
    },
    {
        "name": "GPS L2",
        "frequency_mhz": 1227.60, "freq_tol": 2.0,
        "bandwidth_mhz": 1.0,     "bw_tol": 0.5,
        "modulation": "BPSK",     "mod_family": ["BPSK", "PSK"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -133.0, "ss_tol": 20.0,
    },
    {
        "name": "FM Radio",
        "frequency_mhz": 98.0,    "freq_tol": 10.0,
        "bandwidth_mhz": 150.0,   "bw_tol": 50.0,
        "modulation": "WBFM",     "mod_family": ["WBFM", "FM"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -60.0, "ss_tol": 30.0,
    },
    {
        "name": "AM Radio",
        "frequency_mhz": 1.0,     "freq_tol": 0.5,
        "bandwidth_mhz": 0.010,   "bw_tol": 0.005,
        "modulation": "AM",       "mod_family": ["AM", "DSB"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -50.0, "ss_tol": 30.0,
    },
    {
        "name": "L-band Radar",
        # L-band: 1-2 GHz, used for long-range air search radars
        "frequency_mhz": 1300.0,  "freq_tol": 200.0,
        "bandwidth_mhz": 5.0,     "bw_tol": 3.0,
        "modulation": "PULSE",    "mod_family": ["PULSE"],
        # Pulse rate in pulses per second and its tolerance
        "pulse_rate_pps": 1000.0, "pr_tol": 400.0,
        "signal_strength_dbm": -40.0, "ss_tol": 25.0,
    },
    {
        "name": "S-band Radar",
        # S-band: 2-4 GHz,  used for fire control and tracking radars
        "frequency_mhz": 3000.0,  "freq_tol": 500.0,
        "bandwidth_mhz": 10.0,    "bw_tol": 5.0,
        "modulation": "PULSE",    "mod_family": ["PULSE"],
        "pulse_rate_pps": 500.0,  "pr_tol": 200.0,
        "signal_strength_dbm": -35.0, "ss_tol": 25.0,
    },
    {
        "name": "X-band Radar",
        # X-band: 8-12 GHz, used for maritime navigation and weapons guidance
        "frequency_mhz": 9500.0,  "freq_tol": 500.0,
        "bandwidth_mhz": 25.0,    "bw_tol": 10.0,
        "modulation": "PULSE",    "mod_family": ["PULSE"],
        "pulse_rate_pps": 1500.0, "pr_tol": 500.0,
        "signal_strength_dbm": -30.0, "ss_tol": 25.0,
    },
    {
        "name": "VHF Mil Comms",
        # VHF 30-300 MHz band used for tactical communications
        "frequency_mhz": 150.0,   "freq_tol": 30.0,
        "bandwidth_mhz": 0.025,   "bw_tol": 0.015,
        "modulation": "FM",       "mod_family": ["FM", "NBFM", "WBFM"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -80.0, "ss_tol": 30.0,
    },
    {
        "name": "UHF SATCOM",
        # UHF satellite communications used for beyond-line-of-sight comms
        "frequency_mhz": 360.0,   "freq_tol": 40.0,
        "bandwidth_mhz": 0.5,     "bw_tol": 0.25,
        "modulation": "PSK",      "mod_family": ["PSK", "BPSK", "QPSK"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -100.0, "ss_tol": 25.0,
    },
    {
        "name": "WiFi 2.4GHz",
        # IEEE 802.11 b/g/n channels span 2.4-2.5 GHz
        "frequency_mhz": 2437.0,  "freq_tol": 83.0,
        "bandwidth_mhz": 20.0,    "bw_tol": 2.0,
        "modulation": "OFDM",     "mod_family": ["OFDM"],
        "pulse_rate_pps": None,
        "signal_strength_dbm": -65.0, "ss_tol": 35.0,
    },
]


def _window_score(value, center, tolerance):
    """
    Scores how close a value is to an expected center, within a tolerance window.
    Returns 1.0 when value == center, decaying linearly to 0.0 at center ± tolerance.
    Returns 0.0 for anything outside the tolerance window.

    Example: center=1575, tolerance=2 → value 1575 scores 1.0, value 1576 scores 0.5,
    value 1577 scores 0.0.
    """
    if tolerance == 0:
        return 1.0 if value == center else 0.0
    return max(0.0, 1.0 - abs(value - center) / tolerance)


def _modulation_score(signal_mod, profile_mod, profile_family):
    """
    Categorical scoring for modulation type.
    Exact match (e.g. BPSK == BPSK) → 1.0
    Family match (e.g. BPSK in [BPSK, PSK] family) → 0.5
    No match → 0.0

    The family match handles the real-world case where an analyst labels a signal
    as "PSK" but the profile specifies "BPSK" — they're related but not identical.
    """
    sig = signal_mod.upper()
    if sig == profile_mod.upper():
        return 1.0
    if sig in [f.upper() for f in profile_family]:
        return 0.5
    return 0.0


def _score_against_profile(signal, profile):
    """
    Computes a weighted confidence score (0.0 to 1.0) for how well a signal
    matches a single profile. Each factor is scored independently then combined.

    Weights reflect how reliable each factor is as an identifier:
      40% frequency    — most definitive, each signal type occupies a specific band
      20% bandwidth    — narrows down signal type significantly
      20% modulation   — strong discriminator between comms, radar, and nav signals
      10% pulse rate   — key for distinguishing radar types from each other
      10% signal strength — useful context but highly environment-dependent
    """
    freq_score = _window_score(signal["frequency_mhz"], profile["frequency_mhz"], profile["freq_tol"])
    bw_score   = _window_score(signal["bandwidth_mhz"], profile["bandwidth_mhz"], profile["bw_tol"])
    mod_score  = _modulation_score(signal["modulation"], profile["modulation"], profile["mod_family"])
    ss_score   = _window_score(signal["signal_strength_dbm"], profile["signal_strength_dbm"], profile["ss_tol"])

    signal_pr  = signal.get("pulse_rate_pps")
    profile_pr = profile.get("pulse_rate_pps")

    # Pulse rate scoring handles all four combinations of presence/absence
    if profile_pr is None and signal_pr is None:
        pr_score = 1.0   # Both agree: continuous wave signal — strong positive match
    elif profile_pr is None and signal_pr is not None:
        pr_score = 0.0   # Profile expects CW, signal has pulses — definite mismatch
    elif profile_pr is not None and signal_pr is None:
        pr_score = 0.0   # Profile expects pulses, signal has none — definite mismatch
    else:
        pr_score = _window_score(signal_pr, profile_pr, profile["pr_tol"])

    return (
        0.40 * freq_score +
        0.20 * bw_score +
        0.20 * mod_score +
        0.10 * pr_score +
        0.10 * ss_score
    )


def classify(signal):
    """
    Main classification function. Scores the signal against every profile,
    sorts by confidence, and returns the top result with status label.

    Args:
        signal: dict with keys frequency_mhz, bandwidth_mhz, signal_strength_dbm,
                modulation, and optionally pulse_rate_pps.

    Returns:
        dict with classification name, confidence score (0-100), status string,
        and human-readable notes listing the top 3 matches.
    """
    # Score the signal against every known profile
    results = []
    for profile in PROFILES:
        score = _score_against_profile(signal, profile)
        # Multiply by 100 to express as a percentage
        results.append((profile["name"], round(score * 100, 1)))

    # Sort descending so the best match is first
    results.sort(key=lambda x: x[1], reverse=True)
    top3 = results[:3]
    top_name, top_pct = top3[0]

    # Confidence thresholds
    if top_pct >= 70.0:
        status = "HIGH CONFIDENCE"
    elif top_pct >= 40.0:
        status = "POSSIBLE MATCH"
    else:
        status = "UNKNOWN"

    # Summary of the top 3 matches
    notes = "Top 3: " + ", ".join(f"{name} ({pct}%)" for name, pct in top3)

    return {
        "classification":       top_name,
        "confidence_score":     top_pct,
        "status":               status,
        "classification_notes": notes,
    }
