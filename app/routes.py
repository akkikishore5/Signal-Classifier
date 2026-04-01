# Blueprint lets us define routes in a separate file from the main app.
# This keeps the code organized — app.py handles app setup, routes.py handles endpoints.
import csv
import io

from flask import Blueprint, request, jsonify, Response

# Import the database instance and Signal model from models.py
from models import db, Signal

# Import the classification function from classifier.py
from classifier import classify

# Create a Blueprint named "signals". app.py registers this with app.register_blueprint(bp).
bp = Blueprint("signals", __name__)

# Speed of light in m/s — used to calculate wavelength from frequency (c = fλ → λ = c/f)
SPEED_OF_LIGHT = 3e8

# Fields the client must provide when submitting a signal.
# wavelength_m is intentionally excluded — it's always calculated server-side.
REQUIRED_FIELDS = [
    "frequency_mhz", "bandwidth_mhz", "signal_strength_dbm",
    "modulation", "latitude", "longitude",
]


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

    # Create a new Signal object. SQLAlchemy maps each keyword argument to a column.
    signal = Signal(
        frequency_mhz       = float(data["frequency_mhz"]),
        bandwidth_mhz       = float(data["bandwidth_mhz"]),
        signal_strength_dbm = float(data["signal_strength_dbm"]),
        modulation          = str(data["modulation"]),
        # pulse_rate_pps is optional — use None if not provided
        pulse_rate_pps      = float(data["pulse_rate_pps"]) if data.get("pulse_rate_pps") is not None else None,
        wavelength_m        = wavelength,
        latitude            = float(data["latitude"]),
        longitude           = float(data["longitude"]),
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
    })

    # Write the classification results back to the database record
    signal.classification       = result["classification"]
    signal.confidence_score     = result["confidence_score"]
    signal.classification_notes = result["classification_notes"]
    db.session.commit()

    # Merge the full signal dict with the status field from the classifier result
    # (**dict unpacking combines two dicts into one)
    return jsonify({**signal.to_dict(), "status": result["status"]}), 200


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

        pr = row.get("pulse_rate_pps", "").strip()
        wavelength = SPEED_OF_LIGHT / (float(row["frequency_mhz"]) * 1e6)

        signal = Signal(
            frequency_mhz       = float(row["frequency_mhz"]),
            bandwidth_mhz       = float(row["bandwidth_mhz"]),
            signal_strength_dbm = float(row["signal_strength_dbm"]),
            modulation          = str(row["modulation"]).strip(),
            pulse_rate_pps      = float(pr) if pr else None,
            wavelength_m        = wavelength,
            latitude            = float(row["latitude"]),
            longitude           = float(row["longitude"]),
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
