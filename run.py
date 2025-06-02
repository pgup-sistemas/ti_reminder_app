from app import create_app
import logging
import sys
import socket

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    logger.info("Application created successfully")
except Exception as e:
    logger.error(f"Error creating application: {str(e)}")
    raise

if __name__ == '__main__':
    try:
        modo_rede = '--rede' in sys.argv
        if modo_rede:
            # Descobre IP local real (IPv4, não localhost)
            import re
            local_ip = None
            try:
                # Tenta obter o IP real da rede local (ignora localhost)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            except Exception as e:
                logger.error(f"Error getting local IP: {str(e)}")
                # Fallback para hostname
                local_ip = socket.gethostbyname(socket.gethostname())
            finally:
                s.close()
            # Confirma que não é localhost
            if local_ip.startswith('127.') or local_ip == '0.0.0.0':
                # Busca todos os IPs possíveis
                ips = socket.getaddrinfo(socket.gethostname(), None)
                for result in ips:
                    ip = result[4][0]
                    if re.match(r'^192\.168\.', ip):
                        local_ip = ip
                        break
            logger.info(f"Starting in network mode on {local_ip}")
            print(f'\n>>> Servidor disponível na rede: http://{local_ip}:5000/ <<<\n')
            app.run(debug=True, host='0.0.0.0')
        else:
            logger.info("Starting in debug mode")
            app.run(debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        raise

