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
from typing import Optional, Set
from os import makedirs, listdir
from os.path import expanduser, join, abspath, isfile, isdir, dirname
from ovos_utils.xdg_utils import xdg_config_home
from ovos_utils.log import LOG


class Orchestrator(Enum):
    """
    Enum representing container orchestrators that may be configured
    """
    KUBERNETES = "kubernetes"
    COMPOSE = "docker-compose"


# def _collect_helm_charts(output_path: str, charts_dir: str):
#     """
#     Collect Helm charts in the output directory and remove any leftover build
#     artifacts.
#     """
#     shutil.copytree(join(dirname(__file__), "helm_charts", charts_dir),
#                     join(output_path, charts_dir))
#     # Cleanup any leftover build files
#     for root, _, files in walk(join(output_path, charts_dir)):
#         for file in files:
#             if any((file.endswith(x) for x in (".lock", ".tgz"))):
#                 remove(join(root, file))


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


def make_llm_bot_config():
    """
    Interactive configuration tool to configure llm personas to participate in
    chatbotsforum/Klat.
    """
    with open(join(dirname(__file__), "templates", "llm_personas.yml")) as f:
        persona_config = yaml.safe_load(f)
    configuration = {"llm_bots": dict()}
    if click.confirm("Configure ChatGPT Personas?"):
        configuration['llm_bots']['chat_gpt'] = persona_config['chat_gpt']
    if click.confirm("Configure PaLM2 Personas?"):
        configuration['llm_bots']['palm2'] = persona_config['palm2']
    if click.confirm("Configure Gemini Personas?"):
        configuration['llm_bots']['gemini'] = persona_config['gemini']
    if click.confirm("Configure Claude Personas?"):
        configuration['llm_bots']['claude'] = persona_config['claude']
    return configuration


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
            maps_key = click.prompt("geocode.maps.co API Key", type=str)
            api_services = {
                "wolfram_alpha": {"api_key": wolfram_key},
                "alpha_vantage": {"api_key": alphavantage_key},
                "open_weather_map": {"api_key": owm_key},
                "map_maker": {"api_key": maps_key}
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
    if click.confirm("Configure ChatGPT LLM?"):
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
                "max_tokens": max_tokens,
                "num_parallel_processes": 1
            }
            click.echo(pformat(chatgpt_config))
            config_confirmed = \
                click.confirm("Is this configuration correct?")

    fastchat_config = dict()
    if click.confirm("Configure FastChat LLM?"):
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

    palm2_config = dict()
    if click.confirm("Configure PaLM2 LLM?"):
        config_confirmed = False
        while not config_confirmed:
            role = click.prompt("PaLM2 Role", type=str,
                                default="You are trying to give a short "
                                        "answer in less than 40 words.")
            context = click.prompt("PaLM2 context depth", type=int,
                                   default=3)
            max_tokens = click.prompt("Max number of tokens in responses",
                                      type=int, default=100)
            num_processes = click.prompt(
                "Number of queries to handle in parallel",
                type=int, default=1)
            palm2_config = {
                "key_path": "/config/neon/google.json",
                "role": role,
                "context_depth": context,
                "max_tokens": max_tokens,
                "num_parallel_processes": num_processes
            }
            click.echo(pformat(palm2_config))
            config_confirmed = click.confirm("Is this configuration correct?")

    gemini_config = dict()
    if click.confirm("Configure Gemini LLM?"):
        config_confirmed = False
        while not config_confirmed:
            model = click.prompt("Gemini Model", type=str,
                                 default="gemini-pro")
            role = click.prompt("Gemini Role", type=str,
                                default="You are trying to give a short "
                                        "answer in less than 40 words.")
            context = click.prompt("Gemini context depth", type=int,
                                   default=3)
            max_tokens = click.prompt("Max number of tokens in responses",
                                      type=int, default=100)
            num_processes = click.prompt(
                "Number of queries to handle in parallel",
                type=int, default=1)
            gemini_config = {
                "key_path": "/config/neon/google.json",
                "model": model,
                "role": role,
                "context_depth": context,
                "max_tokens": max_tokens,
                "num_parallel_processes": num_processes
            }
            click.echo(pformat(gemini_config))
            config_confirmed = click.confirm("Is this configuration correct?")

    claude_config = dict()
    if click.confirm("Configure Anthropic Claude LLM?"):
        config_confirmed = False
        while not config_confirmed:
            anthropic_key = click.prompt("Antrhopic API Key", type=str)
            openai_key = click.prompt("OpenAI API Key", type=str,
                                      default=chatgpt_config.get('key'))
            model = click.prompt("Anthropic Model", type=str,
                                 default="claude-2")
            role = click.prompt("Role", type=str,
                                default="You are trying to give a short "
                                        "answer in less than 40 words.")
            context = click.prompt("Context depth", type=int, default=3)
            max_tokens = click.prompt("Maximum tokens in responses", type=int,
                                      default=256)
            claude_config = {
                "key": anthropic_key,
                "openai_key": openai_key,
                "model": model,
                "role": role,
                "context_depth": context,
                "max_tokens": max_tokens
            }
            click.echo(pformat(claude_config))
            config_confirmed = \
                click.confirm("Is this configuration correct?")

    config = {"keys": {"api_services": api_services,
                       "emails": email_config,
                       "track_my_brands": brands_config},
              "LLM_CHAT_GPT": chatgpt_config,
              "LLM_FASTCHAT": fastchat_config,
              "LLM_PALM2": palm2_config,
              "LLM_GEMINI": gemini_config,
              "LLM_CLAUDE": claude_config,
              "FastChat": fastchat_config,  # TODO: Backwards-compat. only
              "hana": {
                  "access_token_secret": secrets.token_hex(32),
                  "refresh_token_secret": secrets.token_hex(32)
              }
              }
    if write_config:
        click.echo(f"Writing configuration to {output_file}")
        with open(output_file, 'w+') as f:
            yaml.dump(config, f)
    return config


