# Neon Diana
Device Independent API for Neon Applications (Diana) is a collection of microservices that provide various functionality 
to NeonAI systems. All services are implemented as standalone Docker containers that are connected to a RabbitMQ server.
This repository contains the files required to launch a Neon API server.

## Running Services
[Docker Compose](https://docs.docker.com/compose/) is used to facilitate starting up separate services that comprise Diana.
The example below assumes that configuration is populated in `~/docker_config` and that metrics should be saved to 
`~/docker_metrics`. These paths are arbitrary and can be changed to any location that is accessible by the user running 
docker. Details of what should be present in `NEON_CONFIG_PATH` can be found in the [Configuration](#configuration) 
section below.

```shell
export NEON_CONFIG_PATH="/home/${USER}/diana_config/"
export NEON_METRIC_PATH="/home/${USER}/diana_metrics/"
docker login ghcr.io
docker-compose up -d
```

If you prefer not to run all services, you may specify which services to run with `docker-compose up`.
```shell
docker-compose up -d neon_rabbitmq neon_api_proxy neon_metrics_service
```

## Initial Configuration
`neon_diana_utils` contains convenience utilities, including for automated initial configuration of RabbitMQ. If you 
have a clean RabbitMQ container, you can use `create_default_mq_server` to configure an admin account and all parameters
required for running Neon Diana. Make sure the `neon_rabbitmq` container is running before running this utility. After 
RabbitMQ Configuration is complete, you can start the remaining containers 

ex:
```shell
export NEON_CONFIG_PATH="/home/${USER}/diana_config/"
# Modify neon-diana-backend/setup_default_server.py with desired username and password
python neon-diana-backend/setup_default_server.py
```

## Configuration
All containers containing an MQ module will expect `mq_config.json` to be mounted to `NEON_CONFIG_PATH` 
(usually `/config` in the containers).

- `neon_api_proxy`, `neon_brands_service`, and `neon_email_proxy` will expect `/config/ngi_auth_vars.yml` to specify any
    account credentials
- `neon_metrics_service` will output metrics files to `/metrics`.
- `neon_rabbitmq` will expect `/config/rabbitmq.conf` to specify a path to the configuration `.json` file to load.

Example configuration file structure:
```
$NEON_CONFIG_DIR
├── mq_config.json
├── ngi_auth_vars.yml
├── rabbitmq.conf
└── rabbit_mq_config.json
```

`mq_config.json` (passwords redacted)
```json
{
  "server": "neon_rabbitmq",
  "users": {
    "test": {
      "user": "test_user",
      "password": ""
    },
    "neon_api_connector": {
      "user": "neon_api",
      "password": ""
    },
    "neon_coupon_connector": {
      "user": "neon_coupons",
      "password": ""
    },
    "neon_email_proxy": {
      "user": "neon_email",
      "password": ""
    },
    "neon_metrics_connector": {
      "user": "neon_metrics",
      "password": ""
    },
    "neon_script_parser_service": {
      "user": "neon_script_parser",
      "password": ""
    }
  }
}
```

`ngi_auth_vars.yml` (passwords redacted)
```yaml
track_my_brands:
  user: admintr1_drup1
  password: 
  host: trackmybrands.com
  database: admintr1_drup1
emails:
  mail: neon@neon.ai
  pass: 
  host: smtp.gmail.com
  port: '465'
api_services:
  wolfram_alpha:
    api_key: ""
  alpha_vantage:
    api_key: ""
  open_weather_map:
    api_key: ""
```

`rabbitmq.conf`
```
load_definitions = /config/rabbit_mq_config.json
```
