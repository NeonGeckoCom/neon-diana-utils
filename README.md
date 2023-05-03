# Neon Diana
Device Independent API for Neon Applications (Diana) is a collection of microservices that provide various functionality 
to NeonAI systems. All services are implemented as standalone Docker containers.

Install the Diana utilities Python package with: `pip install neon-diana-utils`
The `diana` entrypoint is available to handle automated setup and some common administration tasks. You can see get detailed
help via `diana --help`.

## Backend
The Neon Backend is a collection of services that are provided to client applications.
Some backend services connect via a RabbitMQ server, while others are served via HTTP.

### Prerequisites
- `python3` is required to install `neon-diana-utils`
- `kubectl` and `helm` are needed to apply the generated configurations

### Configure Backend with `diana`
A Diana backend can be configured automatically with `diana configure-backend`. A standard example is included here, but 
a description of config options is available via: `diana configure-backend --help`.

```shell
diana configure-mq-backend ~/neon_diana
```
* `~/neon_diana` specifies the output path for configuration files

The above command will generate Helm charts and configuraiton files in 
`~/neon_diana/diana-backend`. For Docker deployment, the `diana.yaml` and
`rabbitmq.json` files from this directory can be used.

## Legacy Documentation
The below documentation is mostly applicable to Docker deployment of the Diana
backend and is no longer fully-supported. Documentation is retained here for
reference.

