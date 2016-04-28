# coding: utf-8

import os
import socket
import time

allow_delete = False
local_ip = socket.gethostbyname(socket.gethostname())
local_port = 8888
diretorio_raiz = os.path.abspath('./raiz')
print diretorio_raiz
EOL = '\n'

def extrai_parametro(comando):
	pos = comando.find(' ')
	parametro = ''
	if pos != -1:
		parametro = comando[pos:].strip()
	return parametro

class ConexaoFTP():
	def __init__(self, (conn, addr), timeout = 1000):
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
		print 'Conectado ao cliente (IP): %s\n' % str(addr)

	def ativo(self):
		return self.esta_ativo

	def encerra(self):
		self.fechar_conexao_de_dados()
		self.conn.close()
		self.esta_ativo = False

	def le_comando(self):
		reply = ''
		while True:
			try:
				reply += self.conn.recv(1024)
				if reply[-1] == EOL:
					break
			except socket.timeout, e:
				err = e.args[0]
				# this next if/else is a bit redundant, but illustrates how the
				# timeout exception is setup
				if err == 'timed out':
					print 'Tempo de espera (' + str(self.timeout) + ' segundos) do socket expirado!'
					self.msg('421 Tempo de espera (' + str(self.timeout) + ' segundos) expirado. Conexão de controle encerrada.')
					break
				else:
					print e
					break
			except socket.error, e:
				# Something else happened, handle error, exit, etc.
				print e
				break
		print '[' + reply.strip() + ']'
		return reply.strip()

	def msg(self, mensagem):
		self.conn.send(str(mensagem) + '\r\n')

	def enviar_dados(self, dados):
		self.conn_dados.send(str(dados) + '\r\n')	

	def processa_comando(self, comando):
		try:
			#print comando.split(' ')[0]
			funcao = getattr(self, comando.split(' ')[0].upper())
			funcao(comando)
		except Exception, e:
			print 'ERROR:', e
			self.msg('500 Comando não reconhecido.')

	def abrir_conexao_de_dados(self):
		if self.pasv_mode:
			self.sock_dados = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock_dados.bind(('', 0)) # Requisita uma porta livre do S.O.
			self.sock_dados.listen(1)
			#ip, porta_dados = self.sock_dados.getsockname()
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
				self.sock_dados.close() # Fecha a conexão de dados.
				self.sock_dados = None
			self.pasv_mode = False

	def USER(self, comando):
		# Falta implementar!
		lista = comando.split(' ')
		if len(lista) > 1:
			if lista[1] == 'anonymous':
				mensagem = '331 Usuário anonymous ok. Informe o seu e-mail completo como a sua senha.'
			else:
				mensagem = '331 Informe a senha para o usuário %s.' % lista[1]
		else:
			mensagem = '501 Erro de sintaxe no comando USER. Parâmetro inválido.'
		self.msg(mensagem)

	def PASS(self, comando):
		# Falta implementar!
		self.msg('230 Senha OK.')
		self.logged = True

	def PASV(self, comando):
		if self.logged:
			self.pasv_mode = True
			porta_dados = self.abrir_conexao_de_dados()
			self.msg('227 Entrando em modo passivo (%s,%u,%u).\n' %
				(','.join(local_ip.split('.')), porta_dados>>8&0xFF, porta_dados&0xFF))
		else:
			# Usuário deve estar logado! Enviar mensagem de erro.
			pass

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
				self.msg('226 Listagem de diretório enviada.')
			else:
				# Deve-se entrar em modo passivo primeiro! Enviar mensagem de erro.
				pass
		else:
			# Usuário deve estar logado! Enviar mensagem de erro.
			pass

	def CWD(self, comando):
		pathname = extrai_parametro(comando)
		if pathname:
			if pathname == '/': # Alterar para o diretório raiz.
				self.cwd = self.basewd
				mensagem = '250 Comando %s OK.' % comando
			else:
				if pathname[0] == '/':
					diretorio = os.path.abspath(os.path.join(self.basewd, pathname[1:]))
				else:
					diretorio = os.path.abspath(os.path.join(self.cwd, pathname))
				if os.path.isdir(diretorio): # Verifica se é um diretório válido.
					# A seguir, verifica-se se está acessando diretório acima do raiz.
					if diretorio.find(self.basewd) == 0:
						self.cwd = diretorio
					else:
						self.cwd = self.basewd
					mensagem = '250 Comando %s OK.' % comando
				else:
					mensagem = '550 %s: Diretório não localizado.' % pathname
		else:
			# Parâmetro inválido. Enviar mensagem de erro.
			mensagem = 'Parâmetro inválido.'
		self.msg(mensagem)

	def MKD(self, comando):
		pathname = extrai_parametro(comando)
		if pathname:
			caminho = pathname
			diretorio = pathname
			nome_dir = ''
			if pathname != '/':
				if pathname[0] == '/':
					diretorio = os.path.abspath(os.path.join(self.basewd, pathname[1:]))
				else:
					diretorio = os.path.abspath(os.path.join(self.cwd, pathname))
				pos = diretorio.rfind('/')
				caminho = diretorio[:pos]
				if pos != (len(diretorio) - 1):
					nome_dir = diretorio[(pos + 1):]
			if os.path.isdir(caminho) and nome_dir: # Verifica se é um diretório válido.
				# A seguir, verifica-se se está acessando diretório acima do raiz.
				if caminho.find(self.basewd) != 0:
					caminho = self.basewd
				diretorio = os.path.join(caminho, nome_dir)
				try:			
					os.mkdir(diretorio)
					mensagem = '257 Diretório criado com sucesso.'
				except Exception, e:
					mensagem = '550 Falha ao criar diretório \'%s\'' % diretorio
			else:
				mensagem = '550 Falha ao criar diretório \'%s\'' % diretorio
		else:
			# Parâmetro inválido. Enviar mensagem de erro.
			mensagem = '501 Parâmetro inválido. Sintaxe: MKD <pathname>'
		self.msg(mensagem)

	def QUIT(self, comando):
		self.msg('221 Adeus.')
		self.encerra()

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print 'IP: %s, porta: %u' % (local_ip, local_port)
	sock.bind(('', local_port))
	sock.listen(1)
	while True:
		print 'Aguardando conexão...'
		ftp = ConexaoFTP(sock.accept())
		ftp.msg('220 Bem-vindo ao servidor FTP!')
		while ftp.ativo():
			comando = ftp.le_comando()
			if not comando:
				ftp.encerra()
			else:
				print 'Recebido:', comando
				ftp.processa_comando(comando)

if __name__=='__main__':
	main()