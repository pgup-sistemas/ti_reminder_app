#!/usr/bin/env python3
"""
Script de verificação de prontidão para produção - TI Reminder App
"""
import subprocess
import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path


class ProductionReadinessChecker:
    """Classe para verificar se o sistema está pronto para produção"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
    
    def run_command(self, command, description):
        """Executa comando e retorna resultado"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip() if e.stderr else str(e)
        except subprocess.TimeoutExpired:
            return False, "Timeout - comando demorou mais de 5 minutos"
        except Exception as e:
            return False, str(e)
    
    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas"""
        print("🔍 Verificando dependências...")
        
        success, output = self.run_command("pip check", "Verificação de dependências")
        
        if success:
            self.results['checks']['dependencies'] = {
                'status': 'PASS',
                'message': 'Todas as dependências estão corretas'
            }
            print("✅ Dependências OK")
            return True
        else:
            self.results['checks']['dependencies'] = {
                'status': 'FAIL',
                'message': f'Problemas nas dependências: {output}'
            }
            self.results['critical_issues'].append('Dependências com conflitos')
            print(f"❌ Problemas nas dependências: {output}")
            return False
    
    def check_code_quality(self):
        """Verifica qualidade do código"""
        print("🔍 Verificando qualidade do código...")
        
        checks = [
            ("flake8 app/ --max-line-length=120 --exclude=migrations --count", "Flake8"),
            ("black --check app/", "Black formatting"),
            ("isort --check-only app/", "Import sorting")
        ]
        
        all_passed = True
        issues = []
        
        for command, name in checks:
            success, output = self.run_command(command, name)
            if not success:
                all_passed = False
                issues.append(f"{name}: {output}")
        
        if all_passed:
            self.results['checks']['code_quality'] = {
                'status': 'PASS',
                'message': 'Código segue padrões de qualidade'
            }
            print("✅ Qualidade do código OK")
        else:
            self.results['checks']['code_quality'] = {
                'status': 'FAIL',
                'message': f'Problemas de qualidade: {"; ".join(issues)}'
            }
            self.results['warnings'].extend(issues)
            print(f"⚠️ Problemas de qualidade encontrados")
        
        return all_passed
    
    def check_security(self):
        """Verifica vulnerabilidades de segurança"""
        print("🔍 Verificando segurança...")
        
        # Verificar vulnerabilidades conhecidas
        success, output = self.run_command("safety check", "Safety check")
        
        security_issues = []
        
        if not success and "No known security vulnerabilities found" not in output:
            security_issues.append(f"Vulnerabilidades encontradas: {output}")
        
        # Verificar configurações de segurança
        env_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = []
        
        for var in env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            security_issues.append(f"Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        
        if not security_issues:
            self.results['checks']['security'] = {
                'status': 'PASS',
                'message': 'Verificações de segurança passaram'
            }
            print("✅ Segurança OK")
            return True
        else:
            self.results['checks']['security'] = {
                'status': 'FAIL',
                'message': '; '.join(security_issues)
            }
            self.results['critical_issues'].extend(security_issues)
            print(f"❌ Problemas de segurança: {'; '.join(security_issues)}")
            return False
    
    def run_tests(self):
        """Executa todos os testes"""
        print("🧪 Executando testes...")
        
        test_commands = [
            ("pytest tests/unit/ -v --tb=short", "Testes unitários"),
            ("pytest tests/integration/ -v --tb=short", "Testes de integração"),
            ("pytest --cov=app --cov-report=term-missing --cov-fail-under=70", "Coverage")
        ]
        
        all_passed = True
        failed_tests = []
        
        for command, name in test_commands:
            print(f"  🔄 Executando {name}...")
            success, output = self.run_command(command, name)
            
            if not success:
                all_passed = False
                failed_tests.append(name)
                print(f"  ❌ {name} falharam")
            else:
                print(f"  ✅ {name} passaram")
        
        if all_passed:
            self.results['checks']['tests'] = {
                'status': 'PASS',
                'message': 'Todos os testes passaram'
            }
            print("✅ Todos os testes OK")
        else:
            self.results['checks']['tests'] = {
                'status': 'FAIL',
                'message': f'Testes falharam: {", ".join(failed_tests)}'
            }
            self.results['critical_issues'].append(f'Testes falharam: {", ".join(failed_tests)}')
            print(f"❌ Testes falharam: {', '.join(failed_tests)}")
        
        return all_passed
    
    def check_database_migrations(self):
        """Verifica se migrações estão atualizadas"""
        print("🔍 Verificando migrações do banco...")
        
        success, output = self.run_command("flask db current", "Verificar migração atual")
        
        if success:
            self.results['checks']['migrations'] = {
                'status': 'PASS',
                'message': 'Migrações estão atualizadas'
            }
            print("✅ Migrações OK")
            return True
        else:
            self.results['checks']['migrations'] = {
                'status': 'FAIL',
                'message': f'Problema com migrações: {output}'
            }
            self.results['critical_issues'].append('Migrações não atualizadas')
            print(f"❌ Problema com migrações: {output}")
            return False
    
    def check_configuration(self):
        """Verifica configurações essenciais"""
        print("🔍 Verificando configurações...")
        
        issues = []
        
        # Verificar arquivo de configuração
        if not os.path.exists('config.py'):
            issues.append('Arquivo config.py não encontrado')
        
        # Verificar variáveis críticas
        critical_vars = {
            'SECRET_KEY': 'Chave secreta não configurada',
            'DATABASE_URL': 'URL do banco não configurada'
        }
        
        for var, message in critical_vars.items():
            value = os.getenv(var)
            if not value:
                issues.append(message)
            elif var == 'SECRET_KEY' and (len(value) < 32 or value == 'dev'):
                issues.append('SECRET_KEY muito simples ou padrão')
        
        # Verificar FLASK_ENV
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env != 'production':
            self.results['warnings'].append(f'FLASK_ENV está como "{flask_env}", deveria ser "production"')
        
        if not issues:
            self.results['checks']['configuration'] = {
                'status': 'PASS',
                'message': 'Configurações estão corretas'
            }
            print("✅ Configurações OK")
            return True
        else:
            self.results['checks']['configuration'] = {
                'status': 'FAIL',
                'message': '; '.join(issues)
            }
            self.results['critical_issues'].extend(issues)
            print(f"❌ Problemas de configuração: {'; '.join(issues)}")
            return False
    
    def check_performance(self):
        """Verifica aspectos de performance"""
        print("🔍 Verificando performance...")
        
        warnings = []
        
        # Verificar se DEBUG está desabilitado
        if os.getenv('FLASK_DEBUG', '').lower() in ['true', '1', 'on']:
            warnings.append('DEBUG está habilitado - deve ser desabilitado em produção')
        
        # Verificar se há arquivos de log configurados
        if not os.getenv('LOG_FILE'):
            warnings.append('LOG_FILE não configurado - logs podem não ser persistidos')
        
        # Verificar compressão de assets
        if not os.path.exists('app/static/css/main.min.css'):
            warnings.append('Assets não estão minificados - considere usar minificação')
        
        if warnings:
            self.results['warnings'].extend(warnings)
            self.results['checks']['performance'] = {
                'status': 'WARNING',
                'message': '; '.join(warnings)
            }
            print(f"⚠️ Avisos de performance: {'; '.join(warnings)}")
        else:
            self.results['checks']['performance'] = {
                'status': 'PASS',
                'message': 'Configurações de performance OK'
            }
            print("✅ Performance OK")
        
        return True
    
    def generate_recommendations(self):
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        # Recomendações baseadas nos problemas encontrados
        if any('Dependências' in issue for issue in self.results['critical_issues']):
            recommendations.append('Execute: pip install -r requirements.txt --upgrade')
        
        if any('Testes' in issue for issue in self.results['critical_issues']):
            recommendations.append('Corrija os testes falhando antes do deploy')
        
        if any('SECRET_KEY' in issue for issue in self.results['critical_issues']):
            recommendations.append('Configure uma SECRET_KEY forte com pelo menos 32 caracteres')
        
        if any('DATABASE_URL' in issue for issue in self.results['critical_issues']):
            recommendations.append('Configure a DATABASE_URL para o banco de produção')
        
        # Recomendações gerais
        recommendations.extend([
            'Execute backup do banco antes do deploy',
            'Configure monitoramento de logs em produção',
            'Teste a aplicação em ambiente de staging primeiro',
            'Configure SSL/HTTPS para produção',
            'Implemente rotação de logs para evitar disco cheio'
        ])
        
        self.results['recommendations'] = recommendations
    
    def run_all_checks(self):
        """Executa todas as verificações"""
        print("🚀 VERIFICAÇÃO DE PRONTIDÃO PARA PRODUÇÃO")
        print("=" * 60)
        
        checks = [
            self.check_dependencies,
            self.check_configuration,
            self.check_security,
            self.check_code_quality,
            self.check_database_migrations,
            self.run_tests,
            self.check_performance
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check in checks:
            try:
                if check():
                    passed_checks += 1
            except Exception as e:
                print(f"❌ Erro inesperado em {check.__name__}: {e}")
                self.results['critical_issues'].append(f'Erro em {check.__name__}: {e}')
        
        # Determinar status geral
        if len(self.results['critical_issues']) == 0:
            if len(self.results['warnings']) == 0:
                self.results['overall_status'] = 'READY'
            else:
                self.results['overall_status'] = 'READY_WITH_WARNINGS'
        else:
            self.results['overall_status'] = 'NOT_READY'
        
        self.generate_recommendations()
        
        return self.results
    
    def print_summary(self):
        """Imprime resumo dos resultados"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DA VERIFICAÇÃO")
        print("=" * 60)
        
        # Status geral
        status_icons = {
            'READY': '🎉',
            'READY_WITH_WARNINGS': '⚠️',
            'NOT_READY': '❌'
        }
        
        status_messages = {
            'READY': 'SISTEMA PRONTO PARA PRODUÇÃO!',
            'READY_WITH_WARNINGS': 'SISTEMA PRONTO COM AVISOS',
            'NOT_READY': 'SISTEMA NÃO ESTÁ PRONTO'
        }
        
        icon = status_icons.get(self.results['overall_status'], '❓')
        message = status_messages.get(self.results['overall_status'], 'STATUS DESCONHECIDO')
        
        print(f"{icon} {message}")
        
        # Problemas críticos
        if self.results['critical_issues']:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues']:
                print(f"  • {issue}")
        
        # Avisos
        if self.results['warnings']:
            print(f"\n⚠️ AVISOS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        # Recomendações
        if self.results['recommendations']:
            print(f"\n💡 RECOMENDAÇÕES:")
            for rec in self.results['recommendations'][:5]:  # Top 5
                print(f"  • {rec}")
        
        # Detalhes dos checks
        print(f"\n📋 DETALHES DOS CHECKS:")
        for check_name, check_result in self.results['checks'].items():
            status = check_result['status']
            icon = '✅' if status == 'PASS' else '⚠️' if status == 'WARNING' else '❌'
            print(f"  {icon} {check_name.replace('_', ' ').title()}: {check_result['message']}")
    
    def save_report(self, filename='production_readiness_report.json'):
        """Salva relatório em arquivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Relatório salvo em: {filename}")


def main():
    """Função principal"""
    checker = ProductionReadinessChecker()
    
    try:
        results = checker.run_all_checks()
        checker.print_summary()
        checker.save_report()
        
        # Exit code baseado no status
        if results['overall_status'] == 'READY':
            sys.exit(0)
        elif results['overall_status'] == 'READY_WITH_WARNINGS':
            sys.exit(1)  # Warning exit code
        else:
            sys.exit(2)  # Error exit code
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Verificação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
