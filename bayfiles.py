#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json, urllib3, poster, sys, urlparse, yaml

class BayFiles:
	''' class to sync bayfiles account with local files '''

	def __init__(self):
		''' loads config '''

		self.config = yaml.load(open('config.yml', 'r'))

	def login(self):
		''' get session token for api '''

		login = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/login/{0}/{1}'.format(bf.config['bayfiles']['username'], bf.config['bayfiles']['password'])))
		
		if login['error'] == '':
			self.session = login['session']
		else:
			sys.exit('[*] Usuário e/ou senha invalido(s)')


	def get_remote(self):
		''' make a list of remote files '''

		files = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/files?session={0}'.format(self.session)))

		if files['error'] == '':
			remote = list()

			for key, value in files.items():
				if key != 'error':
					remote.append(value['filename'])

			remote.sort()

			self.remote = remote
		else:
			sys.exit('[*] Falha ao obter a lista de arquivos remotos')

	def get_local(self):
		''' make a list of local files '''

		local = list()

		for root, dirs, files in os.walk(self.path):
			for f in files:
				name, ext = os.path.splitext(f)
				if ext in bf.config['system']['exts']:
					local.append(os.path.join(root, f))

		local.sort()

		self.local = local

	def compare(self):
		''' compare remote with local files and then upload missing ones '''
		''' TODO exceção se local ou remote vazios '''

		self.count = 0
		for self.l in self.local:
			if os.path.basename(self.l) not in self.remote:
				self.upload(self.l)
				self.count += 1

	def request_cdn(self):
		''' get bayfiles cdn for upload '''

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
		''' do upload '''

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

	def logout(self):
		''' destroy api token '''

		files = json.load(urllib2.urlopen('http://api.bayfiles.net/v1/account/logout?session={0}'.format(self.session)))