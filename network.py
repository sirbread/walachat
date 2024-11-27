from threading import Thread
import socket, time, re

from const import *


def init_udp():
	global udp_socket
	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	
	udp_socket.bind(("", PORT))


def init_tcp():
	global tcp_socket
	
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.bind(("", PORT))


def listen_udp():
	global udp_socket, udp_listening, udp_listen_thread, host_list
	
	udp_listening = True
	host_list = []
	
	udp_socket.settimeout(0.2)
	
	def _listen():
		global udp_listening
		while udp_listening:
			try:
				data, (ip, port) = udp_socket.recvfrom(32)
				
				size = int.from_bytes(data[0:4], "big")
				color = data[4]
				name = str(data[5:], "ascii")
				
				names = [h[0] for h in host_list]
				identification = [tuple([h[0]] + list(h[3:5])) for h in host_list]
				
				if size >= 0xFFFFFFFF:
					if name in names:
						del host_list[names.index(name)]
				elif len(host_list) < MAX_HOSTS:
					if (name, ip, port) in identification:
						host_list[identification.index((name, ip, port))] = (name, color, size, ip, port, time.time())
					else:
						host_list.append((name, color, size, ip, port, time.time()))
				
			except socket.timeout:
				pass
			for h in host_list:
				if h[5] < time.time() - 2:
					host_list.remove(h)
		udp_listening = False
	
	udp_listen_thread = Thread(target=_listen, name="udp_listen_thread", daemon=True)
	udp_listen_thread.start()


def listen_tcp():
	global tcp_socket, tcp_listening, tcp_listen_thread, chatter_list, data_record
	
	chatter_list = []
	data_record = b""
	
	tcp_listening = True
	tcp_socket.settimeout(0.2)
	
	def _listen():
		global tcp_listening, data_record
		while tcp_listening:
			try:
				tcp_socket.listen(MAX_CHATTERS)
				
				s, (ip, port) = tcp_socket.accept()
				
				if len(chatter_list) >= MAX_CHATTERS:
					s.sendall(b"\xE0Server full")
				else:
					name = str(s.recv(32)[1:], "ascii")
					
					t = Thread(target=_comm, args=[name, s], name="tpc_comm_thread", daemon=True)
					t.start()
					
					chatter_list.append((name, s, t, ip, port))
					
					if data_record != b"":
						s.sendall(data_record)
					
					data_record += b"\x10" + bytes(name, "ascii")
					for c in chatter_list:
						c[1].sendall(b"\x10" + bytes(name, "ascii"))
				
			except socket.timeout:
				pass
		tcp_listening = False
	
	def _comm(name, sock):
		sock.settimeout(0.2)
		
		global tcp_listening, data_record
		while tcp_listening:
			try:
				incom = sock.recv(4096)
				data_record += incom
				
				if incom == b"":
					raise ConnectionResetError
				
				for c in chatter_list:
					c[1].sendall(incom)
				
			except socket.timeout:
				pass
				
			except (ConnectionResetError, OSError):
				data_record += b"\x11" + bytes(name, "ascii")
				for c in chatter_list[:]:
					if c[1] == sock:
						chatter_list.remove(c)
					else:
						c[1].sendall(b"\x11" + bytes(name, "ascii"))
				break
	
	tcp_listen_thread = Thread(target=_listen, name="tcp_listen_thread", daemon=True)
	tcp_listen_thread.start()


def broadcast_udp(name, color):
	global udp_socket, udp_broadcasting, udp_broadcast_thread, chatter_list
	
	udp_broadcasting = True
	
	def _broadcast():
		global udp_broadcasting
		while udp_broadcasting:
			udp_socket.sendto(int.to_bytes(len(chatter_list), 4, "big") + int.to_bytes(color, 1, "big") + bytes(name, "ascii"), ("<broadcast>", PORT))
			time.sleep(0.5)
		udp_broadcasting = False
	
	udp_broadcast_thread = Thread(target=_broadcast, name="udp_broadcast_thread", daemon=True)
	udp_broadcast_thread.start()


def connect_tcp(name, ip, port):
	global client_socket, client_listening, client_listen_thread, data_queue
	
	data_queue = []
	
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	try:
		client_socket.connect((ip, port))
	except ConnectionRefusedError:
		data_queue.append((b"\xE0", "Connection refused"))
		client_socket.close()
		return
	
	client_socket.sendall(b"\xFF" + bytes(name, "ascii"))
	
	client_listening = True
	client_socket.settimeout(0.2)
	
	def _listen():
		global client_listening
		while client_listening:
			try:
				data = client_socket.recv(4096)
				
				if data == b"":
					raise ConnectionResetError
				
				for d in re.findall(b"[\x00\x10\x11\xE0\xFF][^\x00\x10\x11\xE0\xFF]+", data):
					hint = d[0:1]
					msg = str(d[1:], "ascii")
					
					data_queue.append((hint, msg))
					
					if hint == b"\xE0":
						client_socket.close()
						break
				
			except socket.timeout:
				pass
			
			except OSError:
				pass
				
			except ConnectionResetError:
				data_queue.append((b"\xE0", "Connection closed unexpectedly"))
				client_socket.close()
				break
			
		client_listening = False
	
	client_listen_thread = Thread(target=_listen, name="client_listen_thread", daemon=True)
	client_listen_thread.start()


def send_tcp(name, color, msg):
	global client_socket
	
	try:
		client_socket.sendall(b"\x00" + bytes(f"{color}\n{name}\n{msg}", "ascii"))
	except OSError: #TODO: Handle this error, unknown how to reproduce
		pass


def terminate_udp_listen():
	global udp_listening, udp_listen_thread
	
	udp_listening = False
	try:
		udp_listen_thread.join()
	except NameError:
		pass


def terminate_broadcast(name):
	global udp_socket, udp_broadcasting, udp_broadcast_thread
	
	udp_broadcasting = False
	try:
		udp_broadcast_thread.join()
	except NameError:
		pass
	
	udp_socket.sendto(b"\xFF\xFF\xFF\xFF" + bytes(name, "ascii"), ("<broadcast>", PORT))


def terminate_tcp_all():
	global tcp_listening, client_listening, client_socket, tcp_socket, tcp_listen_thread, tcp_comm_thread, client_listen_thread, chatter_list
	
	tcp_listening = False
	
	try:
		for c in chatter_list[:]:
			c[1].sendall(b"\xE0Host disconnected")
			c[2].join()
	except NameError:
		pass
	
	try:
		tcp_listen_thread.join()
		tcp_comm_thread.join()
	except NameError:
		pass
	
	try:
		tcp_socket.close()
	except (NameError, OSError):
		pass
	
	client_listening = False
	try:
		client_listen_thread.join()
	except NameError:
		pass
	
	try:
		client_socket.shutdown(socket.SHUT_RDWR)
		client_socket.close()
	except (NameError, OSError):
		pass

