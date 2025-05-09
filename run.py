from app import create_app

app = create_app()

import sys
import socket

if __name__ == '__main__':
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
            s.close()
        except Exception:
            # Fallback para hostname
            local_ip = socket.gethostbyname(socket.gethostname())
        # Confirma que não é localhost
        if local_ip.startswith('127.') or local_ip == '0.0.0.0':
            # Busca todos os IPs possíveis
            ips = socket.getaddrinfo(socket.gethostname(), None)
            for result in ips:
                ip = result[4][0]
                if re.match(r'^192\.168\.', ip):
                    local_ip = ip
                    break
        print(f'\n>>> Servidor disponível na rede: http://{local_ip}:5000/ <<<\n')
        app.run(debug=True, host='0.0.0.0')
    else:
        app.run(debug=True)
