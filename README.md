# Install and Deploy NeonAI Diana 

Device Independent API for Neon Applications (Diana) is a collection of microservices that add functionality to NeonAI systems. Diana microservices are deployed in a Kubernetes cluster.

After you have installed Diana, use `diana --help` to get detailed help.

For more information about using NeonAI, see [the NeonAI documentation site](https://neongeckocom.github.io/neon-docs/).

## Prerequisites

To install Diana:

* [Ubuntu](https://ubuntu.com/) 20.04 or later. 
  * Diana will most likely work on other flavors of Linux, but we have not yet verified this.
* [Python](https://www.python.org/getit/) 3.8 or later.
* [Pip](https://pypi.org/project/pip/) Python package installer.

To deploy Diana: 

*  [Kubectl](https://kubernetes.io/docs/reference/kubectl/) Kubernetes command-line tool.  
* [Helm](https://helm.sh/) package manager for Kubernetes.
* A [Kubernetes](https://kubernetes.io/) installation.
  * The following instructions assume a local installation using [Microk8s](https://microk8s.io/) version 1.26/stable or later.
  * You can likely deploy Diana on a Kubernetes cluster in the cloud, but we have not yet verified this.

## Use a Python virtual environment

We recommend you use a [Python virtual environment](https://docs.python.org/3/library/venv.html) for installing and testing Diana. In addition to the usual benefits, using a virtual environment makes it easier to ensure you are using the correct versions of Python and Diana.

1. Create a Python virtual environment:

Install the python3.10 venv package
```
sudo apt install python3.10 -m venv
```

Create the virtual environment
```
python3.10 -m venv venv
```

2. Open a new terminal window. Activate the Python virtual environment in this new window:

```
. venv/bin/activate
```

Using this new window, proceed with the instructions.

## Install Diana

3. Use Pip to install the current stable version of Diana:

```
pip install neon-diana-utils
```

This command installs the newest stable version, which is described in this tutorial. 

**Tip:** You can use `pip install --pre neon-diana-utils` to install the current pre-release version. 

For more information on the available versions of Diana, see [the Python Package Index repo for Neon Diana](https://pypi.org/project/neon-diana-utils/).

4. Verify Diana is installed:

```
diana --version
```

**Tip:** If your computer does not recognize this command, you may need to add `~/.local/bin` to your $PATH with a command like `export PATH=$PATH:/home/${USER}/.local/bin`.

Use `diana --help` for detailed information about Diana and its commands.

The output of `diana --help` looks like:

```
Usage: diana [OPTIONS] COMMAND [ARGS]...

  Diana: Device Independent API for Neon Applications.

  See also: diana COMMAND --help

Options:
  -v, --version  Print the current version
  --help         Show this message and exit.

Commands:
  configure-backend     Configure a Diana Backend
  configure-mq-backend  Configure RabbitMQ and export user credentials
  make-github-secret    Generate Kubernetes secret for Github images
  make-keys-config      Generate a configuration file with access keys
  make-rmq-config       Generate RabbitMQ definitions
  start-backend         Start a Diana Backend
  stop-backend          Stop a Diana Backend

```

## Deploy NeonAI Diana Backend

This example deploys Diana Backend in a local [Microk8s Kubernetes](https://microk8s.io/) cluster. 

### Install and Run Microk8s

If you don't have Microk8s installed, you can install it and create the necessary user with:

```
sudo snap install microk8s --classic
sudo usermod -aG microk8s $USER
newgrp microk8s
```
This can be done in the virtual environment terminal or in the regular terminal. 

5. Start Microk8s:

```
microk8s start
```

6. Enable the services for persistent storage, DNS, and the Kubernetes dashboard:

```
microk8s enable hostpath-storage
microk8s enable dns
microk8s enable dashboard
```

7. Enable the MetalLB service:

```
microk8s enable metallb
```

At the prompt, enter a subnet  which is not being used by your router. For example: 

```
10.10.10.10-10.10.10.10
```

Note: Unless you plan on adding multiple nodes, this range only needs one address.

8. After Microk8s is running, use `microk8s kubectl create token default` to create a Microk8s token.

9. Use `microk8s kubectl port-forward -n kube-system service/kubernetes-dashboard 1443:443` to forward the dashboard port. 

You can now access your Kubernetes dashboard in a browser at https://localhost:1443/ using the token you created in step 2. 

10. The process in this terminal needs to keep running. Either background the process, or leave this terminal window open and open a new terminal window and activate the virtual environment in it (. venv/bin/activate) to continue working.

### Set Up DNS

The ingress controller needs URLs to be mapped to services. There are a number of different ways you can accomplish this, depending on your networking setup. 

For this guide, we will use the simple case of editing the `/etc/hosts` file.

11. Edit the `/etc/hosts` file. Use either:
```
sudo nano /etc/hosts
```
or if you prefer a GUI text editor:
```
sudo gedit /etc/hosts
```
Add one entry for the domain name of each service you intend to run. Add the canonical domain and point it to the IP address you gave MetalLB in step 3.

For example, if you plan to run a service named `test-service` on the `diana.k8s` domain, add the following line:

```
10.10.10.10 test-service.diana.k8s
```

This tells your computer that `test-service.diana.k8s` is at IP address `10.10.10.10`. Your computer will route all requests for `test-service.diana.k8s` to the Kubernetes cluster you set up at `10.10.10.10`, instead of looking for it on the public internet.

Add one line for each service. Point each service to the same IP address.


### Prepare for Deployment

12. After you set up your Kubernetes cluster and configure DNS, configure the Diana backend with:

```
diana configure-mq-backend OUTPUT_PATH
```

Replace `OUTPUT_PATH` with the directory where you want Diana to store its Helm charts and configurations. For example:

```
diana configure-mq-backend ~/neon_diana
```

Follow the prompts to provide / add any necessary configuration parameters. 
In order to enable all Neon skills, you will need to enable / choose yes for all these services. 

Tips:
- Visit https://github.com/settings/tokens to generate the necessary token for the GitHub private services. 
  > It is only necessary to check the box for permission to read:packages.
- Some parameters are provided for you in brackets.
- SQL username & password are not necessary unless you are working on the brands/coupons skill which is not currently active, so you can skip these (or put in random text if the system won't allow you to leave them blank.)
- If you want to enable ChatGPT, you will need to enter your own API key. You can generate that from an OpenAI account.

13. **Optional:** To add extra TCP ports (i.e. for RabbitMQ), update the `OUTPUT_PATH/ingress-nginx/values.yaml` file accordingly.

14. Deploy the NGINX ingress:

```
microk8s helm install ingress-nginx OUTPUT_PATH/ingress-common --namespace ingress-nginx --create-namespace
```

15. Edit `OUTPUT_PATH/diana-backend/values.yaml` and update any necessary configuration. At minimum, you need to update the following parameters:

* `domain` Change this to the domain you added to the `/etc/hosts` file in step 11.
* `letsencrypt.email` If you are using a "real" domain, change this to the email address you want to use for the [Let's Encrypt](https://letsencrypt.org/) SSL certificate. For local testing, leave this as is.
* `letsencrypt.server` If you are using a "real" domain, change this to a valid Let's Encrypt server address, such as `https://acme-v02.api.letsencrypt.org/directory`. For local testing, leave this as is.

## Deploy the Diana Backend

16. Update the Helm dependency:

```
helm dependency update OUTPUT_PATH/diana-backend
```

17. Use Helm to launch Diana:

If you haven't already:
```
helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
```
Then
```
helm dependency build ~/neon_diana/diana-backend
```
Finally
```
microk8s helm install diana-backend OUTPUT_PATH/diana-backend --namespace backend --create-namespace
```

This creates the `backend` namespace and launches Diana into that namespace. You can change this to any namespace name you prefer. You may want to use separate namespaces for test versus production deployments, to separate the Diana backend from other deployments, or both.


# Legacy Documentation
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
