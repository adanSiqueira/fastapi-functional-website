#  FastAPI Deployment on AWS EC2

This document describes the full process of deploying a FastAPI application on an AWS EC2 instance using **Linux (Ubuntu)**, **Nginx**, and **systemd**.

> Note: This setup uses a **public IPv4 address only** (no custom domain yet), so DNS and HTTPS are explained conceptually but not fully applied.

---

# 1. Infrastructure Overview

### EC2 Instance Configuration

* **Instance name:** `your-instance-name`
* **Public IP:** `YOUR_EC2_PUBLIC_IP`
* **OS:** Ubuntu
* **Access:** SSH using key pair
* **User:** `ubuntu`

---

# 2. Secure Access (SSH)

## What is happening?

SSH (Secure Shell) allows encrypted remote access to your server.

AWS uses **key-based authentication**:

* You hold the **private key (.pem)**
* AWS stores the **public key**

---

## Step

```bash
chmod 400 your-key-pair.pem
ssh -i your-key-pair.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Why `chmod 400`?

SSH refuses keys that are too permissive (security requirement).

---

# 3. Initial Server Setup

## Update system

```bash
sudo apt update && sudo apt upgrade -y
```

Ensures latest security patches.

---

## Create non-root user

```bash
sudo adduser your_username
sudo usermod -aG sudo your_username
```

### Why?

* Avoid using `root`
* Reduce risk of full system compromise

---

## Timezone configuration

```bash
timedatectl status
sudo timedatectl set-timezone UTC
```

UTC is standard in servers/logging.

---

## Hostname (optional)

```bash
sudo hostnamectl set-hostname your-server-name
```

Helps identify the machine internally.

---

# 4. Firewall Configuration (UFW)

## Install and configure

```bash
sudo apt install ufw -y
```

### Default rules:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

Zero-trust model: block everything unless explicitly allowed.

---

## Allow required ports

```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Enable firewall

```bash
sudo ufw enable
sudo ufw status verbose
```

---

# 5. SSH Protection with Fail2Ban

## What it does

Fail2Ban monitors logs and bans IPs after repeated failed logins.

---

## Setup

```bash
sudo apt install fail2ban -y
```

Create local configs:

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

Edit:

```bash
sudo nano /etc/fail2ban/jail.local
```

Example:

```ini
[sshd]
enabled = true
port = ssh
maxretry = 3
findtime = 10m
bantime = 1h
banaction = ufw
```

---

## Start service

```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

# 6. Automatic Security Updates

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

Keeps system patched automatically.

---

# 7. Web Server Setup (Nginx)

## Install

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## Why Nginx?

Nginx acts as:

* Reverse proxy
* Static file server
* Load balancer (later)

---

# ⚠️ DNS & HTTPS (Important Context)

At this stage:

* No domain (like `example.com`)
* No DNS configured
* No HTTPS certificate

So:

* You access via IP: `http://YOUR_EC2_PUBLIC_IP`
* SSL (via Certbot) **cannot be used yet**

---

## Why Certbot doesn't work without domain?

Certbot requires domain validation.

Certificates are issued **for domains, not IPs**.

---

# 8. Application Environment

## Install dependencies

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

---

## Install PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib -y
```

Start:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

# 9. Database Setup

## Create DB and user

```sql
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
CREATE DATABASE your_db_name OWNER your_db_user;
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

---

## Connection string

```
postgresql+asyncpg://your_db_user:your_db_password@localhost/your_db_name
```

---

# 10. Application Deployment

## Create directory

```bash
sudo mkdir -p /var/www/your-app-name
sudo chown $USER:$USER /var/www/your-app-name
```

---

## Clone repository

```bash
cd /var/www/your-app-name
git clone https://github.com/your_github_username/your-repo-name.git .
```

---

## Permissions (security-first approach)

```bash
find . -type f -exec chmod 600 {} \;
find . -type d -exec chmod 700 {} \;
chmod 755 .
chmod -R 755 static
```

---

# 11. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

# 12. Environment Variables

Create `.env`:

```bash
nano .env
chmod 600 .env
```

Example `.env` structure (never commit this file):

```env
DATABASE_URL=postgresql+asyncpg://your_db_user:your_db_password@localhost/your_db_name
SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region
S3_ACCESS_KEY_ID=your_access_key_id        # optional if using IAM role
S3_SECRET_ACCESS_KEY=your_secret_key       # optional if using IAM role
```

Stores secrets (DB credentials, keys, etc.). Always add `.env` to `.gitignore`.

---

# 13. Database Migrations

```bash
alembic upgrade head
```

Applies schema to database.

---

# 14. Test Application (temporary)

```bash
sudo ufw allow 9000/tcp
uvicorn main:app --host 0.0.0.0 --port 9000
```

Validate app works before production setup. Remove this UFW rule after testing:

```bash
sudo ufw delete allow 9000/tcp
```

---

# 15. Production Process Manager (systemd)

## Why?

systemd ensures:

* Auto start on boot
* Restart on crash
* Background execution

---

## Service file

```bash
sudo nano /etc/systemd/system/your-app-name.service
```

```ini
[Unit]
Description=FastAPI Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/your-app-name
Environment="PATH=/var/www/your-app-name/venv/bin"
EnvironmentFile=/var/www/your-app-name/.env
ExecStart=/var/www/your-app-name/venv/bin/uvicorn main:app \
    --workers 2 \
    --host 127.0.0.1 \
    --port 8000 \
    --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Enable service

```bash
sudo systemctl daemon-reload
sudo systemctl start your-app-name
sudo systemctl enable your-app-name
sudo systemctl status your-app-name
```

---

# 16. Reverse Proxy (Nginx → FastAPI)

## Why?

Nginx:

* Handles public traffic
* Forwards to app (127.0.0.1:8000)
* Serves static files efficiently

---

## Config

```bash
sudo nano /etc/nginx/sites-available/your-app-name
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name YOUR_EC2_PUBLIC_IP YOUR_EC2_PUBLIC_DNS;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location /static/ {
        alias /var/www/your-app-name/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    client_max_body_size 5M;
}
```

---

## Enable

```bash
sudo ln -s /etc/nginx/sites-available/your-app-name /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Your app will be live at `http://YOUR_EC2_PUBLIC_IP`.

---

# Final Architecture

```
Internet
   ↓
Nginx (port 80)
   ↓
FastAPI (127.0.0.1:8000)
   ↓
PostgreSQL
```

---

# Future Improvements

## 1. Domain + DNS

Use Amazon Route 53 or any DNS provider to point a domain to your EC2 IP.

---

## 2. HTTPS (SSL)

After obtaining a domain:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## 3. Gunicorn (recommended upgrade)

Instead of Uvicorn directly:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w $(nproc) main:app
```

---

# Key Takeaways

* Non-root user is used by default
* Firewall (UFW) + Fail2Ban for security hardening
* systemd for process management and auto-restart
* Nginx as reverse proxy — app is never exposed directly
* `.env` for secrets — never committed to version control
* IAM Roles preferred over hardcoded AWS credentials