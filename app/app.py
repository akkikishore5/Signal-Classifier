# Flask for REST API, jsonify to convert python dict into json
from flask import Flask, jsonify, render_template

from models import db
from version import VERSION


# factory pattern
def create_app(config=None):
    # Create flask app
    app = Flask(__name__)

    # configure database URI
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///signals.db"

    # Disable bject modification tracking to reduce overhead
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # test injection
    if config:
        app.config.update(config)

    # Bind SQLAlchemy to instance
    db.init_app(app)

    # Push application context for database operations
    with app.app_context():
        # Create tables if they don't already exist.
        db.create_all()

    # Import and register /signals routes
    from routes import bp
    app.register_blueprint(bp)

    # Serve the frontend dashboard at the root URL
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/version")
    def version():
        return jsonify({"version": VERSION}), 200

    # Register the /health route directly for liveness/readiness probes
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


# Create the application instance
app = create_app()
