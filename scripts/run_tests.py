#!/usr/bin/env python3
"""
Script para executar todos os testes do TI Reminder App
"""
import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(command, description):
    """Executa um comando e retorna o resultado"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} - SUCESSO")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALHOU")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def install_dependencies():
    """Instala dependências de teste"""
    return run_command(
        "pip install -r requirements-test.txt",
        "Instalando dependências de teste"
    )


def run_linting():
    """Executa verificações de código"""
    commands = [
        ("flake8 app/ --max-line-length=120 --exclude=migrations", "Verificação de estilo com flake8"),
        ("black --check app/", "Verificação de formatação com black"),
        ("isort --check-only app/", "Verificação de imports com isort")
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)


def run_unit_tests():
    """Executa testes unitários"""
    return run_command(
        "pytest tests/unit/ -v --tb=short",
        "Executando testes unitários"
    )


def run_integration_tests():
    """Executa testes de integração"""
    return run_command(
        "pytest tests/integration/ -v --tb=short",
        "Executando testes de integração"
    )


def run_e2e_tests():
    """Executa testes end-to-end"""
    return run_command(
        "pytest tests/e2e/ -v --tb=short -m 'not slow'",
        "Executando testes end-to-end (rápidos)"
    )


def run_all_tests():
    """Executa todos os testes com coverage"""
    return run_command(
        "pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70",
        "Executando todos os testes com coverage"
    )


def run_security_checks():
    """Executa verificações de segurança"""
    return run_command(
        "pip-audit",
        "Verificação de vulnerabilidades de segurança"
    )


def generate_reports():
    """Gera relatórios de teste"""
    commands = [
        ("pytest --html=reports/test_report.html --self-contained-html", "Gerando relatório HTML"),
        ("pytest --junitxml=reports/junit.xml", "Gerando relatório JUnit XML")
    ]
    
    # Criar diretório de relatórios
    os.makedirs("reports", exist_ok=True)
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description))
    
    return all(results)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Executa testes do TI Reminder App")
    parser.add_argument("--unit", action="store_true", help="Executar apenas testes unitários")
    parser.add_argument("--integration", action="store_true", help="Executar apenas testes de integração")
    parser.add_argument("--e2e", action="store_true", help="Executar apenas testes E2E")
    parser.add_argument("--lint", action="store_true", help="Executar apenas verificações de código")
    parser.add_argument("--security", action="store_true", help="Executar apenas verificações de segurança")
    parser.add_argument("--install", action="store_true", help="Instalar dependências")
    parser.add_argument("--reports", action="store_true", help="Gerar relatórios")
    parser.add_argument("--all", action="store_true", help="Executar pipeline completo")
    
    args = parser.parse_args()
    
    print("🚀 TI Reminder App - Pipeline de Testes")
    print(f"📁 Diretório: {os.getcwd()}")
    
    success = True
    
    # Instalar dependências se solicitado
    if args.install or args.all:
        success &= install_dependencies()
    
    # Executar verificações específicas
    if args.lint or args.all:
        success &= run_linting()
    
    if args.security or args.all:
        success &= run_security_checks()
    
    if args.unit or args.all:
        success &= run_unit_tests()
    
    if args.integration or args.all:
        success &= run_integration_tests()
    
    if args.e2e or args.all:
        success &= run_e2e_tests()
    
    if args.reports or args.all:
        success &= generate_reports()
    
    # Se nenhuma opção específica foi escolhida, executar todos os testes
    if not any([args.unit, args.integration, args.e2e, args.lint, args.security, args.install, args.reports, args.all]):
        success &= run_all_tests()
    
    # Resultado final
    print(f"\n{'='*60}")
    if success:
        print("🎉 PIPELINE DE TESTES CONCLUÍDO COM SUCESSO!")
        print("✅ Todos os testes passaram")
        sys.exit(0)
    else:
        print("💥 PIPELINE DE TESTES FALHOU!")
        print("❌ Alguns testes falharam")
        sys.exit(1)


if __name__ == "__main__":
    main()
