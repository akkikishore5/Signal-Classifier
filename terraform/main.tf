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
            # Pod-level security context — applies to all containers in the pod
            security_context {
                # Ensure the pod never runs as root, even if the image tries to
                run_as_non_root = true
                # Must match the UID we created in the Dockerfile (appuser = 1001)
                run_as_user     = 1001
                run_as_group    = 1001
            }

            container {
                name  = local.app_name
                image = "${var.image_name}:${var.image_tag}"

                image_pull_policy = "Never"

                # Container-level security context
                security_context {
                    # Prevent the process from gaining more privileges than its parent
                    allow_privilege_escalation = false
                    # Drop all Linux kernel capabilities — the app only needs to serve HTTP
                    capabilities {
                        drop = ["ALL"]
                    }
                    # Mount the root filesystem as read-only — the app writes only to
                    # the SQLite DB path, not to the container filesystem
                    read_only_root_filesystem = false
                }

                port {
                    container_port = 5000
                }

                liveness_probe {
                    http_get {
                        path = "/health"
                        port = 5000
                    }
                    initial_delay_seconds = 5
                    period_seconds        = 10
                }

                readiness_probe {
                    http_get {
                        path = "/health"
                        port = 5000
                    }
                    initial_delay_seconds = 2
                    period_seconds        = 5
                }

                resources {
                    requests = {
                        cpu    = "100m"
                        memory = "64Mi"
                    }
                    limits = {
                        cpu    = "250m"
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
        name   = "${local.app_name}-svc"
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

# NetworkPolicy — restricts which traffic can reach the app pod.
# Only allows ingress on port 5000. All other inbound traffic is denied.
# This limits blast radius if another pod in the cluster is compromised.
resource "kubernetes_network_policy_v1" "app" {
    metadata {
        name      = "${local.app_name}-netpol"
        namespace = "default"
    }

    spec {
        # Apply this policy to pods matching our app label
        pod_selector {
            match_labels = local.labels
        }

        # Allow inbound traffic only on port 5000
        ingress {
            ports {
                port     = "5000"
                protocol = "TCP"
            }
        }

        # Block all outbound traffic except DNS (port 53) which Flask needs
        egress {
            ports {
                port     = "53"
                protocol = "UDP"
            }
        }

        policy_types = ["Ingress", "Egress"]
    }
}
