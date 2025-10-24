import os
import logging
import sys
import socket
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,  # Mudado para INFO para ver logs de debug
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configurar níveis de log para bibliotecas de terceiros
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Desativar logs do Flask-Limiter
logging.getLogger('flask_limiter').setLevel(logging.ERROR)

# Logger principal
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Importações após configuração de logging
from app import create_app
from init_db import init_postgres_db, init_migrations

try:
    # Verificar se é a primeira execução (flag simples em arquivo local)
    db_initialized = os.path.exists('db_initialized.flag')
    if not db_initialized:
        logger.info("Inicializando banco de dados PostgreSQL...")
        if init_postgres_db():
            logger.info("Inicializando migrações do Flask...")
            init_migrations()
            # Criar arquivo de flag para indicar que o banco foi inicializado
            with open('db_initialized.flag', 'w') as f:
                f.write('1')
            logger.info("Configuração do banco de dados concluída com sucesso!")
        else:
            logger.error("Falha na configuração do banco de dados.")
            sys.exit(1)
    else:
        logger.info("Banco de dados já inicializado anteriormente.")

    # Criar aplicação
    app = create_app()

except Exception as e:
    logger.error(f"Error creating application: {str(e)}")
    raise

def get_local_ips():
    """Obtém os IPs locais da máquina"""
    try:
        # Método 1: Usando o hostname
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        
        # Filtra apenas IPs locais
        valid_ips = [ip for ip in local_ips 
                    if ip.startswith(('192.168.', '10.0.', '172.16.', '172.17.', '172.18.', '172.19.', 
                                   '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                                   '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.'))]
        
        # Método 2: Se não encontrou, tenta com conexão externa
        if not valid_ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                if not local_ip.startswith('127.') and local_ip not in valid_ips:
                    valid_ips.append(local_ip)
            except:
                pass
        
        return valid_ips
    except Exception as e:
        logger.error(f"Erro ao obter IPs locais: {str(e)}")
        return []

if __name__ == '__main__':
    try:
        # Configuração básica
        port = 5000
        
        # Por padrão, permite acesso em rede (0.0.0.0)
        # Use --local para restringir apenas ao localhost
        modo_local = '--local' in sys.argv
        host = '127.0.0.1' if modo_local else '0.0.0.0'
        
        # Obtém IPs locais
        valid_ips = get_local_ips()
        
        # Exibe informações de acesso
        print("\n" + "="*80)
        print("CONFIGURAÇÃO DO SERVIDOR".center(80))
        print("="*80)
        
        if modo_local:
            print("\nMODO: ACESSO APENAS LOCAL")
            print(f"Servidor escutando em: {host}:{port}")
            print(f"\n✓ Acesso local: http://127.0.0.1:{port}")
            print("\nPara permitir acesso em rede, execute sem o parâmetro --local")
        else:
            print("\nMODO: ACESSO EM REDE (todas as interfaces)")
            print(f"Servidor escutando em: {host}:{port}")
            print(f"\n✓ Acesso local: http://127.0.0.1:{port}")
            
            if valid_ips:
                print("\n✓ Acesso em rede:")
                for ip in valid_ips:
                    print(f"  - http://{ip}:{port}")
            else:
                print("\n⚠ Aviso: Não foi possível detectar automaticamente os IPs de rede.")
                print("  Tente acessar usando o IP da sua máquina na rede local.")
            
            print("\n📌 IMPORTANTE:")
            print("  - Certifique-se de que o Firewall do Windows permite conexões na porta 5000")
            print("  - Outros dispositivos devem estar na mesma rede local")
        
        print("\n" + "="*80 + "\n")
        
        # Iniciar o servidor Flask
        print(f"🚀 Iniciando servidor Flask em {host}:{port}...\n")
        app.run(host=host, port=port, debug=True, use_reloader=False, threaded=True)
        
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {str(e)}")
        sys.exit(1)
