# RF Signal Classifier

A containerized REST API for collecting and classifying RF signals using multi-factor confidence scoring. Built with Python/Flask, deployed on Kubernetes (minikube) with infrastructure managed by Terraform.

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