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
- `docker` should be installed and executable by the user running `diana`
- If installing to a Kubernetes cluster, `kubectl` is needed to apply the generated configurations
- For any Neon services that require authentication, [`ngi_auth_vars.yml`](#ngi_auth_varsyml) is required.
- If configuring private containers (which is not default), `docker` and/or `kubectl` should have credentials configured

#### ngi_auth_vars.yml
Below is an example `ngi_auth_vars.yml` file (passwords redacted)
```yaml
track_my_brands:
  user: admintr1_drup1
  password: 
  host: trackmybrands.com
  database: admintr1_drup1
emails:
  mail: neon@neon.ai
  pass: 
  host: smtp.gmail.com
  port: '465'
api_services:
  wolfram_alpha:
    api_key: ""
  alpha_vantage:
    api_key: ""
  open_weather_map:
    api_key: ""
```
* The `emails` config should reference a smtp email account used in `neon-email-proxy`
* The `api_services` config should reference services used in `neon-api-proxy`
* The `track_my_brands` config provides credentials for the `neon-brands-service`

### RabbitMQ Configuration
All containers containing an MQ module will expect `mq_config.json` to specify credentials.
`neon-rabbitmq` will expect `/config/rabbitmq.conf` to specify a path to the configuration `.json` file to load.
An example configuration directory structure is [included below](#example-configuration-file-structure); these config
files may be generated automatically using `diana`.

#### Generate Config with `diana`
A Diana backend can be configured automatically with `diana configure-backend`. A standard example is included here, but 
a description of config options is available via: `diana configure-backend --help`.

```shell
diana configure-backend -d -u administrator -p password ~/neon_diana
```
* `-d` specifies that default backend services will be configured
* `-u` specifies the MQ user `administrator` for admin portal access
* `-p` specifies the password `password` for the `administrator` user
* `~/neon_diana` specifies the output path for configuration files

The above command will generate RabbitMQ users with randomized passwords and generate 
`mq_config.json`, `rabbitmq.conf`, and `rabbit_mq_config.json` files for all users required
for the specified backend services.

#### Example configuration file structure
```
$NEON_CONFIG_DIR
├── mq_config.json
├── ngi_auth_vars.yml
├── rabbitmq.conf
└── rabbit_mq_config.json
```

`mq_config.json` (passwords redacted)
```json
{
  "server": "neon-rabbitmq",
  "users": {
    "test": {
      "user": "test_user",
      "password": ""
    },
    "neon_api_connector": {
      "user": "neon_api",
      "password": ""
    },
    "neon_coupon_connector": {
      "user": "neon_coupons",
      "password": ""
    },
    "neon_email_proxy": {
      "user": "neon_email",
      "password": ""
    },
    "neon_metrics_connector": {
      "user": "neon_metrics",
      "password": ""
    },
    "neon_script_parser_service": {
      "user": "neon_script_parser",
      "password": ""
    }
  }
}
```

`rabbitmq.conf`
```
load_definitions = /config/rabbit_mq_config.json
```

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
`diana` includes cli utilities for generating ingress definitions for non-http services.
In general, ingress definitions will be created or updated when relevant backend services are configured, but
the `diana add-tcp-service` entrypoint is also available to define these manually. Note that adding configuration
will modify existing spec files in the configured path.

##### Applying Configuration to a Cluster
`kubectl` should be configured to reference the Kubernetes cluster you are deploying to.
If you are accessing private repositories, you will also need to configure the secret `github-auth`. Documentation 
can be found [in the Kubernetes docs](https://kubernetes.io/dkocs/tasks/configure-pod-container/pull-image-private-registry/).

```shell
# Apply configuration and secrets
kubectl apply -f ~/neon_diana/k8s_secret_mq-config.yml -f ~/neon_diana/k8s_config_rabbitmq.yml -f ~/neon_diana/k8s_secret_ngi-auth.yml

# If using ingress-nginx, apply those configurations
kubectl apply -f ~/neon_diana/ingress/k8s_config_tcp_services
kubectl patch -n ingress-nginx service ingress-nginx-controller --patch-file ~/neon_diana/ingress/k8s_patch_nginx_service.yml

# If using private images
kubectl apply -f ~/neon_diana/k8s_secret_github.yml

# Apply ingress rules
kubectl apply -f ~/neon_diana/k8s_ingress_nginx_mq.yml

# Start backend services
kubectl apply -f ~/neon_diana/k8s_diana_backend.yml
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
