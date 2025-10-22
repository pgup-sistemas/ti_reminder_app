from app import create_app

app = create_app()

with app.app_context():
    from app.services.notification_service import NotificationService
    print('Testing notification service...')
    try:
        result = NotificationService.run_notification_checks()
        print(f'Result: {result}')
        print('Test passed!')
    except Exception as e:
        print(f'Error: {e}')
        print('Test failed!')