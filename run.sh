#!/bin/bash
set -e

TAG=$(git rev-parse --short HEAD)
IMAGE="hello-flask:$TAG"

echo "Building image: $IMAGE"
docker build --no-cache -t "$IMAGE" .

echo "Loading image into minikube..."
minikube image rm "$IMAGE" 2>/dev/null || true
minikube image load "$IMAGE"

echo "Deploying with Terraform..."
cd ./terraform
terraform init -input=false
terraform apply -auto-approve -var="image_tag=$TAG"
cd ..

echo "Restarting deployment..."
kubectl rollout restart deployment/hello-flask
kubectl rollout status deployment/hello-flask --timeout=60s

echo ""
echo "App URL:"
minikube service hello-flask-svc --url
