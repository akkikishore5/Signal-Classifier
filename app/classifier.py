PROFILES = [
    {
        "name": "GPS L1",
        "family": "NAV",
        "frequency_mhz": 1575.42, "freq_tol": 2.0,
        "bandwidth_mhz": 2.0,     "bw_tol": 1.0,
        "modulation": "PSK",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -130.0, "ss_tol": 20.0,
    },
    {
        "name": "GPS L2",
        "family": "NAV",
        "frequency_mhz": 1227.60, "freq_tol": 2.0,
        "bandwidth_mhz": 1.0,     "bw_tol": 0.5,
        "modulation": "PSK",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -133.0, "ss_tol": 20.0,
    },
    {
        "name": "FM Radio",
        "family": "COMMERCIAL",
        "frequency_mhz": 98.0,    "freq_tol": 10.0,
        "bandwidth_mhz": 150.0,   "bw_tol": 50.0,
        "modulation": "FM",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -60.0, "ss_tol": 30.0,
    },
    {
        "name": "AM Radio",
        "family": "COMMERCIAL",
        "frequency_mhz": 1.0,     "freq_tol": 0.5,
        "bandwidth_mhz": 0.010,   "bw_tol": 0.005,
        "modulation": "AM",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -50.0, "ss_tol": 30.0,
    },
    {
        "name": "L-band Radar",
        # L-band 1-2 GHz: long-range air search. Uses LFM chirp → FM modulation.
        # Relatively long pulse width (~50 µs) for range resolution.
        "family": "RADAR",
        "frequency_mhz": 1300.0,  "freq_tol": 200.0,
        "bandwidth_mhz": 5.0,     "bw_tol": 3.0,
        "modulation": "FM",
        "pulse_rate_pps": 1000.0, "pr_tol": 400.0,
        "pulse_width_us": 50.0,   "pw_tol": 20.0,
        "signal_strength_dbm": -40.0, "ss_tol": 25.0,
    },
    {
        "name": "S-band Radar",
        # S-band 2-4 GHz: fire control and tracking. Shorter pulse for better resolution.
        "family": "RADAR",
        "frequency_mhz": 3000.0,  "freq_tol": 500.0,
        "bandwidth_mhz": 10.0,    "bw_tol": 5.0,
        "modulation": "FM",
        "pulse_rate_pps": 500.0,  "pr_tol": 200.0,
        "pulse_width_us": 25.0,   "pw_tol": 10.0,
        "signal_strength_dbm": -35.0, "ss_tol": 25.0,
    },
    {
        "name": "X-band Radar",
        # X-band 8-12 GHz: weapons guidance and maritime navigation.
        # Short pulse width for fine range resolution.
        "family": "RADAR",
        "frequency_mhz": 9500.0,  "freq_tol": 500.0,
        "bandwidth_mhz": 25.0,    "bw_tol": 10.0,
        "modulation": "FM",
        "pulse_rate_pps": 1500.0, "pr_tol": 500.0,
        "pulse_width_us": 10.0,   "pw_tol": 5.0,
        "signal_strength_dbm": -30.0, "ss_tol": 25.0,
    },
    {
        "name": "VHF Mil Comms",
        # VHF 30-300 MHz: tactical voice communications (e.g. SINCGARS).
        # Analog FM, narrow bandwidth, no pulse structure.
        "family": "COMMS",
        "frequency_mhz": 150.0,   "freq_tol": 30.0,
        "bandwidth_mhz": 0.025,   "bw_tol": 0.015,
        "modulation": "FM",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -80.0, "ss_tol": 30.0,
    },
    {
        "name": "UHF SATCOM",
        # UHF 300-3000 MHz: beyond-line-of-sight satellite communications.
        # PSK modulation, narrowband.
        "family": "COMMS",
        "frequency_mhz": 360.0,   "freq_tol": 40.0,
        "bandwidth_mhz": 0.5,     "bw_tol": 0.25,
        "modulation": "PSK",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -100.0, "ss_tol": 25.0,
    },
    {
        "name": "HF FHSS Comms",
        # HF 3-30 MHz: frequency hopping spread spectrum used in military HF links.
        # FSK modulation, wider bandwidth due to hopping.
        "family": "COMMS",
        "frequency_mhz": 15.0,    "freq_tol": 12.0,
        "bandwidth_mhz": 3.0,     "bw_tol": 1.5,
        "modulation": "FSK",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -70.0, "ss_tol": 30.0,
    },
    {
        "name": "WiFi 2.4GHz",
        # IEEE 802.11: PSK subcarriers on OFDM. Classified as PSK at the base level.
        "family": "COMMERCIAL",
        "frequency_mhz": 2437.0,  "freq_tol": 83.0,
        "bandwidth_mhz": 20.0,    "bw_tol": 2.0,
        "modulation": "PSK",
        "pulse_rate_pps": None,
        "pulse_width_us": None,
        "signal_strength_dbm": -65.0, "ss_tol": 35.0,
    },
]


