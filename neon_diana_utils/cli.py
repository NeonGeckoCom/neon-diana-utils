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

import logging
import click
import yaml

from ovos_utils.log import LOG
from os import getenv, makedirs
from os.path import isdir, join, expanduser, isfile, dirname, abspath
from pprint import pformat
from click_default_group import DefaultGroup
from ovos_utils.xdg_utils import xdg_config_home
from neon_diana_utils.constants import valid_mq_services, default_mq_services, Orchestrator
from neon_diana_utils.version import __version__


@click.group("diana", cls=DefaultGroup,
             no_args_is_help=True, invoke_without_command=True,
             help="Diana: Device Independent API for Neon Applications.\n\n"
                  "See also: diana COMMAND --help")
@click.option("--version", "-v", is_flag=True, required=False,
              help='Print the current version')
def neon_diana_cli(version: bool = False):
    if version:
        click.echo(f"Diana version {__version__}")


# Backend
@neon_diana_cli.command(help="Configure a Diana Backend")
@click.option('--service', '-s', multiple=True,
              help="Optional service to configure")
@click.option('--default', '-d', is_flag=True, default=False,
              help="Configure the Default MQ Backend Services")
@click.option('--complete', '-c', '-a', is_flag=True, default=False,
              help="Configure All MQ Backend Services. (NOTE: This includes packages that require authentication)")
@click.option('--user', '-u', default="admin",
              help="Username to configure for administration")
@click.option('--password', '-p',
              help="Password associated with admin user to login to console")
@click.option('--volume-driver', default='none',
              help="Docker Volume Driver to use. 'none' and 'nfs' are currently supported")
@click.option('--volume-path', default=None,
              help="Optional fully-qualified path to config (i.e. /opt/diana, 192.168.1.10:/opt/diana")
@click.option('--skip-config', is_flag=True, default=False,
              help="Skip backend configuration and just generate orchestrator definitions")
@click.option('--namespace', '-n', default='default',
              help="Kubernetes namespace to configure services to run in")
@click.option('--mq-namespace', default=None,
              help="Kubernetes namespace to configure MQ services to run in")
@click.option('--http-namespace', default=None,
              help="Kubernetes namespace to configure HTTP services to run in")
@click.option('--http', is_flag=True, default=False,
              help="Configure HTTP backend services in addition to MQ")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def configure_backend(config_path, service, default, complete, user, password,
                      volume_driver, volume_path, skip_config, namespace, http,
                      mq_namespace, http_namespace):
    from neon_diana_utils.utils.backend import cli_configure_backend
    # Determine Services to Configure
    if complete:
        services_to_configure = valid_mq_services()
    elif default:
        services_to_configure = default_mq_services()
    else:
        services_to_configure = None
    if service:
        if services_to_configure:
            click.echo("Service set and individual services specified\n"
                       "Configuring specified services only.")
        services_to_configure = set(service)

    # Call setup
    import sys
    std_out = sys.stdout
    try:
        sys.stdout = open("/dev/null", 'a+')
        mq_namespace = mq_namespace or namespace
        http_namespace = http_namespace or namespace
        cli_configure_backend(config_path, services_to_configure, user,
                              password, http, volume_driver, volume_path,
                              skip_config, mq_namespace, http_namespace)
        sys.stdout = std_out
        if not skip_config:
            click.echo(f"Configured RabbitMQ Administrator: {user}")
            click.echo(f"Remember to place `ngi_auth_vars.yml` in {config_path}")
        click.echo(f"Configured API Services: {services_to_configure}")
        click.echo(f"Configuration was written to: {config_path}")
    except Exception as e:
        sys.stdout = std_out
        if not isinstance(e, ValueError):
            click.echo("An unexpected error occurred during configuration:")
        click.echo(e)
        click.echo("Call `diana configure-backend --help` for more info")


@neon_diana_cli.command(help="Start a Diana Backend")
@click.option('--attach', '-a', is_flag=True, default=False,
              help="Attach terminal to the started containers")
@click.option('--orchestrator', '-o', default="docker",
              help="Orchestrator (docker|kubernetes|openshift")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def start_backend(config_path, attach, orchestrator):
    from neon_diana_utils.utils.backend import cli_start_backend

    # Determine requested orchestrator
    if orchestrator == "docker":
        orchestrator = Orchestrator.DOCKER
    elif orchestrator == "kubernetes":
        orchestrator = Orchestrator.KUBERNETES
    elif orchestrator == "openshift":
        orchestrator = Orchestrator.OPENSHIFT
    else:
        click.echo(f"Invalid orchestrator specified: {orchestrator}")
        return

    # Start the backend
    click.echo(f"Starting backend")
    try:
        cli_start_backend(config_path, attach, orchestrator)
        if not attach:
            click.echo("Diana Backend Started")
    except Exception as e:
        if not isinstance(e, ValueError):
            click.echo("An unexpected error occurred during configuration:")
        click.echo(e)


