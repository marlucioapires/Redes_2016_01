# coding: utf-8

from Crypto.PublicKey import RSA
from Crypto.Util.randpool import RandomPool
import getpass
import os

ARQ_CHAVE_PUBLICA = 'chave_publica.txt'
ARQ_USUARIOS_E_SENHAS = 'usuarios_e_senhas.txt'

chave_publica = None
dicionario_usuarios_e_senhas = {}

def limpa_tela():
	os.system('cls' if os.name == 'nt' else 'clear')

def gerar_chave_publica():
	pool = RandomPool(384)
	pool.stir()
	# randfunc(n) deve retornar uma string de dados aleatórios de
	# comprimento n, no caso de RandomPool, o método get_bytes
	randfunc = pool.get_bytes
	# Tamanho da chave, em bits
	N = 1024
	# Geramos a chave (contendo a chave pública e privada):
	key = RSA.generate(N, randfunc)
	# Separando apenas a chave pública:
	pub_key = key.publickey()
	arquivo = open(ARQ_CHAVE_PUBLICA, 'w')
	arquivo.write(pub_key.exportKey())
	arquivo.close()
	return pub_key

def recuperar_chave_publica():
	if os.path.isfile(ARQ_CHAVE_PUBLICA):
		arquivo = open(ARQ_CHAVE_PUBLICA, 'r')
		chave_lida = arquivo.read()
		arquivo.close()
		pub_key = RSA.importKey(chave_lida)
		return pub_key

def ler_usuarios_e_senhas():
	dicionario = {}
	arquivo = open(ARQ_USUARIOS_E_SENHAS, 'r')
	linha = arquivo.readline()
	while linha:
		partes = linha.split('=')
		if len(partes) > 1:
			dicionario[(partes[0])] = ''.join(partes[1:]).strip()
			print partes[0]
			print ''.join(partes[1:]).strip()
		linha = arquivo.readline()
	arquivo.close()
	print 'TAMANHO DICIONARIO:', len(dicionario)
	return dicionario

def gravar_usuario_e_senha(user, senha):
	if not dicionario_usuarios_e_senhas.has_key(user):
		dicionario_usuarios_e_senhas[user] = senha
		arquivo = open(ARQ_USUARIOS_E_SENHAS, 'a')
		arquivo.write(user + '=' + senha + '\n')
		arquivo.close()

def retira_quebra_de_linha(palavra):
	return ''.join(palavra.split('\n')).strip()

def criptografar_senha(pub_key, senha):
	#print 'SENHA CRIPTOGRAFADA:', retira_quebra_de_linha(pub_key.encrypt(senha, '')[0])
	retorno = retira_quebra_de_linha(pub_key.encrypt(senha, '')[0])
	return ''.join(retorno.split('=')).strip()

def interface_acesso():
	limpa_tela()
	print '=============== CADASTRO DE USUÁRIOS ===============\n\n'
	print 'Informe os campos ou aperte ENTER para cancelar.\n\n'

def cadastrar():
	while True:
		interface_acesso()
		user = raw_input('Usuário: ')
		while user and dicionario_usuarios_e_senhas.has_key(user):
			raw_input('\n\nERRO: Usuário já cadastrado! Escolha outro nome.\n\nPressione Enter...')
			interface_acesso()
			user = raw_input('Usuário: ')
		if not user: break
		senha = getpass.getpass('\nSenha: ')
		if not senha: break
		rep_senha = getpass.getpass('\nRepita a senha: ')
		if not rep_senha: break
		if senha != rep_senha and raw_input('\n\nERRO: Senhas não conferem! Deseja tentar novamente? (S/N): ').upper() == 'N': break
		else:
			gravar_usuario_e_senha(user, criptografar_senha(chave_publica, senha))
			raw_input('\n\nSUCESSO: Usuário cadastrado!\n\nPressione Enter...')
	print '\n\nCadastro de usuários cancelado!'
	raw_input('\nPressione Enter...\n')
	limpa_tela()

if os.path.isfile(ARQ_CHAVE_PUBLICA):
	#ARQUIVO DE CHAVE PÚBLICA JÁ EXISTE!
	chave_publica = recuperar_chave_publica()
else:
	#ARQUIVO DE CHAVE PÚBLICA AINDA NÃO EXISTE!
	chave_publica = gerar_chave_publica()

if os.path.isfile(ARQ_USUARIOS_E_SENHAS):
	# ARQUIVO DE USUÁRIOS E SENHAS JÁ EXISTE!
	dicionario_usuarios_e_senhas = ler_usuarios_e_senhas()
else:
	# ARQUIVO DE USUÁRIOS E SENHAS AINDA NÃO EXISTE!
	arquivo = open(ARQ_USUARIOS_E_SENHAS, 'w')
	arquivo.close()

def main():
	cadastrar()

if __name__=='__main__':
	main()