from app import create_app

app = create_app()

print("\n=== ROTAS ANALYTICS ===")
for rule in app.url_map.iter_rules():
    if 'analytics' in str(rule):
        print(f"{rule.endpoint}: {rule}")