@neon_diana_cli.command(help="Stop a Diana Backend")
@click.option('--orchestrator', '-o', default="docker",
              help="Orchestrator (docker|kubernetes|openshift")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def stop_backend(config_path, orchestrator):
    from neon_diana_utils.utils.backend import cli_stop_backend

    # Determine requested orchestrator
    if orchestrator == "docker":
        orchestrator = Orchestrator.DOCKER
    elif orchestrator == "kubernetes":
        orchestrator = Orchestrator.KUBERNETES
    elif orchestrator == "openshift":
        orchestrator = Orchestrator.OPENSHIFT
    else:
        click.echo(f"Invalid orchestrator specified: {orchestrator}")
        return

    try:
        cli_stop_backend(config_path, orchestrator)
        click.echo("Diana Backend Stopped")
    except Exception as e:
        if not isinstance(e, ValueError):
            click.echo("An unexpected error occurred during configuration:")
        click.echo(e)


# Kubernetes
@neon_diana_cli.command(help="Configure RabbitMQ and export user credentials")
@click.option("--username", "-u", help="RabbitMQ username")
@click.option("--password", "-p", help="RabbitMQ password")
@click.option("--url", help="RabbitMQ Management URL")
@click.argument("output_path", default=None, required=False)
def configure_mq_backend(username, password, url, output_path):
    output_path = expanduser(output_path or join(xdg_config_home(), "diana"))
    if isfile(output_path):
        click.echo(f"Expected dir and got file: {output_path}")
        return
    elif not isdir(output_path):
        makedirs(output_path)

    username = username or click.prompt("RabbitMQ Admin Username", type=str)
    password = password or click.prompt("RabbitMQ Admin Password", type=str,
                                        hide_input=True)
    url = url or click.prompt("RabbitMQ Management URL", type=str)
    click.confirm(f"Configure users on: {url}?", abort=True)
    LOG.level = logging.ERROR
    from neon_diana_utils.utils.backend import configure_mq_backend
    try:
        mq_config_path = join(output_path, "MQ")
        makedirs(mq_config_path, exist_ok=True)
        mq_auth_config = configure_mq_backend(username, password,
                                              config_path=mq_config_path,
                                              url=url)
        click.echo(pformat(mq_auth_config))

        if click.confirm("Configure GitHub token for private services?"):
            gh_username = click.prompt("GitHub username", type=str)
            gh_token = click.prompt("GitHub Token with `read_packages` "
                                    "permission", type=str)
            make_github_secret(gh_username, gh_token, output_path)

        keys_config = _make_keys_config(True)

        confirmed = False
        mq_url = None
        mq_port = None
        while not confirmed:
            mq_url = click.prompt("MQ Service Name or URL", type=str,
                                  default="neon-rabbitmq")
            mq_port = click.prompt("MQ Client Port", type=int, default=5672)
            click.echo(f"{mq_url}:{mq_port}")
            confirmed = click.confirm("Is this MQ Address Correct?")
        config = {**{"MQ": {"users": mq_auth_config,
                            "server": mq_url,
                            "port": mq_port}},
                  **keys_config}
        output_file = join(output_path, "diana.yaml")
        click.echo(f"Writing configuration to {output_file}")
        with open(output_file, 'w+') as f:
            yaml.dump(config, f)
    except Exception as e:
        click.echo(e)


@neon_diana_cli.command(help="Generate a configuration file with access keys")
@click.option("--skip-write", "-s", help="Skip writing config to file",
              is_flag=True)
@click.argument("output_file", default=None, required=False)
def make_keys_config(skip_write, output_file):
    _make_keys_config(skip_write, output_file)


@neon_diana_cli.command(help="Generate Kubernetes secret for Github images")
@click.option("--username", "-u",
              help="Github username")
@click.option("--token", "-t",
              help="Github PAT with read_packages permission")
@click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def make_github_secret(username, token, output_path):
    from neon_diana_utils.utils.kubernetes_utils import cli_make_github_secret
    try:
        output_path = cli_make_github_secret(username, token, output_path)
        click.echo(f"Generated outputs in {output_path}")
    except Exception as e:
        click.echo(e)


def _make_keys_config(skip_write, output_file=None):
    if not skip_write:
        output_file = expanduser(abspath((output_file or join(xdg_config_home(),
                                                              "diana",
                                                              "diana.yaml"))))
        if isfile(output_file):
            click.echo(f"File already exists: {output_file}")
            return
        elif not isdir(dirname(output_file)):
            makedirs(dirname(output_file))

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

    config = {"keys": {"api_services": api_services,
                       "emails": email_config,
                       "track_my_brands": brands_config}
              }
    if not skip_write:
        click.echo(f"Writing configuration to {output_file}")
        with open(output_file, 'w+') as f:
            yaml.dump(config, f)
    return config
