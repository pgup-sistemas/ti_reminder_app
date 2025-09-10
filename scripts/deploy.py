#!/usr/bin/env python3
"""
Script de deployment para TI Reminder App
"""
import subprocess
import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path


def run_command(command, description, check=True):
    """Executa um comando e retorna o resultado"""
    print(f"\n🔄 {description}")
    print(f"Comando: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} - SUCESSO")
            if result.stdout:
                print(result.stdout)
            return True, result.stdout
        else:
            print(f"❌ {description} - FALHOU")
            if result.stderr:
                print("STDERR:", result.stderr)
            return False, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERRO")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False, str(e)


def check_environment():
    """Verifica se o ambiente está pronto para deployment"""
    print("🔍 Verificando ambiente...")
    
    checks = [
        ("python --version", "Verificando Python"),
        ("pip --version", "Verificando pip"),
        ("git --version", "Verificando Git")
    ]
    
    for command, description in checks:
        success, output = run_command(command, description)
        if not success:
            return False
    
    return True


def run_tests():
    """Executa testes antes do deployment"""
    print("🧪 Executando testes...")
    
    success, output = run_command(
        "python scripts/run_tests.py --all",
        "Executando pipeline completo de testes"
    )
    
    return success


def backup_database():
    """Cria backup do banco de dados"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_db_{timestamp}.sql"
    
    print(f"💾 Criando backup do banco de dados: {backup_file}")
    
    # Para PostgreSQL
    success, output = run_command(
        f"pg_dump $DATABASE_URL > backups/{backup_file}",
        "Criando backup PostgreSQL",
        check=False
    )
    
    if not success:
        # Para SQLite (desenvolvimento)
        success, output = run_command(
            f"cp instance/ti_reminder.db backups/ti_reminder_{timestamp}.db",
            "Criando backup SQLite",
            check=False
        )
    
    return success


def update_dependencies():
    """Atualiza dependências"""
    print("📦 Atualizando dependências...")
    
    success, output = run_command(
        "pip install -r requirements.txt --upgrade",
        "Atualizando dependências Python"
    )
    
    return success


def run_migrations():
    """Executa migrações do banco de dados"""
    print("🗄️ Executando migrações...")
    
    commands = [
        ("flask db upgrade", "Aplicando migrações do banco"),
        ("python init_db.py", "Inicializando dados padrão")
    ]
    
    for command, description in commands:
        success, output = run_command(command, description, check=False)
        if not success:
            print(f"⚠️ {description} falhou, mas continuando...")
    
    return True


def collect_static_files():
    """Coleta arquivos estáticos"""
    print("📁 Coletando arquivos estáticos...")
    
    # Minificar CSS e JS se necessário
    success, output = run_command(
        "python scripts/minify_assets.py",
        "Minificando assets",
        check=False
    )
    
    return True


def restart_services():
    """Reinicia serviços"""
    print("🔄 Reiniciando serviços...")
    
    services = [
        ("systemctl restart ti-reminder", "Reiniciando aplicação"),
        ("systemctl restart nginx", "Reiniciando Nginx")
    ]
    
    for command, description in services:
        success, output = run_command(command, description, check=False)
        if not success:
            print(f"⚠️ {description} falhou - pode precisar de sudo")
    
    return True


def health_check():
    """Verifica se a aplicação está funcionando"""
    print("🏥 Verificando saúde da aplicação...")
    
    import requests
    import time
    
    # Aguardar um pouco para a aplicação iniciar
    time.sleep(5)
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Aplicação está respondendo corretamente")
            return True
        else:
            print(f"❌ Aplicação retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar aplicação: {e}")
        return False


def create_deployment_log():
    """Cria log do deployment"""
    timestamp = datetime.now().isoformat()
    
    log_data = {
        "timestamp": timestamp,
        "version": get_app_version(),
        "environment": os.getenv("FLASK_ENV", "production"),
        "deployed_by": os.getenv("USER", "unknown"),
        "git_commit": get_git_commit()
    }
    
    os.makedirs("logs", exist_ok=True)
    
    with open(f"logs/deployment_{timestamp.replace(':', '-')}.json", "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"📝 Log de deployment criado: {log_data}")


def get_app_version():
    """Obtém versão da aplicação"""
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


def get_git_commit():
    """Obtém hash do commit atual"""
    success, output = run_command("git rev-parse HEAD", "Obtendo commit hash", check=False)
    return output.strip() if success else "unknown"


def deploy_production():
    """Pipeline completo de deployment para produção"""
    print("🚀 INICIANDO DEPLOYMENT PARA PRODUÇÃO")
    print("="*60)
    
    steps = [
        (check_environment, "Verificação do ambiente"),
        (run_tests, "Execução de testes"),
        (backup_database, "Backup do banco de dados"),
        (update_dependencies, "Atualização de dependências"),
        (run_migrations, "Execução de migrações"),
        (collect_static_files, "Coleta de arquivos estáticos"),
        (restart_services, "Reinicialização de serviços"),
        (health_check, "Verificação de saúde"),
        (create_deployment_log, "Criação de log")
    ]
    
    for step_func, description in steps:
        print(f"\n📋 Executando: {description}")
        try:
            success = step_func()
            if not success and step_func in [check_environment, run_tests]:
                print(f"❌ Deployment interrompido em: {description}")
                return False
        except Exception as e:
            print(f"❌ Erro em {description}: {e}")
            if step_func in [check_environment, run_tests]:
                return False
    
    print("\n🎉 DEPLOYMENT CONCLUÍDO COM SUCESSO!")
    return True


def deploy_staging():
    """Pipeline de deployment para staging"""
    print("🧪 INICIANDO DEPLOYMENT PARA STAGING")
    print("="*50)
    
    steps = [
        (check_environment, "Verificação do ambiente"),
        (run_tests, "Execução de testes"),
        (update_dependencies, "Atualização de dependências"),
        (run_migrations, "Execução de migrações"),
        (health_check, "Verificação de saúde")
    ]
    
    for step_func, description in steps:
        print(f"\n📋 Executando: {description}")
        try:
            success = step_func()
            if not success and step_func in [check_environment, run_tests]:
                print(f"❌ Deployment interrompido em: {description}")
                return False
        except Exception as e:
            print(f"❌ Erro em {description}: {e}")
    
    print("\n✅ DEPLOYMENT DE STAGING CONCLUÍDO!")
    return True


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Deploy do TI Reminder App")
    parser.add_argument("--env", choices=["production", "staging"], default="staging",
                       help="Ambiente de deployment")
    parser.add_argument("--skip-tests", action="store_true", 
                       help="Pular execução de testes")
    parser.add_argument("--skip-backup", action="store_true",
                       help="Pular backup do banco")
    parser.add_argument("--dry-run", action="store_true",
                       help="Simular deployment sem executar")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 MODO DRY-RUN - Simulando deployment")
        print(f"Ambiente: {args.env}")
        print(f"Pular testes: {args.skip_tests}")
        print(f"Pular backup: {args.skip_backup}")
        return
    
    # Criar diretórios necessários
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    if args.env == "production":
        success = deploy_production()
    else:
        success = deploy_staging()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
