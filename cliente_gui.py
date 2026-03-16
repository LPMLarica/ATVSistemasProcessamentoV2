"""
=============================================================
  CLIENTE GUI - CALCULADORA REMOTA DE EXPRESSÕES
  Arquitetura: TCP/IP Síncrona (sem multithreads)
  Disciplina: Redes de Computadores - Aula 4
  GUI: tkinter (nativo Python)
=============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json

SERVER_HOST = '127.0.0.1'
SERVER_PORT  = 65432

COR_FUNDO       = '#0d0f14'
COR_PAINEL      = '#141720'
COR_BORDA       = '#1e2330'
COR_ACCENT      = '#00e5ff'      
COR_ACCENT2     = '#ff6b35'    
COR_TEXTO       = '#c8d0e0'
COR_TEXTO_DIM   = '#4a5568'
COR_INPUT_BG    = '#0a0c12'
COR_ENTRADA     = '#1a1f2e'
COR_BTN         = '#00e5ff'
COR_BTN_FG      = '#0d0f14'
COR_ERRO        = '#ff4757'
COR_OK          = '#2ed573'
COR_LABEL       = '#7b8fa8'
FONTE_MONO      = ('Courier New', 10)
FONTE_TITULO    = ('Courier New', 18, 'bold')
FONTE_NORMAL    = ('Courier New', 10)
FONTE_GRANDE    = ('Courier New', 26, 'bold')
FONTE_PEQUENA   = ('Courier New', 9)

OPERACOES = [
    ('Adição       (A + B)',         'soma'),
    ('Subtração    (A − B)',         'subtracao'),
    ('Multiplicação (A × B)',        'multiplicacao'),
    ('Divisão      (A ÷ B)',         'divisao'),
    ('Potenciação  (A ^ B)',         'potencia'),
    ('Módulo       (A mod B)',       'modulo'),
    ('Raiz N-ésima (ⁿ√A)',           'raiz'),
    ('Logaritmo    (log_B A)',       'log'),
]
LABELS_OP   = [op[0] for op in OPERACOES]
CODIGOS_OP  = {op[0]: op[1] for op in OPERACOES}

OP_SEM_B = {'raiz'}


class CalculadoraClienteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CalcNet — Calculadora Remota TCP/IP")
        self.root.configure(bg=COR_FUNDO)
        self.root.resizable(False, False)
        self._construir_ui()
        self._centralizar_janela(600, 700)

    # Layout
    def _construir_ui(self):
        cabecalho = tk.Frame(self.root, bg=COR_FUNDO)
        cabecalho.pack(fill='x', padx=24, pady=(24, 0))

        tk.Label(
            cabecalho, text="[ CALCNET ]",
            font=FONTE_TITULO, fg=COR_ACCENT, bg=COR_FUNDO
        ).pack(anchor='w')

        tk.Label(
            cabecalho,
            text="CALCULADORA REMOTA  ·  TCP/IP SÍNCRONA  ·  REDES · AULA 4",
            font=('Courier New', 8), fg=COR_TEXTO_DIM, bg=COR_FUNDO
        ).pack(anchor='w')

        tk.Frame(self.root, bg=COR_ACCENT, height=1).pack(fill='x', padx=24, pady=10)

        painel = tk.Frame(self.root, bg=COR_PAINEL, bd=0, highlightthickness=1,
                          highlightbackground=COR_BORDA)
        painel.pack(fill='x', padx=24, pady=4)

        inner = tk.Frame(painel, bg=COR_PAINEL)
        inner.pack(fill='x', padx=20, pady=18)

        # Configuração de servidor
        srv_frame = tk.Frame(inner, bg=COR_PAINEL)
        srv_frame.pack(fill='x', pady=(0, 14))

        tk.Label(srv_frame, text="▸ ENDEREÇO DO SERVIDOR",
                 font=('Courier New', 8, 'bold'), fg=COR_ACCENT, bg=COR_PAINEL
                 ).pack(anchor='w')

        addr_row = tk.Frame(srv_frame, bg=COR_PAINEL)
        addr_row.pack(fill='x', pady=(4, 0))

        tk.Label(addr_row, text="HOST:", font=FONTE_PEQUENA,
                 fg=COR_LABEL, bg=COR_PAINEL, width=6, anchor='w').pack(side='left')
        self.var_host = tk.StringVar(value=SERVER_HOST)
        self._campo(addr_row, self.var_host, width=18).pack(side='left', padx=(0, 16))

        tk.Label(addr_row, text="PORTA:", font=FONTE_PEQUENA,
                 fg=COR_LABEL, bg=COR_PAINEL, width=7, anchor='w').pack(side='left')
        self.var_porta = tk.StringVar(value=str(SERVER_PORT))
        self._campo(addr_row, self.var_porta, width=8).pack(side='left')

        tk.Frame(inner, bg=COR_BORDA, height=1).pack(fill='x', pady=12)

        tk.Label(inner, text="▸ OPERAÇÃO MATEMÁTICA",
                 font=('Courier New', 8, 'bold'), fg=COR_ACCENT, bg=COR_PAINEL
                 ).pack(anchor='w')

        self.var_op = tk.StringVar(value=LABELS_OP[0])
        self.combo_op = ttk.Combobox(
            inner, textvariable=self.var_op,
            values=LABELS_OP, state='readonly',
            font=FONTE_MONO, width=40
        )
        self._estilizar_combo()
        self.combo_op.pack(anchor='w', pady=(6, 14))
        self.combo_op.bind('<<ComboboxSelected>>', self._ao_mudar_op)

        ops_frame = tk.Frame(inner, bg=COR_PAINEL)
        ops_frame.pack(fill='x')

        col_a = tk.Frame(ops_frame, bg=COR_PAINEL)
        col_a.pack(side='left', fill='x', expand=True, padx=(0, 12))

        tk.Label(col_a, text="▸ OPERANDO  A",
                 font=('Courier New', 8, 'bold'), fg=COR_ACCENT, bg=COR_PAINEL
                 ).pack(anchor='w')
        self.var_a = tk.StringVar()
        self._campo(col_a, self.var_a, width=18).pack(anchor='w', pady=(4, 0))

        col_b = tk.Frame(ops_frame, bg=COR_PAINEL)
        col_b.pack(side='left', fill='x', expand=True)

        self.lbl_b = tk.Label(col_b, text="▸ OPERANDO  B",
                              font=('Courier New', 8, 'bold'), fg=COR_ACCENT, bg=COR_PAINEL)
        self.lbl_b.pack(anchor='w')
        self.var_b = tk.StringVar()
        self.entry_b = self._campo(col_b, self.var_b, width=18)
        self.entry_b.pack(anchor='w', pady=(4, 0))

        tk.Frame(inner, bg=COR_BORDA, height=1).pack(fill='x', pady=16)

        self.btn_calcular = tk.Button(
            inner,
            text="  ▶  CALCULAR  (ENVIAR AO SERVIDOR)  ",
            font=('Courier New', 11, 'bold'),
            bg=COR_BTN, fg=COR_BTN_FG,
            activebackground='#00b8d4', activeforeground=COR_BTN_FG,
            relief='flat', cursor='hand2', bd=0,
            command=self._enviar_requisicao
        )
        self.btn_calcular.pack(fill='x', ipady=10)

        # Resp
        resp_frame = tk.Frame(self.root, bg=COR_PAINEL, bd=0,
                              highlightthickness=1, highlightbackground=COR_BORDA)
        resp_frame.pack(fill='x', padx=24, pady=(10, 0))

        resp_inner = tk.Frame(resp_frame, bg=COR_PAINEL)
        resp_inner.pack(fill='x', padx=20, pady=16)

        tk.Label(resp_inner, text="▸ RESULTADO DO SERVIDOR",
                 font=('Courier New', 8, 'bold'), fg=COR_ACCENT2, bg=COR_PAINEL
                 ).pack(anchor='w')

        self.lbl_resultado = tk.Label(
            resp_inner, text="---",
            font=FONTE_GRANDE, fg=COR_TEXTO_DIM, bg=COR_PAINEL,
            anchor='w'
        )
        self.lbl_resultado.pack(anchor='w', pady=(8, 4))

        self.lbl_expressao = tk.Label(
            resp_inner, text="Nenhuma operação realizada.",
            font=('Courier New', 9), fg=COR_TEXTO_DIM, bg=COR_PAINEL, anchor='w'
        )
        self.lbl_expressao.pack(anchor='w')

        # Log de atv
        log_frame = tk.Frame(self.root, bg=COR_PAINEL, bd=0,
                             highlightthickness=1, highlightbackground=COR_BORDA)
        log_frame.pack(fill='both', expand=True, padx=24, pady=(10, 24))

        log_header = tk.Frame(log_frame, bg=COR_PAINEL)
        log_header.pack(fill='x', padx=12, pady=(10, 0))

        tk.Label(log_header, text="▸ LOG DE ATIVIDADE DO CLIENTE",
                 font=('Courier New', 8, 'bold'), fg=COR_ACCENT2, bg=COR_PAINEL
                 ).pack(side='left')

        btn_limpar = tk.Button(
            log_header, text="LIMPAR", font=('Courier New', 7),
            bg=COR_BORDA, fg=COR_LABEL, relief='flat', cursor='hand2', bd=0,
            command=self._limpar_log
        )
        btn_limpar.pack(side='right')

        self.txt_log = tk.Text(
            log_frame, height=7, font=('Courier New', 9),
            bg=COR_INPUT_BG, fg=COR_TEXTO, insertbackground=COR_ACCENT,
            relief='flat', bd=0, state='disabled',
            wrap='word', padx=10, pady=8
        )
        self.txt_log.pack(fill='both', expand=True, padx=12, pady=(6, 12))

        self.txt_log.tag_config('ok',    foreground=COR_OK)
        self.txt_log.tag_config('erro',  foreground=COR_ERRO)
        self.txt_log.tag_config('info',  foreground=COR_ACCENT)
        self.txt_log.tag_config('send',  foreground='#ffd700')
        self.txt_log.tag_config('dim',   foreground=COR_TEXTO_DIM)

        # Footer
        rodape = tk.Frame(self.root, bg=COR_FUNDO)
        rodape.pack(fill='x', padx=24, pady=(0, 8))
        tk.Label(
            rodape,
            text=f"Socket: AF_INET / SOCK_STREAM  ·  Síncrono  ·  {SERVER_HOST}:{SERVER_PORT}",
            font=('Courier New', 7), fg=COR_TEXTO_DIM, bg=COR_FUNDO
        ).pack(anchor='w')

        self._ao_mudar_op()
        self._registrar_log("Sistema iniciado. Servidor alvo: "
                            f"{SERVER_HOST}:{SERVER_PORT}", 'info')

    def _campo(self, parent, textvariable, width=20):
        return tk.Entry(
            parent, textvariable=textvariable,
            font=FONTE_MONO, width=width,
            bg=COR_ENTRADA, fg=COR_TEXTO,
            insertbackground=COR_ACCENT,
            relief='flat', bd=0,
            highlightthickness=1,
            highlightbackground=COR_BORDA,
            highlightcolor=COR_ACCENT
        )

    def _estilizar_combo(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TCombobox',
                        fieldbackground=COR_ENTRADA,
                        background=COR_BORDA,
                        foreground=COR_TEXTO,
                        selectbackground=COR_ACCENT,
                        selectforeground=COR_BTN_FG,
                        bordercolor=COR_BORDA,
                        arrowcolor=COR_ACCENT)

    # UI Design
    def _ao_mudar_op(self, event=None):
        op_label = self.var_op.get()
        codigo   = CODIGOS_OP.get(op_label, '')
        usa_b    = codigo not in OP_SEM_B

        estado = 'normal' if usa_b else 'disabled'
        self.entry_b.config(state=estado)

        if not usa_b:
            self.var_b.set('')
            self.lbl_b.config(fg=COR_TEXTO_DIM)
        else:
            self.lbl_b.config(fg=COR_ACCENT)

    def _centralizar_janela(self, largura, altura):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - largura) // 2
        y  = (sh - altura)  // 2
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

    # Registro
    def _registrar_log(self, mensagem, tag='dim'):
        import datetime
        agora = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.config(state='normal')
        self.txt_log.insert('end', f"[{agora}] {mensagem}\n", tag)
        self.txt_log.see('end')
        self.txt_log.config(state='disabled')

    def _limpar_log(self):
        self.txt_log.config(state='normal')
        self.txt_log.delete('1.0', 'end')
        self.txt_log.config(state='disabled')

    # Validar Entradas
    def _validar_entradas(self):
        op_label = self.var_op.get()
        codigo   = CODIGOS_OP.get(op_label)

        if not op_label or not codigo:
            messagebox.showerror("Erro de Entrada", "Selecione uma operação válida.")
            return None, None, None

        val_a = self.var_a.get().strip().replace(',', '.')
        val_b = self.var_b.get().strip().replace(',', '.')

        try:
            a = float(val_a)
        except ValueError:
            messagebox.showerror("Erro de Entrada",
                                 "O campo 'Operando A' deve conter um número válido.")
            return None, None, None

        b = 0.0
        if codigo not in OP_SEM_B:
            try:
                b = float(val_b)
            except ValueError:
                messagebox.showerror("Erro de Entrada",
                                     "O campo 'Operando B' deve conter um número válido.")
                return None, None, None

        return codigo, a, b

    # Comunica TCP/IP
    def _enviar_requisicao(self):
        codigo, a, b = self._validar_entradas()
        if codigo is None:
            return

        host  = self.var_host.get().strip()
        porta_str = self.var_porta.get().strip()

        try:
            porta = int(porta_str)
        except ValueError:
            messagebox.showerror("Erro de Configuração", "A porta deve ser um número inteiro.")
            return

        payload = json.dumps({'operacao': codigo, 'a': a, 'b': b}, ensure_ascii=False)
        self._registrar_log(f"→ Conectando a {host}:{porta}...", 'info')
        self._registrar_log(f"→ Enviando: {payload}", 'send')

        # Desabilita o botão durante o ciclo
        self.btn_calcular.config(state='disabled', text="  ◌  AGUARDANDO SERVIDOR...")
        self.root.update()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(8)                   # timeout de 8 segundos
                s.connect((host, porta))
                s.sendall(payload.encode('utf-8'))

                resposta_raw = s.recv(4096).decode('utf-8')

            # Processa resposta
            resposta = json.loads(resposta_raw)
            self._registrar_log(f"← Recebido : {resposta_raw}", 'ok')

            if resposta.get('status') == 'ok':
                resultado  = resposta.get('resultado', '?')
                expressao  = resposta.get('expressao', '')
                self.lbl_resultado.config(text=str(resultado), fg=COR_OK)
                self.lbl_expressao.config(
                    text=f"Expressão: {expressao} = {resultado}",
                    fg=COR_TEXTO
                )
                self._registrar_log(
                    f"✓ Resultado: {expressao} = {resultado}", 'ok')
            else:
                msg_erro = resposta.get('mensagem', 'Erro desconhecido.')
                self.lbl_resultado.config(text="ERRO", fg=COR_ERRO)
                self.lbl_expressao.config(text=f"Servidor retornou: {msg_erro}", fg=COR_ERRO)
                self._registrar_log(f"✗ Erro do servidor: {msg_erro}", 'erro')

        except ConnectionRefusedError:
            self._registrar_log("✗ Conexão recusada — servidor indisponível.", 'erro')
            self.lbl_resultado.config(text="SEM RESP.", fg=COR_ERRO)
            self.lbl_expressao.config(text="Falha ao conectar ao servidor.", fg=COR_ERRO)
            messagebox.showerror(
                "Falha de Conexão",
                f"Falha de conexão: O servidor encontra-se indisponível.\n\n"
                f"Verifique se o servidor está em execução em:\n"
                f"  {host}:{porta}"
            )

        except socket.timeout:
            self._registrar_log("✗ Tempo esgotado — servidor não respondeu.", 'erro')
            self.lbl_resultado.config(text="TIMEOUT", fg=COR_ERRO)
            self.lbl_expressao.config(text="O servidor não respondeu a tempo.", fg=COR_ERRO)
            messagebox.showerror(
                "Tempo Esgotado",
                "Falha de conexão: O servidor não respondeu dentro do tempo limite (8s).\n\n"
                "O servidor pode estar sobrecarregado ou inacessível."
            )

        except OSError as e:
            self._registrar_log(f"✗ Erro de rede: {e}", 'erro')
            self.lbl_resultado.config(text="ERRO", fg=COR_ERRO)
            messagebox.showerror(
                "Erro de Rede",
                f"Falha de conexão: O servidor encontra-se indisponível.\n\nDetalhe: {e}"
            )

        finally:
            self.btn_calcular.config(
                state='normal',
                text="  ▶  CALCULAR  (ENVIAR AO SERVIDOR)  "
            )

if __name__ == '__main__':
    root = tk.Tk()
    app  = CalculadoraClienteApp(root)
    root.mainloop()