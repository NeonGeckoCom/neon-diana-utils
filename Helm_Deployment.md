# Deployment via Helm Charts
[Helm](https://helm.sh/) is a standard framework for deploying Kubernetes applications.
The Helm charts for Neon Diana are the recommended method for production deployment.

## Preparing for Backend Deployment
Before deploying a Diana backend, ensure the following has been completed:
- Kubernetes Cluster is deployed and `helm` CLI is properly configured
- Desired domain is ready to forward all relevant subdomains to the cluster
- Add the following Helm repositories:
  ```shell
  helm repo add diana https://neongeckocom.github.io/neon-diana-utils
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo add jetstack https://charts.jetstack.io
  helm repo add bitnami https://charts.bitnami.com/bitnami
  ```
## Backend Configuration
Configure the backend deployment with 
`diana configure-mq-backend <output_path>`. Follow the shell prompts to 
provide any necessary configuration parameters; when complete, the specified
`output_path` will be populated with Helm charts to deploy.

### Ingress
An NGINX ingress chart is provided at `<output_path>/ingress-nginx`. `values.yaml`
may be updated to include any additional TCP ports to be used (i.e. for RabbitMQ)
and then the chart is generally deployed to the `ingress-nginx` namespace. Only
one ingress is necessary for a cluster. Deploy the configured ingress with:

```
helm dependency update <output_path>/ingress-common
helm install ingress-nginx <output_path>/ingress-common --namespace ingress-nginx --create-namespace
```
> At this point, check to make sure all expected subdomains resolve to the ingress
> IP address (ping each domain and check the resolved address)

### Diana Backend
Validate the configuration in `<output_path>/diana-backend/values.yaml`; at minimum,
the following parameters MUST be updated:
- `domain`
- `letsencrypt.email`
- `letsencrypt.server` (default is test endpoint)

After updating or overriding these values, deploy the backend via:

```
helm dependency update <output_path>/diana-backend
helm install diana-backend <output_path>/diana-backend --namespace backend --create-namespace
```

### Neon Core
After [the backend](#diana-backend) has been deployed, Neon Core services may also
be deployed to the same namespace. If you were prompted to configure Neon when setting
up the backend, then the Helm charts and configuration has already been completed.

If Neon was not configured with the backend, you can generate helm charts via
`diana configure-neon-core <output_path>`, where `<output_path>` is the same
path used for the backend. Follow the prompts to either generate an updated MQ
configuration or input values if you wish to manually update RabbitMQ. If you
had `diana` automatically update MQ configuration, you can update an existing
deployment via:
```
helm upgrade diana-backend <output_path>/diana-backend --namespace backend
```

Once the backend has been deployed or updated, Neon Core services can be deployed via:

```
helm install neon-core <output_path>/neon-core --namespace backend
```

### Klat Chat
After [the backend](#diana-backend) has been deployed, Klat Chat may also
be deployed to the same namespace. If you were prompted to configure Klat when setting
up the backend, then the Helm charts and configuration has already been completed.
> Note that you will need a configured [MongoDB](https://www.mongodb.com/) 
> instance as well as an available [SFTP Share](https://www.digitalocean.com/community/tutorials/how-to-use-sftp-to-securely-transfer-files-with-a-remote-server) 
> to complete this deployment

If Klat was not configured with the backend, you can generate helm charts via
`diana configure-klat <output_path>`, where `<output_path>` is the same
path used for the backend. Follow the prompts to either generate an updated MQ
configuration or input values if you wish to manually update RabbitMQ. If you
had `diana` automatically update MQ configuration, you can update an existing
deployment via:
```
helm upgrade diana-backend <output_path>/diana-backend --namespace backend
```

Once the backend has been deployed or updated, Klat services can be deployed via:

```
helm install klat-chat <output_path>/klat-chat --namespace backend
```


## Other Notes
- The namespace used for Backend deployment is configurable; it may be desirable
  to use namespaces for test vs production deployments, to separate the Diana
  backend from other deployments, or both.