def update_rmq_config(config_file: str = None) -> str:
    """
    Update an existing RabbitMQ configuration with new definitions from DIANA.
    This can be used to handle added service users without changing existing
    ones and to reset/update permissions and vhosts.
    @param config_file: Path to file to be updated
    @returns: Path to updated file
    """
    if not config_file:
        config_file = join(xdg_config_home(), "diana", "diana-backend",
                           "rabbitmq.json")
    else:
        config_file = expanduser(config_file)

    if not isfile(config_file):
        raise FileNotFoundError(config_file)

    with open(config_file) as f:
        real_config = json.load(f)
    new_config = generate_rmq_config("", "")
    existing_users = [user['name'] for user in real_config['users']]
    for user in new_config['users']:
        if user['name'] in existing_users:
            continue
        LOG.info(f"Adding user: {user['name']}")
        real_config['users'].append(user)
    real_config['vhosts'] = new_config['vhosts']
    real_config['permissions'] = new_config['permissions']

    shutil.move(config_file, f"{config_file}.old")
    with open(config_file, 'w+') as f:
        json.dump(real_config, f, indent=2)
    return config_file


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

    if admin_username and admin_password:
        base_config['users'].append({'name': admin_username,
                                     'password': admin_password,
                                     'tags': ['administrator']})
    else:
        LOG.debug("Not adding unconfigured admin user")
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


def generate_hana_config() -> dict:
    """
    Generate HANA config based on user inputs.
    :returns: Configuration for HANA frontend
    """
    click.echo("Configuring HANA (HTTP API for Neon AI)")
    email = click.confirm("Enable endpoint to send email?")
    node_user, node_pass = None, None
    if click.confirm("Enable node websocket connections?"):
        node_user = click.prompt("Node username", type=str, default="neon")
        node_pass = click.prompt("Node password", type=str, default="neon")
    rpm = click.prompt("Client maximum requests per limit", type=int,
                       default=60)
    auth_rpm = click.prompt("Client maximum auth requests per limit",
                            type=int, default=6)

    hana_config = {"enable_email": email,
                   "node_username": node_user,
                   "node_password": node_pass,
                   "access_token_secret": secrets.token_hex(32),
                   "refresh_token_secret": secrets.token_hex(32),
                   "requests_per_minute": rpm,
                   "auth_requests_per_minute": auth_rpm
                   }
    LOG.debug(pformat(hana_config))
    return {"hana": hana_config}


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


