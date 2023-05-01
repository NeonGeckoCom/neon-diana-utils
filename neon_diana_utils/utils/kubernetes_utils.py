# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
# BSD-3
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os.path
import yaml

from typing import Optional
from os import getenv
from os.path import dirname, join, expanduser, isdir, isfile
from ovos_utils.log import LOG


def cli_make_rmq_config_map(input_path: str, output_path: str) -> str:
    """
    Generate a ConfigMap object for RabbitMQ from general config files
    :param input_path: path to directory containing RabbitMQ config files
    :param output_path: file or dir to write Kubernetes spec file to
    :returns: path to output config file
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    file_path = expanduser(input_path)
    if not isdir(file_path):
        raise FileNotFoundError(f"Could not find requested directory: "
                                f"{input_path}")
    output_path = expanduser(output_path)
    if isdir(output_path):
        output_file = join(output_path, f"k8s_config_rabbitmq.yml")
    elif isfile(output_path):
        output_file = output_path
    else:
        raise ValueError(f"Invalid output_path: {output_path}")

    with open(join(file_path, "rabbitmq.conf"), 'r') as f:
        rabbitmq_file_contents = f.read()
    with open(join(file_path, "rabbit_mq_config.json")) as f:
        rmq_config = f.read()
    generate_config_map("rabbitmq", {"rabbitmq.conf": rabbitmq_file_contents,
                                     "rabbit_mq_config.json": rmq_config}, output_file)
    return output_file


def cli_make_api_secret(input_path: str, output_path: str) -> str:
    """
    Generate a Secret object for ngi-auth from general config files
    :param input_path: path to directory containing ngi_auth_vars.yml
    :param output_path: file or dir to write Kubernetes spec file to
    :returns: path to output config file
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    file_path = expanduser(input_path)
    if not isdir(file_path):
        raise FileNotFoundError(f"Could not find requested directory: {input_path}")
    output_path = expanduser(output_path)
    if isfile(output_path):
        output_path = dirname(output_path)

    with open(join(file_path, "ngi_auth_vars.yml")) as f:
        ngi_auth = f.read()
    generate_secret("ngi-auth", {"ngi_auth_vars.yml": ngi_auth},
                    join(output_path, "k8s_secret_ngi-auth.yml"))
    return output_path


def cli_make_github_secret(username: str, token: str, config_dir: str) -> str:
    """
    Generate a Secret object for a GitHub image pull secret
    :param username: Github username
    :param token: Github PAT with package_read permissions
    :param config_dir: Directory to write output spec file to
    :returns: path to output config file
    """
    output_file = _create_github_secret(username, token,
                                        join(config_dir,
                                             "k8s_secret_github.yml"))
    return output_file


def write_kubernetes_spec(k8s_config: list, output_path: Optional[str] = None,
                          namespaces: dict = None):
    """
    Generates and writes a kubernetes.yml spec file according to the passed services
    :param k8s_config: list of k8s objects specified, usually read from service_mappings.yml
    :param output_path: path to write spec files to
    :param namespaces: dict of placeholders to namespaces
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    namespaces = namespaces or dict()
    output_dir = expanduser(output_path) if output_path else \
        expanduser(getenv("NEON_CONFIG_PATH", "~/.config/neon"))

    diana_spec_file = join(output_dir, "services", "k8s_diana_backend.yml")
    os.makedirs(dirname(diana_spec_file), exist_ok=True)

    # Write Diana services spec file
    with open(join(dirname(dirname(__file__)), "templates",
                   "kubernetes.yml")) as f:
        diana_spec_contents = yaml.safe_load(f)
    diana_spec_contents["items"].extend(k8s_config)

    with open(diana_spec_file, "w+") as f:
        yaml.dump(diana_spec_contents, f)
        f.seek(0)
        string_contents = f.read()
        for placeholder, replacement in namespaces.items():
            string_contents = string_contents.replace(
                '${' + placeholder + '}', replacement)
        f.seek(0)
        f.truncate(0)
        f.write(string_contents)

    # Write Ingress spec file
    os.makedirs(join(output_path, "ingress"), exist_ok=True)

    tcp_config = {'5672': f"{namespaces.get('MQ_NAMESPACE') or 'default'}"
                          f"/neon-rabbitmq:5672"}
    tcp_config = _update_tcp_config(tcp_config,
                                    join(output_path, "ingress",
                                         "k8s_config_tcp_services.yml"))
    LOG.info(f"Wrote {tcp_config}")
    ingress_config = _patch_ingress_nginx_controller_service(
        "neon-rabbitmq", 5672,
        output_path=join(output_path, "ingress",
                         "k8s_patch_nginx_service.yml"))
    LOG.info(f"Wrote {ingress_config}")


def generate_config_map(name: str, config_data: dict, output_path: str):
    """
    Generate a Kubernetes ConfigMap yml definition
    :param name: ConfigMap name
    :param config_data: Dict data to store
    :param output_path: output file to write
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_path = output_path or join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), f"k8s_config_{name}.yml")
    output_path = expanduser(output_path)
    if not isdir(dirname(output_path)):
        os.makedirs(dirname(output_path), exist_ok=True)
    config_template = join(dirname(dirname(__file__)),
                           "templates", "k8s_config_map.yml")
    with open(config_template) as f:
        config_map = yaml.safe_load(f)

    config_map["metadata"]["name"] = name
    config_map["data"] = config_data

    with open(output_path, 'w+') as f:
        yaml.dump(config_map, f)