### Orchestrator Configuration
The following sections describe how to initialize a standard backend with 
[Docker](#docker-compose) or [Kubernetes](#kubernetes).

#### Docker Compose
For testing or running on a dedicated host, `Docker Compose` offers a simple method for starting a set of services.
This deployment assumes all services will run a single instance on a shared host with any configuration or other files 
saved to the host filesystem or a configured NFS share. The configuration files 
[generated earlier](#generate-config-with-diana) are all that is necessary to start the backend with Docker Compose

##### Running Configured Backend Services
After a backend is configured, it can be started with `diana start-backend`. A standard example is included here, but 
a description of config options is available via: `diana start-backend --help`.

> *Note*: If running private containers, you will need to authenticate with Docker.
> Documentation is available [from docker](https://docs.docker.com/engine/reference/commandline/login/).
> Containers from NeonGecko are published to the `ghcr.io` server

```shell
diana start-backend ~/neon_diana
```
* `~/neon_diana` specifies the path to backend configuration

##### Stopping a Running Backend
After a backend is started, it can be stopped with `diana stop-backend`. A standard example is included here, but 
a description of config options is available via: `diana stop-backend --help`.
```shell
diana stop-backend ~/neon_diana
```
* `~/neon_diana` specifies the path to backend configuration

#### Kubernetes
For deployment, Kubernetes provides a managed solution that can handle scaling, rolling updates, and other benefits.
This deployment assumes you have an existing cluster; it is assumed that the Cluster or system administrator will manage
creation of `PersistentVolume` and `LoadBalancer` objects as necessary.

##### Cluster Preparation
The config generation in this project assumes your cluster has the `NGINX Ingress Controller` deployed.
Installation instructions are available [from Kubernetes](https://kubernetes.github.io/ingress-nginx/deploy/).

The `ingress-nginx-controller` service should have External Endpoints exposed. If you are deploying locally, you may use
[MetalLB](https://metallb.universe.tf/) to configure a `LoadBalancer`.

The [Kubernets Cluser References section below](#kubernetes-cluster-references)
contains references to documentation and guides used to configure a cluster.

##### Providing GitHub Image Pull Secrets
For private container images, you will need to specify GitHub credentials. Documentation for creating GitHub Personal 
Access Tokens can be found [in the GitHub docs](https://docs.github.com/en/enterprise-cloud@latest/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).
The configured token must have the permission: `read:packages`.

```shell
diana make-api-secrets -u <github_username> -t <github_pat> ~/neon_diana
```

##### Providing Backend Service Credentials
Kubernetes uses [secrets](https://kubernetes.io/docs/concepts/configuration/secret/) to store sensitive data in a cluster.
Generate a Kubernetes secret spec with `ngi_auth_vars.yml` (`k8s_secret_ngi-auth.yml`).

```shell
diana make-api-secrets -p ~/.config/neon ~/neon_diana
```
* `-p` specifies the path to the directory containing `ngi_auth_vars.yml`
* `~/neon_diana` specifies the output path for configuration files

##### Defining Ingress

###### TCP Services
`diana` includes cli utilities for generating ingress definitions for non-http services.
In general, ingress definitions will be created or updated when relevant backend services are configured, but
the `diana add-tcp-service` entrypoint is also available to define these manually. Note that adding configuration
will modify existing spec files in the configured path.

###### HTTP Services
`diana` includes cli utilities for generating ingress rules for http services when using `ingress-nginx`.
It is assumed that the `ingress-nginx` and `cert-manager` namespaced services are deployed as described 
[below](#kubernetes-cluster-references) and that A Records are defined for all configured subdomains.

HTTP `Ingress` is namespaced, so the configurations generated here must be applied to the same namespace
as the HTTP `Service`s they forward to. The commands in this guide will assume everything is in the "default"
namespace unless otherwise specified.

```shell
# Create a certificate issuer (must be deployed to each namespace)
diana make-cert-issuer -e <email_address> ~/neon_diana

# Update an Ingress configuration for every HTTP service
diana add-ingress -s <service_name> -p <service_http_port> -h <url_for_service> ~/neon_diana
```

##### Applying Configuration to a Cluster
`kubectl` should be configured to reference the Kubernetes cluster you are deploying to.
If you are accessing private repositories, you will also need to configure the secret `github-auth`. Documentation 
can be found [in the Kubernetes docs](https://kubernetes.io/dkocs/tasks/configure-pod-container/pull-image-private-registry/).

```shell
# Apply configuration and secrets
kubectl apply -f ~/neon_diana/config/k8s_secret_mq-config.yml -f ~/neon_diana/config/k8s_config_rabbitmq.yml -f ~/neon_diana/k8s_secret_ngi-auth.yml

# If using ingress-nginx, apply those configurations
kubectl apply -f ~/neon_diana/ingress/k8s_config_tcp_services.yml
kubectl patch -n ingress-nginx service ingress-nginx-controller --patch-file ~/neon_diana/ingress/k8s_patch_nginx_service.yml

# If using HTTP services, apply ingress rules
kubectl apply -f ~/neon_diana/ingress/k8s_config_cert_issuer.yml -f ~/neon_diana/ingress/k8s_config_ingress.yml

# If using private images
kubectl apply -f ~/neon_diana/k8s_secret_github.yml

# Start backend services
kubectl apply -f ~/neon_diana/services/k8s_diana_backend.yml
```

# Kubernetes Cluster References
The following configurations were used at the time of writing this document:

- [ingress-nginx](https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.1.0/deploy/static/provider/cloud/deploy.yaml)
- [cert-manager](https://github.com/jetstack/cert-manager/releases/download/v1.6.1/cert-manager.yaml)

These guides also may be useful for configuration that isn't handled in this repository:

- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/deploy/)
- [cert-manager](https://cert-manager.io/docs/tutorials/acme/ingress/)
- [MetalLB](https://metallb.universe.tf/installation/)
- [GitHub Token Auth](https://dev.to/asizikov/using-github-container-registry-with-kubernetes-38fb)

### Certbot SSL
The definition below can be used to configure LetsEncrypt
```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    # The ACME server URL
    server: https://acme-v02.api.letsencrypt.org/directory
    # Email address used for ACME registration
    email: ${CERT_EMAIL}
    # Name of a secret used to store the ACME account private key
    privateKeySecretRef:
      name: letsencrypt-prod
    # Enable the HTTP-01 challenge provider
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Ingress Definitions
The definition below can be used to configure ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-backend
  annotations:
    cert-manager.io/issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - mqadmin.${domain}
      secretName: ${domain}-tls
  ingressClassName: nginx
  rules:
    - host: "mqadmin.${domain}"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: neon-rabbitmq
                port:
                  number: 15672
```
