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

import click
import yaml
import json
import secrets
import shutil

from enum import Enum
from pprint import pformat
from typing import Optional
from os import makedirs, listdir, walk, remove
from os.path import expanduser, join, abspath, isfile, isdir, dirname
from ovos_utils.xdg_utils import xdg_config_home
from ovos_utils.log import LOG


class Orchestrator(Enum):
    """
    Enum representing container orchestrators that may be configured
    """
    KUBERNETES = "kubernetes"
    COMPOSE = "docker-compose"


def validate_output_path(output_path: str) -> bool:
    """
    Ensure the requested output path is available to be written
    @returns: True if path is valid, else False
    """
    if isfile(output_path):
        LOG.warning(f"File already exists: {output_path}")
        return False
    elif isdir(output_path) and listdir(output_path):
        LOG.warning(f"Directory is not empty: {output_path}")
        return False
    elif not isdir(dirname(output_path)):
        makedirs(dirname(output_path))
    return True


def make_keys_config(write_config: bool,
                     output_file: str = None) -> Optional[dict]:
    """
    Interactive configuration tool to prompt user for expected API keys and
    service accounts to be included in Configuration.
    @param write_config: If true, write config to `output_file`
    @param output_file: Configuration file to write keys to
    @returns: dict configuration
    """
    if write_config:
        output_file = expanduser(abspath((output_file or join(xdg_config_home(),
                                                              "diana",
                                                              "diana.yaml"))))
        if not validate_output_path(output_file):
            click.echo(f"File already exists: {output_file}")
            return

    api_services = dict()
    if click.confirm("Configure API Proxy Services?"):
        keys_confirmed = False
        while not keys_confirmed:
            wolfram_key = click.prompt("Wolfram|Alpha API Key", type=str)
            alphavantage_key = click.prompt("AlphaVantage API Key",
                                            type=str)
            owm_key = click.prompt("OpenWeatherMap API Key", type=str)
            api_services = {
                "wolfram_alpha": {"api_key": wolfram_key},
                "alpha_vantage": {"api_key": alphavantage_key},
                "open_weather_map": {"api_key": owm_key}
            }
            click.echo(pformat(api_services))
            keys_confirmed = click.confirm("Are these keys correct?")

    email_config = dict()
    if click.confirm("Configure Email Service?"):
        config_confirmed = False
        while not config_confirmed:
            email_addr = click.prompt("Email Address", type=str)
            email_password = click.prompt("Password", type=str)
            smtp_host = click.prompt("SMTP URL", type=str,
                                     default="smtp.gmail.com")
            smtp_port = click.prompt("SMTP Port", type=str,
                                     default="465")
            email_config = {"mail": email_addr,
                            "pass": email_password,
                            "host": smtp_host,
                            "port": smtp_port}
            click.echo(pformat(email_config))
            config_confirmed = \
                click.confirm("Is this configuration correct?")

    brands_config = dict()
    if click.confirm("Configure Brands/Coupons Service?"):
        config_confirmed = False
        while not config_confirmed:
            server_host = click.prompt("SQL Host Address", type=str,
                                       default="trackmybrands.com")
            sql_database = click.prompt("SQL Database", type=str,
                                        default="admintr1_drup1")
            sql_username = click.prompt("SQL Username", type=str)
            sql_password = click.prompt("SQL Password", type=str)
            brands_config = {"host": server_host,
                             "database": sql_database,
                             "user": sql_username,
                             "password": sql_password}
            click.echo(pformat(brands_config))
            config_confirmed = \
                click.confirm("Is this configuration correct?")

    chatgpt_config = dict()
    if click.confirm("Configure ChatGPT Service?"):
        config_confirmed = False
        while not config_confirmed:
            gpt_key = click.prompt("ChatGPT API Key", type=str)
            gpt_model = click.prompt("ChatGPT Model", type=str,
                                     default="gpt-3.5-turbo")
            gpt_role = click.prompt("ChatGPT Role", type=str,
                                    default="You are trying to give a short "
                                            "answer in less than 40 words.")
            gpt_context = click.prompt("ChatGPT Context depth", type=int,
                                       default=3)
            max_tokens = click.prompt("Maximum tokens in responses", type=int,
                                      default=100)
            chatgpt_config = {
                "key": gpt_key,
                "model": gpt_model,
                "role": gpt_role,
                "context_depth": gpt_context,
                "max_tokens": max_tokens
            }
            click.echo(pformat(chatgpt_config))
            config_confirmed = \
                click.confirm("Is this configuration correct?")

    fastchat_config = dict()
    if click.confirm("Configure FastChat Service?"):
        config_confirmed = False
        while not config_confirmed:
            model = click.prompt("FastChat Model", type=str,
                                 default="fastchat")
            context = click.prompt("FastChat context depth", type=int,
                                   default=3)
            max_tokens = click.prompt("Max number of tokens in responses",
                                      type=int, default=128)
            num_processes = click.prompt(
                "Number of queries to handle in parallel",
                type=int, default=1)
            num_threads = click.prompt("Number of threads to use per query",
                                       type=int, default=2)
            fastchat_config = {
                "model": model,
                "context_depth": context,
                "max_tokens": max_tokens,
                "num_parallel_processes": num_processes,
                "num_threads_per_process": num_threads
            }
            click.echo(pformat(fastchat_config))
            config_confirmed = click.confirm("Is this configuration correct?")

    config = {"keys": {"api_services": api_services,
                       "emails": email_config,
                       "track_my_brands": brands_config},
              "ChatGPT": chatgpt_config,
              "FastChat": fastchat_config
              }
    if write_config:
        click.echo(f"Writing configuration to {output_file}")
        with open(output_file, 'w+') as f:
            yaml.dump(config, f)
    return config


