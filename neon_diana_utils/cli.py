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
from os.path import expanduser, isdir, isfile, join, basename, dirname
from click_default_group import DefaultGroup

from neon_diana_utils.orchestrators import Orchestrator
from neon_diana_utils.utils import generate_config
from neon_diana_utils.utils.kompose_utils import convert_docker_compose, \
    generate_config_map, generate_secret
from neon_diana_utils.version import __version__

# TODO: Valid services can be read from service_mappings.yml directly
VALID_SERVICES = ("neon-rabbitmq",
                  "neon-api-proxy",
                  "neon-brands-service",
                  "neon-email-proxy",
                  "neon-script-parser",
                  "neon-metrics-service")

# TODO: Consider tagging these in service_mappings.yml or some other method for easier extensibility DM
DEFAULT_SERVICES = ("neon-rabbitmq",
                    "neon-api-proxy",
                    "neon-email-proxy",
                    "neon-metrics-service")


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
@click.option('--volume-driver', default='none',
              help="Docker Volume Driver to use. 'none' and 'nfs' are currently supported")
@click.option('--volume-path', default=None,
              help="Optional fully-qualified path to config (i.e. /opt/diana, 192.168.1.10:/opt/diana")
@click.option('--skip-config', is_flag=True, default=False,
              help="Skip backend configuration and just generate orchestrator definitions")
@click.option('--namespace', '-n', default='default',
              help="Kubernetes namespace to configure services to run in")
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def configure_backend(config_path, service, default, complete, user, password,
                      volume_driver, volume_path, skip_config, namespace):
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
    if not skip_config and not password:
        click.echo(f"No password specified, please specify a password for RabbitMQ admin access")
        return ValueError("Null password")

    if not skip_config:
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
        services_to_configure = set(service)
        # for service in services_to_configure:
        #     if service not in VALID_SERVICES:
        #         click.echo(f"Invalid service requested will be ignored: {service}")
        #         services_to_configure.remove(service)
        # services_to_configure = set(services_to_configure)
    if not services_to_configure:
        click.echo("No services specified. Call `diana configure-backend --help` for more info")
        return ValueError("No services provided")
    click.echo(f"Configuring API Services: {services_to_configure}")
    click.echo(f"Configuration will be written to: {config_path}")

    # Parse Configuration paths
    volumes = None
    if volume_path:
        volumes = {"config": join(volume_path, "config"),
                   "metrics": join(volume_path, "metrics")}
        click.echo(f"Remote volumes specified, ensure NFS permissions are set.")
    elif not skip_config:
        click.echo(f"Remember to place `ngi_auth_vars.yml` in {config_path}")

    # Call setup
    import sys
    std_out = sys.stdout
    sys.stdout = open("/dev/null", 'a+')

    if not skip_config:
        from .utils import create_diana_configurations
        create_diana_configurations(user, password, services_to_configure,
                                    config_path, volume_driver=volume_driver,
                                    volumes=volumes, namespace=namespace)
    else:
        generate_config(services_to_configure, config_path, volume_driver,
                        volumes, namespace)
    sys.stdout = std_out
    click.echo(f"Configuration Complete")


@neon_diana_cli.command(help="Convert Diana resources for Container Orchestration")
@click.option("--kubernetes", "-k", is_flag=True, default=False)
@click.option("--openshift", "-o", is_flag=True, default=False)
@click.argument('config_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def convert(kubernetes, openshift, config_path):
    # Validate path to docker-compose.yml
    config_path = expanduser(config_path)
    if not config_path:
        return ValueError("Null config_path")
    compose_file = join(config_path, "docker-compose.yml")
    if not isfile(compose_file):
        click.echo(f"docker-compose.yml not found in {config_path}")
        return ValueError(f"docker-compose.yml not found")

    if not kubernetes or openshift:
        kubernetes = True

    if kubernetes:
        click.echo(f"Converting {compose_file} to Kubernetes definition")
        convert_docker_compose(compose_file, Orchestrator.KUBERNETES)
    if openshift:
        click.echo(f"Converting {compose_file} to OpenShift definition")
        convert_docker_compose(compose_file, Orchestrator.OPENSHIFT)


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


@neon_diana_cli.command(help="Generate a Kubernetes ConfigMap for RabbitMQ")
@click.option("--path", "-p",
              help="Path to config files to populate")
@click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def make_config_map(path, output_path):
    try:
        file_path = expanduser(path)
        if not isdir(file_path):
            raise FileNotFoundError(f"Could not find requested directory: {path}")
        output_path = expanduser(output_path)
        if isdir(output_path):
            output_file = join(output_path, f"k8s_config_rabbitmq.yml")
        elif isfile(output_path):
            output_file = output_path
        else:
            raise ValueError(f"Invalid output_path: {output_path}")

        with open(join(file_path, "rabbitmq.conf"), 'r') as f:
            rabbitmq_file_contents = f.read()
        with open(join(file_path, "rabbit_mq_config.json")) as f:
            rmq_config = f.read()
        generate_config_map("rabbitmq", {"rabbitmq.conf": rabbitmq_file_contents,
                                         "rabbit_mq_config.json": rmq_config}, output_file)
        click.echo(f"Generated {output_file}")
    except Exception as e:
        click.echo(e)


@neon_diana_cli.command(help="Generate Kubernetes Secrets for ngi_auth_vars.yml")
@click.option("--path", "-p",
              help="Path to config files to populate")
@click.argument('output_path', default=getenv("NEON_CONFIG_DIR", "~/.config/neon/"))
def make_api_secrets(path, output_path):
    try:
        file_path = expanduser(path)
        if not isdir(file_path):
            raise FileNotFoundError(f"Could not find requested directory: {path}")
        output_path = expanduser(output_path)
        if isfile(output_path):
            output_path = dirname(output_path)

        with open(join(file_path, "ngi_auth_vars.yml")) as f:
            ngi_auth = f.read()
        generate_secret("ngi-auth", {"ngi_auth_vars.yml": ngi_auth},
                        join(output_path, "k8s_secret_ngi-auth.yml"))
        # generate_secret("mq-auth", {"mq_config.json": mq_config_contents},
        #                 join(output_path, "k8s_secret_mq_config.yml"))
        click.echo(f"Generated outputs in {output_path}")
    except Exception as e:
        click.echo(e)


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