def _get_mq_service_user_config(mq_user: Optional[str], mq_pass: Optional[str],
                                mq_tag: str, rmq_config: str) -> dict:
    """
    Get MQ config for an added service from an existing RabbitMQ configuration.
    @param mq_user: RabbitMQ service username
    @param mq_pass: RabbitMQ service password
    @param mq_tag: RabbitMQ User tag used to identify this service
    @param rmq_config: Path to RabbitMQ configuration file to import
    @returns dict user config to connect Neon Core to an MQ instance
    """
    # Check for passed or previously configured MQ user
    if not all((mq_user, mq_pass)) and isfile(rmq_config):
        if click.confirm(f"Import {mq_tag} MQ user from {rmq_config}?"):
            with open(rmq_config) as f:
                config = json.load(f)
            for user in config['users']:
                if mq_tag in user['tags']:
                    mq_user = user['name']
                    mq_pass = user['password']
                    break

    # Interactively configure MQ authentication
    user_config = {"user": mq_user, "password": mq_pass}
    if not all((mq_user, mq_pass)):
        if click.confirm("Configure MQ Connection Manually?"):
            confirmed = False
            while not confirmed:
                mq_user = click.prompt("MQ Username", type=str)
                mq_pass = click.prompt("MQ Password", type=str)
                user_config = {
                    "user": mq_user,
                    "password": mq_pass
                }
                click.echo(pformat(user_config))
                confirmed = click.confirm("Is this configuration correct?")

    return user_config


def _get_chatbots_mq_config(rmq_config: str) -> dict:
    """
    Get MQ config for chatbots.
    @param rmq_config: Path to RabbitMQ configuration file to import
    @returns: dict configuration for chatbots
    """
    # Define default user mappings and MQ config
    mq_map_file = join(dirname(__file__), "templates", "mq_user_mapping.yml")
    chatbot_config = {"server": "neon-rabbitmq",
                      "port": 5672,
                      "users": {}}
    with open(mq_map_file) as f:
        mq_mapping = yaml.safe_load(f)
    subminds = mq_mapping['neon_bot_submind']
    facilitators = mq_mapping['neon_bot_facilitator']
    for user in subminds:
        chatbot_config['users'][user] = {"user": "neon_bot_submind",
                                         "password": ""}
    for user in facilitators:
        chatbot_config['users'][user] = {"user": "neon_bot_facilitator",
                                         "password": ""}
    if not click.confirm(f"Import Chatbot users from {rmq_config}?"):
        click.echo("Chatbot user passwords will need to be manually configured")
        return {"MQ": chatbot_config}

    with open(rmq_config) as f:
        config = json.load(f)

    # Get auth from MQ config
    submind_pass = ""
    facilitator_pass = ""
    for user in config['users']:
        if user['name'] == 'neon_bot_submind':
            submind_pass = user['password']
        if user['name'] == 'neon_bot_facilitator':
            facilitator_pass = user['password']

    # Update MQ config for chatbot users with MQ auth
    for user in chatbot_config['users']:
        if chatbot_config['users'][user]['user'] == 'neon_bot_submind':
            chatbot_config['users'][user]['password'] = submind_pass
        elif chatbot_config['users'][user]['user'] == 'neon_bot_facilitator':
            chatbot_config['users'][user]['password'] = facilitator_pass
        else:
            LOG.warning(f"Unknown user: {user}")

    return {"MQ": chatbot_config}