def generate_rmq_config(admin_username: str, admin_password: str,
                        output_file: str = None) -> dict:
    """
    Generate a default configuration for RabbitMQ. This defines all default
    users, vhosts, and permissions that may be used with a deployment.
    @param admin_username: Username for admin account
    @param admin_password: Password for admin account
    @param output_file: Optional path to write configuration to
    @returns: dict RabbitMQ Configuration
    """
    base_config_file = join((dirname(__file__)), "templates",
                            "rmq_backend_config.yml")
    with open(base_config_file) as f:
        base_config = yaml.safe_load(f)
    for user in base_config['users']:
        if user["password"]:
            # Skip users with defined passwords
            continue
        user['password'] = secrets.token_urlsafe(32)

    base_config['users'].append({'name': admin_username,
                                 'password': admin_password,
                                 'tags': ['administrator']})

    if output_file and validate_output_path(output_file):
        with open(output_file, 'w+') as f:
            json.dump(base_config, f, indent=2)
    return base_config


def generate_mq_auth_config(rmq_config: dict) -> dict:
    """
    Generate an MQ auth config from RabbitMQ config
    :param rmq_config: RabbitMQ definitions, i.d. from `generate_rmq_config
    :returns: Configuration for Neon MQ-Connector
    """
    mq_user_mapping_file = join(dirname(__file__), "templates",
                                "mq_user_mapping.yml")
    with open(mq_user_mapping_file) as f:
        mq_user_mapping = yaml.safe_load(f)

    mq_config = dict()
    LOG.debug(rmq_config.keys())
    for user in rmq_config['users']:
        username = user['name']
        for service in mq_user_mapping.get(username, []):
            mq_config[service] = {"user": username,
                                  "password": user['password']}
    return mq_config


def update_env_file(env_file: str):
    """
    Update a .env file with absolute paths for `docker compose` compat.
    :param env_file: path to `.env` file to modify
    """
    if not isfile(env_file):
        raise FileNotFoundError(env_file)
    with open(env_file, 'r') as f:
        contents = f.read()
    contents = contents.replace('./', f"{dirname(env_file)}/")
    with open(env_file, 'w') as f:
        f.write(contents)


