# coding: utf-8

import acesso
import os
import shutil
import socket
import threading
import time

local_ip = socket.gethostbyname(socket.gethostname())
local_port = 8888
diretorio_raiz = os.path.abspath('./raiz')
print diretorio_raiz
EOL = '\n'
chave_publica = None

def extrai_parametro(comando):
	pos = comando.find(' ')
	parametro = ''
	if pos != -1:
		parametro = comando[pos:].strip()
	return parametro

class ServidorFTPThread(threading.Thread):
	def __init__(self, (conn, addr), timeout = 100):
		self.conn = conn
		self.conn.settimeout(timeout)
		self.timeout = timeout
		self.addr = addr
		self.basewd = diretorio_raiz
		self.cwd = self.basewd
		self.pasv_mode = False
		self.logged = False
		self.sock_dados = None
		self.conn_dados = None
		self.esta_ativo = True
		self.user = None
		self.dicionario_usuarios_e_senhas = {}
		print 'Conectado ao cliente (IP): %s\n' % str(addr)
		threading.Thread.__init__(self)

	def run(self):
		self.msg('220 Bem-vindo ao servidor FTP!')
		while self.ativo():
			cmd = self.conn.recv(1024).strip()
			if not cmd: break
			else:
				print 'Recebido:', cmd
				try:
					func = getattr(self, cmd.split(' ')[0].upper())
					func(cmd)
				except Exception,e:
					print 'ERROR:', e
					#traceback.print_exc()
					self.conn.send('500 Sorry.\r\n')

	def msg(self, mensagem):
		self.conn.send(str(mensagem) + '\n')

	def enviar_dados(self, dados):
		self.conn_dados.send(str(dados) + '\n')

	def ativo(self):
		return self.esta_ativo

	def encerra(self):
		self.fechar_conexao_de_dados()
		self.conn.close()
		self.esta_ativo = False

	def processa_comando(self, comando):
		try:
			funcao = getattr(self, comando.split(' ')[0].upper())
			funcao(comando)
		except Exception, e:
			print 'ERRO:', e
			self.msg('500 Comando "%s" não reconhecido.' % comando)

	def USER(self, comando):
		if not self.logged:
			lista = comando.split(' ')
			if len(lista) > 1:
				self.user = lista[1]
				if self.user == 'anonymous':
					mensagem = '331 Usuário "anonymous" OK. Informe o seu e-mail completo como a sua senha.'
				else:
					mensagem = '331 Informe a senha para o usuário "%s".' % self.user
			else:
				mensagem = '501 Parâmetro inválido. Sintaxe: USER <username>'
		else:
			mensagem = '500 Sequência errada de comandos.'
		self.msg(mensagem)

	def atualizar_dicionario_de_senhas(self):
		self.dicionario_usuarios_e_senhas = acesso.ler_usuarios_e_senhas()

	def PASS(self, comando):
		if not self.logged:
			if self.user:
				lista = comando.split(' ')
				if len(lista) > 1:
					senha = lista[1]
					if self.user == 'anonymous':
						self.logged = True
					else:
						self.atualizar_dicionario_de_senhas()
						if self.dicionario_usuarios_e_senhas.has_key(self.user):
							if acesso.criptografar_senha(chave_publica, senha) == self.dicionario_usuarios_e_senhas[self.user]:
								self.logged = True
					if self.logged:
						mensagem = '230 Senha OK. Usuário "%s" logado.' % self.user
					else:
						mensagem = '530 Usuário e/ou senha incorretos.'
				else:
					mensagem = '501 Parâmetro inválido. Sintaxe: PASS <password>'
			else:
				mensagem = '503 Utilize o comando USER antes.'
		else:
			mensagem = '500 Sequência errada de comandos.'
		self.msg(mensagem)

	def NOOP(self, cmd):
		self.msg('200 OK.')

	def envia_msg_comando_nao_implementado(self):
		self.msg('202 Comando não implementado, supérfluo a este servidor FTP.')

	def TYPE(self,cmd):
		self.envia_msg_comando_nao_implementado()

	def abrir_conexao_de_dados(self):
		if self.pasv_mode:
			self.sock_dados = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock_dados.bind(('', 0)) # Requisita uma porta livre do S.O.
			self.sock_dados.listen(1)
			porta_dados = self.sock_dados.getsockname()[1]
			print 'Conexão de dados aberta:', local_ip, porta_dados
			return porta_dados

	def iniciar_conexao_de_dados(self):
		if self.pasv_mode:
			self.conn_dados, addr = self.sock_dados.accept()
			print 'CONEXÃO DE DADOS: Conectado ao cliente (IP): %s' % str(addr)

	def fechar_conexao_de_dados(self):
		if self.pasv_mode:
			if self.conn_dados:
				self.conn_dados.close() # Fecha a conexão de dados.
				self.conn_dados = None
			if self.sock_dados:
				self.sock_dados.close() # Libera o socket de dados.
				self.sock_dados = None
			self.pasv_mode = False

	def PASV(self, comando):
		if self.logged:
			self.pasv_mode = True
			porta_dados = self.abrir_conexao_de_dados()
			self.msg('227 Entrando em modo passivo (%s,%u,%u).\n' %
				(','.join(local_ip.split('.')), porta_dados>>8&0xFF, porta_dados&0xFF))
		else:
			self.msg('530 Realize o login antes (comandos USER e PASS).')

	def toListItem(self, fn): # Copiado da Internet.
		st = os.stat(fn)
		fullmode = 'rwxrwxrwx'
		mode = ''
		for i in range(9):
			mode += ((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
		d = (os.path.isdir(fn)) and 'd' or '-'
		ftime = time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
		return d + mode + ' 1 user group ' + str(st.st_size) + ftime + os.path.basename(fn)

	def LIST(self, comando):
		if self.logged:
			if self.pasv_mode:
				self.msg('150 Enviando listagem de diretório.')
				print 'LIST:', self.cwd
				self.iniciar_conexao_de_dados()
				for t in os.listdir(self.cwd):
					k = self.toListItem(os.path.join(self.cwd, t))
					self.conn_dados.send(k + '\r\n')
				self.fechar_conexao_de_dados()
				mensagem = '226 Listagem de diretório enviada.'
			else:
				mensagem = '502 Entre no modo passivo.'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def atualiza_caminho(self, caminho):
		if caminho[0] == '/':
			diretorio_atual = self.basewd
		else:
			diretorio_atual = self.cwd
		for c in caminho.strip().split('/'):
			diretorio = os.path.abspath(os.path.join(diretorio_atual, c))
			if os.path.isdir(diretorio): # Verifica se é um diretório válido.
				# A seguir, verifica-se se está acessando diretório acima do raiz.
				if diretorio.find(self.basewd) == 0:
					diretorio_atual = diretorio
				else:
					diretorio_atual = self.basewd
			else:
				return False
		self.cwd = diretorio_atual
		return True

	def CWD(self, comando):
		if self.logged:
			pathname = extrai_parametro(comando)
			if pathname:
				if pathname == '/': # Alterar para o diretório raiz.
					self.cwd = self.basewd
					mensagem = '250 Comando "%s" OK.' % comando
				else:
					if self.atualiza_caminho(pathname):
						mensagem = '250 Comando "%s" OK.' % comando
					else:
						mensagem = '550 Diretório "%s" não localizado.' % pathname
			else:
				mensagem = '501 Parâmetro inválido. Sintaxe: CWD <pathname>'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def caminho_relativo(self, caminho, raiz):
		cwd = os.path.relpath(caminho, raiz)
		if cwd == '.':
			cwd = '/'
		else:
			cwd = '/' + cwd
		return cwd

	def PWD(self, comando):
		if self.logged:
			mensagem = '257 Diretório corrente: "%s"' % self.caminho_relativo(self.cwd, self.basewd)
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def MKD(self, comando):
		if self.logged:
			pathname = extrai_parametro(comando)
			if pathname and pathname != '/':
				if pathname[-1] == '/':
					pathname = pathname[:-1]
				pos = pathname.rfind('/')
				if pos == -1:
					caminho = ' '
				elif pos == 0:
					caminho = '/'
				else:
					caminho = pathname[:pos]
				nome_dir = pathname[(pos + 1):]
				salva_cwd = self.cwd
				if self.atualiza_caminho(caminho):
					caminho_completo = os.path.join(self.cwd, nome_dir)
					try:
						os.mkdir(caminho_completo)
						mensagem = '257 Diretório "%s" criado com sucesso.' % self.caminho_relativo(caminho_completo, self.basewd)
					except Exception, e:
						mensagem = '550 Falha ao criar diretório "%s"' % self.caminho_relativo(caminho_completo, self.basewd)
					self.cwd = salva_cwd
				else:
					mensagem = '550 Falha ao criar diretório "%s"' % pathname
			else:
				mensagem = '501 Parâmetro inválido. Sintaxe: MKD <pathname>'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def RMD(self, comando):
		if self.logged:
			pathname = extrai_parametro(comando)
			if pathname and pathname != '/':
				if pathname[-1] == '/':
					pathname = pathname[:-1]
				pos = pathname.rfind('/')
				if pos == -1:
					caminho = ' '
				elif pos == 0:
					caminho = '/'
				else:
					caminho = pathname[:pos]
				nome_dir = pathname[(pos + 1):]
				salva_cwd = self.cwd
				if self.atualiza_caminho(caminho):
					caminho_completo = os.path.join(self.cwd, nome_dir)
					try:
						shutil.rmtree(caminho_completo)
						mensagem = '250 Diretório "%s" removido.' % self.caminho_relativo(caminho_completo, self.basewd)
					except Exception, e:
						mensagem = '550 Falha ao remover o diretório "%s"' % self.caminho_relativo(caminho_completo, self.basewd)
					self.cwd = salva_cwd
				else:
					mensagem = '550 Diretório "%s" não localizado.' % pathname
			else:
				mensagem = '501 Parâmetro inválido. Sintaxe: MKD <pathname>'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def DELE(self, comando):
		if self.logged:
			pathname = extrai_parametro(comando)
			if pathname and pathname != '/' and pathname[-1] != '/':
				pos = pathname.rfind('/')
				if pos == -1:
					caminho = ' '
				elif pos == 0:
					caminho = '/'
				else:
					caminho = pathname[:pos]
				nome_arq = pathname[(pos + 1):]
				salva_cwd = self.cwd
				if self.atualiza_caminho(caminho):
					caminho = os.path.join(self.cwd, nome_arq)
					if os.path.isfile(caminho):
						os.remove(caminho)
						mensagem = '250 Arquivo deletado.\r\n'
					else:
						mensagem = '550 Arquivo "%s" não localizado.' % nome_arq
					self.cwd = salva_cwd
				else:
					mensagem = '550 Arquivo "%s" não localizado.' % nome_arq
			else:
				mensagem = '501 Parâmetro inválido. Sintaxe: DELE <pathname>'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def RETR(self, comando):
		if self.logged:
			if self.pasv_mode:
				pathname = extrai_parametro(comando)
				if pathname and pathname != '/' and pathname[-1] != '/':
					pos = pathname.rfind('/')
					if pos == -1:
						caminho = ' '
					elif pos == 0:
						caminho = '/'
					else:
						caminho = pathname[:pos]
					nome_arq = pathname[(pos + 1):]
					salva_cwd = self.cwd
					if self.atualiza_caminho(caminho):
						if os.path.isfile(os.path.join(self.cwd, nome_arq)):
							arquivo = open(os.path.join(self.cwd, nome_arq), 'r')
							print 'Downloading:', arquivo
							self.msg('150 Enviando arquivo.')
							self.iniciar_conexao_de_dados()
							dados = arquivo.read(1024)
							while dados:
								self.enviar_dados(dados)
								dados = arquivo.read(1024)
							arquivo.close()
							self.fechar_conexao_de_dados()
							mensagem = '226 Transferência completa.\r\n'
						else:
							mensagem = '550 Arquivo "%s" não localizado.' % os.path.join(self.cwd, nome_arq)
						self.cwd = salva_cwd
					else:
						mensagem = '550 Caminho do arquivo ("%s") não localizado.' % caminho
				else:
					mensagem = '501 Parâmetro inválido. Sintaxe: RETR <pathname>'
			else:
				mensagem = '502 Entre no modo passivo.'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def STOR(self, comando):
		if self.logged:
			if self.pasv_mode:
				pathname = extrai_parametro(comando)
				if pathname and pathname != '/' and pathname[-1] != '/':
					pos = pathname.rfind('/')
					if pos == -1:
						caminho = ' '
					elif pos == 0:
						caminho = '/'
					else:
						caminho = pathname[:pos]
					nome_arq = pathname[(pos + 1):]
					salva_cwd = self.cwd
					if self.atualiza_caminho(caminho):
						if os.path.isdir(self.cwd):
							arquivo = open(os.path.join(self.cwd, nome_arq), 'w')
							print 'Uploading:', arquivo
							self.msg('150 Abrindo conexão de dados para recebimento do arquivo.')
							self.iniciar_conexao_de_dados()
							while True:
								dados = self.conn_dados.recv(1024)
								if not dados: break
							arquivo.write(dados)
							arquivo.close()
							self.fechar_conexao_de_dados()
							mensagem = '226 Transferência completa.\r\n'
						else:
							mensagem = '550 Diretório "%s" não localizado.' % self.cwd
						self.cwd = salva_cwd
					else:
						mensagem = '550 Diretório "%s" não localizado.' % caminho
				else:
					mensagem = '501 Parâmetro inválido. Sintaxe: STOR <pathname>'
			else:
				mensagem = '502 Entre no modo passivo.'
		else:
			mensagem = '530 Realize o login antes (comandos USER e PASS).'
		self.msg(mensagem)

	def QUIT(self, comando):
		self.msg('221 Adeus.')
		self.encerra()

class ServidorFTP(threading.Thread):
	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('', local_port))
		threading.Thread.__init__(self)

	def run(self):
		self.sock.listen(1)
		while True:
			print 'Aguardando conexão...'
			th = ServidorFTPThread(self.sock.accept())
			th.daemon = True
			th.start()

	def encerra(self):
		self.sock.close()

def configuracoes_iniciais():
	global chave_publica
	chave_publica = acesso.recuperar_chave_publica()
	if not os.path.isdir(diretorio_raiz):
		try:
			os.mkdir(diretorio_raiz)
			print 'Diretório raiz (./raiz) não existia e foi criado.'
		except Exception, e:
			print 'ERRO: Não foi possível criar o diretório raiz (./raiz).'
	else:
		print 'Diretório raiz (./raiz) já existe.'

if __name__ == '__main__':
	configuracoes_iniciais()
	ftp = ServidorFTP()
	ftp.daemon = True
	ftp.start()
	print 'IP Local', local_ip, ', PORTA:', local_port
	raw_input('ENTER para finalizar...\n')
	ftp.encerra()