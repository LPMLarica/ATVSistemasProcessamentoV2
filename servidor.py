"""
=============================================================
  SERVIDOR - CALCULADORA REMOTA DE EXPRESSÕES
  Arquitetura: TCP/IP Síncrona (sem multithreads)
  Disciplina: Redes de Computadores - Aula 4
=============================================================
"""

import socket
import json
import datetime
import math
import operator

HOST = '0.0.0.0'  
PORT = 65432      

OPERACOES = {
    'soma':          lambda a, b: a + b,
    'subtracao':     lambda a, b: a - b,
    'multiplicacao': lambda a, b: a * b,
    'divisao':       lambda a, b: a / b if b != 0 else None,
    'potencia':      lambda a, b: a ** b,
    'modulo':        lambda a, b: a % b if b != 0 else None,
    'raiz':          lambda a, b: math.sqrt(a) if a >= 0 else None,
    'log':           lambda a, b: math.log(a, b) if a > 0 and b > 0 and b != 1 else None,
}

NOMES_OPERACOES = {
    'soma':          '+',
    'subtracao':     '−',
    'multiplicacao': '×',
    'divisao':       '÷',
    'potencia':      '^',
    'modulo':        'mod',
    'raiz':          '√',
    'log':           'log',
}


def log(nivel, mensagem):
    """Exibe log formatado no console do servidor."""
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    prefixos = {
        'INFO':   '\033[96m[INFO]\033[0m ',
        'OK':     '\033[92m[ OK ]\033[0m ',
        'RECV':   '\033[93m[RECV]\033[0m ',
        'SEND':   '\033[94m[SEND]\033[0m ',
        'ERRO':   '\033[91m[ERRO]\033[0m ',
        'WAIT':   '\033[90m[WAIT]\033[0m ',
    }
    prefixo = prefixos.get(nivel, '[????] ')
    print(f"  {agora}  {prefixo} {mensagem}")


def processar_requisicao(dados_raw):
    """Processa a requisição recebida e retorna o resultado."""
    try:
        dados = json.loads(dados_raw)
        op   = dados.get('operacao', '').lower()
        a    = float(dados.get('a', 0))
        b    = float(dados.get('b', 0))

        if op not in OPERACOES:
            return {'status': 'erro', 'mensagem': f"Operação desconhecida: '{op}'"}

        resultado = OPERACOES[op](a, b)

        if resultado is None:
            if op == 'divisao' or op == 'modulo':
                return {'status': 'erro', 'mensagem': 'Divisão por zero não é permitida.'}
            elif op == 'raiz':
                return {'status': 'erro', 'mensagem': 'Raiz de número negativo não é suportada.'}
            elif op == 'log':
                return {'status': 'erro', 'mensagem': 'Logaritmo inválido (verifique base e argumento).'}
            return {'status': 'erro', 'mensagem': 'Resultado inválido.'}

        # Formata o resultado 
        resultado_fmt = int(resultado) if isinstance(resultado, float) and resultado.is_integer() else round(resultado, 10)

        simb = NOMES_OPERACOES.get(op, op)
        if op in ('raiz',):
            expressao = f"√{a}"
        elif op in ('log',):
            expressao = f"log_{b}({a})"
        else:
            expressao = f"{a} {simb} {b}"

        return {
            'status':    'ok',
            'resultado': resultado_fmt,
            'expressao': expressao,
        }

    except json.JSONDecodeError:
        return {'status': 'erro', 'mensagem': 'Formato de dados inválido (JSON corrompido).'}
    except (ValueError, KeyError) as e:
        return {'status': 'erro', 'mensagem': f'Dados inválidos: {e}'}
    except Exception as e:
        return {'status': 'erro', 'mensagem': f'Erro interno: {e}'}


def iniciar_servidor():
    """Loop principal do servidor — síncrono e bloqueante."""

    print()
    print("  \033[96m╔══════════════════════════════════════════════════════╗\033[0m")
    print("  \033[96m║        SERVIDOR — CALCULADORA REMOTA TCP/IP          ║\033[0m")
    print("  \033[96m║         Redes de Computadores · Aula 4               ║\033[0m")
    print("  \033[96m╚══════════════════════════════════════════════════════╝\033[0m")
    print()

    # Cria TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(1)

        log('INFO', f"Socket criado — AF_INET / SOCK_STREAM")
        log('INFO', f"Endereço de escuta : {HOST}:{PORT}")
        log('INFO', f"Modo              : SÍNCRONO (1 requisição por vez)")
        log('WAIT', f"Aguardando conexão de clientes...\n")

        ciclo = 0
        while True:
            try:
                conn, addr = srv.accept()

                with conn:
                    ciclo += 1
                    print(f"  {'─'*54}")
                    log('OK',   f"Ciclo #{ciclo:04d} — Cliente conectado: {addr[0]}:{addr[1]}")

                    # Recebe dados
                    dados_raw = conn.recv(4096).decode('utf-8').strip()
                    if not dados_raw:
                        log('ERRO', "Pacote vazio recebido. Conexão encerrada.")
                        continue

                    log('RECV', f"Dados recebidos  : {dados_raw}")

                    # Processa
                    resposta = processar_requisicao(dados_raw)
                    resposta_json = json.dumps(resposta, ensure_ascii=False)

                    # Envia resposta
                    conn.sendall(resposta_json.encode('utf-8'))
                    log('SEND', f"Resposta enviada : {resposta_json}")

                    if resposta['status'] == 'ok':
                        log('OK',   f"Resultado        : {resposta['expressao']} = {resposta['resultado']}")
                    else:
                        log('ERRO', f"Erro retornado   : {resposta['mensagem']}")

                    log('INFO', f"Conexão encerrada com {addr[0]}:{addr[1]}")

            except KeyboardInterrupt:
                print()
                log('INFO', "Servidor encerrado pelo operador (Ctrl+C).")
                print()
                break
            except Exception as e:
                log('ERRO', f"Exceção inesperada no ciclo: {e}")


if __name__ == '__main__':
    iniciar_servidor()