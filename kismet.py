import socket
import string


KISMET_DEFAULT_HOST = '127.0.0.1'
KISMET_DEFAULT_PORT = 2501


def split(msg, format):
	args = format.split(',')
	data = msg.strip()
	pack = {}
	
	i = 0
	while data:
		if data.startswith('\01'):
			data = data[1:]
			p = data.find('\01', 1)
			
			pack[args[i]] = data[:p]
			data = data[p + 2:]
		
		else:
			p = data.find(' ', 1)
			if p == -1:
				p = len(data)
			
			pack[args[i]] = data[:p]
			data = data[p + 1:]
		
		i += 1
	
	return pack



class KismetClient:
	def __init__(self, **kwargs):
		self.__handlers = {}
		
		self.__sock = None
		self.__buff = ''
		
		self.__queue = []
		self.__respons = {}
		
		self.__s_version = None
		self.__s_starttime = None
		self.__s_servername = None
		self.__s_timestamp = None
		self.__s_channelhop = None
		self.__s_newversion = None
		self.__s_protocols = None
		
		if 'host' in kwargs:
			self.connect(kwargs.get('host', GPSD_DEFAULT_HOST), kwargs.get('port', GPSD_DEFAULT_PORT))
	
	
	def connect(self, host=KISMET_DEFAULT_HOST, port=KISMET_DEFAULT_PORT):
		self.close()
		
		for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
			af, socktype, proto, canonname, sa = res
			
			try:
				self.__sock = socket.socket(af, socktype, proto)
				self.__sock.connect(sa)
			
			except socket.error, msg:
				self.close()
				continue
			
			break
		
		while not self.__s_protocols:
			self._queue_pump()
	
	def close(self):
		if self.__sock:
			self.__sock.close()
		
		self.__sock = None
		self.__buff = ''
	
	def is_alive(self):
		return bool(self.__sock)
	
	
	def send(self, oid, command, *options):
		if oid is not 0 and oid not in self.__respons:
			self.__respons[oid] = None
		
		self.__sock.send('!%i %s %s\n\n' % (oid, command, ' '.join(options)))
	
	def recv(self, oid):
		ret = 'INVALID_ID', ''
		if oid in self.__respons:
			while not self.__respons[oid]:
				self._queue_pump()
			
			ret = self.__respons[oid]
			del self.__respons[oid]
		
		return ret
	
	
	def server_version(self):
		return self.__s_version
	
	def server_starttime(self):
		return self.__s_starttime
	
	def server_name(self):
		return self.__s_servername
	
	def server_timestamp(self):
		return self.__s_timestamp
	
	def server_channelhop(self):
		return self.__s_channelhop
	
	def server_newversion(self):
		return self.__s_newversion
	
	def server_protocols(self):
		return self.__s_protocols
	
	
	def push_handlers(self, **kwargs):
		for header, function in kwargs.items():
			if header not in self.__handlers:
				self.__handlers[header] = []
			
			self.__handlers[header] += [function]
	
	
	def pump_messages(self):
		self._queue_pump()
		
		for header, data in self.__queue:
			if 'all' in self.__handlers:
				for handler in self.__handlers['all']:
					handler(header, data)
			
			if header in self.__handlers:
				for handler in self.__handlers[header]:
					handler(data)
		
		self.__queue[:] = []
	
	
	def _queue_pump(self):
		try:
			chunk = self.__sock.recv(512)
			if chunk == '':
				self.close()
				return
			
			self.__buff += chunk
		
		except socket.error:
			self.close()
			return
		
		p = self.__buff.rfind('\n')
		if p >= 0:
			for line in map(string.strip, self.__buff[:p].splitlines()):
				c = line.find(':')
				
				header, data = (line[1:c], line[c + 2:])
				
				#check for respons and server info
				if header == 'ACK':
					if int(data) in self.__respons:
						self.__respons[int(data)] = [header, '']
				
				elif header == 'ERROR':
					oid, msg = data.split(' ', 1)
					if int(oid) in self.__respons:
						self.__respons[int(oid)] = [header, msg]
				
				elif header == 'KISMET':
					self.__s_version, self.__s_starttime, self.__s_servername, self.__s_timestamp, self.__s_channelhop, self.__s_newversion = data.split(' ', 5)
				
				elif header == 'PROTOCOLS':
					self.__s_protocols = data.split(',')
				
				self.__queue += [[header, data]]
			
			self.__buff = self.__buff[p + 1:]
	
