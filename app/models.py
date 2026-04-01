from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo

db = SQLAlchemy()


class Signal(db.Model):
    __tablename__ = "signals"

    id                   = db.Column(db.Integer, primary_key=True)
    frequency_mhz        = db.Column(db.Float, nullable=False)
    bandwidth_mhz        = db.Column(db.Float, nullable=False)
    signal_strength_dbm  = db.Column(db.Float, nullable=False)

    # Simplified modulation scheme: AM, FM, PM, ASK, PSK, FSK
    modulation           = db.Column(db.String(64), nullable=False)

    # Pulse parameters — only relevant for pulsed signals like radar
    pulse_rate_pps       = db.Column(db.Float, nullable=True)
    pulse_width_us       = db.Column(db.Float, nullable=True)

    # Auto-calculated from frequency server-side
    wavelength_m         = db.Column(db.Float, nullable=False)

    latitude             = db.Column(db.Float, nullable=False)
    longitude            = db.Column(db.Float, nullable=False)
    location_name        = db.Column(db.String(256), nullable=True)   # reverse-geocoded city/place name
    timestamp            = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("America/Chicago")), nullable=False)

    # Classification results — null until classify is called
    classification       = db.Column(db.String(128), nullable=True)
    confidence_score     = db.Column(db.Float, nullable=True)
    confidence_delta     = db.Column(db.Float, nullable=True)   # gap between #1 and #2 match
    signal_family        = db.Column(db.String(32), nullable=True)  # RADAR, COMMS, NAV, COMMERCIAL
    classification_notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id":                   self.id,
            "frequency_mhz":        self.frequency_mhz,
            "bandwidth_mhz":        self.bandwidth_mhz,
            "signal_strength_dbm":  self.signal_strength_dbm,
            "modulation":           self.modulation,
            "pulse_rate_pps":       self.pulse_rate_pps,
            "pulse_width_us":       self.pulse_width_us,
            "wavelength_m":         self.wavelength_m,
            "latitude":             self.latitude,
            "longitude":            self.longitude,
            "location_name":        self.location_name,
            "timestamp":            self.timestamp.isoformat(),
            "classification":       self.classification,
            "confidence_score":     self.confidence_score,
            "confidence_delta":     self.confidence_delta,
            "signal_family":        self.signal_family,
            "classification_notes": self.classification_notes,
        }
