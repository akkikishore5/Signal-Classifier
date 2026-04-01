# RF Signal Classifier

A containerized REST API for collecting and classifying RF signals using multi-factor confidence scoring. Built with Python/Flask, deployed to Kubernetes via Terraform.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Tier 1        │     │   Tier 2        │     │   Tier 3        │
│   Frontend      │────▶│   Flask API     │────▶│   SQLite DB     │
│   (Jinja2/HTML) │     │   (Python)      │     │   (SQLAlchemy)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                        ┌───────┴───────┐
                        │  Classifier   │
                        │  (10 signal   │
                        │   profiles)   │
                        └───────────────┘
```

Deployed on Kubernetes (minikube) with infrastructure managed by Terraform.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

## Running the Project

**1. Start minikube**
```bash
minikube start
```

**2. Run the full build and deploy script**
```bash
./run.sh
```

This will:
- Build the Docker image
- Load it into minikube
- Run `terraform init` and `terraform apply`
- Print the URL to access the app

**3. Open the URL printed by the script in your browser**

The dashboard will be available at the printed URL (e.g. `http://127.0.0.1:XXXXX`).

**4. (Optional) Load demo data**
```bash
python3 demo/seed.py <URL>
```
Replace `<URL>` with the URL from step 3. This submits and classifies a set of sample signals.

## Running Tests

```bash
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Frontend dashboard |
| `GET` | `/health` | Health check (used by Kubernetes probes) |
| `POST` | `/signals` | Submit a new signal |
| `GET` | `/signals` | List all signals |
| `GET` | `/signals/<id>` | Get a single signal |
| `POST` | `/signals/<id>/classify` | Classify a signal |
| `DELETE` | `/signals/<id>` | Delete a signal |

### Example: Submit and classify a GPS L1 signal

```bash
# Submit
curl -X POST <URL>/signals \
  -H "Content-Type: application/json" \
  -d '{
    "frequency_mhz": 1575.42,
    "bandwidth_mhz": 2.0,
    "signal_strength_dbm": -128,
    "modulation": "BPSK",
    "latitude": 38.8977,
    "longitude": -77.0365
  }'

# Classify
curl -X POST <URL>/signals/1/classify
```

## Signal Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `frequency_mhz` | float | Yes | Center frequency in MHz |
| `bandwidth_mhz` | float | Yes | Signal bandwidth in MHz |
| `signal_strength_dbm` | float | Yes | Received power in dBm |
| `modulation` | string | Yes | Modulation type (BPSK, FM, PULSE, etc.) |
| `latitude` | float | Yes | Collection latitude |
| `longitude` | float | Yes | Collection longitude |
| `pulse_rate_pps` | float | No | Pulses per second (radar signals only) |
| `wavelength_m` | float | Auto | Auto-calculated from frequency — do not submit |

## Classifier

Signals are scored against 10 known profiles using weighted factors:

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Frequency | 40% | Most definitive identifier |
| Bandwidth | 20% | Narrows down signal type |
| Modulation | 20% | Discriminates comms vs radar vs nav |
| Pulse rate | 10% | Key for radar type identification |
| Signal strength | 10% | Environment-dependent, used as supporting evidence |

**Confidence thresholds:**
- `HIGH CONFIDENCE` — ≥ 70%
- `POSSIBLE MATCH` — ≥ 40%
- `UNKNOWN` — < 40%

## CI/CD Pipeline

GitHub Actions runs on every push to `main`:

```
push → [run tests] → [build image] → [Trivy security scan] → [push to Docker Hub]
```

The build will fail if any unit tests fail or if critical CVEs are found in the image.

## Teardown

```bash
cd terraform
terraform destroy -auto-approve
minikube stop
```
