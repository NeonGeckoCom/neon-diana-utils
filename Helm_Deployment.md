# Deployment via Helm Charts
[Helm](https://helm.sh/) is a standard framework for deploying Kubernetes applications.
The Helm charts for Neon Diana are the recommended method for production deployment.

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
helm dependency update <output_path>/ingress-nginx
helm install ingress-nginx <output_path>/ingress-nginx --namespace ingress-nginx --create-namespace
```

### Diana Backend
Validate the configuration in `<output_path>/diana-backend/values.yaml`; at minimum,
the following parameters MUST be updated:
- `domain`
- `letsencrypt.email`

After updating or overriding these values, deploy the backend via:

```
helm dependency update <output_path>/diana-backend
helm install diana-backend <output_path>/diana-backend --namespace backend --create-namespace
```

## Other Notes
- The namespace used for Backend deployment is configurable; it may be desirable
  to use namespaces for test vs production deployments, to separate the Diana
  backend from other deployments, or both.
  