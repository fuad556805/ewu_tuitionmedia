# 📚 EWU TuitionMedia

> A Bangladesh-based tuition matching platform connecting students with tutors — built with Django, REST API, and an AI assistant powered by Google Gemini.

[![Django](https://img.shields.io/badge/Django-6.0.4-green?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.17.1-red)](https://www.django-rest-framework.org)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue?logo=postgresql)](https://postgresql.org)

---

## ✨ Features

- **Student–Tutor Matching** — Students post tuition requirements; tutors apply; admins approve
- **OTP-Based Authentication** — Phone number signup with OTP verification via SMS
- **JWT Auth** — Secure REST API with access/refresh token flow
- **Real-time Chat** — Inbox messaging with chat request system
- **Payment Integration** — bKash and Nagad mobile payment gateways
- **AI Guru Assistant** — In-app AI chatbot powered by Google Gemini
- **Admin Panel** — Custom admin dashboard for managing users, posts, and approvals
- **Push Notifications** — Web push notification support via pywebpush
- **PWA Ready** — Service worker included (`sw.js`)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.4 (Python 3.12) |
| REST API | Django REST Framework + SimpleJWT |
| Database | PostgreSQL |
| Frontend | Django Templates (SSR) + Vanilla JS |
| AI | Google Gemini API |
| Static Files | WhiteNoise |
| Production Server | Gunicorn |
| SMS | Twilio / BulkSMSBD / SSLWireless |
| Payments | bKash, Nagad |

---

## 📁 Project Structure

```
ewutuitionmedia/
├── accounts/           # User auth, OTP, profiles, notifications, REST API
├── posts/              # Tuition post management (templates + REST API)
├── tuitions/           # Tuition request lifecycle & commission tracking
├── chat/               # Messaging system (templates + REST API)
├── payments/           # bKash & Nagad payment integration
├── guru/               # AI assistant (Google Gemini)
├── admin_panel/        # Custom admin interface
├── templates/          # Global Django HTML templates
├── static/             # Global CSS/JS assets
├── tuitionmedia/       # Django project settings & root URLs
├── requirements.txt
├── manage.py
├── build.sh
├── Procfile
└── render.yaml
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ewutuitionmedia.git
cd ewutuitionmedia
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/tuitionmedia

# AI
GEMINI_API_KEY=your-google-gemini-api-key

# SMS backend: console | twilio | bulksmsbd | sslwireless
SMS_BACKEND=console

# Twilio (if SMS_BACKEND=twilio)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Payments
BKASH_APP_KEY=
BKASH_APP_SECRET=
BKASH_USERNAME=
BKASH_PASSWORD=
NAGAD_MERCHANT_ID=
NAGAD_MERCHANT_PRIVATE_KEY=

# Web Push
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=admin@example.com
```

### 5. Apply migrations & collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Run the development server

```bash
python manage.py runserver 0.0.0.0:5000
```

Visit `http://localhost:5000`

---

## 🔐 Default Admin Account

Created automatically on every `migrate` run via data migration:

| Field | Value |
|---|---|
| Phone | `01609227183` |
| Password | `fuad1234@` |
| Username | `fuad_admin` |

> ⚠️ Change this immediately in any production deployment.

---

## 🌐 REST API Reference

All protected endpoints require the header:
```
Authorization: Bearer <access_token>
```

### Auth — `/api/auth/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/send-otp/` | Send OTP for signup |
| POST | `/verify-otp/` | Verify OTP + create account → returns JWT |
| POST | `/resend-otp/` | Resend OTP |
| GET | `/otp-status/` | Check OTP status |
| POST | `/login/` | Login with phone + password → returns JWT |
| POST | `/token/refresh/` | Refresh access token |
| POST | `/forgot-password/send/` | Send reset OTP |
| POST | `/forgot-password/reset/` | Reset password → returns JWT |
| GET | `/me/` | Get current user profile |
| PUT/PATCH | `/profile/` | Update profile |
| GET | `/notifications/` | List notifications |
| POST | `/notifications/<pk>/read/` | Mark notification read |

### Home — `/api/home/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/stats/` | Platform stats (tutors, students, posts, featured) |

### Tuition Posts — `/api/tuition/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/list/` | List active posts (public; `?subject=` `?location=`) |
| POST | `/create/` | Create post (students only) |
| GET | `/my/` | My posts (student) |
| GET | `/<pk>/` | Single post detail |
| PUT/PATCH | `/update/<pk>/` | Update post (resets to pending) |
| DELETE | `/<pk>/delete/` | Delete own post |

### Chat — `/api/chat/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/send/` | Send message |
| GET | `/messages/?with=<id>&after=<id>` | Get messages |
| GET | `/inbox/` | Inbox contact list |
| GET | `/requests/` | Pending chat requests |
| POST | `/requests/` | Send chat request |
| POST | `/requests/<pk>/respond/` | Accept/reject request |

### Payment — `/api/payment/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/create/` | Create bKash or Nagad payment |
| POST | `/verify/` | Verify payment status |
| GET | `/history/` | My payment history |
| GET | `/contacts/` | Unlocked tutor contacts (student) |
| GET | `/commissions/` | Commission records (tutor) |

### Admin — `/api/admin/`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/broadcast/` | Send notification to all users (admin only) |

### JWT Token Lifetimes

| Token | Lifetime |
|---|---|
| Access | 1 day |
| Refresh | 30 days |

---

## ☁️ Deployment

### Render

1. Create a PostgreSQL database on Render and set `DATABASE_URL`
2. Set all environment variables in the Render dashboard
3. Configure the service:

```
Build command:  bash build.sh
Start command:  gunicorn tuitionmedia.wsgi:application --bind 0.0.0.0:8000
```

### Replit

Autoscale deployment is pre-configured. The `build.sh` script runs `collectstatic` and `migrate` automatically.

---

## 🧪 Seed Demo Data

```bash
python manage.py seed_demo
```

---

## 📄 License

This project is for academic/educational purposes at East West University (EWU), Bangladesh.
