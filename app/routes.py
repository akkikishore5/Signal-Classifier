# Blueprint lets us define routes in a separate file from the main app.
# This keeps the code organized — app.py handles app setup, routes.py handles endpoints.
import csv
import io

import requests as http
from flask import Blueprint, request, jsonify, Response

# Import the database instance and Signal model from models.py
from models import db, Signal

# Import the classification function from classifier.py
from classifier import classify

# Create a Blueprint named "signals". app.py registers this with app.register_blueprint(bp).
bp = Blueprint("signals", __name__)

_NOMINATIM_HEADERS = {"User-Agent": "rf-signal-classifier/1.0"}


def _reverse_geocode(lat, lon):
    """Return a human-readable city/place name for a lat/lon pair, or None on failure."""
    try:
        r = http.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=_NOMINATIM_HEADERS,
            timeout=5,
        )
        r.raise_for_status()
        addr    = r.json().get("address", {})
        city    = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
        country = addr.get("country", "")
        parts   = [p for p in [city, country] if p]
        return ", ".join(parts) if parts else None
    except Exception:
        return None


def _forward_geocode(city):
    """Return (lat, lon, display_name) for a city name, or None on failure."""
    try:
        r = http.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers=_NOMINATIM_HEADERS,
            timeout=5,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            return None
        best    = results[0]
        lat     = float(best["lat"])
        lon     = float(best["lon"])
        # Build a tidy display name from address components if available
        addr    = best.get("address", {})
        city_n  = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
        country = addr.get("country", "")
        parts   = [p for p in [city_n, country] if p]
        name    = ", ".join(parts) if parts else best.get("display_name", city)
        return lat, lon, name
    except Exception:
        return None

# Speed of light in m/s — used to calculate wavelength from frequency (c = fλ → λ = c/f)
SPEED_OF_LIGHT = 3e8

# Fields the client must provide when submitting a signal.
# wavelength_m is intentionally excluded — it's always calculated server-side.
REQUIRED_FIELDS = [
    "frequency_mhz", "bandwidth_mhz", "signal_strength_dbm",
    "modulation", "latitude", "longitude",
]


@bp.post("/geocode")
def geocode():
    """
    Dual-purpose geocoding endpoint.
    - Send {"city": "Washington DC"}        → returns {lat, lng, location_name}
    - Send {"lat": 38.89, "lng": -77.03}   → returns {location_name}
    """
    data = request.get_json(silent=True) or {}

    if "city" in data:
        result = _forward_geocode(data["city"])
        if not result:
            return jsonify({"error": "City not found"}), 404
        lat, lon, name = result
        return jsonify({"lat": lat, "lng": lon, "location_name": name}), 200

    if "lat" in data and "lng" in data:
        name = _reverse_geocode(float(data["lat"]), float(data["lng"]))
        if not name:
            return jsonify({"error": "Location not found"}), 404
        return jsonify({"location_name": name}), 200

    return jsonify({"error": "Provide either 'city' or 'lat'+'lng'"}), 400


@bp.post("/signals")
def create_signal():
    """
    Submit a new signal for storage.
    Validates required fields, auto-calculates wavelength, and saves to the database.
    Returns the created signal as JSON with HTTP 201 Created.
    """
    # Parse JSON body — silent=True returns None instead of raising an error
    # if the body is missing or not valid JSON. The `or {}` handles the None case.
    data = request.get_json(silent=True) or {}

    # Check all required fields are present and return a helpful error if not.
    # This is input validation at the API boundary — we never trust client input.
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    # Derive wavelength from frequency using the wave equation: λ = c / f
    # Convert MHz to Hz by multiplying by 1e6 before dividing
    wavelength = SPEED_OF_LIGHT / (float(data["frequency_mhz"]) * 1e6)

    lat = float(data["latitude"])
    lon = float(data["longitude"])

    # If the client sent a city name it was already resolved to lat/lon on the frontend.
    # Use whatever location_name they supply; fall back to reverse geocoding from lat/lon.
    location_name = data.get("location_name") or _reverse_geocode(lat, lon)

    # Create a new Signal object. SQLAlchemy maps each keyword argument to a column.
    signal = Signal(
        frequency_mhz       = float(data["frequency_mhz"]),
        bandwidth_mhz       = float(data["bandwidth_mhz"]),
        signal_strength_dbm = float(data["signal_strength_dbm"]),
        modulation          = str(data["modulation"]),
        # pulse parameters are optional — only relevant for pulsed signals like radar
        pulse_rate_pps      = float(data["pulse_rate_pps"]) if data.get("pulse_rate_pps") is not None else None,
        pulse_width_us      = float(data["pulse_width_us"]) if data.get("pulse_width_us") is not None else None,
        wavelength_m        = wavelength,
        latitude            = lat,
        longitude           = lon,
        location_name       = location_name,
    )

    # Stage the new record and write it to the database
    db.session.add(signal)
    db.session.commit()

    # Return the saved signal (now including its auto-assigned id and timestamp)
    return jsonify(signal.to_dict()), 201