def _get_unconfigured_mq_backend_services(config: dict) -> Set[str]:
    """
    Get a list of MQ Backend services that are not configured to run
    @param config: dict Configuration (diana.yaml)
    """
    config_to_service = {'keys.api_services': 'neon-api-proxy',
                         'keys.emails': 'neon-email-proxy',
                         'keys.track_my_brands': 'neon-brands-service',
                         'LLM_CHAT_GPT': 'neon-llm-chatgpt',
                         'LLM_FASTCHAT': 'neon-llm-fastchat',
                         'LLM_CLAUDE': 'neon-llm-claude',
                         'LLM_GEMINI': 'neon-llm-gemini',
                         'LLM_PALM2': 'neon-llm-palm'}
    disabled = list()
    for key, service in config_to_service.items():
        if '.' in key:
            parts = key.split('.')
            test = dict(config)
            for part in parts:
                test = test.get(part)
            if not test:
                disabled.append(service)
        else:
            if not config.get(key):
                disabled.append(service)
    return set(disabled)


def _get_optional_http_backend() -> Set[str]:
    """
    Get a set of optional HTTP backend services
    """
    return {'tts-larynx', 'tts-ljspeech', 'tts-mozilla', 'tts-nancy',
            'tts-glados', 'ww-snowboy'}


