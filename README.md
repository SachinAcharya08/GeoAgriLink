# Template API

Production-ready Django REST API with JWT authentication, MySQL, and modern tooling.

## Features

- **Django 5.2** + **DRF** + **SimpleJWT**
- **Python 3.12+**
- **MySQL** with PyMySQL (no mysqlclient compilation)
- **WhiteNoise** for static files
- **Django Jazzmin** enhanced admin UI
- **HTML Email Templates** - responsive, professional
- **Service Layer Pattern** - clean business logic
- **Base Abstract Model** - timestamps, soft delete
- **Pytest** with coverage
- **In-memory caching** (no Redis required)

## Quick Start

### 1. Setup Environment

```bash
cd django-backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Database

Create MySQL database:
```bash
mysql -u root -p
CREATE DATABASE template_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

Copy and edit environment:
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 4. Start Server

```bash
python manage.py runserver
```

- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/schema/swagger-ui/

## Project Structure

```
django-backend/
├── config/              # Django settings
├── apps/
│   ├── core/           # Base model, permissions, email service, utils
│   └── users/          # Custom user model, auth endpoints
├── templates/emails/   # HTML email templates
├── tests/              # Pytest test suite
├── static/             # Static files
├── media/              # User uploads
└── logs/               # Application logs
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/users/register/` | POST | No | Register new user |
| `/api/v1/users/login/` | POST | No | Login with JWT |
| `/api/v1/users/profile/` | GET/PATCH | Yes | Get/Update profile |
| `/api/v1/users/change-password/` | PUT | Yes | Change password |

### Example: Register

```bash
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123",
    "password_confirm": "SecurePassword123"
  }'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'
```

## Key Components

### Email Service (`apps/core/services.py`)

```python
from apps.core.services import EmailService

# Send welcome email
EmailService.send_welcome_email(user)

# Custom email with template
EmailService.send_email(
    subject="Notification",
    to_email="user@example.com",
    template_name="custom_template",
    context={"name": "John"}
)
```

### Utilities (`apps/core/utils/`)

- `generate_token()` - Secure random tokens
- `validate_email_format()` - Email validation
- `get_client_ip()` - Extract client IP
- `StandardResultsSetPagination` - DRF pagination

### Base Model (`apps/core/base_model.py`)

All models inherit from `BaseModel`:
- `created_at` - Auto timestamp
- `updated_at` - Auto update timestamp
- `is_active` - Soft delete flag

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific test file
pytest tests/test_users_api.py
```

## Environment Variables

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=template_db
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=no-reply@template.com
FRONTEND_URL=http://localhost:3000
```

## Production Deployment

### cPanel Deployment

1. **Upload Files**
   - Upload project to `public_html` or subdirectory
   - Set correct permissions: `755` for directories, `644` for files

2. **Create Python Application**
   - Go to cPanel > Setup Python App
   - Python version: 3.12
   - Application root: `django-backend`
   - Application URL: `/` or subdirectory
   - Enter project directory: `public_html/django-backend`
   - Entry point: `config.wsgi`

3. **Install Dependencies**
   - Click "Run Pip Install" in cPanel Python App
   - Or manually: `pip install -r requirements.txt`

4. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Set `DEBUG=False`
   - Update `ALLOWED_HOSTS` with your domain
   - Configure MySQL database (create via cPanel MySQL Wizard)
   - Update SMTP email settings

5. **Run Commands**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

6. **Restart Application**
   - Restart Python App in cPanel

### VPS Deployment (Ubuntu/Debian)

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3-pip mysql-server nginx
   ```

2. **Setup Project**
   ```bash
   cd /var/www
   git clone <your-repo> template
   cd template
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Database**
   ```bash
   sudo mysql
   CREATE DATABASE template_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'template'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT ALL PRIVILEGES ON template_db.* TO 'template'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env
   # Set DEBUG=False, SECRET_KEY, DB credentials, etc.
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

6. **Setup Gunicorn Service**
   ```bash
   sudo nano /etc/systemd/system/template.service
   ```
   ```
   [Unit]
   Description=Template Gunicorn
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/template
   ExecStart=/var/www/template/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl start template
   sudo systemctl enable template
   ```

7. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/template
   ```
   ```
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /var/www/template/staticfiles/;
       }

       location /media/ {
           alias /var/www/template/media/;
       }
   }
   ```
   ```bash
   sudo ln -s /etc/nginx/sites-available/template /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

8. **Setup SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

**Pre-deployment checklist:**
- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY`
- [ ] Database backups configured
- [ ] SMTP email configured
- [ ] HTTPS/SSL enabled
- [ ] Run `python manage.py check --deploy`
- [ ] Firewall configured (VPS)
- [ ] Log rotation setup

## Requirements

- Python 3.12+
- MySQL 8.0+ (or MariaDB 10.5+)

See `requirements.txt` for full dependency list.