def _window_score(value, center, tolerance):
    """
    Linear decay score: 1.0 at center, 0.0 at center ± tolerance.
    Returns 0.0 for anything outside the window.
    """
    if tolerance == 0:
        return 1.0 if value == center else 0.0
    return max(0.0, 1.0 - abs(value - center) / tolerance)


def _modulation_score(signal_mod, profile_mod):
    """
    Exact match = 1.0, no match = 0.0.
    With the simplified 6-type taxonomy there are no partial family matches —
    either the modulation matches the profile or it doesn't.
    """
    return 1.0 if signal_mod.upper() == profile_mod.upper() else 0.0


def _score_against_profile(signal, profile):
    """
    Weighted confidence score (0.0 to 1.0) for how well a signal matches a profile.

    Revised weights vs original:
      30% frequency     — necessary but not sufficient; multiple signal types share bands
      20% bandwidth     — strong discriminator between narrowband comms and wideband radar
      25% modulation    — increased because simplified taxonomy makes matches more meaningful
      10% pulse rate    — key for radar type discrimination
      10% pulse width   — added: short pulse = high-resolution radar, long pulse = search radar
       5% signal strength — reduced: too environment-dependent to be reliable
    """
    freq_score = _window_score(signal["frequency_mhz"], profile["frequency_mhz"], profile["freq_tol"])
    bw_score   = _window_score(signal["bandwidth_mhz"], profile["bandwidth_mhz"], profile["bw_tol"])
    mod_score  = _modulation_score(signal["modulation"], profile["modulation"])
    ss_score   = _window_score(signal["signal_strength_dbm"], profile["signal_strength_dbm"], profile["ss_tol"])

    # Pulse rate scoring
    signal_pr  = signal.get("pulse_rate_pps")
    profile_pr = profile.get("pulse_rate_pps")
    if profile_pr is None and signal_pr is None:
        pr_score = 1.0  
    elif profile_pr is None and signal_pr is not None:
        pr_score = 0.0   
    elif profile_pr is not None and signal_pr is None:
        pr_score = 0.0  
    else:
        pr_score = _window_score(signal_pr, profile_pr, profile["pr_tol"])

    # Pulse width scoring
    signal_pw  = signal.get("pulse_width_us")
    profile_pw = profile.get("pulse_width_us")
    if profile_pw is None and signal_pw is None:
        pw_score = 1.0
    elif profile_pw is None and signal_pw is not None:
        pw_score = 0.0
    elif profile_pw is not None and signal_pw is None:
        pw_score = 0.0
    else:
        pw_score = _window_score(signal_pw, profile_pw, profile["pw_tol"])

    return (
        0.30 * freq_score +
        0.20 * bw_score +
        0.25 * mod_score +
        0.10 * pr_score +
        0.10 * pw_score +
        0.05 * ss_score
    )


def classify(signal):
    """
    Score the signal against every profile and return the best match.

    Returns:
        classification       — name of the top-matching profile
        confidence_score     — percentage (0-100) of the top match
        confidence_delta     — gap between #1 and #2 match (higher = more certain)
        signal_family        — operational category of the top match
        status               — HIGH CONFIDENCE / POSSIBLE MATCH / UNKNOWN
        classification_notes — top 3 matches with scores
    """
    results = []
    for profile in PROFILES:
        score = _score_against_profile(signal, profile)
        results.append((profile["name"], profile["family"], round(score * 100, 1)))

    results.sort(key=lambda x: x[2], reverse=True)

    top_name, top_family, top_pct  = results[0]
    _, _, second_pct               = results[1]

    # Confidence delta: how far ahead of the next best match.
    # A large delta means the classifier is highly certain; small delta means ambiguous.
    delta = round(top_pct - second_pct, 1)

    if top_pct >= 70.0:
        status = "HIGH CONFIDENCE"
    elif top_pct >= 40.0:
        status = "POSSIBLE MATCH"
    else:
        status = "UNKNOWN"

    top3  = results[:3]
    notes = "Top 3: " + ", ".join(f"{n} ({p}%)" for n, _, p in top3)

    return {
        "classification":       top_name,
        "confidence_score":     top_pct,
        "confidence_delta":     delta,
        "signal_family":        top_family,
        "status":               status,
        "classification_notes": notes,
    }