def _read_backend_domain(deploy_path: str) -> str:
    """
    Read backend configuration to determine the configured root domain
    @param deploy_path: Path to diana-backend deployment
    """
    if isdir(join(deploy_path, "diana-backend")):
        deploy_path = join(deploy_path, "diana-backend")
    values_file = join(deploy_path, "values.yaml")
    if not isfile(values_file):
        raise FileNotFoundError(values_file)
    with open(values_file, 'r') as f:
        backend_config = yaml.safe_load(f)
    root_domain = backend_config.get('backend', {}).get('diana-http',
                                                        {}).get('domain')
    if not root_domain:
        raise ValueError(f"Expected config not found in: {values_file}")
    return root_domain


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
    if not validate_output_path(join(output_path, "backend")):
        click.echo(f"Path exists: {output_path}")
        return

    # Collect user inputs for service configuration
    keys_config = make_keys_config(False)
    disabled_mq_services = list(
        _get_unconfigured_mq_backend_services(keys_config))

    if orchestrator == Orchestrator.KUBERNETES:
        shutil.copytree(join(dirname(__file__), "templates", "backend"),
                        join(output_path, "diana-backend"))
        rmq_file = join(output_path, "diana-backend", "rabbitmq.json")
        diana_config = join(output_path, "diana-backend", "diana.yaml")

        # Do Helm configuration
        from neon_diana_utils.kubernetes_utils import get_github_encoded_auth
        # Generate GH Auth config secret
        if click.confirm("Configure GitHub token for private services?"):
            gh_username = click.prompt("GitHub username", type=str)
            gh_token = click.prompt("GitHub Token with `read:packages` "
                                    "permission", type=str)
            encoded_token = get_github_encoded_auth(gh_username, gh_token)
            click.echo(f"Parsed GH token for {gh_username}")
        else:
            # Define a default value so secret can be generated
            encoded_token = get_github_encoded_auth("", "")
            to_disable = ['neon-brands-service', 'neon-script-parser']
            disabled_mq_services += to_disable
        confirmed = False
        email = ''
        domain = ''
        tag = 'latest'
        while not confirmed:
            email = click.prompt("Email address for SSL Certificates",
                                 type=str, default=email)
            domain = click.prompt("Root domain for HTTP services",
                                  type=str, default=domain)
            tag = click.prompt("Image tags to use for MQ Services",
                               type=str, default=tag)
            click.echo(pformat({'email': email,
                                'domain': domain,
                                'tag': tag}))
            confirmed = click.confirm("Is this configuration correct?")

        click.echo(f"The following MQ services are disabled: "
                   f"{disabled_mq_services}")

        if click.confirm(f"Disable optional HTTP Services?"):
            disabled_http_services = _get_optional_http_backend()
            click.echo(f"The following HTTP services are disabled: "
                       f"{disabled_http_services}")
        else:
            disabled_http_services = set()

        # Generate values.yaml with configured params
        values_file = join(output_path, "diana-backend", "values.yaml")
        with open(values_file, 'r') as f:
            helm_values = yaml.safe_load(f)
        helm_values['backend']['letsencrypt']['email'] = email
        helm_values['backend']['diana-http']['domain'] = domain
        helm_values['backend']['ghTokenEncoded'] = encoded_token
        for service in disabled_mq_services:
            LOG.debug(f"Disable {service}")
            helm_values['backend']['diana-mq'][service]['replicaCount'] = 0
        for service in disabled_http_services:
            LOG.debug(f"Disable {service}")
            helm_values['backend']['diana-http'].setdefault(service, dict())
            helm_values['backend']['diana-http'][service]['replicaCount'] = 0
        for service in helm_values['backend']['diana-mq']:
            helm_values['backend']['diana-mq'][service]['image']['tag'] = \
                tag
        helm_values['backend']['diana-http']['endpoint-hana']['image']['tag'] \
            = tag
        with open(values_file, 'w') as f:
            yaml.safe_dump(helm_values, f)
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

        # Generate HANA frontend config
        hana_config = generate_hana_config()

        # Generate `diana.yaml` output
        if keys_config.get("LLM_CHAT_GPT"):
            llm_config = make_llm_bot_config()
        else:
            llm_config = dict()
        # Check if google.json file is expected
        if any((keys_config['LLM_PALM2'], keys_config['LLM_GEMINI'])):
            handled = False
            while not handled:
                cred = click.prompt("Path to Google credential file", type=str)
                cred = expanduser(cred)
                if not isfile(cred):
                    click.echo(f"Invalid path ({cred}). Please, try again.")
                else:
                    shutil.copyfile(cred, join(dirname(diana_config),
                                               "google.json"))
                    handled = True
        config = {**{"MQ": {"users": mq_auth_config,
                            "server": "neon-rabbitmq",
                            "port": 5672}},
                  **keys_config,
                  **llm_config,
                  **hana_config}
        click.echo(f"Writing configuration to {diana_config}")
        with open(diana_config, 'w+') as f:
            yaml.dump(config, f)
        click.echo(f"Outputs generated in {output_path}")

        # Prompt to continue to Neon Core config
        if click.confirm("Configure Neon Core?"):
            user = mq_auth_config.get("chat_api_proxy")
            configure_neon_core(user.get('user'), user.get('password'),
                                output_path, orchestrator)

        # Prompt to continue to Chatbots config
        if click.confirm("Configure Chatbots?"):
            configure_chatbots(rmq_file, output_path, False, orchestrator)

        # TODO: Prompt for Klat deployment?

    except Exception as e:
        click.echo(e)


