import socket
import threading

HEADER = 1024  # standard accepted header size in bytes. saves faffing with numbers in the code
PORT = 6667  # hard coded port
SERVER = "::"  # hard coded IP
ADDR = (SERVER, PORT)  # tuple for connecting to server

# server boot up
# need to add error handling for a failed connection (should be fine tho)
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server_socket.bind(ADDR)
# server_socket.listen()
print(f"[LISTENING] Server is listening on port {PORT}")

clients = []  # stores the connection instances for all clients
nicks = []  # stores the nicknames of all clients


# send message to all clients
# no idea if this is neccessary but nice to have
def broadcast(message):
    for client in clients:  # messy implementation but it does the job
        client.send(message)


def print_total_clients():
    if (len(clients) == 1):
        print(str(len(clients)) + " client on the server")
    else:
        print(str(len(clients)) + " clients on the server")


def set_nick(rcv, client):
    bad_nick = True
    while bad_nick:
        subs = rcv.split("\\r\\n")  # NICK command also contains the USER part
        print(subs[1])

        # but we don't want that, so we split around the
        # new line
        nick = subs[1].replace("NICK ", "")  # set the nickname to everything following "NICK "
        # if nick
        if len(nicks) != 0 and nick in nicks == True:
            text = "Nickname is already in use"
            send_to_client(client, text)
            rcv = receive_from_client(client)
            bad_nick = True
        else:
            bad_nick = False
    text = "Your nickname is " + nick

    ####?????
    send_to_client(client, text)

    i = clients.index(client)
    if len(nicks[i]) < i + 1:  # if there is a client with no nick , append a new nick
        nicks.append(nick)  # may need to check if its a nick for a new client or old
        joinmsg_serv = "{0} joined the server!\r\n"
        joinmsg_client = "Welcome to the server {0}!\r\n"
        broadcast(joinmsg_serv.format(nick).encode('ascii'))
        client.send(joinmsg_client.format(nick).encode())
    else:
        nicks[i] = nick  # update an old nick
    return nick


def send_to_client(client_socket, text):
    address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
    client_socket.send(text.encode('ascii'))
    print("[", address, "] <- " + text)


# returns a message received
def receive_from_client(client_socket):
    print("2")
    # rcv = client_socket.recv(HEADER)  # decode the bytes into words
    msg_l = client_socket.recv(HEADER).decode('ascii')
    msg_l = int(msg_l)
    rcv = client_socket.recv(msg_l).decode('ascii')
    address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
    print("[", address, "] -> " + rcv)
    return rcv


# handle the clients messages that are sent
def thread_function(client, addr):
    while True:
        i = clients.index(client)
        try:
            # rcv = client.recv(HEADER).rstrip("\r\n")
            # rcv =rcv.decode()
            rcv = str(bytes(client.recv(4096)))
            address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])
            print("[", address, "] -> " + rcv)
            if "NICK" in rcv:
                nick = set_nick(rcv, client)
                client.close()
                server_socket.close()
            elif "Disconnected" in rcv:
                address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])
                print(address + " disconnected")
                clients.remove(client)
                client.close()
                break
            else:
                print("[", address, "] <- " + "Unknown command")
                # broadcast(f"[{nicks[i]}]: {rcv}".encode('ascii'))


        except:
            clients.remove(client)
            client.close()
            break


# handle first communication from clients
def receive():
    server_socket.listen()
    while True:
        client_socket, addr = server_socket.accept()  # open connection (error handling not present yet)

        address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
        print(f"Connected with {address}")

        clients.append(client_socket)  # add client instance to the array
        # thread = threading.Thread(target=thread_function, args=(client_socket, addr))
        # thread.start()
        thread_function(client_socket, addr)
        """

        #1st 2 messages sent by clients
        rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
        print("[" + address + "] -> " + rcv)
        rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
        print("[" + address + "] -> " + rcv)

        first_chars = rcv[0:4]  # take the first 4 characters of the message
        if "NICK" in first_chars:  # handling NICK command
            nick=set_nick(rcv, client_socket)
        else:
            break



        #print(f"Active clients {threading.activeCount() - 1}")

        # for the first 2 recieved comms
        for x in range(2):
            #client_socket, addr = server_socket.accept()  # open connection (error handling not present yet)
            #print(f"Connected with {address}")
            rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
            print("["+address+"] -> "+rcv)
            rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
            print("["+address+"] -> "+rcv)

            first_chars = rcv[0:4]  # take the first 4 characters of the message
                # this will be where the command is e.g. NICK,
                # JOIN, etc. if some wise guy decides to call them-
                # -self "NICK" to mess up the system, this counters that

            if "NICK" in first_chars:  # handling NICK command

                subs = rcv.split('\n')  # NICK command also contains the USER part
                    # but we don't want that, so we split around the
                    # new line
                nick = subs[0][5:]  # set the nickname to everything following "NICK "
                bad_nick = True
                while bad_nick:
                    if len(nicks)!=0 or nick in nicks ==True:
                        text = "Nickname is already in use"
                        send_to_client(client_socket, text)
                        nick=receive_from_client()
                        bad_nick=True
                    else:
                        bad_nick =False
            elif "JOIN" in first_chars:  # handling JOIN command
                break
            text="Your nickname is "+ nick
            send_to_client(client_socket,text)
            nicks.append(nick)
            joinmsg_serv = "{0} joined the server!\r\n"
            joinmsg_client = "Welcome to the server {0}!\r\n"
            broadcast(joinmsg_serv.format(nick).encode('ascii'))
            client_socket.send(joinmsg_client.format(nick).encode('ascii'))





        nicks.append(nick)  # add nickname to array

        # start a thread for handling the client comms
        """


# def send_ping():


print("[STARTING] Server is starting...")
receive()

