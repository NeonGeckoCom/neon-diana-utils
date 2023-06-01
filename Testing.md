## Getting Started
To begin testing, we start with a clean environment and install a Kubernetes
runtime. For this example, we will use Ubuntu 22.04 and MicroK8s.
1. Start with Ubuntu 22.04 (with Snap).
2. Install Kubernetes runtime
```shell
sudo snap install microk8s --classic
sudo usermod -aG microk8s $USER
newgrp microk8s
```
3. Enable services for persistent storage, DNS, Dashboard, and MetalLB
```shell
microk8s enable hostpath-storage
microk8s enable dns
microk8s enable dashboard
microk8s enable metallb
# When prompted, choose a subnet that is different than anything your router uses,
# i.e. 10.10.10.10-10.10.10.10
# Unless you plan on adding multiple nodes, this range only needs one address.
```
3. Forward the Kubernetes Dashboard port. You will need to run this in a separate terminal, or
   fork the process to the background to continue after starting the dashboard.
```shell
microk8s kubectl create token default  # Copy this token
microk8s kubectl port-forward -n kube-system service/kubernetes-dashboard 1443:443
# Dashboard is now available at: https://localhost:1443 using the token generated earlier
```
> Note: Add `--address="0.0.0.0` to expose the dashboard to your local network

## DNS Resolution
Ingress configuration will expect URLs to map to services, for local testing you may
either configure subdomains for a domain you own to forward to your ingress controller
(in our example this is `10.10.10.10`), or you can modify the hosts file 
(`/etc/hosts` for Ubuntu) on a computer you use for testing to forward to a fake
domain, or a real domain that you own. You could also configure dnsmasq or any
number of other services, but this guide will assume the simple case of overriding
the hosts file.

### Modify `/etc/hosts`
Every HTTP service you enable will expect a unique subdomain to bind to. For
example, a service that binds to `service.diana.k8s` would need the following
line added to `/etc/hosts`:
```
10.10.10.10    service.diana.k8s
```
A line like this is required for each HTTP service enabled for testing. This tells
the operating system that `service.diana.k8s` exists at IP address `10.10.10.10`,
so the request is routed to the Kubernetes cluster instead of out to a DNS resolver.

## Next Steps
From here on, the testing environment should closely match a deployment 
environment (Digital Ocean, Google Cloud, Azure, etc).

### References
[ingress-nginx Installation Guide](https://kubernetes.github.io/ingress-nginx/deploy/)
[microk8s Addon: dashboard](https://microk8s.io/docs/addon-dashboard)
[microk8s Addon: MetalLB](https://microk8s.io/docs/addon-metallb)