def configure_chatbots(rmq_path: str = None,
                       output_path: str = None,
                       prompt_update_rmq: bool = True,
                       orchestrator: Orchestrator = Orchestrator.KUBERNETES):
    """
    Generate Chatbots definitions
    @param rmq_path: Path to RabbitMQ configuration file
    @param output_path: directory to write output definitions to
    @param prompt_update_rmq: if True, prompt user to update RabbitMQ config to
        add chatbot-related users, vhosts, etc.
    @param orchestrator: Container orchestrator to generate configuration for
    """
    output_path = expanduser(output_path or join(xdg_config_home(), "diana"))
    rmq_config = rmq_path or join(output_path, "diana-backend", "rabbitmq.json")
    # Output to `chatbots` subdirectory
    if not validate_output_path(join(output_path, "chatbots")):
        click.echo(f"Path exists: {output_path}")
        return
    try:
        if orchestrator == Orchestrator.KUBERNETES:
            shutil.copytree(join(dirname(__file__), "templates", "chatbots"),
                            join(output_path, "chatbots"))
        else:
            raise RuntimeError(f"{orchestrator} is not yet supported")

        if prompt_update_rmq and click.confirm("Configure RabbitMQ for chatbots?"):
            update_rmq_config(rmq_config)
            click.echo(f"Updated RabbitMQ config file: {rmq_config}")
        chatbots_config = _get_chatbots_mq_config(rmq_config)
        with open(join(output_path, "chatbots", "chatbots.yaml"), 'w+') as f:
            yaml.safe_dump(chatbots_config, f)
        click.echo(f"Outputs generated in {output_path}")

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
    rmq_config = join(output_path, "diana-backend", "rabbitmq.json")
    # Output to `core` subdirectory
    if not validate_output_path(join(output_path, "neon-core")):
        click.echo(f"Path exists: {output_path}")
        return

    # Prompt for IRIS Web UI configuration
    iris_domain = None
    if click.confirm("Configure IRIS Gradio Web UI?"):
        confirmed = False
        try:
            domain = _read_backend_domain(output_path)
        except FileNotFoundError:
            domain = "diana.k8s"
        while not confirmed:
            iris_domain = click.prompt("Hostname for Iris Gradio Web UI",
                                       type=str, default=f"iris.{domain}")
            confirmed = click.confirm(f"Is {iris_domain} correct?")

    if orchestrator == Orchestrator.KUBERNETES:
        shutil.copytree(join(dirname(__file__), "templates", "neon"),
                        join(output_path, "neon-core"))
        neon_config_file = join(output_path, "neon-core", "neon.yaml")

        # Determine image tag to use
        tag = 'latest'
        confirmed = False
        while not confirmed:
            tag = click.prompt("Image tags to use for Neon Core Services",
                               type=str, default=tag)
            confirmed = click.confirm(f"Is `{tag}` correct?")
        values = join(output_path, "neon-core", "values.yaml")
        with open(values, "r") as f:
            config = yaml.safe_load(f)
        for service in {'neon-messagebus', 'neon-speech', 'neon-skills',
                        'neon-audio', 'neon-enclosure', 'neon-gui',
                        'iris-gradio'}:
            config['core'][service]['image']['tag'] = tag

        if iris_domain:
            iris_subdomain, iris_domain = iris_domain.split('.', 1)
            config['core']['domain'] = iris_domain
            config['core']['ingress']['rules'].append(
                {'host': iris_subdomain, 'serviceName': 'neon-core-iris',
                 'servicePort': 7860})
        else:
            click.echo("iris Gradio UI disabled")
            config['core']['iris-gradio']['replicaCount'] = 0

        if not config['core']['ingress']['rules']:
            click.echo('No HTTP ingress configured')
            config['core']['ingress']['enabled'] = False
        with open(values, 'w') as f:
            yaml.safe_dump(config, f)
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
        user_config = _get_mq_service_user_config(mq_user, mq_pass, "core",
                                                  rmq_config)
        if not all((user_config['user'], user_config['password'])):
            # TODO: Prompt to configure MQ server/port?
            mq_config = dict()
        else:
            mq_config = {"users": {"neon_chat_api": user_config},
                         "server": "neon-rabbitmq", "port": 5672}
        # Build default Neon config
        neon_config = {
            "websocket": {"host": "neon-core-messagebus",
                          "shared_connection": True},
            "gui_websocket": {"host": "neon-core-gui"},
            "gui": {"server_path": "/xdg/data/neon/gui_files"},
            "ready_settings": ["skills", "voice", "audio", "gui_service"],
            "listener": {"enable_voice_loop": False},
            "stt": {"module": "neon-stt-plugin-nemo-remote",
                    "neon-stt-plugin-nemo-remote": {
                        "url": "http://backend-nemo:4430"}},
            "tts": {"module": "neon-tts-plugin-coqui-remote",
                    "neon-tts-plugin-coqui-remote": {
                        "url": "http://backend-coqui:4430"}},
            "skills": {"blacklisted_skills": [
                "skill-local_music.neongeckocom",
                "skill-device_controls.neongeckocom",
                "skill-update.neongeckocom",
                "neon_homeassistant_skill.mikejgray",
                "skill-homescreen-lite.openvoiceos"]},
            "MQ": mq_config,
            "iris": {"languages": ["en-us", "uk-ua"]},
            "log_level": "DEBUG"
        }
        click.echo(f"Writing configuration to {neon_config_file}")
        with open(neon_config_file, 'w+') as f:
            yaml.dump(neon_config, f)
        click.echo(f"Outputs generated in {output_path}")
    except Exception as e:
        click.echo(e)


