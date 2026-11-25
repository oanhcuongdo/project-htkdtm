# Training Analytics & Recommendation System

## Công nghệ thực tế

- Windows 10/11 64-bit
- Python 3.12.3
- Django 5.2.8
- Wagtail CMS 6.4.2
- Django Templates, HTML5, CSS3, JavaScript
- Bootstrap 5.3.3
- Chart.js 4.4.7
- Font Awesome 6.7.2
- PostgreSQL đề xuất 16.x
- SQLite 3 cho môi trường phát triển mặc định
- psycopg 3.2.12

## Cài đặt

```powershell
cd nhom05-65httt\src\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u, _ = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'}); u.is_staff=True; u.is_superuser=True; u.set_password('admin123'); u.save()"
python manage.py runserver
```

Đăng nhập nhanh:

- Tên đăng nhập: `admin`
- Mật khẩu: `admin123`

Truy cập:

- Giao diện quản trị: http://127.0.0.1:8000/
- Đăng nhập: http://127.0.0.1:8000/login/
- Wagtail Admin: http://127.0.0.1:8000/admin/
- Django Admin: http://127.0.0.1:8000/django-admin/

## Cấu hình PostgreSQL

Đề xuất PostgreSQL 16.x trên Windows 10/11. Tạo database và cấu hình trong `.env`:

```text
DB_ENGINE=postgresql
DB_NAME=training_analytics
DB_USER=postgres
DB_PASSWORD=<mat_khau_cua_ban>
DB_HOST=127.0.0.1
DB_PORT=5432
```

Sau đó chạy `python manage.py migrate`. Không commit `.env` hoặc thông tin mật khẩu.
