"""Teste rápido para verificar se a rota de exportação funciona"""
import requests

# Testar a rota
url = "http://192.168.1.86:5000/api/analytics/export/pdf?start=2025-09-23&end=2025-10-23"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        print("✅ Rota funcionando! PDF gerado com sucesso.")
        print(f"Tamanho do arquivo: {len(response.content)} bytes")
    elif response.status_code == 404:
        print("❌ Rota não encontrada (404)")
        print(response.text)
    elif response.status_code == 302:
        print("⚠️ Redirecionamento (302) - provavelmente não está autenticado")
        print(f"Redirect para: {response.headers.get('Location')}")
    else:
        print(f"❌ Erro {response.status_code}")
        print(response.text[:500])
except Exception as e:
    print(f"❌ Erro ao fazer requisição: {e}")
