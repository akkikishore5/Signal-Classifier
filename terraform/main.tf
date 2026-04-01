locals {
    app_name = "hello-flask"
    labels = {
        app = local.app_name
    }
}

resource "kubernetes_deployment_v1" "app" {
  metadata {
    name = local.app_name
    labels = local.labels
  }

  spec {
    replicas = 1

    selector {
        match_labels = local.labels
    }

    template {
        metadata {
            labels = local.labels
         }
        spec {
            container {
              name = local.app_name
              image = "${var.image_name}:${var.image_tag}"

              image_pull_policy = "Never"

              port{
                container_port = 5000
            }
                liveness_probe {
                http_get {
                    path = "/health"
                    port = 5000
                }
                initial_delay_seconds = 5
                period_seconds = 10
            }

            readiness_probe {
                http_get {
                    path = "/health"
                    port = 5000
                }
                initial_delay_seconds = 2
                period_seconds = 5
            }

            resources {
                requests = {
                   cpu = "100m"
                   memory = "64Mi"
                }

                limits = {
                    cpu = "250m"
                    memory = "128Mi"
                 }
                }
            }
            }
    }
  }
}

resource "kubernetes_service_v1" "svc" {
    metadata {
        name = "${local.app_name}-svc"
        labels = local.labels
    }

    spec {
        selector = local.labels

        port {
            port        = 80
            target_port = 5000
            node_port   = 30500
            protocol    = "TCP"
        }

        type = "NodePort"
    }
}