@bp.get("/signals")
def list_signals():
    """
    Retrieve all stored signals.
    Uses SQLAlchemy 2.0-style select() query instead of the legacy Model.query interface.
    Returns a JSON array, empty array if no signals exist.
    """
    # db.select(Signal) builds a SELECT * FROM signals query
    # .scalars().all() executes it and returns a flat list of Signal objects
    signals = db.session.execute(db.select(Signal)).scalars().all()
    return jsonify([s.to_dict() for s in signals]), 200


@bp.get("/signals/<int:signal_id>")
def get_signal(signal_id):
    """
    Retrieve a single signal by ID.
    db.get_or_404 looks up by primary key and automatically returns a 404
    response if no record exists — no manual if/else needed.
    """
    signal = db.get_or_404(Signal, signal_id)
    return jsonify(signal.to_dict()), 200


@bp.post("/signals/<int:signal_id>/classify")
def classify_signal(signal_id):
    """
    Run the classifier on a stored signal and persist the result.
    The signal must already exist (submitted via POST /signals first).
    Returns the full signal with classification fields populated plus a status label.
    """
    signal = db.get_or_404(Signal, signal_id)

    # Pass only the fields the classifier needs — it doesn't need the database ID,
    # timestamps, or location data, so we don't expose those to the business logic layer.
    result = classify({
        "frequency_mhz":       signal.frequency_mhz,
        "bandwidth_mhz":       signal.bandwidth_mhz,
        "signal_strength_dbm": signal.signal_strength_dbm,
        "modulation":          signal.modulation,
        "pulse_rate_pps":      signal.pulse_rate_pps,
        "pulse_width_us":      signal.pulse_width_us,
    })

    # Write the classification results back to the database record
    signal.classification       = result["classification"]
    signal.confidence_score     = result["confidence_score"]
    signal.confidence_delta     = result["confidence_delta"]
    signal.signal_family        = result["signal_family"]
    signal.classification_notes = result["classification_notes"]
    db.session.commit()

    # Merge the full signal dict with the status field from the classifier result
    # (**dict unpacking combines two dicts into one)
    return jsonify({**signal.to_dict(), "status": result["status"]}), 200


CSV_FIELDS = [
    "id", "frequency_mhz", "bandwidth_mhz", "signal_strength_dbm",
    "modulation", "pulse_rate_pps", "pulse_width_us", "wavelength_m",
    "latitude", "longitude", "location_name",
    "timestamp", "classification", "confidence_score", "confidence_delta",
    "signal_family", "classification_notes",
]


@bp.post("/signals/classify-all")
def classify_all():
    unclassified = db.session.execute(
        db.select(Signal).where(Signal.classification == None)
    ).scalars().all()

    for signal in unclassified:
        result = classify({
            "frequency_mhz":       signal.frequency_mhz,
            "bandwidth_mhz":       signal.bandwidth_mhz,
            "signal_strength_dbm": signal.signal_strength_dbm,
            "modulation":          signal.modulation,
            "pulse_rate_pps":      signal.pulse_rate_pps,
            "pulse_width_us":      signal.pulse_width_us,
        })
        signal.classification       = result["classification"]
        signal.confidence_score     = result["confidence_score"]
        signal.confidence_delta     = result["confidence_delta"]
        signal.signal_family        = result["signal_family"]
        signal.classification_notes = result["classification_notes"]

    db.session.commit()
    return jsonify({"classified": len(unclassified)}), 200


@bp.get("/signals/export")
def export_csv():
    signals = db.session.execute(db.select(Signal)).scalars().all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for s in signals:
        writer.writerow(s.to_dict())

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=signals.csv"},
    )


@bp.post("/signals/import")
def import_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "File must be a .csv"}), 400

    content = file.read().decode("utf-8-sig")
    reader  = csv.DictReader(io.StringIO(content))
    imported = 0
    skipped  = 0

    for row in reader:
        if not all(row.get(f, "").strip() for f in REQUIRED_FIELDS):
            skipped += 1
            continue

        pr   = row.get("pulse_rate_pps", "").strip()
        pw   = row.get("pulse_width_us", "").strip()
        loc  = row.get("location_name", "").strip() or None
        lat  = float(row["latitude"])
        lon  = float(row["longitude"])
        wavelength = SPEED_OF_LIGHT / (float(row["frequency_mhz"]) * 1e6)

        signal = Signal(
            frequency_mhz       = float(row["frequency_mhz"]),
            bandwidth_mhz       = float(row["bandwidth_mhz"]),
            signal_strength_dbm = float(row["signal_strength_dbm"]),
            modulation          = str(row["modulation"]).strip(),
            pulse_rate_pps      = float(pr) if pr else None,
            pulse_width_us      = float(pw) if pw else None,
            wavelength_m        = wavelength,
            latitude            = lat,
            longitude           = lon,
            location_name       = loc,
        )
        db.session.add(signal)
        imported += 1

    db.session.commit()
    return jsonify({"imported": imported, "skipped": skipped}), 201


@bp.delete("/signals/<int:signal_id>")
def delete_signal(signal_id):
    """
    Delete a signal by ID. Returns a confirmation message.
    Returns 404 automatically if the signal doesn't exist.
    """
    signal = db.get_or_404(Signal, signal_id)
    db.session.delete(signal)
    db.session.commit()
    return jsonify({"message": f"Signal {signal_id} deleted"}), 200
