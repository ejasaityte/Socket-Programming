import socket
import threading

HEADER = 1024  # standard accepted header size in bytes. saves faffing with numbers in the code
PORT = 6667  # hard coded port
SERVER = "::"  # hard coded IP
ADDR = (SERVER, PORT)  # tuple for connecting to server

# server boot up
# need to add error handling for a failed connection (should be fine tho)
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
# print(socket.getaddrinfo('localhost', PORT)[0][4][0])
# SERVER = socket.getaddrinfo('localhost',PORT)[0][4][0]   #getting ipv6
server_socket.bind(ADDR)
server_socket.listen()
print(f"[LISTENING] Server is listening on {PORT}")


# class for Channels
class Channel():
    name = ''
    members = []

    def __init__(self, name):
        self.name = name


# class for Clients
# currently just used for storing clients in channels
class Client():
    nick = ''
    connection = None

    def __init__(self, nick, connection):
        self.nick = nick
        self.connection = connection


clients = []  # stores the connection instances for all clients
nicks = []  # stores the nicknames of all clients
users = []  # stores the username of all clients
channels = []  # stores the channels on the server
threads = []
semaphore = threading.Semaphore()


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



# handle the clients messages that are sent
def handle_client(client, addr):
    # semaphore.acquire()
    while True:
        i = clients.index(client)
        try:
            msg = client.recv(HEADER).decode('ascii')
            address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])

            print(f"[{address}] -> {str(bytes(msg.encode()))}")

            # broadcast(f"[{nicks[i]}]: {msg}".encode('ascii'))

            # get the hostmask
            hostmask = f"{users[i]}@{addr[0]}"
            # get the server name
            serverName = socket.gethostname()

            command = msg.split()[0]
            # handles commands
            # handles private message command
            if (command == "PRIVMSG"):
                target = msg.split()[1]
                print(target)
                # get the server name from the message
                if "#" in target:  # message sent in a chat
                    # find the searched for channel
                    for channel in channels:
                        if target == channel.name:
                            outmsg = f":{nicks[i]}!{hostmask} {msg}\n"
                            # send the message to each member of the channel
                            for member in channel.members:
                                if member.connection != client:
                                    member.connection.send((outmsg).encode('ascii'))
                            # stop the loop
                            break
                else:
                    text = msg.split(":")[1]
                    print(text)
                    j = nicks.index(target) # index of a client that must receive the message
                    print(f"index {j}")
                    text = f":{nicks[i]}!{users[i]}@::1 PRIVMSG {nicks[i]} :{text}"
                    # needs testing ---
                    #i = nicks.index(receiving_client)
                    # j= clients.index(sending_client)
                    # print(nicks[j])
                    # msg=f"{nicks[j]} PRIVMSG {receiving_client} :{text}"
                    # sending_client.send(bytes(text.encode()))
                    clients[j].send(bytes(text.encode()))
                    address1=str(clients[j].getpeername()[0]) + ":" + str(clients[j].getpeername()[1])

                    print(f"[{address1}] <- {str(bytes(text.encode()))}")

            # handles join command
            elif (command == "JOIN"):
                # get the channel name from the message
                channelName = msg.split()[1]
                # temporary channel variable
                tempChannel = None
                # check if channel exists
                for channel in channels:
                    # if the channel is found
                    if (channel.name == channelName):
                        # store the channel
                        tempChannel = channel
                        # add the client to the channel
                        channel.members.append(Client(nicks[i], client))
                        # stop the loop
                        break
                # if the channel doesn't exist
                if (tempChannel == None):
                    # create the channel
                    tempChannel = Channel(channelName)
                    # add the client to the channel
                    tempChannel.members.append(Client(nicks[i], client))
                    # add the channel to the list
                    channels.append(tempChannel)

                # create the response for the client
                namesList = ""
                members = tempChannel.members
                for member in members:
                    namesList += member.nick
                    namesList += " "

                reply = (
                    f":{nicks[i]}!{hostmask} JOIN {channelName}\n"
                    f":{serverName} 331 {nicks[i]} {channelName} :No topic is set\n"
                    f":{serverName} 353 {nicks[i]} = {channelName}:{nicks[i]}\n"
                    f":{serverName} 366 {namesList} {channelName} :End of NAMES list\n"
                )

                # send the reply
                client.send(reply.encode('ascii'))
                #print(f"{address} <- {str(bytes(reply.encode()))}")
            elif command == "MODE":
                chat = msg.split()[1]
                text = f":{serverName} 324 {nicks[i]} {chat} +\r\n"
                # client.send(text.encode())
                print(f"[{address}] <- {str(bytes(text.encode()))}")
            elif command == "WHO":
                chat = msg.split()[1]
                text = f":{serverName} 352 {nicks[i]} {chat} {nicks[i]} \r\n"  # should be added more
                # lient.send(text.encode())
                print(f"[{address}] <- {str(bytes(text.encode()))}")
            elif command == "PART":
                channelName = msg.split()[1]
                for channel in channels:
                    if channel.name == channelName:
                        for member in channel.members:
                            outmsg = f":{nicks[i]}!{hostmask} {msg} : Leaving\n"
                            member.connection.send((outmsg).encode('ascii'))
                            if member.connection == client:
                                channel.members.remove(member)
                        break
            elif command == "QUIT":
                print(address + " disconnected")
                clients.remove(clients[i])
                nicks.remove(nicks[i])
                threads[i].kill()  # but not removed from list
                client.close()
                # semaphore.release()
                break


        except:
            clients.remove(client)
            client.close()
            # semaphore.release()

            break


# handle first communication from clients
# handle first communication from clients
def recieve(client_socket, addr):
    address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
    print(f"Connected with {address}")

    # for the first 2 recieved comms
    for x in range(2):
        rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
        print(f"[{address}] -> {str(bytes(rcv.encode()))}")
        first_chars = rcv[0:4]  # take the first 4 characters of the message
        # this will be where the command is e.g. NICK,
        # JOIN, etc. if some wise guy decides to call them-
        # -self "NICK" to mess up the system, this counters that

        if "NICK" in first_chars:  # handling NICK command

            subs = rcv.split('\r\n')  # NICK command also contains the USER part
            # but we don't want that, so we split around the
            # new line
            nick = subs[0][5:]  # set the nickname to everything following "NICK "
            user = subs[1].split()[1]
            users.append(user)
            nicks.append(nick)  # add nickname to array
            break
        elif "CAP" in first_chars and "NICK" in rcv:
            subs = rcv.split('\r\n')
            nick = subs[1][5:]  # set the nickname to everything following "NICK "
            user = subs[2].split()[1]
            users.append(user)
            nicks.append(nick)
            break

    clients.append(client_socket)  # add client instance to the array
    print(nicks)
    print(nick, user)
    joinmsg_serv = "{0} joined the server!\r\n"
    joinmsg_client = "Welcome to the server {0}!\r\n"
    broadcast(joinmsg_serv.format(nick).encode('ascii'))
    client_socket.send(joinmsg_client.format(nick).encode('ascii'))
    welcome = "Welcome to the server " + nick
    print(f"[{address}] <- {str(bytes(welcome.encode()))}")
    # start a thread for handling the client comms
    thread = threading.Thread(target=handle_client, args=(client_socket, addr))
    threads.append(thread)
    thread.start()


def main():
    print("[STARTING] Server is starting...")
    while True:
        client_socket, addr = server_socket.accept()  # open connection (error handling not present yet)
        try:
            recieve(client_socket, addr)
        except:
            print("No client detected")


main()
