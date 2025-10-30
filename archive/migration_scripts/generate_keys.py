import secrets

print("Copie estas chaves para o arquivo .env:")
print()
print(f"SECRET_KEY={secrets.token_hex(32)}")
print(f"JWT_SECRET_KEY={secrets.token_hex(32)}")
