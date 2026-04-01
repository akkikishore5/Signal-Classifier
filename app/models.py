# import SQLAlchemy for ORM
from flask_sqlalchemy import SQLAlchemy

# use datetime and zoneinfo to automatically timestamp signals
from datetime import datetime
from zoneinfo import ZoneInfo

# Create the SQLAlchemy instance 
db = SQLAlchemy()


# Create tables/schema
class Signal(db.Model):
    # set table name
    __tablename__ = "signals"

    # Primary key
    id                   = db.Column(db.Integer, primary_key=True)

    # Frequency in megahertz. Required field.
    frequency_mhz        = db.Column(db.Float, nullable=False)

    # bandwidth in mhz Required field.
    bandwidth_mhz        = db.Column(db.Float, nullable=False)

    # RSignal power in decibels per milliwatt.
    signal_strength_dbm  = db.Column(db.Float, nullable=False)

    # Modulation scheme
    modulation           = db.Column(db.String(64), nullable=False)

    # Pulses per second (radar)
    pulse_rate_pps       = db.Column(db.Float, nullable=True)

    # wavelength in meters
    wavelength_m         = db.Column(db.Float, nullable=False)

    # Geographic coordinates where the signal was collected.
    latitude             = db.Column(db.Float, nullable=False)
    longitude            = db.Column(db.Float, nullable=False)

    # log when the signal was submitted
    timestamp            = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("America/Chicago")), nullable=False)

    # The name of the best-matching signal profile 
    classification       = db.Column(db.String(128), nullable=True)

    # Confidence percentage (0-100) from the classifier's weighted scoring.
    confidence_score     = db.Column(db.Float, nullable=True)

    # Summary of the top 3 classification matches.
    classification_notes = db.Column(db.Text, nullable=True)

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