def _get_neon_mq_user_config(mq_user: Optional[str], mq_pass: Optional[str],
                             backend_config: str) -> dict:
    """
    Get MQ config for neon core.
    @param mq_user: RabbitMQ Neon username
    @param mq_pass: RabbitMQ Neon password
    @param backend_config: Path to Diana Backend configuration file to import
    @returns dict user config to connect Neon Core to an MQ instance
    """
    # Check for passed or previously configured MQ user
    if not all((mq_user, mq_pass)) and isfile(backend_config):
        if click.confirm(f"Import Neon MQ user from {backend_config}?"):
            with open(backend_config) as f:
                config = yaml.safe_load(f)
            user_config = config.get('MQ', {}).get('users',
                                                   {}).get('chat_api_proxy', {})
            mq_user = user_config.get('user')
            mq_pass = user_config.get('password')

    # Interactively configure MQ authentication
    user_config = {"user": mq_user, "password": mq_pass}
    if not all((mq_user, mq_pass)):
        if click.confirm("Configure MQ Connection?"):
            confirmed = False
            while not confirmed:
                mq_user = click.prompt("MQ Username", type=str,
                                       default="neon_core")
                mq_pass = click.prompt("MQ Password", type=str)
                user_config = {
                    "user": mq_user,
                    "password": mq_pass
                }
                click.echo(pformat(user_config))
                confirmed = click.confirm("Is this configuration correct?")

    return user_config


def configure_backend(username: str = None,
                      password: str = None,
                      output_path: str = None,
                      orchestrator: Orchestrator = Orchestrator.KUBERNETES):
    """
    Generate DIANA backend definitions
    @param username: RabbitMQ Admin username to configure
    @param password: RabbitMQ Admin password to configure
    @param output_path: directory to write output definitions to
    @param orchestrator: Container orchestrator to generate configuration for
    """

    # Validate output paths
    output_path = expanduser(output_path or join(xdg_config_home(), "diana"))

    # Output to `backend` subdirectory
    if not validate_output_path(join(output_path, "diana-backend")):
        click.echo(f"Path exists: {output_path}")
        return

    if orchestrator == Orchestrator.KUBERNETES:
        for path in ("diana-backend", "http-services", "ingress-common",
                     "mq-services", "neon-rabbitmq"):
            shutil.copytree(join(dirname(__file__), "helm_charts", path),
                            join(output_path, path))
        # Cleanup any leftover build files
        for root, _, files in walk(dirname(output_path)):
            for file in files:
                if any((file.endswith(x) for x in (".lock", ".tgz"))):
                    remove(join(root, file))
        rmq_file = join(output_path, "diana-backend", "rabbitmq.json")
        diana_config = join(output_path, "diana-backend", "diana.yaml")

    elif orchestrator == Orchestrator.COMPOSE:
        shutil.copytree(join(dirname(__file__), "docker", "backend"),
                        output_path)
        update_env_file(join(output_path, ".env"))
        rmq_file = join(output_path, "xdg", "config", "rabbitmq",
                        "rabbitmq.json")
        diana_config = join(output_path, "xdg", "config", "neon", "diana.yaml")
    else:
        raise RuntimeError(f"{orchestrator} is not yet supported")
    try:
        # Generate RabbitMQ config
        username = username or click.prompt("RabbitMQ Admin Username", type=str)
        password = password or click.prompt("RabbitMQ Admin Password", type=str,
                                            hide_input=True)
        rmq_config = generate_rmq_config(username, password, rmq_file)
        click.echo(f"Generated RabbitMQ config at {rmq_file}")

        # Generate MQ Auth config
        mq_auth_config = generate_mq_auth_config(rmq_config)
        click.echo(f"Generated auth for services: {set(mq_auth_config.keys())}")

        # Generate GH Auth config secret
        if orchestrator == Orchestrator.KUBERNETES:
            from neon_diana_utils.kubernetes_utils import create_github_secret
            if click.confirm("Configure GitHub token for private services?"):
                gh_username = click.prompt("GitHub username", type=str)
                gh_token = click.prompt("GitHub Token with `read:packages` "
                                        "permission", type=str)
                gh_secret_path = join(output_path, "templates",
                                      "secret_gh_token.yaml")
                create_github_secret(gh_username, gh_token, gh_secret_path)
                click.echo(f"Generated GH secret at {gh_secret_path}")

        # Generate `diana.yaml` output
        keys_config = make_keys_config(False)
        config = {**{"MQ": {"users": mq_auth_config,
                            "server": "neon-rabbitmq",
                            "port": 5672}},
                  **keys_config}
        click.echo(f"Writing configuration to {diana_config}")
        with open(diana_config, 'w+') as f:
            yaml.dump(config, f)
        click.echo(f"Outputs generated in {output_path}")

        # Prompt to continue to Neon Core config
        if click.confirm("Configure Neon Core?"):
            user = mq_auth_config.get("chat_api_proxy")
            configure_neon_core(user.get('user'), user.get('password'),
                                output_path, orchestrator)

    except Exception as e:
        click.echo(e)


