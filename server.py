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
try:
    server_socket.bind(ADDR)
except:
    print("Binding error. ")
server_socket.listen()
print(f"[LISTENING] Server is listening on {PORT}")
serverName = socket.gethostname()



# class for Channels
class Channel():
    name = ''
    members = []

    def __init__(self, name, members):
        self.name = name
        self.members=members


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
semaphore = threading.Semaphore(1)
full_login =[] #stores nick usrname mode number special character and real name


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
    semaphore.acquire()
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

                    text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} PRIVMSG {nicks[i]} :{text}"
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
                if channelName[0] == "#" or channelName[0] == "&":
                    # temporary channel variable
                    tempChannel = None
                    # check if channel exists
                    for channel in channels:
                        # if the channel is found
                        if (channel.name == channelName):
                            # store the channel
                            tempChannel = channel
                            members_list = tempChannel.members

                            for member in members_list:
                                print(member.nick)
                                k = nicks.index(member.nick)
                                print(k)
                                text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} JOIN {channelName}\r\n"
                                clients[k].send(bytes(text.encode()))
                                address1 = str(clients[k].getpeername()[0]) + ":" + str(clients[k].getpeername()[1])
                                print(f"[{address1}] <- {str(bytes(text.encode()))}")
                            # add the client to the channel
                            # add the client to the channel
                            channel.members.append(Client(nicks[i], client))
                            # stop the loop
                            break
                    # if the channel doesn't exist
                    if (tempChannel == None):
                        # create the channel
                        tempChannel = Channel(channelName,[])
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

                    print(f"chat name {tempChannel.name} length {len(tempChannel.members)}")

                    reply = (
                        f":{nicks[i]}!{hostmask} JOIN {channelName}\r\n"
                        f":{serverName} 331 {nicks[i]} {channelName} :No topic is set\r\n"
                        f":{serverName} 353 {nicks[i]} = {channelName} :{namesList}\r\n"
                        f":{serverName} 366 {nicks[i]} {channelName} :End of NAMES list\r\n"
                        )

                else:
                    reply = f":{serverName} 403 {nicks[i]} {channelName} :No such channel\r\n"

                client.send(reply.encode('ascii'))
                print(f"[{address}] <- {str(bytes(reply.encode()))}")

            elif command == "MODE":
                chat = msg.split()[1]
                text = f":{serverName} 324 {nicks[i]} {chat} +\r\n"
                client.send(text.encode())
                #client.send(bytes(text.encode()))
                print(f"[{address}] <- {str(bytes(text.encode()))}")
            elif command == "WHO":
                chat_name = msg.split()[1]
                clients_in_channel = None
                reply_to_WHO =""
                for channel in channels:
                    if (channel.name == channelName):
                        clients_in_channel=channel.members
                        break
                for member in clients_in_channel:
                    l = nicks.index(member.nick)
                    reply_to_WHO += f":{serverName} 352 {nicks[i]} {channelName} {users[l]} {addr[0]} {serverName} {full_login[l]}\r\n"
                reply_to_WHO += f":{serverName} 315 {nicks[i]} {channelName} :End of WHO list\r\n"
                client.send(reply_to_WHO.encode())
                print(f"[{address}] <- {str(bytes(reply_to_WHO.encode()))}")

            elif command == "PART":
                channelName = msg.split()[1]
                for channel in channels:
                    if channel.name == channelName:
                        for member in channel.members:
                            outmsg = f":{nicks[i]}!{hostmask} {msg} : Leaving\n"
                            member.connection.send((outmsg).encode('ascii'))
                            print(f"[{address}] <- {str(bytes(outmsg.encode()))}")
                            if member.connection == client:
                                channel.members.remove(member)
                        break

            elif command == "NICK":
                new_nick = msg.split()[1]
                if valid_nick_TF(new_nick, client) == 0:
                    text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} NICK {new_nick}\n"
                    nicks[i] = new_nick

                elif valid_nick_TF(new_nick, client) == 1:
                    text = f":{serverName} 433 {nicks[i]} {new_nick} :Nickname is already in use\r\n"
                elif valid_nick_TF(new_nick, client) == 2:
                    text = f":{serverName} 432 {nicks[i]} {new_nick} :Erroneous Nickname\r\n"



                send_to_client(client, text)

            elif command == "QUIT":
                print(address + " disconnected")
                clients.remove(clients[i])
                nicks.remove(nicks[i])
                #threads[i].kill()  # but not removed from list
                client.close()
                semaphore.release()
                break
            else:
                r = f":{serverName} 421 {nicks[i]} {command} :Unknown command\r\n"
                client.send(r.encode('ascii'))
                print(f"[{address}] <- {str(bytes(r.encode()))}")

            semaphore.release()

        except:
            clients.remove(client)
            client.close()
            semaphore.release()

            break
