# Stop Docker Containers

Use these commands from the project root.

## Stop containers without removing them

```powershell
docker compose --env-file .env.docker stop
```

This stops the running containers but keeps them so they can be started again later.

## Stop and remove containers

```powershell
docker compose --env-file .env.docker down
```

Use this when you are finished working with the project.

## Start again

```powershell
docker compose --env-file .env.docker up -d
```

## Check container status

```powershell
docker compose --env-file .env.docker ps
```

## Recommended daily workflow

Start:

```powershell
docker compose --env-file .env.docker up -d
```

Stop when finished:

```powershell
docker compose --env-file .env.docker down
```
