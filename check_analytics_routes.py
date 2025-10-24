from app import create_app

app = create_app()

print("\n=== ROTAS ANALYTICS EXPORT ===")
for rule in app.url_map.iter_rules():
    if 'export' in str(rule) and 'analytics' in str(rule):
        print(f"{rule.endpoint}: {rule}")

print("\n=== TODAS AS ROTAS ANALYTICS ===")
for rule in app.url_map.iter_rules():
    if 'analytics' in str(rule):
        print(f"{rule.endpoint}: {rule}")
