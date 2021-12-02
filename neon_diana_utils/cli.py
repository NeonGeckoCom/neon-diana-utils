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
import click

from os import makedirs, getenv
from os.path import expanduser, isdir, isfile, join
from click_default_group import DefaultGroup

from .version import __version__

# TODO: Valid services can be read from service_mappings.yml directly
VALID_SERVICES = ("neon_rabbitmq",
                  "neon_api_proxy",
                  "neon_brands_service",
                  "neon_email_proxy",
                  "neon_script_parser",
                  "neon_metrics_service")

# TODO: Consider tagging these in service_mappings.yml or some other method for easier extensibility DM
DEFAULT_SERVICES = ("neon_rabbitmq",
                    "neon_api_proxy",
                    "neon_email_proxy",
                    "neon_metrics_service")


@click.group("diana", cls=DefaultGroup,
             no_args_is_help=True, invoke_without_command=True,
             help="Diana: Device Independent API for Neon Applications.\n\n"
                  "See also: diana COMMAND --help")
@click.option("--version", "-v", is_flag=True, required=False,
              help='Print the current version')
def neon_diana_cli(version: bool = False):
    if version:
        click.echo(f"Diana version {__version__}")


@neon_diana_cli.command(help="Configure a Diana Backend")
@click.option('--service', '-s', multiple=True,
              help="Optional service to configure")
@click.option('--default', '-d', is_flag=True, default=False,
              help="Configure the Default Backend Services")
@click.option('--complete', '-c', is_flag=True, default=False,
              help="Configure All Backend Services. (NOTE: This includes packages that require authentication)")
@click.option('--user', '-u', default="admin",
              help="Username to configure for administration")
@click.option('--password', '-p',
              help="Password associated with admin user to login to console")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def configure_backend(config_path, service, default, complete, user, password):
    # Determine Configuration Path
    config_path = expanduser(config_path)
    if not config_path:
        return ValueError("Null config_path")
    if not isdir(config_path):
        try:
            makedirs(config_path)
        except Exception:
            return ValueError(f"Unable to create config directory: {config_path}")

    # Determine admin credentials
    if not password:
        click.echo(f"No password specified, please specify a password for RabbitMQ admin access")
        return ValueError("Null password")

    click.echo(f"Configuring RabbitMQ Administrator: {user}")

    # Determine Services to Configure
    if complete:
        services_to_configure = VALID_SERVICES
    elif default:
        services_to_configure = DEFAULT_SERVICES
    else:
        services_to_configure = None
    if service:
        if services_to_configure:
            click.echo("Service set and individual services specified\n"
                       "Configuring specified services only.")
        services_to_configure = list(service)
        for service in services_to_configure:
            if service not in VALID_SERVICES:
                click.echo(f"Invalid service requested will be ignored: {service}")
                services_to_configure.remove(service)
        services_to_configure = set(services_to_configure)
    if not services_to_configure:
        click.echo("No services specified. Call `diana configure-backend --help` for more info")
        return ValueError("No services provided")
    click.echo(f"Configuring API Services: {services_to_configure}")
    click.echo(f"Configuration will be written to: {config_path}")

    # Call setup
    import sys
    std_out = sys.stdout
    sys.stdout = open("/dev/null", 'a+')
    from .utils import create_diana_configurations
    create_diana_configurations(user, password, services_to_configure, config_path)
    sys.stdout = std_out
    click.echo(f"Configuration Complete")
    click.echo(f"Remember to place `ngi_auth_vars.yml` in {config_path}")


@neon_diana_cli.command(help="Start a Diana Backend")
@click.option('--service', '-s', multiple=True,
              help="Optional service to start")
@click.option('--attach', '-a', is_flag=True, default=False,
              help="Attach terminal to the started containers")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def start_backend(config_path, service, attach):
    # Validate path to docker-compose.yml
    config_path = expanduser(config_path)
    if not config_path:
        return ValueError("Null config_path")
    if not isfile(join(config_path, "docker-compose.yml")):
        click.echo(f"docker-compose.yml not found in {config_path}")
        return ValueError(f"docker-compose.yml not found")

    docker_compose_command = "docker-compose up"
    if service:
        # TODO: Validate services are in docker compose file
        docker_compose_command = " ".join((docker_compose_command, " ".join(service)))
    if not attach:
        docker_compose_command += " --detach"
        subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()
        click.echo("Diana Backend Started")
    else:
        subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()


@neon_diana_cli.command(help="Stop a Diana Backend")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def stop_backend(config_path):
    # Validate path to docker-compose.yml
    config_path = expanduser(config_path)
    if not config_path:
        return ValueError("Null config_path")
    if not isfile(join(config_path, "docker-compose.yml")):
        click.echo(f"docker-compose.yml not found in {config_path}")
        return ValueError(f"docker-compose.yml not found")

    docker_compose_command = "docker-compose down"
    subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()
    click.echo("Diana Backend Stopped")
