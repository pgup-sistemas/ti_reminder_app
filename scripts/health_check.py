#!/usr/bin/env python3
"""
Script de health check para TI Reminder App
"""
import requests
import sys
import time
import argparse
from datetime import datetime


def check_database_connection():
    """Verifica conexão com banco de dados"""
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Tentar executar uma query simples
            db.engine.execute('SELECT 1')
            return True, "Conexão com banco OK"
    except Exception as e:
        return False, f"Erro na conexão com banco: {e}"


def check_web_server(url="http://localhost:5000"):
    """Verifica se o servidor web está respondendo"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            return True, f"Servidor web OK (status: {response.status_code})"
        else:
            return False, f"Servidor web retornou status: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Servidor web não está respondendo"
    except requests.exceptions.Timeout:
        return False, "Timeout ao conectar com servidor web"
    except Exception as e:
        return False, f"Erro ao verificar servidor web: {e}"


def check_scheduler():
    """Verifica se o scheduler está funcionando"""
    try:
        from app import create_app, scheduler
        
        app = create_app()
        with app.app_context():
            if scheduler.running:
                return True, "Scheduler está rodando"
            else:
                return False, "Scheduler não está rodando"
    except Exception as e:
        return False, f"Erro ao verificar scheduler: {e}"


def check_disk_space():
    """Verifica espaço em disco"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        
        if free_gb < 1:
            return False, f"Pouco espaço em disco: {free_gb}GB livres"
        else:
            return True, f"Espaço em disco OK: {free_gb}GB livres"
    except Exception as e:
        return False, f"Erro ao verificar espaço em disco: {e}"


def check_memory_usage():
    """Verifica uso de memória"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            return False, f"Uso de memória alto: {memory.percent}%"
        else:
            return True, f"Uso de memória OK: {memory.percent}%"
    except ImportError:
        return True, "psutil não instalado - verificação de memória pulada"
    except Exception as e:
        return False, f"Erro ao verificar memória: {e}"


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Health check do TI Reminder App")
    parser.add_argument("--url", default="http://localhost:5000", 
                       help="URL base da aplicação")
    parser.add_argument("--wait", type=int, default=0,
                       help="Segundos para aguardar antes do check")
    parser.add_argument("--retry", type=int, default=1,
                       help="Número de tentativas")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Aguardando {args.wait} segundos...")
        time.sleep(args.wait)
    
    checks = [
        (check_database_connection, "Conexão com Banco de Dados"),
        (check_web_server, "Servidor Web", args.url),
        (check_scheduler, "Scheduler"),
        (check_disk_space, "Espaço em Disco"),
        (check_memory_usage, "Uso de Memória")
    ]
    
    print(f"🏥 Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_healthy = True
    
    for attempt in range(args.retry):
        if attempt > 0:
            print(f"\n🔄 Tentativa {attempt + 1}/{args.retry}")
        
        attempt_healthy = True
        
        for check_data in checks:
            check_func = check_data[0]
            check_name = check_data[1]
            check_args = check_data[2:] if len(check_data) > 2 else []
            
            try:
                if check_args:
                    healthy, message = check_func(*check_args)
                else:
                    healthy, message = check_func()
                
                status = "✅" if healthy else "❌"
                print(f"{status} {check_name}: {message}")
                
                if not healthy:
                    attempt_healthy = False
                    
            except Exception as e:
                print(f"❌ {check_name}: Erro inesperado - {e}")
                attempt_healthy = False
        
        if attempt_healthy:
            break
        elif attempt < args.retry - 1:
            print("⏳ Aguardando 5 segundos antes da próxima tentativa...")
            time.sleep(5)
    
    all_healthy = attempt_healthy
    
    print("\n" + "="*60)
    if all_healthy:
        print("🎉 SISTEMA SAUDÁVEL - Todos os checks passaram!")
        sys.exit(0)
    else:
        print("💥 SISTEMA COM PROBLEMAS - Alguns checks falharam!")
        sys.exit(1)


if __name__ == "__main__":
    main()
