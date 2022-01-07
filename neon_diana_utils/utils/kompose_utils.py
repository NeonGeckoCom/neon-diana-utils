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

import subprocess
import ruamel.yaml as yaml

from typing import Optional
from os import getenv
from os.path import dirname, join, isfile, isdir, expanduser
from neon_utils.logger import LOG
from ruamel.yaml import YAML

from neon_diana_utils.orchestrators import Orchestrator


def write_kubernetes_spec(k8s_config: list, output_path: Optional[str] = None,
                          mq_namespace: str = "default"):
    """
    Generates and writes a kubernetes.yml spec file according to the passed services
    :param k8s_config: list of k8s objects specified, usually read from service_mappings.yml
    :param output_path: path to write spec files to
    :param mq_namespace: k8s namespace to configure backend MQ services for
    """
    output_dir = expanduser(output_path) if output_path else \
        expanduser(getenv("NEON_CONFIG_PATH", "~/.config/neon"))

    diana_spec_file = join(output_dir, "k8s_diana.yml")
    ingress_spec_file = join(output_dir, "k8s_ingress_nginx_mq.yml")

    # Write Diana services spec file
    with open(join(dirname(dirname(__file__)), "templates",
                   "kubernetes.yml")) as f:
        diana_spec_contents = YAML().load(f)
    diana_spec_contents["items"].extend(k8s_config)

    with open(diana_spec_file, "w+") as f:
        YAML().dump(diana_spec_contents, f)
        f.seek(0)
        string_contents = f.read()
        string_contents = string_contents \
            .replace("${MQ_NAMESPACE}", mq_namespace)
        f.seek(0)
        f.truncate(0)
        f.write(string_contents)

    # Write Ingress spec file
    with open(join(dirname(dirname(__file__)), "templates",
                   "k8s_ingress_nginx_mq.yml")) as f:
        ingress_string_contents = f.read()
    ingress_string_contents = ingress_string_contents\
        .replace("${MQ_NAMESPACE}", mq_namespace)

    with open(ingress_spec_file, "w+") as f:
        f.write(ingress_string_contents)


def generate_config_map(name: str, config_data: dict, output_path: str):
    """
    Generate a Kubernetes ConfigMap yml definition
    :param name: ConfigMap name
    :param config_data: Dict data to store
    :param output_path: output file to write
    """
    output_path = output_path or join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), f"k8s_config_{name}.yml")
    output_path = expanduser(output_path)
    config_template = join(dirname(dirname(__file__)),
                           "templates", "k8s_config_map.yml")
    with open(config_template) as f:
        config_map = yaml.safe_load(f)

    config_map["metadata"]["name"] = name
    config_map["data"] = config_data

    with open(output_path, 'w+') as f:
        yaml.dump(config_map, f)


def generate_secret(name: str, secret_data: dict, output_path: Optional[str] = None):
    """
    Generate a Kubernetes Secret yml definition
    :param name: ConfigMap name
    :param secret_data: Dict data to store
    :param output_path: output file to write
    """
    output_path = output_path or join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), f"k8s_secret_{name}.yml")
    output_path = expanduser(output_path)
    config_template = join(dirname(dirname(__file__)),
                           "templates", "k8s_secret.yml")
    with open(config_template) as f:
        config_map = yaml.safe_load(f)

    config_map["metadata"]["name"] = name
    config_map["stringData"] = secret_data

    with open(output_path, 'w+') as f:
        yaml.dump(config_map, f)


# def generate_nfs_volume_config(host: str, config_path: str, metric_path: str, output_path: str):
#     """
#     Generate a Kubernetes configuration for NFS-based persistent volumes
#     :param host: NFS Server hostname
#     :param config_path: host path to config dir
#     :param metric_path: host path to metric dir
#     :param output_path: path to output file
#     """
#     output_path = expanduser(output_path)
#     nfs_volume_template = join(dirname(dirname(__file__)),
#                                "templates", "k8s_nfs_volume.yml")
#     with open(nfs_volume_template, 'r') as f:
#         nfs_config = f.read()
#     nfs_config = nfs_config.replace("${HOST}", host)\
#         .replace("${METRIC_PATH}", metric_path)\
#         .replace("${CONFIG_PATH}", config_path)
#
#     with open(output_path, 'w+') as f:
#         f.write(nfs_config)


def convert_docker_compose(compose_file: str, orchestrator: Orchestrator):
    """
    Convert the specified compose file into resources to deploy to Kubernetes.
    :param compose_file: path to docker-compose.yml file to convert
    :param orchestrator: orchestrator to generate resources for
    """
    LOG.warning("Kompose outputs are not validated and may require manual modifications")
    docker_compose_dir = dirname(compose_file)
    if orchestrator == Orchestrator.KUBERNETES:
        provider = "kubernetes"
    elif orchestrator == Orchestrator.OPENSHIFT:
        provider = "openshift"
    else:
        LOG.error(f"Unhandled orchestrator: {orchestrator.name}. Fallback to Kubernetes")
        provider = "kubernetes"
    output_file = f'{join(docker_compose_dir, provider)}.yml'
    subprocess.Popen(["/bin/bash", "-c",
                      f"kompose convert -f {compose_file} "
                      f"-o {output_file} "
                      f"--provider {provider}"]).communicate()

    # TODO: Volume R/W only applies to nfs shares, not config/secrets
    # Patch Volume Read/Write
    with open(output_file, 'r') as f:
        contents = f.read()
    contents = contents.replace("ReadWriteOnce", "ReadWriteMany")

    k8s_config = yaml.safe_load(contents)
    for item in k8s_config.get("items", list()):
        # Remove NetworkPolicy that blocks outside connections and duplicated PVC
        if item.get("kind") in ("NetworkPolicy", "PersistentVolumeClaim"):
            k8s_config["items"].remove(item)

    with open(output_file, 'w') as f:
        yaml.safe_dump(k8s_config, f)