def configure_klat_chat(external_url: str = None,
                        mongo_config: dict = None,
                        sftp_config: dict = None,
                        mq_user: str = None,
                        mq_pass: str = None,
                        output_path: str = None,
                        orchestrator: Orchestrator = Orchestrator.KUBERNETES,
                        prompt_update_rmq: bool = True):
    """
    Generate Klat chat definitions
    @param mq_user: RabbitMQ Klat observer username to configure
    @param mq_pass: RabbitMQ Klat observer password to configure
    @param output_path: directory to write output definitions to
    @param orchestrator: Container orchestrator to generate configuration for
    """

    # Validate output paths
    output_path = expanduser(output_path or join(xdg_config_home(), "diana"))
    rmq_config = join(output_path, "diana-backend", "rabbitmq.json")
    # Output to `core` subdirectory
    if not validate_output_path(join(output_path, "klat-chat")):
        click.echo(f"Path exists: {output_path}")
        return

    # Get MQ User Configuration
    if prompt_update_rmq and click.confirm("(Re-)Configure RabbitMQ for Klat?"):
        update_rmq_config(rmq_config)
        click.echo(f"Updated RabbitMQ config file: {rmq_config}")
    user_config = _get_mq_service_user_config(mq_user, mq_pass, "klat",
                                              rmq_config)
    # Get configuration
    mongo_config = mongo_config or dict()
    mongodb_port = mongo_config.get("port") or 27017
    sftp_config = sftp_config or dict()

    # Confirm URL
    while not external_url:
        external_url = click.prompt("Klat Client URL", type=str)
        if not click.confirm(f"Is '{external_url}' correct?"):
            external_url = None
    if not external_url.startswith("http"):
        external_url = f"https://{external_url}"

    # Confirm API URL
    subdomain, domain = external_url.split('://', 1)[1].split('.', 1)
    api_url = external_url.replace(subdomain, "klatapi", 1)
    confirmed = False
    while not confirmed:
        api_url = click.prompt("Klat API URL", type=str,
                               default=api_url)
        confirmed = click.confirm(f"Is '{api_url}' correct?")
    api_subdomain = api_url.split('://', 1)[1].split('.', 1)[0]

    forward_www = False
    if subdomain != "www":
        forward_www = click.confirm(f"Route www.{domain} traffic to Klat?")

    # Get Libretranslate HTTP API URL
    libretranslate_url = "https://libretranslate.2022.us"
    confirmed = False
    while not confirmed:
        libretranslate_url = click.prompt("Libretranslate API URL", type=str,
                                          default=libretranslate_url)
        confirmed = click.confirm(f"Is '{libretranslate_url}' correct?")

    # Validate https URL
    https = external_url.startswith("https")

    # Confirm MongoDB host/port
    confirmed = False
    while not confirmed:
        mongodb_host = click.prompt("MongoDB host address", type=str,
                                    default=mongo_config.get("host"))
        if ':' in mongodb_host:
            mongodb_host, mongodb_port = mongodb_host.split(':')
            mongodb_port = int(mongodb_port)
        else:
            mongodb_port = click.prompt("MongoDB port", type=int,
                                        default=mongodb_port)
        mongodb_user = click.prompt("MongoDB username", type=str,
                                    default=mongo_config.get("username"))
        mongodb_pass = click.prompt("MongoDB password", type=str,
                                    default=mongo_config.get("password"))
        mongo_database = click.prompt("MongoDB database", type=str,
                                      default=mongo_config.get("database"))

        mongo_config = {"host": mongodb_host,
                        "port": mongodb_port,
                        "username": mongodb_user,
                        "password": mongodb_pass,
                        "database": mongo_database}
        click.echo(pformat(mongo_config))
        confirmed = click.confirm("Is this configuration correct?")
    mongo_config['dialect'] = 'mongo'

    # Configure SFTP
    confirmed = False
    while not confirmed:
        sftp_host = click.prompt("SFTP host URL/IP address", type=str)
        sftp_port = click.prompt("SFTP port", type=int, default=22)
        sftp_user = click.prompt("SFTP auth username", type=str)
        sftp_pass = click.prompt("SFTP auth password", type=str)
        sftp_root = click.prompt("SFTP root path", type=str,
                                 default="/files/klat/")
        sftp_config = {"HOST": sftp_host,
                       "PORT": sftp_port,
                       "USERNAME": sftp_user,
                       "PASSWORD": sftp_pass,
                       "ROOT_PATH": sftp_root}
        click.echo(pformat(sftp_config))
        confirmed = click.confirm("Is this configuration correct?")

    # Define klat.yaml config
    config = {"SIO_URL": api_url,
              "MQ": {"users": {"chat_observer": user_config},
                     "server": "neon-rabbitmq",
                     "port": 5672},
              "CHAT_CLIENT": {"SERVER_URL": api_url,
                              "FORCE_HTTPS": https,
                              "RUNTIME_CONFIG": {
                                  "CHAT_SERVER_URL_BASE": api_url}},
              "CHAT_SERVER": {"DEBUG": True,
                              "MINIFY": False,
                              "SERVER_IP": "klat-chat-server",
                              "COOKIES": {
                                  "LIFETIME": 3600,
                                  "REFRESH_RATE": 300,
                                  "SECRET": "775115fdecb9b4971193b919d27d410a",
                                  "JWT_ALGO": "HS256"},
                              "LIBRE_TRANSLATE_URL": libretranslate_url,
                              "SFTP": sftp_config
                              },
              "DATABASE_CONFIG": mongo_config}

    if orchestrator == Orchestrator.KUBERNETES:
        shutil.copytree(join(dirname(__file__), "templates", "klat"),
                        join(output_path, "klat-chat"))
        klat_config_file = join(output_path, "klat-chat", "klat.yaml")
        # Update Helm values with configured URL
        with open(join(output_path, "klat-chat", "values.yaml"), 'r') as f:
            helm_values = yaml.safe_load(f)
        admin_subdomain = "klatadmin"  # TODO: Allow user override
        helm_values['klat']['domain'] = domain
        helm_values['klat']['clientSubdomain'] = subdomain
        helm_values['klat']['serverSubdomain'] = api_subdomain
        helm_values['klat']['adminSubdomain'] = admin_subdomain
        helm_values['klat']['images']['tag'] = 'dev'  # TODO: Get user config
        helm_values['klat']['ingress']['rules'] = [
            {'host': subdomain, 'serviceName': 'klat-chat-client',
             'servicePort': 8001},
            {'host': api_subdomain, 'serviceName': 'klat-chat-server',
             'servicePort': 8010},
            {'host': admin_subdomain, 'serviceName': 'klat-chat-admin',
             'servicePort': 3000}
        ]
        if forward_www:
            helm_values['klat']['ingress']['rules'].append(
                {'host': 'www', 'serviceName': 'klat-chat-client',
                 'servicePort': 8001}
            )
        with open(join(output_path, "klat-chat", "values.yaml"), 'w') as f:
            yaml.safe_dump(helm_values, f)
    else:
        raise RuntimeError(f"{orchestrator} is not yet supported")

    # Write Klat configuration
    with open(klat_config_file, 'w+') as f:
        yaml.safe_dump(config, f)
    click.echo(f"Wrote Klat configuration to {klat_config_file}")
