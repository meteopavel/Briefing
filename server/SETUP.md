# Первый деплой Briefing на Home Router

## 1. На сервере — один раз

```bash
# Создать папку приложения
mkdir -p ~/apps/briefing

# Клонировать репо
cd ~/apps
git clone git@github.com:meteopavel/Briefing.git briefing

# Создать venv и поставить зависимости
cd briefing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Скопировать .env
cp env.example .env
# Заполнить REDMINE_URL, REDMINE_API_KEY, REDMINE_USER_ID

# Установить systemd-сервис
sudo cp server/briefing.service /etc/systemd/system/
# Отредактировать: заменить YOUR_USER на реальное имя пользователя
sudo nano /etc/systemd/system/briefing.service

sudo systemctl daemon-reload
sudo systemctl enable briefing
sudo systemctl start briefing
sudo systemctl status briefing

# Добавить sudo без пароля для restart (в sudoers)
# YOUR_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart briefing, /bin/systemctl status briefing *
```

## 2. Nginx

```bash
sudo cp server/briefing.nginx /etc/nginx/sites-available/briefing
sudo ln -s /etc/nginx/sites-available/briefing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 3. dnsmasq — резолвинг briefing.local

Добавить в `/etc/dnsmasq.conf` (или в отдельный файл):

```
address=/briefing.local/192.168.100.1
```

Затем:
```bash
sudo systemctl reload dnsmasq
```

После этого `briefing.local` будет открываться в браузере из локальной сети.

## 4. Локально — заполнить .env

```bash
cp env.example .env
# Заполнить DEPLOY_USER, DEPLOY_APP_DIR и остальные переменные
```

Затем обычный деплой:
```bash
bash deploy-local.sh "feat: первый деплой"
```
