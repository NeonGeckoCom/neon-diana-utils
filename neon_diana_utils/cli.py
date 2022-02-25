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

from os import getenv
from click_default_group import DefaultGroup

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


# @neon_diana_cli.command(help="Generate a volume config for NFS-based shares")
# @click.option("--hostname",
#               help="Hostname or IP address of NFS Server")
# @click.option("--config_path", "-c",
#               help="Host path to configuration share")
# @click.option("--metric_path", "-m",
#               help="Host path to metrics share")
# @click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
# def make_nfs_config(hostname, config_path, metric_path, output_path):
#     try:
#         output_path = expanduser(output_path)
#         if isdir(output_path):
#             output_file = join(output_path, "k8s_nfs_volumes.yml")
#         elif isfile(output_path):
#             output_file = output_path
#         else:
#             raise ValueError(f"Invalid output_path: {output_path}")
#         generate_nfs_volume_config(hostname, config_path, metric_path, output_file)
#         click.echo(f"Generated {output_file}")
#     except Exception as e:
#         click.echo(e)

# Kubernetes
@neon_diana_cli.command(help="Generate a Kubernetes ConfigMap for RabbitMQ")
@click.option("--path", "-p",
              help="Path to config files to populate")
@click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def make_config_map(path, output_path):
    from neon_diana_utils.utils.kubernetes_utils import cli_make_rmq_config_map
    try:
        output_file = cli_make_rmq_config_map(path, output_path)
        click.echo(f"Generated {output_file}")
    except Exception as e:
        click.echo(e)


@neon_diana_cli.command(help="Generate Kubernetes Secrets for ngi_auth_vars.yml")
@click.option("--path", "-p",
              help="Path to config files to populate")
@click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def make_api_secrets(path, output_path):
    from neon_diana_utils.utils.kubernetes_utils import cli_make_api_secret
    try:
        output_path = cli_make_api_secret(path, output_path)
        click.echo(f"Generated outputs in {output_path}")
    except Exception as e:
        click.echo(e)
