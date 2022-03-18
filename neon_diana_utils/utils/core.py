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

from os import makedirs
from os.path import expanduser, isfile, join, isdir, dirname
from typing import Tuple

from neon_utils.logger import LOG
from ruamel.yaml import YAML

from neon_diana_utils.utils.docker_utils import write_docker_compose
from neon_diana_utils.utils.kubernetes_utils import write_kubernetes_spec, generate_config_map, generate_secret


def _validate_core_configuration(config_path: str) -> bool:
    """
    Check for the existence of core configuration files and
    warn if any are missing
    :returns: True if all expected files exist
    """
    valid_config_files = ("ngi_local_conf.yml",
                          "ngi_user_info.yml",
                          "ngi_auth_vars.yml")
    if all([isfile(join(config_path, file)) for file in valid_config_files]):
        return True
    LOG.warning(f"{valid_config_files} not defined in {config_path}."
                f" Default config will be loaded on container start.")
    return False


def _parse_core_services() -> Tuple[dict, list]:
    """
    Parse template service_mappings and return core Docker and Kubernetes specs
    :returns: docker-compose spec, kubernetes spec
    """
    template_file = join(dirname(dirname(__file__)), "templates",
                         "service_mappings.yml")
    with open(template_file) as f:
        template_data = YAML().load(f)
    config = {name: dict(template_data[name])
              for name in template_data if
              template_data[name]["service_class"] == "neon-core"}
    docker_compose_config = dict()
    kubernetes_config = list()
    for name, service in config.items():
        docker_compose_config[name] = service["docker_compose"]
        kubernetes_config.extend(service.get("kubernetes") or list())
    return docker_compose_config, kubernetes_config


def cli_configure_core(config_path: str, output_path: str, namespace: str):
    """
    Handle `configure-core` CLI command
    :param config_path: path to valid core configuration files
    :param output_path: path to write output orchestrator config
    :param namespace: Kubernetes namespace to configure for output
    """
    # Validate input configuration
    if not config_path:
        raise ValueError("config_path not specified")
    config_path = expanduser(config_path)
    if isfile(config_path):
        raise FileExistsError(f"Specified output path is a file")
    _validate_core_configuration(config_path)

    # Validate output path
    output_path = join(expanduser(output_path), "core")
    if not isdir(output_path):
        makedirs(output_path)

    skills_dir = join(config_path, "skills")
    if not isdir(skills_dir):
        makedirs(skills_dir)

    volumes = {"config": config_path,
               "skills": skills_dir}
    namespaces = {"CORE_NAMESPACE": namespace}
    generate_core_config(config_path, output_path, namespaces, volumes)


def generate_core_config(config_path: str, output_path: str, namespaces: dict,
                         volumes: dict):
    """

    """
    docker_compose, kubernetes = _parse_core_services()
    docker_compose_file = join(expanduser(output_path), "docker-compose.yml")
    write_docker_compose(docker_compose, docker_compose_file, "none", volumes)
    write_kubernetes_spec(kubernetes, output_path, namespaces)

    with open(join(config_path, "ngi_local_conf.yml"), 'r+') as f:
        local_config = f.read()
    with open(join(config_path, "ngi_user_info.yml"), 'r+') as f:
        user_config = f.read()
    with open(join(config_path, "ngi_auth_vars.yml"), 'r+') as f:
        auth_config = f.read()
    config_map = {"ngi_local_conf.yml": local_config,
                  "ngi_user_info.yml": user_config}
    secret_map = {"ngi_auth_vars.yml": auth_config}
    generate_config_map("neon-core-config", config_map,
                        join(output_path, "k8s_config_neon.yml"))
    generate_secret("neon-core-auth", secret_map,
                    join(output_path, "k8s_secret_neon.yml"))
