# Deployment via Helm Charts
[Helm](https://helm.sh/) is a standard framework for deploying Kubernetes applications.
The Helm charts for Neon Diana are the recommended method for production deployment.

## Ingress
An NGINX ingress chart is provided at `helm_charts/ingress-nginx`. `values.yaml`
may be updated to include any additional TCP ports to be used (i.e. for RabbitMQ)
and then the chart is generally deployed to the `ingress-nginx` namespace. Only
one ingress is necessary for a cluster.

## Backend
With Ingress applied, deploy the backend services with `helm_charts/diana-backend`.
Update `values.yaml` and ensure `diana.yaml` is defined in that directory.