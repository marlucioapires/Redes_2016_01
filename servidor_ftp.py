# coding: utf-8

import os
import socket

allow_delete = False
local_ip = socket.gethostbyname(socket.gethostname())
local_port = 8888
currdir = os.path.abspath('.')
print currdir
EOL = '\n'

class ConexaoFTP():
	def __init__(self, (conn, addr), timeout = 100):
		self.conn = conn
		self.conn.settimeout(timeout)
		self.timeout = timeout
		self.addr = addr
		self.basewd = currdir
		self.cwd = self.basewd
		self.pasv_mode = False
		self.logged = False
		print 'Conectado ao cliente (IP): %s' % str(addr)

	def encerra(self):
		self.conn.close()

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
					print 'Tempo de leitura (' + str(self.timeout) + ' segundos) do socket expirado!'
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
		self.conn.send(str(mensagem) + '\n')

	def processa_comando(self, comando):
		try:
			#print comando.split(' ')[0]
			funcao = getattr(self, comando.split(' ')[0].upper())
			funcao(comando)
		except Exception, e:
			print 'ERROR:', e
			self.msg('500 Comando não reconhecido.\n')

	def USER(self, comando):
		# Falta implementar!
		lista = comando.split(' ')
		if len(lista) > 1:
			if lista[1] == 'anonymous':
				mensagem = '331 Usuário anonymous ok. Informe o seu e-mail completo como a sua senha.\n'
			else:
				mensagem = '331 Informe a senha para o usuário %s.\n' % lista[1]
		else:
			mensagem = '501 Erro de sintaxe no comando USER. Parâmetro inválido.\n'
		self.msg(mensagem)

	def PASS(self,cmd):
		# Falta implementar!
		self.msg('230 Senha OK.\n')
		self.logged = True

	def PASV(self,cmd):
		if self.logged:
			self.pasv_mode = True
			self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			self.servsock.bind((local_ip, 0)) # Requisita uma porta livre do S.O.
			self.servsock.listen(1)
			ip, porta_dados = self.servsock.getsockname()
			print 'Conexão de dados aberta', ip, porta_dados
			self.conn.send('227 Entrando em modo passivo (%s,%u,%u).\n' %
				(','.join(ip.split('.')), porta_dados>>8&0xFF, porta_dados&0xFF))

	def QUIT(self, comando):
		self.msg('221 Adeus.\n')

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print 'IP: %s, porta: %u' % (local_ip, local_port)
	sock.bind(('', local_port))
	sock.listen(1)
	while True:
		print 'Aguardando conexão...'
		ftp = ConexaoFTP(sock.accept())
		ftp.msg('220 Bem-vindo ao servidor FTP!\n')
		while True:
			comando = ftp.le_comando()
			if not comando:
				break
			else:
				print 'Recebido:', comando
				ftp.processa_comando(comando)
			if comando.split(' ')[0].upper() == 'QUIT':
				break
			comando = ''
		ftp.encerra()

if __name__=='__main__':
	main()