from app import create_app

app = create_app()

print("\n=== TODAS AS ROTAS (filtradas por 'export') ===")
export_routes = []
for rule in app.url_map.iter_rules():
    if 'export' in str(rule).lower():
        export_routes.append(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
        
if export_routes:
    for route in sorted(export_routes):
        print(route)
else:
    print("❌ Nenhuma rota com 'export' encontrada!")

print(f"\n📊 Total de rotas no app: {len(list(app.url_map.iter_rules()))}")
