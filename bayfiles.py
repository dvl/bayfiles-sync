#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, urllib2, poster, sys, urlparse, mysql.connector

class BayFiles:
	def __init__(self):
		# arquivos
		self.path = '/home/dvl/media'
		#self.path = 'c:/files'
		self.exts = ['.mkv', '.avi']

		# bayfiles
		self.username = 'dvl'
		self.password = '123456'

		# mysql
		self.dbhost = 'localhost'
		self.dbuser = 'root'
		self.dbpass = 'deadpool'
		#self.dbpass = 'pwned'
		self.dbname = 'cdzforever'

	def login(self):
		login = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/login/{0}/{1}'.format(self.username, self.password)))
		
		if login['error'] == '':
			return login['session']
		else:
			sys.exit('[*] Usuário e/ou senha invalido(s)')


	def get_remote(self):
		files = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/files?session={0}'.format(self.session)))

		if files['error'] == '':
			remote = []

			for key, value in files.items():
				if key != 'error':
					remote.append(value['filename'])

			remote.sort()

			return remote
		else:
			sys.exit('[*] Falha ao obter a lista de arquivos remotos')

	def get_local(self):

		local = []

		for root, dirs, files in os.walk(self.path):
			for f in files:
				name, ext = os.path.splitext(f)
				if ext in self.exts:
					local.append(os.path.join(root, f))

		local.sort()

		return local

	def compare(self):
		self.count = 0
		for self.l in self.local:
			if os.path.basename(self.l) not in self.remote:
				self.upload(self.l)
				self.count += 1

	def request_cdn(self):
		hasurl = False
		while not hasurl:
			try: 
				upload = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/file/uploadUrl?session={0}'.format(self.session)))
				hasurl = True
			except urllib2.HTTPError, e:
				print '[!] %s' % str(e.code)
			except urllib2.URLError, e:
				print '[!] %s' % str(e.reason)

		return upload

	def upload(self, filepath):
		uploaded = False
		while not uploaded:
			try:
				self.cdn = self.request_cdn()

				print "[!] Tentando efetuar upload de: %s usando CDN: %s" % (os.path.basename(filepath), urlparse.urlparse(self.cdn['uploadUrl']).hostname)

				poster.streaminghttp.register_openers()
				
				self.datagen, self.headers = poster.encode.multipart_encode({"file":open(self.l, 'rb')}, cb=self.upload_callback)
				self.request = json.load(urllib2.urlopen(urllib2.Request(self.cdn['uploadUrl'], self.datagen, self.headers)))

				if self.request['error'] == '':
					print "[!] Upload de %s efetuado, download %s" % (os.path.basename(self.l), self.request['downloadUrl'])
					uploaded = True
				else:
					print "[!] Erro durante upload: %s, reiniciando..." % request['error']

			except urllib2.HTTPError, e:
				print '[!] %s' % str(e.code)
			except urllib2.URLError, e:
				print '[!] %s' % str(e.reason)

	def upload_callback(self, param, current, total):
		self.total_datasize = total
		self.cursize = current
		self.show_progress(current, float(total))

	def show_progress(self, current, total):
		percent = (current / total) * 100

		info = "{0}/{1}MB".format(round(current/1000.0**2,2), round(total/1000.0**2,2))

		sys.stdout.write("[!] %d%% %s\r" % (percent, info))
		sys.stdout.flush()

	def dbconn(self):
		return mysql.connector.connect(user=self.dbuser, password=self.dbpass, host=self.dbhost, database=self.dbname)

	def sync(self):
		con = self.dbconn()
		cursor = con.cursor()

		files = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/files?session={0}'.format(self.session)))
		if files['error'] == '':

			for key, value in files.items():
				if key != 'error':
					cursor.execute("SELECT `filename` FROM `files` WHERE `filename` = '{0}'".format(str(value['filename'])))
					row = cursor.fetchall()

					if len(row):
						cursor.execute("UPDATE files SET `url` = %s WHERE `filename` = %s", ('http://bayfiles.com/file/{0}/{1}/{2}'.format(key, value['infoToken'], str(value['filename'])), str(value['filename'])))
					else:
						cursor.execute("INSERT INTO files (`size`, `sha1`, `filename`, `url`, `subtitle`, `category_id`, `title`) VALUES (%s, %s, %s, %s, NULL, NULL, NULL)", (value['size'], value['sha1'], value['filename'], 'http://bayfiles.com/file/{0}/{1}/{2}'.format(key, value['infoToken'], str(value['filename']))))

		else:
			sys.exit('[*] Falha ao obter a lista de arquivos remotos')

		cursor.close()
		con.commit()
		con.close()

	def logout(self):
		files = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/logout?session={0}'.format(self.session)))

if __name__ == "__main__":
	bf = BayFiles()

	print "[*] Iniciando o script de correção de links"
	bf.session = bf.login()
	print "[!] Logado como %s" % bf.username
	if '--skip-upload' not in sys.argv and '-s' not in sys.argv:
		bf.local = bf.get_local()
		print "[!] Preparando os arquivos locais..."
		bf.remote = bf.get_remote()
		print "[!] Preparando os arquivos remotos..."
		print "[!] Total de %r arquivos locais e %r remotos" % (len(bf.local), len(bf.remote))
		bf.compare()
		print "[!] Uploads finalizandos, %d arquivos upados" % bf.count
	print "[!] Atualizando banco de dados com os links"
	bf.sync()
	print "[!] Script finalizado, efetuando logout!" 
	bf.logout()