def receive_from_client(client):
    rcv = client.recv(HEADER).decode('ascii')# decode the bytes into words
    address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])
    print("[", address, "] -> " + str(bytes(rcv.encode())))
    return rcv

def send_to_client(client_socket, text):
    address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
    client_socket.send(text.encode())
    print(f"[{address}] <- " + str(bytes(text.encode())))

def valid_nick_TF(nick, client):
    special_chars = "'!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}"
    numbers = "0123456789"
    if not any(i in nick for i in special_chars) and len(nick) > 0 and not nick[0] in numbers:
        if len(nicks) == 0:  # first nickname
            return 0  # accept nickname
        elif nick in nicks:
            return 1  # nickname in use
        else:
            return 0
    else:
        return 2  # nickname has wrong format (e.g. symbols or starts with a number)

def valid_nick(nick, client, special_char):
    bad_nick = True
    special_chars = "!#$%&()*+,./:;<=>?@"
    numbers = "0123456789"
    print("enter")
    while bad_nick:
        if not any(i in nick for i in special_chars) and len(nick) >0 and len(nick) <10 and not nick[0] in numbers:
            if len(nicks) ==0:
                return nick

            elif nick in nicks:
                print("inside")

                text = f":{serverName} 433 {special_char} {nick} :Nickname is already in use\r\n"

                send_to_client(client,text)
                rcv = receive_from_client(client)
                print(rcv)
                nick= rcv.split()[1]
            else:
                bad_nick = False
        else:
            text =f":{serverName} 432 {special_char} {nick} :Erroneous Nickname\r\n"
            send_to_client(client, text)
            rcv = receive_from_client(client)
            print(rcv)
            nick = rcv.split()[1]
    return nick

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

            subs = rcv.split('\r\n')
            nick = subs[0][5:]  # set the nickname to everything following "NICK "
            special_char = subs[1].split()[3]
            nick = valid_nick(nick,client_socket, special_char)
            user = subs[1].split()[1]
            users.append(user)
            nicks.append(nick)  # add nickname to array
            log = nick + " " + subs[1].replace("USER ","")
            print(log)
            full_login.append(log)
            break
        elif "CAP" in first_chars and "NICK" in rcv:
            subs = rcv.split('\r\n')
            nick = subs[1][5:]  # set the nickname to everything following "NICK "
            nick = valid_nick(nick,client_socket)
            user = subs[2].split()[1]
            users.append(user)
            nicks.append(nick)
            log = nick + " " + subs[2].replace("USER ", "")
            print(log)
            full_login.append(log)
            break

    clients.append(client_socket)  # add client instance to the array
    print(nicks)
    print(nick, user)
    joinmsg_serv = "{0} joined the server!\r\n"
    joinmsg_client = "Welcome to the server {0}!\r\n"
    """
    [::1: 54898] < - b':LAPTOP-D411HM5B.broadband 001 jb :Hi, welcome to IRC\r\n' \
                     b':LAPTOP-D411HM5B.broadband 002 jb :Your host is LAPTOP-D411HM5B.broadband, running version miniircd-2.1\r\n' \
                     b':LAPTOP-D411HM5B.broadband 003 jb :This server was created sometime\r\n' \
                     b':LAPTOP-D411HM5B.broadband 004 jb LAPTOP-D411HM5B.broadband miniircd-2.1 o o\r\n' \
                     b':LAPTOP-D411HM5B.broadband 251 jb :There are 2 users and 0 services on 1 server\r\n' \
                     b':LAPTOP-D411HM5B.broadband 422 jb :MOTD File is missing\r\n'
    """
    welcome=(
        f":{serverName} 001 {nick} :Welcome to IRC\r\n"
        f":{serverName} 002 {nick} :Your host is {serverName}\r\n"
        f":{serverName} 003 {nick} :This server was created in 2021\r\n"
        f":{serverName} 004 {nick} {serverName} group_5 server\r\n"
        f":{serverName} 256 {nick} :There are {len(clients)} and 0 servise\r\n"
       # f":{serverName} 422 {nick} :MOTD File is missing\r\n"
              )

    broadcast(joinmsg_serv.format(nick).encode('ascii'))
    client_socket.send(welcome.format(nick).encode('ascii'))
   # welcome = "Welcome to the server " + nick
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

