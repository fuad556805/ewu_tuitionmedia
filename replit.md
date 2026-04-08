# TuitionMedia

A Bangladesh-based web platform for tuition matching between students and tutors. Students can post tuition requirements, tutors can apply, and admins manage approvals. Includes an AI assistant ("Guru") powered by Anthropic's Claude.

## Tech Stack

- **Backend:** Django 6.0.4 (Python 3.12)
- **Database:** PostgreSQL (Replit built-in)
- **Frontend:** Django Templates (server-side rendering), HTML/CSS/JavaScript
- **AI:** Anthropic Claude API (Guru assistant)
- **Static files:** WhiteNoise
- **Production server:** Gunicorn

## Project Structure

- `accounts/` - User auth, custom user profiles (Student, Tutor, Admin)
- `posts/` - Tuition post management
- `tuitions/` - Tuition request lifecycle & commission tracking
- `chat/` - Messaging system between students and tutors
- `guru/` - AI assistant using Anthropic Claude
- `admin_panel/` - Custom admin interface
- `templates/` - Global Django templates
- `static/` - Global CSS/JS assets
- `tuitionmedia/` - Core Django project settings and URLs

## Running the App

The app runs on port 5000 via the "Start application" workflow:
```
python manage.py runserver 0.0.0.0:5000
```

## Database

Uses Replit's built-in PostgreSQL database via the `DATABASE_URL` environment variable. Migrations are applied automatically on deploy.

## Environment Variables

- `SECRET_KEY` - Django secret key
- `DEBUG` - Set to "True" for development
- `ANTHROPIC_API_KEY` - API key for the Guru AI assistant
- `DATABASE_URL` - Replit PostgreSQL connection string (auto-set)

## Default Admin Account

A permanent admin account is guaranteed by data migration `accounts/0004_create_default_admin.py`.
Every time `migrate` runs (on any deploy), this account is created or restored:

- **Phone:** 01609227183
- **Password:** fuad1234@
- **Username:** fuad_admin
- **Role:** admin / superuser

## Deployment

### Replit
Configured for autoscale deployment using Gunicorn on port 5000.
Build step runs `collectstatic` and `migrate` automatically.

### Render
Use `build.sh` as the build command and the following start command:
```
gunicorn tuitionmedia.wsgi:application --bind 0.0.0.0:8000
```
A `render.yaml` is included for reference. Set `DATABASE_URL` in Render's environment
variables to use a persistent PostgreSQL database (recommended). Without `DATABASE_URL`,
the app falls back to SQLite which is wiped on each deploy.
