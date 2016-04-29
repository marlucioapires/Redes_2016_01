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
		print '[' + reply + ']'
		return reply

	def msg(self, mensagem):
		self.conn.send(str(mensagem) + '\n')

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((local_ip, local_port))
	sock.listen(1)
	while True:
		ftp = ConexaoFTP(sock.accept())
		dados = ftp.le_comando()
		print dados
		ftp.encerra()

if __name__=='__main__':
	main()