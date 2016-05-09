<h1>Servidor FTP (File Transfer Protocol)</h1>

Projeto da disciplina Redes de Computadores do curso Superior de <a href="http://www.barbacena.ifsudestemg.edu.br/tsi">Tecnologia em Sistemas para Internet</a> pelo <a href="http://www.barbacena.ifsudestemg.edu.br/">Instituto Federal do Sudeste de Minas Gerais - <em>Campus</em> Barbacena</a>.

Autor: <a href="https://github.com/marlucioapires">Marlúcio Alves Pires</a> (<em><a href="http://lattes.cnpq.br/9893409194805043">Lattes</a></em>)

Semestre: primeiro semestre de 2016.

Prof.: <a href="https://github.com/rafjaa">Rafael José de Alencar Almeida</a> (<em><a href="http://lattes.cnpq.br/3995585094514614">Lattes</a></em>)

<h2>Descrição do Projeto</h2>
<p>Servidor FTP que implementa as seguintes funcionalidades:</p>
<ul>
	<li>Receber conexões autenticadas e anônimas;</li>
	<li>Responder às seguintes requisições do cliente:</li>
	<div>
		<ol>
			<li>Enviar um arquivo para o cliente;</li>
			<li>Receber um arquivo do cliente;</li>
			<li>Listar os arquivos e pastas do diretório corrente;</li>
			<li>Criar um diretório;</li>
			<li>Remover um diretório (recursivamente);</li>
			<li>Remover um arquivo;</li>
			<li>Acessar outro diretório.</li>
		</ol>
	</div>
</ul>

<h2>Como Usar</h2>
<p>Siga os passos abaixo:</p>
<ol>
	<li>Baixe os arquivos do projeto para um diretório em seu computador (descompactando se necessário);</li>
	<li>Delete o arquivo <strong>"usuarios_e_senhas.txt"</strong>;</li>
	<li>Execute o programa <strong>"acesso.py"</strong> para cadastrar os acessos (usuário e senha);</li>
	<li>Execute o programa <strong>"servidor_ftp.py"</strong>;</li>
	<li>Utilize algum programa cliente FTP (p. ex. <a href="https://filezilla-project.org/">FileZilla</a>) para testar o servidor;</li>
	<li>Configure no cliente FTP: o IP do Servidor, a porta 8888, o usuário e a senha cadastrados. <strong>Obs.:</strong> O Servidor aceita conexões anônimas (USER anonymous).</li>
</ol>
