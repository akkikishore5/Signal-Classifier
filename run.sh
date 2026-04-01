#!/bin/bash
set -e

docker build -t hello-flask:1.0.1 .

# Remove the old image from minikube cache so the new build is used
minikube image rm hello-flask:1.0.1 2>/dev/null || true
minikube image load hello-flask:1.0.1

cd ./terraform
terraform init
terraform apply -auto-approve
cd ..

# Force Kubernetes to restart the pod and pick up the new image
kubectl rollout restart deployment/hello-flask
kubectl rollout status deployment/hello-flask --timeout=60s

echo ""
echo "App URL:"
minikube service hello-flask-svc --url

#DELETION COMMANDS
# terraform destroy -auto-approve
# minikube stop
# kubectl delete deployment