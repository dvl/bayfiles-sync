#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bayfiles import BayFiles

if __name__ == "__main__":
	bf = BayFiles()

	print "[*] Iniciando o script de correção de links"
	print "[!] Logado como %s" % bf.config['bayfiles']['username']
	if '--skip-upload' not in sys.argv and '-s' not in sys.argv:
		bf.get_local()
		print "[!] Preparando os arquivos locais..."
		bf.get_remote()
		print "[!] Preparando os arquivos remotos..."
		print "[!] Total de %r arquivos locais e %r remotos" % (len(bf.local), len(bf.remote))
		bf.compare()
		print "[!] Uploads finalizandos, %d arquivos upados" % bf.count
	# print "[!] Atualizando banco de dados com os links"
	# bf.sync()
	print "[!] Script finalizado, efetuando logout!" 
	bf.logout()
