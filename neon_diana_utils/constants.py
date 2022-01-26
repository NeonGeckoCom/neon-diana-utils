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

from enum import Enum, IntEnum
from os.path import join, dirname
from ruamel.yaml import YAML


class Orchestrator(IntEnum):
    DOCKER = 0
    KUBERNETES = 1
    OPENSHIFT = 2


class ServiceClass(Enum):
    MQ = "mq-backend"
    HTTP = "http-backend"
    CORE = "neon-core"


def _get_services_by_class() -> dict:
    """
    Gets a dict of service names by ServiceClass
    """
    service_mappings = join(dirname(__file__), "templates", "service_mappings.yml")
    with open(service_mappings) as f:
        services = YAML().load(f)
    # valid_service_classes = set([svc.get("service_class") for name, svc in services.items()])
    services_by_class = dict()
    for name, data in services.items():
        if data["service_class"] not in services_by_class:
            services_by_class[data["service_class"]] = list()
        services_by_class[data["service_class"]].append(name)
    return services_by_class


def valid_mq_services() -> set:
    """
    Get the set of valid MQ services that can be automatically configured
    """
    return set(_get_services_by_class()[ServiceClass.MQ.value])


def valid_http_services() -> set:
    """
    Get the set of valid HTTP services that can be automatically configured
    """
    return set(_get_services_by_class()[ServiceClass.HTTP.value])


def default_mq_services() -> set:
    """
    Return a specified set of default MQ services
    """
    return {"neon-rabbitmq",
            "neon-api-proxy",
            "neon-email-proxy",
            "neon-metrics-service"}
