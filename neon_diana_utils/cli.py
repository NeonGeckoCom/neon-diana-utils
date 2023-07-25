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

from click_default_group import DefaultGroup
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


# Core
@neon_diana_cli.command(help="Configure Neon Core")
@click.option("--username", "-u", help="RabbitMQ username for Neon AI")
@click.option("--password", "-p", help="RabbitMQ password for Neon AI")
@click.option("--orchestrator", "-o", default="kubernetes",
              help="Container orchestrator (`kubernetes` or `docker-compose`")
@click.argument("output_path", default=None, required=False)
def configure_neon_core(username, password, orchestrator, output_path):
    from neon_diana_utils.configuration import configure_neon_core, Orchestrator
    try:
        orchestrator = Orchestrator(orchestrator)
    except ValueError:
        click.echo(f"{orchestrator} is not a valid orchestrator")
        return
    configure_neon_core(username, password, output_path, orchestrator)


# Backend
@neon_diana_cli.command(help="Configure DIANA Backend")
@click.option("--username", "-u", help="RabbitMQ username")
@click.option("--password", "-p", help="RabbitMQ password")
@click.option("--orchestrator", "-o", default="kubernetes",
              help="Container orchestrator (`kubernetes` or `docker-compose`")
@click.argument("output_path", default=None, required=False)
def configure_backend(username, password, orchestrator, output_path):
    from neon_diana_utils.configuration import configure_backend, Orchestrator
    try:
        orchestrator = Orchestrator(orchestrator)
    except ValueError:
        click.echo(f"{orchestrator} is not a valid orchestrator")
        return
    configure_backend(username, password, output_path, orchestrator)


@neon_diana_cli.command(help="Configure backend services for deployment")
@click.option("--username", "-u", help="RabbitMQ username")
@click.option("--password", "-p", help="RabbitMQ password")
@click.argument("output_path", default=None, required=False)
def configure_mq_backend(username, password, output_path):
    # TODO: Deprecate in favor of `configure_backend`
    from neon_diana_utils.configuration import configure_backend
    configure_backend(username, password, output_path)


@neon_diana_cli.command(help="Generate RabbitMQ definitions")
@click.option("--username", "-u", help="RabbitMQ username")
@click.option("--password", "-p", help="RabbitMQ password")
@click.argument("output_file", default=None, required=False)
def make_rmq_config(username, password, output_file):
    from neon_diana_utils.configuration import generate_rmq_config
    generate_rmq_config(username, password, output_file)


@neon_diana_cli.command(help="Generate a configuration file with access keys")
@click.option("--skip-write", "-s", help="Skip writing config to file",
              is_flag=True)
@click.argument("output_file", default=None, required=False)
def make_keys_config(skip_write, output_file):
    from neon_diana_utils.configuration import make_keys_config
    make_keys_config(not skip_write, output_file)
