# TI OSN System - Replit Environment Setup

## Project Overview
This is the TI OSN System, a comprehensive IT management web application built with Flask. The system provides management for reminders, tasks, support tickets, tutorials, and equipment with features like Progressive Web App (PWA) support, offline functionality, and a professional dashboard.

## Current Status
✅ **Setup Complete** - The application is successfully running in the Replit environment.

## Recent Changes (September 05, 2025)
- Configured Python 3.11 environment
- Installed all required Flask dependencies
- Configured PostgreSQL database connection (using Replit's built-in PostgreSQL)
- Set up Flask application to run on 0.0.0.0:5000 for Replit proxy compatibility
- Configured workflow to run the Flask server
- Set up deployment configuration for autoscale deployment with Gunicorn
- **IMPLEMENTED SLA SYSTEM**: Complete Service Level Agreement functionality for support tickets
  - Automatic SLA calculation based on priority levels (Crítica: 2h, Alta: 4h, Média: 24h, Baixa: 72h)
  - Visual indicators in dashboard and ticket listings
  - Comprehensive SLA reports and performance metrics
  - Automatic alerts for overdue and critical SLA tickets

## Project Architecture
- **Backend**: Flask 3.1.2 with SQLAlchemy, APScheduler, Flask-Mail
- **Database**: PostgreSQL (heliumdb) with Alembic migrations
- **Frontend**: Bootstrap 5 + JavaScript (PWA-enabled)
- **Features**: Authentication, Dashboard, Reminders, Tasks, Support Tickets, Tutorials, Equipment Management
- **Deployment**: Gunicorn WSGI server for production

## Environment Configuration
- **Host**: 0.0.0.0 (required for Replit proxy)
- **Port**: 5000 (required by Replit)
- **Database**: PostgreSQL (configured via DATABASE_URL environment variable)
- **Debug Mode**: Enabled in development
- **PWA**: Service Worker and manifest.json configured

## Key Files
- `run.py`: Main application entry point
- `app/__init__.py`: Flask app factory
- `config.py`: Application configuration
- `wsgi.py`: WSGI entry point for production
- `requirements.txt`: Python dependencies
- Database initialization handled by `init_db.py`

## Database Status
- PostgreSQL connection configured and working
- Database initialized with existing flag system
- Migrations managed through Flask-Migrate/Alembic

## Workflow Configuration
- **Flask Server**: Runs `python run.py` on port 5000
- **Output Type**: webview (for website preview)
- **Auto-restart**: Enabled

## Deployment Configuration
- **Target**: autoscale (stateless web application)
- **Production Server**: Gunicorn with reuse-port for performance
- **Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port wsgi:app`

## User Preferences
- Standard Flask development practices
- Bootstrap UI framework
- PostgreSQL database preference
- PWA functionality enabled