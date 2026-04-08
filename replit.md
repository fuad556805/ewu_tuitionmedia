# TuitionMedia

A Bangladesh-based web platform for tuition matching between students and tutors. Students post tuition requirements, tutors apply, admins manage approvals. Includes an AI assistant ("Guru") powered by Google Gemini.

## Tech Stack

- **Backend:** Django 6.0.4 (Python 3.12)
- **API:** Django REST Framework + JWT (djangorestframework-simplejwt)
- **Database:** PostgreSQL (Replit built-in)
- **Frontend:** Django Templates (server-side rendering), HTML/CSS/JavaScript
- **AI:** Google Gemini API (Guru assistant)
- **Static files:** WhiteNoise
- **Production server:** Gunicorn

## Project Structure

- `accounts/` - User auth, OTP, profiles, notifications; REST API in `api_views.py` / `api_urls.py`
- `posts/` - Tuition post management (templates + REST API in `api_views.py`)
- `tuitions/` - Tuition request lifecycle & commission tracking
- `chat/` - Messaging system (templates + REST API in `api_views.py`)
- `payments/` - bKash & Nagad payment integration
- `guru/` - AI assistant using Google Gemini
- `admin_panel/` - Custom admin interface (template-based)
- `templates/` - Global Django templates
- `static/` - Global CSS/JS assets
- `tuitionmedia/` - Core Django project settings and URLs

## REST API Endpoints

### Auth (`/api/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/send-otp/` | Send OTP for signup |
| POST | `/api/auth/verify-otp/` | Verify OTP + create account → returns JWT |
| POST | `/api/auth/resend-otp/` | Resend OTP |
| GET  | `/api/auth/otp-status/` | Check OTP status |
| POST | `/api/auth/login/` | Login with phone + password → returns JWT |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/forgot-password/send/` | Send reset OTP |
| POST | `/api/auth/forgot-password/reset/` | Verify OTP + reset password → returns JWT |
| GET  | `/api/auth/me/` | Get current user profile |
| PUT/PATCH | `/api/auth/profile/` | Update profile |
| GET  | `/api/auth/notifications/` | List notifications |
| POST | `/api/auth/notifications/<pk>/read/` | Mark notification read |

### Home (`/api/home/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/home/stats/` | Platform stats (tutors, students, posts, featured) |

### Tuition Posts (`/api/tuition/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/tuition/list/` | List active posts (public; supports ?subject= ?location=) |
| POST | `/api/tuition/create/` | Create post (students only) |
| GET  | `/api/tuition/my/` | My posts (student) |
| GET  | `/api/tuition/<pk>/` | Single post detail |
| PUT/PATCH | `/api/tuition/update/<pk>/` | Update post (resets to pending) |
| DELETE | `/api/tuition/<pk>/delete/` | Delete own post |

### Chat (`/api/chat/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/send/` | Send message |
| GET  | `/api/chat/messages/?with=<id>&after=<id>` | Get messages |
| GET  | `/api/chat/inbox/` | Inbox contact list |
| GET  | `/api/chat/requests/` | Pending chat requests |
| POST | `/api/chat/requests/` | Send chat request |
| POST | `/api/chat/requests/<pk>/respond/` | Accept/reject chat request |

### Payment (`/api/payment/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payment/create/` | Create bKash or Nagad payment |
| POST | `/api/payment/verify/` | Verify payment status |
| GET  | `/api/payment/history/` | My payment history |
| GET  | `/api/payment/contacts/` | Unlocked tutor contacts (student) |
| GET  | `/api/payment/commissions/` | Commission records (tutor) |

### Admin (`/api/admin/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/broadcast/` | Send notification to all users (admin only) |

## JWT Authentication

All protected endpoints require: `Authorization: Bearer <access_token>`

- Access token expires in **1 day**
- Refresh token expires in **30 days**
- Use `POST /api/auth/token/refresh/` with `{ "refresh": "<token>" }` to get a new access token

## Running the App

```
python manage.py runserver 0.0.0.0:5000
```

## Database

Uses Replit's built-in PostgreSQL via `DATABASE_URL` environment variable. Migrations auto-applied on deploy.

## Environment Variables

See `.env.example` for all required variables. Key ones:
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection (auto-set by Replit)
- `GEMINI_API_KEY` — Google Gemini AI key (for Guru)
- `SMS_BACKEND` — `console` (dev) | `twilio` | `bulksmsbd` | `sslwireless`

## Default Admin Account

Guaranteed by data migration `accounts/migrations/0004_create_default_admin.py`.
Created/restored on every `migrate` run:

- **Phone:** 01609227183
- **Password:** fuad1234@
- **Username:** fuad_admin

## Deployment

### Replit
Autoscale deployment with Gunicorn. Build step: `collectstatic` + `migrate`.

### Render
Build command: `bash build.sh`
Start command: `gunicorn tuitionmedia.wsgi:application --bind 0.0.0.0:8000`
Set `DATABASE_URL` env var to a Render PostgreSQL database for persistent data.
