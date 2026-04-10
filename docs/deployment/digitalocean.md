# DigitalOcean Deployment

This guide provides a ready setup for running Scrapling on DigitalOcean in two modes:

1. Full CI-style test run
2. Built-in web UI (`scrapling ui`)

## Files Added

- `deploy/digitalocean/run_scrapling.sh`: one script for both full tests and UI run.
- `deploy/digitalocean/app.yaml`: App Platform spec for running the built-in UI.

## Option A: DigitalOcean Droplet (Ubuntu)

### 1) Create a Droplet

- Ubuntu 24.04+
- At least 2 vCPU / 4GB RAM (recommended for browser tests)

### 2) SSH and install base tools

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv curl
```

### 3) Clone repository

```bash
sudo mkdir -p /opt && sudo chown "$USER":"$USER" /opt
git clone https://github.com/D4Vinci/Scrapling.git /opt/scrapling
cd /opt/scrapling
```

### 4) Run full test suite (CI-style split)

```bash
bash deploy/digitalocean/run_scrapling.sh full-test
```

What this does:

- Creates venv (`/opt/scrapling/.venv`) if missing
- Installs Scrapling with extras: `.[all]`
- Installs test requirements
- Installs Playwright browser binaries + system dependencies
- Runs the same 3-part test split used in `tox.ini`

### 5) Run built-in UI

```bash
PORT=7788 bash deploy/digitalocean/run_scrapling.sh ui
```

Then open:

- `http://<droplet-ip>:7788/`

If using UFW:

```bash
sudo ufw allow 7788/tcp
sudo ufw reload
```

## Option B: App Platform

Use `deploy/digitalocean/app.yaml` as a starting spec.

### 1) Install `doctl` and authenticate

```bash
doctl auth init
```

### 2) Create app from spec

```bash
doctl apps create --spec deploy/digitalocean/app.yaml
```

### 3) Open assigned URL

App Platform provides a public URL after deployment.

## Notes

- Browser tests require extra system packages and virtual display support. The script handles this via Playwright installers.
- If your server has custom apt repositories that break `apt update`, fix them first before running the script.
- For production UI serving, put a reverse proxy (Nginx/Caddy) in front and enforce HTTPS.
