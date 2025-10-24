try:
    from app import routes
    print("✅ routes.py importado com sucesso")
    print(f"Blueprint: {routes.bp}")
    print(f"Número de rotas no blueprint: {len([r for r in routes.bp.deferred_functions])}")
except Exception as e:
    print(f"❌ Erro ao importar routes.py: {e}")
    import traceback
    traceback.print_exc()
