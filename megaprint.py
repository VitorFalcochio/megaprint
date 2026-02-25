import requests
import time
import win32print
import os
import json
import sys

# ================= CONFIGURAÇÃO =================
URL_BASE = "https://megaprint2.onrender.com"
ARQUIVO_CONFIG = "config.txt"
# ================================================


def get_caminho_base():
    """Pasta onde o .PY está ou onde o .EXE está (PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def caminho_config():
    return os.path.join(get_caminho_base(), ARQUIVO_CONFIG)


def listar_impressoras():
    """Lista impressoras instaladas no Windows."""
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    # printers: lista de tuplas; nome geralmente no índice 2
    nomes = []
    for p in printers:
        try:
            nomes.append(p[2])
        except Exception:
            pass
    return nomes


def salvar_configuracao(loja_id, senha_waychef, nome_impressora):
    path = caminho_config()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write((loja_id or "").strip() + "\n")
            f.write((senha_waychef or "").strip() + "\n")
            f.write((nome_impressora or "").strip() + "\n")
        print(f"[OK] Config salva em: {path}")
    except Exception as e:
        print(f"[ERRO] Não consegui salvar config: {e}")


def pedir_configuracao_interativa():
    print("\n=== CONFIGURAÇÃO INICIAL ===")

    loja_id = input("Digite o ID da loja (ex: loja_01): ").strip()
    while not loja_id:
        loja_id = input("ID da loja não pode ficar vazio. Digite novamente: ").strip()

    # Observação: isso vai aparecer no terminal. Se quiser “esconder” a senha, eu troco por getpass.
    senha_waychef = input("Digite a SENHA do Waychef: ").strip()
    while not senha_waychef:
        senha_waychef = input("Senha não pode ficar vazia. Digite novamente: ").strip()

    print("\nImpressoras detectadas no Windows:")
    nomes = listar_impressoras()
    if nomes:
        for i, n in enumerate(nomes, start=1):
            print(f"  {i}) {n}")
    else:
        print("  (não consegui listar; digite o nome manualmente)")

    nome_impressora = input("\nDigite o NOME EXATO da impressora (como no Windows): ").strip()
    while not nome_impressora:
        nome_impressora = input("Nome da impressora não pode ficar vazio. Digite novamente: ").strip()

    salvar_configuracao(loja_id, senha_waychef, nome_impressora)
    return loja_id, senha_waychef, nome_impressora


def ler_configuracao():
    """Lê config.txt. Se não existir, pergunta e cria."""
    path = caminho_config()
    print(f"Procurando config em: {path}")

    if not os.path.exists(path):
        print("\n[AVISO] config.txt não encontrado. Vou configurar agora.")
        return pedir_configuracao_interativa()

    try:
        with open(path, "r", encoding="utf-8") as f:
            linhas = [l.strip() for l in f.readlines() if l.strip() != ""]

        # Esperado: 3 linhas
        if len(linhas) < 3:
            print("\n[AVISO] config.txt incompleto. Vou reconfigurar.")
            return pedir_configuracao_interativa()

        loja_id = linhas[0]
        senha_waychef = linhas[1]
        nome_impressora = linhas[2]
        return loja_id, senha_waychef, nome_impressora

    except Exception as e:
        print(f"[ERRO] Falha ao ler config: {e}")
        return pedir_configuracao_interativa()


def imprimir_cupom(conteudo, nome_impressora):
    try:
        hPrinter = win32print.OpenPrinter(nome_impressora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Cupom Bot", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)

            # Comandos ESC/POS
            CMD_INIT        = b'\x1b\x40'
            CMD_CENTRALIZAR = b'\x1b\x61\x01'
            CMD_ESQUERDA    = b'\x1b\x61\x00'
            CMD_NEGRITO_ON  = b'\x1b\x45\x01'
            CMD_NEGRITO_OFF = b'\x1b\x45\x00'
            CMD_CORTE       = b'\x1d\x56\x00'

            win32print.WritePrinter(hPrinter, CMD_INIT)
            win32print.WritePrinter(hPrinter, CMD_CENTRALIZAR + CMD_NEGRITO_ON)
            win32print.WritePrinter(hPrinter, "=== NOVO PEDIDO ===\n\n".encode("cp850", errors="ignore"))
            win32print.WritePrinter(hPrinter, CMD_NEGRITO_OFF + CMD_ESQUERDA)

            texto_final = str(conteudo)
            win32print.WritePrinter(hPrinter, texto_final.encode("cp850", errors="ignore"))

            win32print.WritePrinter(hPrinter, b"\n\n-------------------\n\n\n\n\n")
            win32print.WritePrinter(hPrinter, CMD_CORTE)

            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)

            print(" >> [SUCESSO] Impresso com sucesso!")

        finally:
            win32print.ClosePrinter(hPrinter)

    except Exception as e:
        print(f" >> [ERRO IMPRESSORA] {e}")
        print("Verifique se o nome no config está EXATO (como no Windows).")


def iniciar():
    print("--- SISTEMA DE IMPRESSÃO MULTI-LOJA ---")

    loja_id, senha_waychef, minha_impressora = ler_configuracao()

    if not loja_id or not senha_waychef or not minha_impressora:
        print("Configuração inválida. Fechando...")
        time.sleep(5)
        return

    print(f"LOJA IDENTIFICADA: {loja_id}")
    print(f"WAYCHEF (senha):   {'*' * len(senha_waychef)}")  # não mostra a senha
    print(f"IMPRESSORA ALVO:   {minha_impressora}")
    print("Iniciando monitoramento...")

    while True:
        try:
            url = f"{URL_BASE}/buscar_pedido/{loja_id}"

            # Se você quiser mandar a senha pro servidor validar, dá pra enviar no header:
            # headers = {"X-WAYCHEF-SENHA": senha_waychef}
            # response = requests.get(url, headers=headers, timeout=10)

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                dados = response.json()

                if dados:
                    print("\n[RECEBIDO] Pedido encontrado!")

                    chave = list(dados.keys())[0]
                    texto = dados[chave]

                    imprimir_cupom(texto, minha_impressora)

            else:
                print(f"[HTTP] Status {response.status_code}: {response.text[:200]}")

        except Exception as e:
            print(f"Erro de conexão: {e}")

        time.sleep(5)


if __name__ == "__main__":
    iniciar()
