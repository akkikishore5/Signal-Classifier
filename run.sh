#!/bin/bash
docker build -t hello-flask:1.0.1 .

minikube image load hello-flask:1.0.1

cd ./terraform
terraform init
terraform apply -auto-approve

minikube service hello-flask-svc --url

#DELETION COMMANDS
# terraform destroy -auto-approve
# minikube stop
# kubectl delete deployment