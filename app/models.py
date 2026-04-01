# SQLAlchemy is an ORM (Object Relational Mapper) — it lets us define database
# tables as Python classes and interact with them using Python instead of SQL.
from flask_sqlalchemy import SQLAlchemy

# datetime is used to automatically timestamp signals when they are created.
from datetime import datetime

# Create the SQLAlchemy instance without binding it to a Flask app yet.
# This pattern (sometimes called "lazy initialization") avoids circular imports —
# app.py imports db from here, and routes.py also imports db from here.
# The actual binding to the Flask app happens in app.py via db.init_app(app).
db = SQLAlchemy()


# Each class that inherits from db.Model becomes a database table.
# SQLAlchemy reads the Column definitions below and creates the schema.
class Signal(db.Model):
    # __tablename__ sets the actual table name in the database.
    # Without this, SQLAlchemy would default to "signal" (lowercase class name).
    __tablename__ = "signals"

    # Primary key — auto-incrementing integer, uniquely identifies each signal.
    id                   = db.Column(db.Integer, primary_key=True)

    # Center frequency of the signal in megahertz. Required field.
    frequency_mhz        = db.Column(db.Float, nullable=False)

    # Width of the frequency band the signal occupies. Required field.
    bandwidth_mhz        = db.Column(db.Float, nullable=False)

    # Received signal power in decibels relative to 1 milliwatt.
    # Negative values are typical — e.g. -128 dBm is a very weak signal.
    signal_strength_dbm  = db.Column(db.Float, nullable=False)

    # Modulation scheme — how data is encoded onto the carrier wave.
    # Examples: BPSK, QPSK, AM, FM, PULSE, OFDM.
    modulation           = db.Column(db.String(64), nullable=False)

    # Pulses per second — only relevant for pulsed signals like radar.
    # nullable=True means this column can be empty (continuous wave signals
    # like GPS or FM radio don't have a pulse rate).
    pulse_rate_pps       = db.Column(db.Float, nullable=True)

    # Physical wavelength in meters, derived from frequency using c = fλ.
    # Always auto-calculated server-side — never accepted from the client.
    wavelength_m         = db.Column(db.Float, nullable=False)

    # Geographic coordinates where the signal was collected.
    latitude             = db.Column(db.Float, nullable=False)
    longitude            = db.Column(db.Float, nullable=False)

    # When the signal was submitted. default=datetime.utcnow (without calling
    # it — no parentheses) tells SQLAlchemy to evaluate this at insert time,
    # not when the class is defined.
    timestamp            = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # The following three fields are null until POST /signals/<id>/classify is called.

    # The name of the best-matching signal profile (e.g. "GPS L1", "X-band Radar").
    classification       = db.Column(db.String(128), nullable=True)

    # Confidence percentage (0-100) from the classifier's weighted scoring.
    confidence_score     = db.Column(db.Float, nullable=True)

    # Human-readable summary of the top 3 classification matches.
    classification_notes = db.Column(db.Text, nullable=True)

    # Converts this database row into a plain Python dict so Flask can
    # serialize it to JSON. Called in routes.py before jsonify().
    def to_dict(self):
        return {
            "id":                   self.id,
            "frequency_mhz":        self.frequency_mhz,
            "bandwidth_mhz":        self.bandwidth_mhz,
            "signal_strength_dbm":  self.signal_strength_dbm,
            "modulation":           self.modulation,
            "pulse_rate_pps":       self.pulse_rate_pps,
            "wavelength_m":         self.wavelength_m,
            "latitude":             self.latitude,
            "longitude":            self.longitude,
            "timestamp":            self.timestamp.isoformat(),  # Convert to readable string
            "classification":       self.classification,
            "confidence_score":     self.confidence_score,
            "classification_notes": self.classification_notes,
        }
