#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml, json, urllib3, sys, poster
from time import sleep

class BayFiles:

	def __init__(self):
		self.config = yaml.load(open('config.yml', 'r'))
		self.http = urllib3.PoolManager()

	def _request(self, url, method = 'GET', body = None):
		return self.http.request(method, url, body, {'user-agent': 'python-urllib3'})

	def _get(self, url):
		if hasattr(self, 'session'):
			url = '%s?session=%s' % (url, self.session)

		request = json.loads(self._request(url).data)

		if request['error']:
			raise RuntimeError(request['error'])
		else:
			return request

	def _post(self, url, body):
		request = json.loads(self._request(url, 'POST', body).data)

		if request['error']:
			raise RuntimeError(request['error'])
		else:
			return request

	def login(self):
		auth = (self.config['bayfiles']['username'], self.config['bayfiles']['password'])

		request = self._get('http://api.bayfiles.net/v1/account/login/%s/%s' % auth)

		self.session = request['session']
		self.info = self._info()

	def logout(self):
		request = self._get('http://api.bayfiles.net/v1/account/logout')

		del self.session

	def _info(self):
		return self._get('http://api.bayfiles.net/v1/account/info')

	def _uploadurl(self):
		request = self._get('http://api.bayfiles.net/v1/file/uploadUrl')

		return request['uploadUrl']

	def upload(self, localfile):
		success = False
		attempt = 0

		while not success and attempt < self.config['system']['maxretries']:
			uploadurl = self._uploadurl()
			attempt += 1

			try:
				poster.streaminghttp.register_openers()
				datagen, headers = poster.encode.multipart_encode({"file":open(localfile, 'rb')}, cb=upload_callback)
				# request = json.load(urllib2.urlopen(urllib2.Request(uploadurl, datagen, headers)))

				success = True
			# except:
			# 	print 'Erro inesperado, próxima tentativa em %d segundos' % (5 * attempt)
			# 	sleep(5 * attempt)

			finally:
				print 'meh'


	def _upload_callback(self, param, current, total):
		percent = (current / float(total)) * 100

		info = '{0}/{1}MB'.format(round(current/1000.0**2,2), round(float(total)/1000.0**2,2))

		sys.stdout.write("[!] %d%% %s\r" % (percent, info))
		sys.stdout.flush()


if __name__ == '__main__':
	bf = BayFiles()
	bf.login()

	bf.upload('errr')

	bf.logout()