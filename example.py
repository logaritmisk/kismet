import kismet


if __name__ == '__main__':
	q = kismet.KismetClient()
	
	try:
		q.connect()
		
		print q.server_protocols()
		
		q.send(0, 'REMOVE', 'TIME')
		q.send(1, 'ENABLEA', 'GPS', 'fix,lat,lon,alt')
		q.send(2, 'ENABLE', 'NETWORK', 'bssid,type,quality,signal,noise,ssid')
		
		print q.recv(1)
		print q.recv(2)
		
		
		def handle_all(header, data):
			print '%s: %s' % (header, data)
		
		def handle_gps(data):
			print "gps:", data
		
		def handle_network(data):
			print "network:", data
		
		
		
		q.push_handlers(all=handle_all, GPS=handle_gps, NETWORK=handle_network)
		
		while q.is_alive():
			q.pump_messages()
		
		print 'Kismet server disconnected...'
	
	except KeyboardInterrupt:
		print '^C received, shutting down server'
	
	q.close()
