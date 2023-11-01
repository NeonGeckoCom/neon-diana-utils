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

import yaml

from typing import Optional
from os import getenv
from os.path import join, expanduser

from ovos_utils.log import log_deprecation

from neon_diana_utils.configuration import validate_output_path


def create_github_secret(username: str, token: str,
                         output_file: Optional[str] = None) -> str:
    """
    Generate a Kubernetes Secret to authenticate to GitHub for image pulls
    :param username: GitHub username
    :param token: GitHub token with read_packages permission
    :param output_file: output file to write
    :returns: path to written Kubernetes config file
    """
    log_deprecation("Secret specs are handled in Helm charts. Use "
                    "`get_github_encoded_auth` to get textual config value.",
                    "2.0.0")
    import json
    from base64 import b64encode
    output_file = output_file or join(getenv("NEON_CONFIG_PATH",
                                             "~/.config/neon"),
                                      f"k8s_secret_github.yml")
    output_file = expanduser(output_file)
    if not validate_output_path(output_file):
        raise FileExistsError(output_file)
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
    with open(output_file, 'w+') as f:
        yaml.dump(secret_spec, f)
    return output_file


def get_github_encoded_auth(username: str, token: str) -> str:
    """
    Parse a GitHub username and token into an encoded string to use in a
    Kubernetes secret for pulling images.
    :param username: GitHub username
    :param token: GitHub token with read_packages permission
    :returns: string Kubernetes config value (ghTokenEncoded)
    """
    import json
    from base64 import b64encode
    encoded_auth = b64encode(f"{username}:{token}".encode())
    auth_dict = {"auths": {"ghcr.io": {"auth": encoded_auth.decode()}}}
    auth_str = json.dumps(auth_dict)
    encoded_config = b64encode(auth_str.encode())
    return encoded_config.decode()
