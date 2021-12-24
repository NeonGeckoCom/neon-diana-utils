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

from os.path import dirname, join, isfile, isdir
from neon_utils.logger import LOG
from neon_diana_utils.orchestrators import Orchestrator


def convert_docker_compose(compose_file: str, orchestrator: Orchestrator):
    """
    Convert the specified compose file into resources to deploy to Kubernetes.
    :param compose_file: path to docker-compose.yml file to convert
    :param orchestrator: orchestrator to generate resources for
    """
    docker_compose_dir = dirname(compose_file)
    if orchestrator == Orchestrator.KUBERNETES:
        provider = "kubernetes"
    elif orchestrator == Orchestrator.OPENSHIFT:
        provider = "openshift"
    else:
        LOG.error(f"Unhandled orchestrator: {orchestrator.name}. Fallback to Kubernetes")
        provider = "kubernetes"
    subprocess.Popen(["/bin/bash", "-c",
                      f"kompose convert -f {compose_file} "
                      f"-o {join(docker_compose_dir, provider)}.yml "
                      f"--provider {provider}"]).communicate()
    # TODO: PVC RWO -> RWM DM


def generate_nfs_volume_config(host: str, config_path: str, metric_path: str, output_path: str):
    """
    Generate a Kubernetes configuration for NFS-based persistent volumes
    :param host: NFS Server hostname
    :param config_path: host path to config dir
    :param metric_path: host path to metric dir
    :param output_path: path to output file
    """
    if isfile(output_path):
        raise FileExistsError(f"{output_path} already exists!")
    if not isdir(dirname(output_path)):
        raise ValueError(f"Output directory does not exist: {dirname(output_path)}")

    nfs_volume_template = join(dirname(dirname(__file__)),
                               "templates", "k8s_nfs_volume.yml")
    with open(nfs_volume_template, 'r') as f:
        nfs_config = f.read()
    nfs_config.replace("${HOST}", host)\
        .replace("${METRIC_PATH}", metric_path)\
        .replace("${CONFIG_PATH}", config_path)

    with open(output_path, 'w+') as f:
        f.write(nfs_config)

    # TODO: How to associate a specific PV with a PVC DM
