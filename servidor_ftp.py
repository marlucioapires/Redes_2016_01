# coding: utf-8

import os
import socket

allow_delete = False
local_ip = socket.gethostbyname(socket.gethostname())
local_ip = ''
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
		lista = comando.split(' ')
		if len(lista) > 1:
			if lista[1] == 'anonymous':
				mensagem = '331 Usuário anonymous ok. Informe o seu e-mail completo como a sua senha.\n'
			else:
				mensagem = '331 Informe a senha para o usuário %s.\n' % lista[1]
		else:
			mensagem = '501 Erro de sintaxe no comando USER. Parâmetro inválido.\n'
		self.msg(mensagem)

	def QUIT(self, comando):
		self.msg('221 Adeus.\n')

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((local_ip, local_port))
	sock.listen(1)
	while True:
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