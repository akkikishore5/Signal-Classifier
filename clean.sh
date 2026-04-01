#!/bin/bash

echo "Destroying Terraform resources..."
cd ./terraform
terraform destroy -auto-approve 2>/dev/null || true
cd ..

echo "Deleting Kubernetes resources..."
kubectl delete service hello-flask-svc 2>/dev/null || true
kubectl delete deployment hello-flask 2>/dev/null || true

echo "Removing all hello-flask images from minikube..."
minikube image ls 2>/dev/null | grep hello-flask | awk '{print $1}' | xargs -I{} minikube image rm {} 2>/dev/null || true

echo "Removing local Docker images..."
docker images hello-flask --format "{{.Repository}}:{{.Tag}}" | xargs docker rmi 2>/dev/null || true

echo "Done. Run ./run.sh to rebuild."
