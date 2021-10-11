import socket
import threading

HEADER = 1024
PORT = 6667
SERVER = "::1"
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")

clients = []
nicks = []

def broadcast(message):
	for client in clients:
		client.send(message)

def handle_client(client):
	while True:
		i = clients.index(client)
		try:
			msg = client.recv(HEADER)
			broadcast(f"[{nicks[i]}]: {msg}".encode('ascii'))
		except:
			clients.remove(client)
			client.close()
			break

def recieve():
	while True:
		client, addr = server.accept()
		print(f"Connected with {str(addr)}")

		for x in range(2):
			rcv = client.recv(HEADER).decode('ascii')
			first_chars = rcv[0:4]
			if "NICK" in first_chars:
				subs = rcv.split('\n')
				nick = subs[0][5: ]
				print(nick)
				nicks.append(nick)
				joinmsg_serv = "{0} joined the server!\r\n"
				joinmsg_client = "Welcome to the server {0}!\r\n"
				broadcast(joinmsg_serv.format(nick).encode('ascii'))
				client.send(joinmsg_client.format(nick).encode('ascii'))
			elif "JOIN" in first_chars:
				break
		
		clients.append(client)

		thread = threading.Thread(target = handle_client, args = (client,))
		thread.start()

print("[STARTING] Server is starting...")
recieve()