def configure_neon_core(mq_user: str = None,
                        mq_pass: str = None,
                        output_path: str = None,
                        orchestrator: Orchestrator = Orchestrator.KUBERNETES):
    """
    Generate Neon Core definitions
    @param mq_user: RabbitMQ Neon username to configure
    @param mq_pass: RabbitMQ Neon password to configure
    @param output_path: directory to write output definitions to
    @param orchestrator: Container orchestrator to generate configuration for
    """

    # Validate output paths
    output_path = expanduser(output_path or join(xdg_config_home(), "diana"))
    backend_config = join(output_path, "diana-backend", "diana.yaml")
    # Output to `core` subdirectory
    if not validate_output_path(join(output_path, "neon-core")):
        click.echo(f"Path exists: {output_path}")
        return

    if orchestrator == Orchestrator.KUBERNETES:
        shutil.copytree(join(dirname(__file__), "helm_charts", "neon-core"),
                        join(output_path, "neon-core"))
        # Cleanup any leftover build files
        for root, _, files in walk(join(output_path, "neon-core")):
            for file in files:
                if any((file.endswith(x) for x in (".lock", ".tgz"))):
                    remove(join(root, file))
        neon_config_file = join(output_path, "neon-core", "neon.yaml")

    elif orchestrator == Orchestrator.COMPOSE:
        shutil.copytree(join(dirname(__file__), "docker", "neon_core"),
                        output_path)
        update_env_file(join(output_path, ".env"))
        neon_config_file = join(output_path, "xdg", "config", "neon",
                                "neon.yaml")
    else:
        raise RuntimeError(f"{orchestrator} is not yet supported")

    try:
        # Get MQ User Configuration
        user_config = _get_neon_mq_user_config(mq_user, mq_pass, backend_config)
        if not all((user_config['user'], user_config['password'])):
            # TODO: Prompt to configure MQ server/port?
            mq_config = dict()
        else:
            mq_config = {"users": {"neon_chat_api": user_config},
                         "server": "neon-rabbitmq", "port": 5672}
        # Build default Neon config
        neon_config = {
            "websocket": {"host": "neon-messagebus",
                          "shared_connection": True},
            "gui_websocket": {"host": "neon-gui"},
            "gui": {"server_path": "/xdg/data/neon/gui_files"},
            "ready_settings": ["skills", "voice", "audio", "gui_service"],
            "listener": {"enable_voice_loop": False},
            "stt": {"fallback_module": None},
            "skills": {"blacklisted_skills": [
                "skill-local_music.neongeckocom",
                "skill-device_controls.neongeckocom",
                "skill-update.neongeckocom",
                "neon_homeassistant_skill.mikejgray"]},
            "MQ": mq_config
        }
        click.echo(f"Writing configuration to {neon_config_file}")
        with open(neon_config_file, 'w+') as f:
            yaml.dump(neon_config, f)
        click.echo(f"Outputs generated in {output_path}")
    except Exception as e:
        click.echo(e)
