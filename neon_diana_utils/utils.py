# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
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

import json
import os

from os import getenv
from os.path import join, dirname, expanduser, basename, exists
from typing import Optional

from rabbitmq_api import RabbitMQAPI


DEFAULT_USERS = ["neon_api", "neon_coupons", "neon_email", "neon_metrics", "neon_script_parser"]
DEFAULT_VHOSTS = ["/neon_api", "/neon_coupons", "/neon_emails", "/neon_metrics", "/neon_script_parser", "/neon_testing"]


def create_default_mq_server(url: str, admin_user: str, admin_pass: str):
    """
    Configures the specified MQ server with defaults to support a Neon Diana system.
    """
    api = RabbitMQAPI(url)

    # Configure Administrator
    api.login("guest", "guest")
    api.configure_admin_account(admin_user, admin_pass)

    # Default users
    api.add_user("neon_api_utils", "Klatchat2021")
    credentials = api.create_default_users(DEFAULT_USERS)

    # Default vhosts
    for vhost in DEFAULT_VHOSTS:
        api.add_vhost(vhost)

    # Default permissions
    api.configure_vhost_user_permissions("/neon_api", "neon_api")
    api.configure_vhost_user_permissions("/neon_api", "neon_api_utils")  # TODO: More specific read perms DM
    api.configure_vhost_user_permissions("/neon_coupons", "neon_coupons")
    api.configure_vhost_user_permissions("/neon_coupons", "neon_api_utils")  # TODO: More specific read perms DM
    api.configure_vhost_user_permissions("/neon_emails", "neon_email")
    api.configure_vhost_user_permissions("/neon_emails", "neon_api_utils", read="^(?!neon_emails_input).*")
    api.configure_vhost_user_permissions("/neon_metrics", "neon_metrics")
    api.configure_vhost_user_permissions("/neon_metrics", "neon_api_utils", read="")
    api.configure_vhost_user_permissions("/neon_script_parser", "neon_script_parser")
    api.configure_vhost_user_permissions("/neon_script_parser", "neon_api_utils")  # TODO: More specific read perms DM
    api.configure_vhost_user_permissions("/neon_testing", "neon_api_utils")

    # Write out MQ config file
    write_mq_config(credentials)

    # Export and save rabbitMQ Config
    write_rabbit_config(api)


def write_mq_config(credentials: dict, config_file: Optional[str] = None):
    """
    Takes the passed credentials and exports an MQ config file based on the
    """
    config_file = config_file if config_file else join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), "mq_config.json")
    config_file = expanduser(config_file)
    if not exists(dirname(config_file)):
        os.makedirs(dirname(config_file))

    default_config = join(dirname(__file__), "clean_mq_config.json")
    with open(default_config, 'r') as default_conf:
        configuration = json.load(default_conf)
    for service in configuration["users"]:
        configuration["users"][service]["password"] = credentials.get(configuration["users"][service]["user"])
    with open(config_file, 'w+') as new_config:
        json.dump(configuration, new_config, indent=2)


def write_rabbit_config(api: RabbitMQAPI, config_file: Optional[str] = None):
    """
    Writes out RabbitMQ config files for persistence on next run
    """
    config_file = config_file if config_file else join(getenv("NEON_CONFIG_PATH", "~/.config/neon"),
                                                       "rabbit_mq_config.json")
    config_file = expanduser(config_file)
    config_path = dirname(config_file)
    if not exists(config_path):
        os.makedirs(config_path)

    config = api.get_definitions()
    with open(config_file, "w+") as exported:
        json.dump(config, exported, indent=2)

    config_basename = basename(config_file)
    with open(join(config_path, "rabbitmq.conf"), 'w+') as rabbit:
        rabbit.write(f"load_definitions = /config/{config_basename}")
