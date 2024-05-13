import socket

if __name__ == '__main__':
	print("""
                 ____                           
     _______  __/ __/_  _______                 
    / ___/ / / / /_/ / / / ___/  ______         
   / /  / /_/ / __/ /_/ (__  )  /_____/         
  /_/   \__,_/_/  \__,_/____/                   
                 ______                         
     _________  / __/ /__      ______ _________ 
    / ___/ __ \/ /_/ __/ | /| / / __ `/ ___/ _ \ 
   (__  ) /_/ / __/ /_ | |/ |/ / /_/ / /  /  __/
  /____/\____/_/  \__/ |__/|__/\__,_/_/   \___/                 

	   
	This program is a module.
""")


class handler:# the idea is that the handler stores and controlls the sockets for you
	def __init__(self):
		self.server = socket.socket()
		self.sockets = {}#stores and client sockets (not server)
	def listen(self,amount):# this will listen for a specific number of connections, or if -1 is given, infinite untill stop_listen is called
		self.listening = True
		count = 0
		existing_count = len(self.sockets) #so we dont overwrite sockets when listening again
		while self.listening:
			try:
				self.server.listen(1)
				print("listening")
				con, address = self.server.accept()
				print("accepted connection")
				self.sockets[count+existing_count] = con #stored as the noumber of the order they connected in (index at 0)
				count += 1
				if count >= amount:
					print("finnishing search")
					self.server.close()#stops connections leaking through
					break
			except Exception as problem:
				self.auto_bind(self.saved_port)
	def stop_listen(self):#stops the listener, meant for when unlimited connections are wanted
		self.listening = False
	def auto_bind(self,port):#finds your ip and binds (requires port)
		self.saved_port = port
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ip_address = s.getsockname()[0]
		s.close()
		print("ip address:",ip_address)
		try:
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except:
			self.server = socket.socket()#in case it was closed before
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind((ip_address,port))
		return self.server #returns the socket if you want it, allowing flexibility if you want to manage the socket from here on out
	def recvall(self,server):#designed to receive every last byte of data when sending large amounts reliably
		buffer = b""
		recv = b""#data not decoded
		while recv != b"\0":#end of transmition signifyed by this character
			buffer += recv
			recv = server.recv(1)
		return buffer