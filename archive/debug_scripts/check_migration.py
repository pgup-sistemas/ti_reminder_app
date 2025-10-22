from app import create_app

app = create_app()

with app.app_context():
    print('Checking database migration status...')
    from flask_migrate import upgrade
    try:
        upgrade()
        print('Migrations applied successfully')
    except Exception as e:
        print(f'Migration error: {e}')