def generate_secret(name: str, secret_data: dict,
                    output_path: Optional[str] = None):
    """
    Generate a Kubernetes Secret yml definition
    :param name: ConfigMap name
    :param secret_data: Dict data to store
    :param output_path: output file to write
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_path = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"),
                                      f"k8s_secret_{name}.yml")
    output_path = expanduser(output_path)
    if not isdir(dirname(output_path)):
        os.makedirs(dirname(output_path), exist_ok=True)
    config_template = join(dirname(dirname(__file__)),
                           "templates", "k8s_secret.yml")
    with open(config_template) as f:
        config_map = yaml.safe_load(f)

    config_map["metadata"]["name"] = name
    config_map["stringData"] = secret_data

    with open(output_path, 'w+') as f:
        yaml.dump(config_map, f)


def _create_github_secret(username: str, token: str,
                          output_path: Optional[str] = None) -> str:
    """
    Generate a Kubernetes Secret to authenticate to GitHub for image pulls
    :param username: GitHub username
    :param token: GitHub token with read_packages permission
    :param output_path: output file to write
    :returns: path to written Kubernetes config file
    """
    import json
    from base64 import b64encode
    output_path = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"),
                                      f"k8s_secret_github.yml")
    output_path = expanduser(output_path)
    encoded_auth = b64encode(f"{username}:{token}".encode())
    auth_dict = {"auths": {"ghcr.io": {"auth": encoded_auth.decode()}}}
    auth_str = json.dumps(auth_dict)
    encoded_config = b64encode(auth_str.encode())
    secret_spec = {
        "kind": "Secret",
        "type": "kubernetes.io/dockerconfigjson",
        "apiVersion": "v1",
        "metadata": {
            "name": "github-auth"
        },
        "data": {
            ".dockerconfigjson": encoded_config.decode()
        }
    }
    with open(output_path, 'w+') as f:
        yaml.dump(secret_spec, f)
    return output_path


def _update_tcp_config(port_config: dict,
                       output_path: Optional[str] = None) -> str:
    """
    Generate (or update) a tcp-services config spec for ingress-nginx
    :param port_config: dict of "{port}" to "{namespace}/{service}:{port}"
    :param output_path: output file to write
    :returns: path to `tcp-services` k8s config map spec to be applied
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_file = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"), "ingress",
                                      f"k8s_config_tcp_services.yml")
    output_file = expanduser(output_file)

    if isfile(output_file):
        with open(output_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {'apiVersion': 'v1',
                  'kind': 'ConfigMap',
                  'metadata': {
                      'name': 'tcp-services',
                      'namespace': 'ingress-nginx'
                  },
                  'data': {}
                  }
    config['data'] = {**config['data'], **port_config}
    with open(output_file, 'w+') as f:
        yaml.dump(config, f, default_flow_style=False)
    return output_file


def _patch_ingress_nginx_controller_service(name: str, port: int,
                                            target_port: Optional[int] = None,
                                            protocol: str = "TCP",
                                            output_path: Optional[str] = None):
    """
    Generate an updated nginx controller service spec
    :param name: name of TCP service to configure
    :param port: port to forward
    :param target_port: optional target port (else uses `port`)
    :param protocol: transport protocol (default TCP)
    :param output_path: path to output file to write
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_file = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"), "ingress",
                                      f"k8s_patch_nginx_service.yml")
    output_file = expanduser(output_file)
    if os.path.isfile(output_file):
        LOG.info(f"Reading ingress config from {output_file}")
        with open(output_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {"spec": {"ports": []}}

    if any([i['name'] == name for i in config['spec']['ports']]):
        LOG.info(f"Skipping already configured port: {name}")
        return output_file
    config['spec']['ports'].append({'name': name,
                                    'port': port,
                                    'targetPort': target_port or port,
                                    'protocol': protocol})

    with open(output_file, 'w+') as f:
        yaml.dump(config, f, default_flow_style=False)
    return output_file


def _update_ingress_config(address: str, service: str, port: int,
                           cert_issuer: str = "letsencrypt-prod",
                           output_path: Optional[str] = None):
    """
    Update routing rules to route traffic to a service.
    Note this assumes you are using ingress-nginx and tls
    :param address: hostname rule applies to
    :param service: service name
    :param port: exposed container port service is running on
    :param cert_issuer: Name of k8s Issuer to provide TLS certificates
    :param output_path: path to output file to write
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_file = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"), "ingress",
                                      f"k8s_config_ingress.yml")
    output_file = expanduser(output_file)
    if os.path.isfile(output_file):
        LOG.info(f"Reading ingress config from {output_file}")
        with open(output_file) as f:
            config = yaml.safe_load(f)
        if config['metadata']['annotations']['cert-manager.io/issuer'] != cert_issuer:
            raise RuntimeError("Config cert_issuer conflict, skipping update")
    else:
        config = {
            "kind": "Ingress",
            "apiVersion": "networking.k8s.io/v1",
            "metadata": {
                "name": "ingress-diana",
                "annotations": {
                    "cert-manager.io/issuer": cert_issuer
                }
            },
            "spec": {
                "ingressClassName": "nginx",
                "tls": [
                    {"hosts": [],
                     "secretName": f"tls-{cert_issuer}"}
                ],
                "rules": []
            }
        }

    if address in config['spec']['tls'][0]['hosts']:
        LOG.warning(f"Skipping address already configured: {address}")
        return output_file

    config['spec']['tls'][0]['hosts'].append(address)
    config['spec']['rules'].append({"host": address,
                                    "http": {"paths": [
                                        {"path": '/',
                                         "pathType": "Prefix",
                                         "backend": {
                                             "service": {
                                                 "name": service,
                                                 "port": {
                                                     "number": port
                                                 }
                                             }
                                         }}
                                    ]}})
    with open(output_file, 'w+') as f:
        yaml.dump(config, f, default_flow_style=False)
    return output_file


def _create_cert_issuer(name: str, email: str,
                        output_path: Optional[str] = None) -> str:
    """
    Create a certificate Issuer k8s spec
    :param name: name for Issuer
    :param email: email to use for ACME registration
    :param output_path: spec file to write
    """
    # TODO: Deprecate Method
    LOG.warning("This function is deprecated")
    output_file = output_path or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"), "ingress",
                                      f"k8s_config_cert_issuer.yml")
    output_file = expanduser(output_file)
    spec = {
        "apiVersion": "cert-manager.io/v1",
        "kind": "Issuer",
        "metadata": {
            "name": name
        },
        "spec": {
            "acme": {
                "server": "https://acme-v02.api.letsencrypt.org/directory",
                "email": email,
                "privateKeySecretRef": {
                    "name": name
                },
                "solvers": [
                    {
                        "http01": {
                            "ingress": {
                                "class": "nginx"
                            }
                        }
                    }
                ]
            }
        }
    }
    with open(output_file, 'w+') as f:
        yaml.safe_dump(spec, f, default_flow_style=False)
    return output_file
