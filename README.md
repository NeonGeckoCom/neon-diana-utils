# Neon Diana
Device Independent API for Neon Applications (Diana) is a collection of microservices that provide various functionality 
to NeonAI systems. All services are implemented as standalone Docker containers that are connected to a RabbitMQ server.
This repository contains the files required to launch a Neon API server.

Install the Diana utilities Python package with: `pip install neon-diana-utils`

## Automated Configuration
The `diana` entrypoint is available to handle automated setup and some common administration tasks. You can see get detailed
help via `diana --help`. A standard configuration is described here:

### Docker Compose
For testing or running on a dedicated host, `Docker Compose` offers a simple method for starting a set of services.
This deployment assumes all services will run a single instance on a shared host with any configuration or other files 
saved to the host filesystem or a configured NFS share.

#### Configuring Default Backend Services
A Diana backend can be configured automatically with `diana configure-backend`. A standard example is included here, but 
a description of config options is available via: `diana configure-backend --help`.

```shell
diana configure-backend -d -u administrator -p password ~/neon_diana
```
* `-d` specifies that default backend services will be configured
* `-u` specifies the MQ user `administrator` for admin portal access
* `-p` specifies the password `password` for the `administrator` user
* `~/neon_diana` specifies the output path for configuration files

#### Providing Backend Service Credentials
Many backend services rely on configured credentials for authentication. Before running a configured backend, `ngi_auth_vars.yml`
must be defined with the appropriate credentials. A more complete example can be seen in the [Configuration section](#configuration).

##### ~/neon_diana/ngi_auth_vars.yml
```yaml
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

#### Running Configured Backend Services
After a backend is configured, it can be started with `diana start-backend`. A standard example is included here, but 
a description of config options is available via: `diana start-backend --help`.

```shell
diana start-backend ~/neon_diana
```
* `~/neon_diana` specifies the path to backend configuration

#### Stopping a Running Backend
After a backend is started, it can be stopped with `diana stop-backend`. A standard example is included here, but 
a description of config options is available via: `diana stop-backend --help`.
```shell
diana stop-backend ~/neon_diana
```
* `~/neon_diana` specifies the path to backend configuration

### Kubernetes
For deployment, Kubernetes provides a managed solution that can handle scaling, rolling updates, and other benefits.
This deployment assumes you have an existing cluster; it is assumed that the Cluster or system administrator will manage
creation of `PersistentVolume` and `LoadBalancer` objects as necessary.

#### Cluster Preparation
The config generation in this project assumes your cluster has the `NGINX Ingress Controller` deployed.
Installation instructions are available [from Kubernetes](https://kubernetes.github.io/ingress-nginx/deploy/).

The `ingress-nginx-controller` service should have External Endpoints exposed. If you are deploying locally, you may use
[MetalLB](https://metallb.universe.tf/) to configure a `LoadBalancer`.

#### Configuring Default Backend Services
A Diana backend can be configured automatically with `diana configure-backend`. A standard example is included here, but 
a description of config options is available via: `diana configure-backend --help`.
This will generate `k8s_secret_mq-config.yml`, `k8s_config_rabbitmq.yml`, and `kubernetes.yml` spec files.
>*Note*: This will use `docker` on your local system to start and configure an instance of RabbitMQ 

```shell
diana configure-backend -d -u administrator -p password -n backend ~/neon_diana
```
* `-d` specifies that default backend services will be configured
* `-u` specifies the MQ user `administrator` for admin portal access
* `-p` specifies the password `password` for the `administrator` user
* `-n` specifies the k8s namespace `backend` will be used for generated configurations
* `~/neon_diana` specifies the output path for configuration files

#### Providing Backend Service Credentials
Many backend services rely on configured credentials for authentication. Before running a configured backend, `ngi_auth_vars.yml`
must be defined with the appropriate credentials. A more complete example can be seen in the [Configuration section](#configuration).

Generate a Kubernetes secret spec with these files (`k8s_secret_ngi-auth.yml`).

```shell
diana make-api-secrets -p ~/.config/neon ~/neon_diana
```
* `-p` specifies the path to the directory containing `ngi_auth_vars.yml`
* `~/neon_diana` specifies the output path for configuration files

##### ~/neon_diana/ngi_auth_vars.yml
```yaml
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

#### Applying Configuration to a Cluster
`kubectl` should be installed and configured to reference the Kubernetes cluster you are deploying to.
If you are accessing private repositories, you will also need to configure the secret `github-auth`. Documentation 
can be found [in the Kubernetes docs](https://kubernetes.io/dkocs/tasks/configure-pod-container/pull-image-private-registry/).

```shell
# Apply configuration and secrets
kubectl apply -n backend -f ~/neon_diana/k8s_secret_mq-config.yml -f ~/neon_diana/k8s_config_rabbitmq.yml -f ~/neon_diana/k8s_secret_ngi-auth.yml

# Apply ingress rules
kubectl apply -f ~/neon_diana/k8s_ingress_nginx_mq.yml

# Start backend services
kubectl apply -f ~/neon_diana/k8s_diana.yml
```


## Manual Configuration
### Running Services
[Docker Compose](https://docs.docker.com/compose/) is used to facilitate starting up separate services that comprise Diana.
The example below assumes that configuration is populated in `~/docker_config` and that metrics should be saved to 
`~/docker_metrics`. These paths are arbitrary and can be changed to any location that is accessible by the user running 
docker. Details of what should be present in `NEON_CONFIG_PATH` can be found in the [Configuration](#configuration) 
section below.

```shell
export NEON_CONFIG_PATH="/home/${USER}/diana_config/"
export NEON_METRIC_PATH="/home/${USER}/diana_metrics/"
docker login ghcr.io
docker-compose up -d
```

If you prefer not to run all services, you may specify which services to run with `docker-compose up`.
```shell
docker-compose up -d neon-rabbitmq neon-api-proxy neon-metrics-service
```

### Initial Configuration
`neon_diana_utils` contains convenience utilities, including for automated initial configuration of RabbitMQ. If you 
have a clean RabbitMQ container, you can use `create_default_mq_server` to configure an admin account and all parameters
required for running Neon Diana. Make sure the `neon-rabbitmq` container is running before running this utility. After 
RabbitMQ Configuration is complete, you can start the remaining containers 

ex:
```shell
export NEON_CONFIG_PATH="/home/${USER}/diana_config/"
# Modify neon-diana-backend/setup_default_server.py with desired username and password
python neon-diana-backend/setup_default_server.py
```

### Configuration
All containers containing an MQ module will expect `mq_config.json` to be mounted to `NEON_CONFIG_PATH` 
(usually `/config` in the containers).

- `neon-api-proxy`, `neon-brands-service`, and `neon-email-proxy` will expect `/config/ngi_auth_vars.yml` to specify any
    account credentials
- `neon-metrics-service` will output metrics files to `/metrics`.
- `neon-rabbitmq` will expect `/config/rabbitmq.conf` to specify a path to the configuration `.json` file to load.

Example configuration file structure:
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

`ngi_auth_vars.yml` (passwords redacted)
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

`rabbitmq.conf`
```
load_definitions = /config/rabbit_mq_config.json
```


## Container Orchestration
The default behavior for Diana assumes docker-compose will be used to run applications.
Resources for `Kubernetes` and `OpenShift` can be optionally generated for deploying 
containers under those infrastructures.

### Requirements
Conversion of `docker-compose` files requires [Kompose](https://github.com/kubernetes/kompose).
Detailed installation instructions can be found [here](https://github.com/kubernetes/kompose/blob/master/docs/installation.md)

```shell
diana convert --kubernetes ~/neon_diana
```
