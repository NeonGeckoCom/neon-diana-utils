# Deployment via Docker Compose
[Docker Compose](https://docs.docker.com/compose/) is a standard tool used for
deploying multiple containers.

### Diana Backend
To generate configuration files for deployment in ~/diana, run: 
```
diana configure-backend -o docker-compose /home/$USER/diana
```
Follow the interactive prompts to configure keys for services you want to run.
To run the output configured containers:
```
cd ~/diana
docker-compose up -d
```

> Note that default backend services will be included in the output 
> `docker-compose.yml`. You may wish to remove some services that you didn't
> configure or add others to run with the backend.