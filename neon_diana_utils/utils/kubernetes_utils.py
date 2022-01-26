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
from os.path import dirname, join, expanduser, isdir, isfile
from neon_utils.logger import LOG
from ruamel.yaml import YAML

from neon_diana_utils.constants import Orchestrator


def cli_make_rmq_config_map(input_path: str, output_path: str) -> str:
    """
    Generate a ConfigMap object for RabbitMQ from general config files
    :param input_path: path to directory containing RabbitMQ config files
    :param output_path: file or dir to write Kubernetes spec file to
    """
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
    """
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


def write_kubernetes_spec(k8s_config: list, output_path: Optional[str] = None,
                          namespaces: dict = None):
    """
    Generates and writes a kubernetes.yml spec file according to the passed services
    :param k8s_config: list of k8s objects specified, usually read from service_mappings.yml
    :param output_path: path to write spec files to
    :param namespaces: dict of placeholders to namespaces
    """
    namespaces = namespaces or dict()
    output_dir = expanduser(output_path) if output_path else \
        expanduser(getenv("NEON_CONFIG_PATH", "~/.config/neon"))

    diana_spec_file = join(output_dir, "k8s_diana_backend.yml")
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
        for placeholder, replacement in namespaces.items():
            string_contents = string_contents.replace(
                '${' + placeholder + '}', replacement)
        f.seek(0)
        f.truncate(0)
        f.write(string_contents)

    # Write Ingress spec file
    with open(join(dirname(dirname(__file__)), "templates",
                   "k8s_ingress_nginx_mq.yml")) as f:
        ingress_string_contents = f.read()
    for placeholder, replacement in namespaces.items():
        ingress_string_contents = ingress_string_contents.replace(
            '${' + placeholder + '}', replacement)

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
