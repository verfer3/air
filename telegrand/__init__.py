# -*- coding: utf-8 -*-

"""
	----------------------------------------------------------------
		Copyright - 2018
		Tolomeo Samuele
		USAGE PERMISSION ONLY
		SHARING/MODIFICATION OF THIS SOFTWARE IS NOT ALLOWED
	----------------------------------------------------------------
"""

import json, requests, operator, threading
from collections import namedtuple

class Bot:

	def _json_object_hook(self, d): return namedtuple('X', d.keys())(*d.values())
	def toObj(self, data): return json.loads(data, object_hook=self._json_object_hook)

	def __init__(self, token):
		self.token = token
		self.__nsh = {}
		self.session = requests.Session()
		self.handlers = []
		self.API = "https://api.telegram.org/bot%s/" % (token)

	def handle(self, _filter=None, value=None, sw=False):
		def dec(function):
			self.handlers.append({
				"function": function,
				"filter": _filter,
				"value": value,
				"sw": sw
			})
		return dec

	def polling(self, threaded=False):
		offset = 0
		while True:
			update = self.session.get(
				self.API + "getUpdates",
				params={
					"offset": offset
				}
			).text.replace('"from"', '"from_user"')
			update = self.toObj(update)
			if len(update.result) > 0:
				offset = update.result[0].update_id + 1
				try:
					msg = update.result[0].message
					msg.text
				except:
					continue
				try:
					self.__nsh[msg.chat.id]['function']
				except:
					self.__nsh[msg.chat.id] = {}
					for handler in self.handlers:
						if handler['filter'] == None:
							threading.Thread(target=handler['function'], args=[msg]).start()
							break
						else:
							for value in handler['value']:
								if not handler['sw']:
									if operator.attrgetter(handler['filter'])(msg) == value:
										threading.Thread(target=handler['function'], args=[msg]).start()
										break
									else:
										if operator.attrgetter(handler['filter'])(msg).startswith(value):
											threading.Thread(target=handler['function'], args=[msg]).start()
											break
				else:
					handler = self.__nsh[msg.chat.id]
					threading.Thread(target=handler['function'], args=(msg, *handler['args'])).start()
					del self.__nsh[msg.chat.id]

	def req(self, res, **kwargs):
		req = self.toObj(
				self.session.post(
					self.API + res,
				**kwargs
			).text.replace(
				'"from"',
				'"from_user"'
			)
		)
		try:
			return req.result
		except:
			return req
			
	def nsh(self, chat_id, function, **kwargs):
		self.__nsh[chat_id] = {}
		self.__nsh[chat_id]['function'] = function
		self.__nsh[chat_id]['args'] = kwargs
