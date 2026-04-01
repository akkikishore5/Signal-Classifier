#!/bin/bash

echo "Destroying Terraform resources..."
cd ./terraform
terraform destroy -auto-approve 2>/dev/null || true
cd ..

echo "Deleting Kubernetes resources..."
kubectl delete service hello-flask-svc 2>/dev/null || true
kubectl delete deployment hello-flask 2>/dev/null || true

echo "Removing images..."
minikube image rm hello-flask:1.0.1 2>/dev/null || true
docker rmi hello-flask:1.0.1 2>/dev/null || true

echo "Done. Run ./run.sh to rebuild."
