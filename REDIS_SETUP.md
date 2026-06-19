# Redis Setup

Redis is optional for the confidence-scoring checkpoint cache. If `REDIS_URL` is not set, Loom falls back to an in-memory dictionary and logs a warning. Use Redis when you want checkpoints to survive process-local memory loss during a pipeline run.

## Environment Variable

```bash
export REDIS_URL=redis://localhost:6379/0
```

## Docker

```bash
docker run --name loom-redis -p 6379:6379 -d redis:7
redis-cli ping
```

## macOS With Homebrew

```bash
brew install redis
brew services start redis
redis-cli ping
```

## Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable --now redis-server
redis-cli ping
```

`redis-cli ping` should return `PONG`.
