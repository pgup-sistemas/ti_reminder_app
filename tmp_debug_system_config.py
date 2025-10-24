import traceback

try:
    import app.blueprints.system_config  # noqa: F401
except Exception as exc:
    print("ERROR:", exc)
    traceback.print_exc()
else:
    print("Blueprint import OK")
