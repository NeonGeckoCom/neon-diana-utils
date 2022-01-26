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

import docker

from os import getenv
from os.path import join, dirname, expanduser
from typing import Optional

from docker.errors import APIError
from docker.models.containers import Container
from ruamel.yaml import YAML
from neon_utils import LOG


def run_clean_rabbit_mq_docker(bind_existing: bool = False) -> Container:
    """
    Start a clean RabbitMQ Docker instance to generate configuration files
    :param bind_existing: If true, allows for binding to a running container
        WARNING: setting `bind_existing` can result in overwriting valid MQ configuration
    """
    docker_client = docker.from_env()
    try:
        container = docker_client.containers.run("rabbitmq:3-management",
                                                 ports={"15672": "15672",
                                                        "5672": "5672"},
                                                 detach=True)
    except APIError as e:
        if e.status_code == 500:
            LOG.warning("Is an instance of RabbitMQ already running?")
            if bind_existing:
                for c in docker_client.containers.list():
                    if "rabbitmq:3-management" in c.image.tags:
                        LOG.info(f"Found a running RabbitMQ instance to configure")
                        return c
        else:
            LOG.error(e)
        raise e
    return container


def cleanup_docker_container(container_to_remove: Container):
    """
    Stop and remove the specified Docker Container
    :param container_to_remove: Docker.Container object to stop and remove
    """
    container_to_remove.stop()
    container_to_remove.remove()


def write_docker_compose(services_config: dict, compose_file: Optional[str] = None,
                         volume_type: str = "none",
                         volumes: Optional[dict] = None):
    """
    Generates and writes a docker-compose.yml file according to the specified services
    :param services_config: dict services, usually read from service_mappings.yml
    :param compose_file: path to docker-compose.yml file to write
    :param volume_type: volume type to use for config (default "none" uses local fs)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    """
    compose_file = compose_file if compose_file else \
        join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), "docker-compose.yml")
    compose_file = expanduser(compose_file)

    with open(join(dirname(dirname(__file__)), "templates", "docker-compose.yml")) as f:
        compose_boilerplate = YAML().load(f)
    compose_contents = {**compose_boilerplate, **{"services": services_config}}

    neon_config_path = volumes.get("config") if volumes else \
        None or dirname(compose_file)
    neon_metric_path = volumes.get("metrics") if volumes else \
        None or expanduser(getenv("NEON_METRIC_PATH", f"{neon_config_path}/metrics"))

    if not volume_type or volume_type == "none":
        config_opts = "bind"
        metric_opts = "bind"
    elif volume_type == "nfs":
        config_host, config_path = neon_config_path.split(':')
        neon_config_path = f"\":{config_path}\""
        metric_host, metric_volume = neon_metric_path.split(':')
        neon_metric_path = f"\":{metric_volume}\""
        config_opts = f"addr={config_host},nolock,rw,soft,nfsvers=4"
        metric_opts = f"addr={metric_host},nolock,rw,soft,nfsvers=4"
    else:
        raise ValueError(f"Unsupported volume_type requested: {volume_type}")

    with open(compose_file, "w+") as f:
        YAML().dump(compose_contents, f)
        f.seek(0)
        string_contents = f.read()
        string_contents = string_contents\
            .replace("${NEON_CONFIG_PATH}", neon_config_path)\
            .replace("${NEON_METRIC_PATH}", neon_metric_path)\
            .replace("${VOLUME_TYPE}", volume_type)\
            .replace("${CONFIG_OPTS}", config_opts)\
            .replace("${METRIC_OPTS}", metric_opts)
        f.seek(0)
        f.truncate(0)
        f.write(string_contents)
