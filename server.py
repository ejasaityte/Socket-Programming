import socket
import threading
import traceback
import sys
import time


HEADER = 1024  # standard accepted header size in bytes. saves faffing with numbers in the code
PORT = 6667  # hard coded port
SERVER = "::"  # hard coded IP
ADDR = (SERVER, PORT)  # tuple for connecting to server

# server boot up
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind(ADDR)
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
class Client():
    nick = ''
    connection = None
    last_ping_time = time.time()

    def __init__(self, nick, connection):
        self.nick = nick
        self.connection = connection


last_ping_time = [] #stores last time client responded to ping
clients = []  # stores the connection instances for all clients
nicks = []  # stores the nicknames of all clients
users = []  # stores the username of all clients
channels = []  # stores the channels on the server
threads = [] #stores threads which correspond to each client
semaphore = threading.Semaphore(1)
full_login =[] #stores nick usrname mode number special character and real name


# send message to all clients
def broadcast(message):
    for client in clients:  # messy implementation but it does the job
        client.send(message)

# handle the clients messages that are sent
def handle_client(client, addr):
    semaphore.acquire()
    last_ping_time.append(time.time())
    while True:
        i = clients.index(client)
        try:
            msg = client.recv(HEADER).decode('ascii')

            try:
                address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])
            except:
                break

            print(f"[{address}] -> {str(bytes(msg.encode()))}")

            # get the hostmask
            hostmask = f"{users[i]}@{addr[0]}"

            if msg.split()[0] == "PONG":
                last_ping_time[i]=time.time()

            # handles commands
            elif msg == "" or msg.split()[0] == "QUIT":
                print(address + " disconnected")
                for channel in channels:
                    for member in channel.members:
                        if member.nick==nicks[i]:
                            channel.members.remove(member)
                clients.remove(clients[i])
                nicks.remove(nicks[i])
                last_ping_time.remove(last_ping_time[i])
                full_login.remove(full_login[i])
                print(full_login)
                #threads[i].kill()  # but not removed from list
                client.close()
                semaphore.release()
                break
            elif (msg.split()[0] == "PRIVMSG" or msg.split()[0] == "privmsg"):
                target = msg.split()[1]
                #print(target)
                # get the server name from the message
                if "#" in target:  # message sent in a chat
                    # find the searched for channel
                    for channel in channels:
                        if target == channel.name:
                            outmsg = f":{nicks[i]}!{hostmask} {msg}"
                            # send the message to each member of the channel
                            for member in channel.members:
                                if member.connection != client:
                                    send_to_client(member.connection, outmsg)
                                    #member.connection.send((outmsg).encode('ascii'))

                            # stop the loop
                            break

                else:
                    text = msg.split(target)[1]
                    #print(text)
                    if target in nicks:
                        j = nicks.index(target) # index of a client that must receive the message
                    #print(f"index {j}")

                        text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} PRIVMSG {nicks[j]} :{text}"
                        clients[j].send(bytes(text.encode()))
                        address1=str(clients[j].getpeername()[0]) + ":" + str(clients[j].getpeername()[1])
                        print(f"[{address1}] <- {str(bytes(text.encode()))}")

            # handles join command
            elif (msg.split()[0] == "JOIN"):
                # get the channel name from the message
                channelName = msg.split()[1]
                #channel name must contain #
                if channelName[0] == "#":
                    # temporary channel variable
                    tempChannel = None
                    # check if channel exists
                    for channel in channels:
                        # if the channel is found
                        if (channel.name == channelName):
                            # store the channel
                            tempChannel = channel
                            members_list = tempChannel.members
                            #sending JOIN to those members that are already in a channel but not to the member that wants to join it
                            for member in members_list:
                                if member is not None:
                                    k = nicks.index(member.nick)
                                    text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} JOIN {channelName}\r\n"
                                    clients[k].send(bytes(text.encode()))
                                    address1 = str(clients[k].getpeername()[0]) + ":" + str(clients[k].getpeername()[1])
                                    print(f"[{address1}] <- {str(bytes(text.encode()))}")
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

                    reply = (
                        f":{nicks[i]}!{hostmask} JOIN {channelName}\r\n"
                        f":{serverName} 331 {nicks[i]} {channelName} :No topic is set\r\n"
                        f":{serverName} 353 {nicks[i]} = {channelName} :{namesList}\r\n"
                        f":{serverName} 366 {nicks[i]} {channelName} :End of NAMES list\r\n"
                        )
                # if channel name does not contain #
                else:
                    reply = f":{serverName} 403 {nicks[i]} {channelName} :No such channel\r\n"

                client.send(reply.encode())
                print(f"[{address}] <- {str(bytes(reply.encode()))}")

            elif msg.split()[0] == "MODE":
                chat = msg.split()[1]
                text = f":{serverName} 324 {nicks[i]} {chat} +\r\n"
                client.send(text.encode())
                print(f"[{address}] <- {str(bytes(text.encode()))}")
            elif msg.split()[0] == "WHO":
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

            elif msg.split()[0] == "PART":
                channelName = msg.split()[1]
                for channel in channels:
                    if channel.name == channelName:
                        outmsg = f":{nicks[i]}!{hostmask} {msg} : Leaving\n"
                        remove = Client(nicks[i], client)
                        for member in channel.members:
                            print(member.nick)
                            if member.nick == nicks[i]:
                                remove=member
                                continue
                            member.connection.send((outmsg).encode('ascii'))
                            add = str(member.connection.getpeername()[0]) + ":" + str(member.connection.getpeername()[1])
                            print(f"[{add}] <- {str(bytes(outmsg.encode()))}")
                           # if member.connection == client:
                        client.send((outmsg).encode('ascii'))
                        print(f"[{address}] <- {str(bytes(outmsg.encode()))}")
                        channel.members.remove(remove)
                        break
            #update a nick of a current user
            elif msg.split()[0] == "NICK":
                new_nick = msg.split()[1]
                if valid_nick_TF(new_nick, client) == 0:
                    text = f":{nicks[i]}!{users[i]}@{clients[i].getpeername()[0]} NICK {new_nick}\n"
                    nicks[i] = new_nick

                elif valid_nick_TF(new_nick, client) == 1:
                    text = f":{serverName} 433 {nicks[i]} {new_nick} :Nickname is already in use\r\n"
                elif valid_nick_TF(new_nick, client) == 2:
                    text = f":{serverName} 432 {nicks[i]} {new_nick} :Erroneous Nickname\r\n"
                send_to_client(client, text)

            #if NAMES command
            elif msg.split()[0] == "NAMES":
                #get the name(s) of the channel(s)
                channelsStr = msg.split()[1]
                channelNames = channelsStr.split(",")
                #for each channel requested
                for channelName in channelNames:
                    #for each channel on the server
                    for channel in channels:
                        #if the channel names match
                        if channel.name == channelName:
                            #make a list of channel members
                            namesList = ""
                            for member in channel.members:
                                namesList += member.nick
                                namesList += " "
                            #send the outgoing message
                            outmsg = ""
                            outmsg += f":{serverName} 353 {nicks[i]} = {channelName} :{namesList}\r\n"
                            outmsg += f":{serverName} 366 {nicks[i]} {channelName} :End of NAMES list\r\n"
                            client.send((outmsg).encode('ascii'))
                            print(f"[{address}] <- {str(bytes(outmsg.encode()))}")
                            break

            elif msg.split()[0] == "PING":
                msg1 = msg.split()[1]
                resp = f":{serverName} PONG {serverName} :{msg1}"
                send_to_client(client,resp)
            else:
                r = f":{serverName} 421 {nicks[i]} {msg.split()[0]} :Unknown command\r\n"
                client.send(r.encode('ascii'))
                print(f"[{address}] <- {str(bytes(r.encode()))}")

            semaphore.release()

        except Exception:
            #print(traceback.format_exc())
            clients.remove(client)
            client.close()
            semaphore.release()
            break
#get message from client and display it in server in bytes format
def receive_from_client(client):
    rcv = client.recv(HEADER).decode('ascii')# decode the bytes into words
    address = str(client.getpeername()[0]) + ":" + str(client.getpeername()[1])
    print("[", address, "] -> " + str(bytes(rcv.encode())))
    return rcv

#send message to client and display it in server in bytes format
def send_to_client(client_socket, text):
    address = str(client_socket.getpeername()[0]) + ":" + str(client_socket.getpeername()[1])
    client_socket.send(text.encode())
    print(f"[{address}] <- " + str(bytes(text.encode())))

#cheching validity of a nick that a client wants to update
def valid_nick_TF(nick, client):
    special_chars = "'!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}"
    numbers = "0123456789"
    if not any(i in nick for i in special_chars) and len(nick) > 0 and not nick[0] in numbers:
        if len(nicks) == 0:  # first nickname
            return 0  # accept nickname
        elif nick in nicks:
            return 1  # nickname in use error
        else:
            return 0
    else:
        return 2  # nickname has wrong format (e.g. symbols or starts with a number) error

#getting a valid nickname during registration process. If 1st nick is in use, use second one and so on
def valid_nick(nick, client ):
    bad_nick = True
    special_chars = "!#$%&()*+,./:;<=>?@"
    numbers = "0123456789"

    while bad_nick:
        if not any(i in nick for i in special_chars) and len(nick) >0 and len(nick) <10 and not nick[0] in numbers:
            if len(nicks) ==0:
                return nick

            elif nick in nicks:
                text = f":{serverName} 433 * {nick} :Nickname is already in use\r\n"
                send_to_client(client,text)
                rcv = receive_from_client(client)
                #print(rcv)
                nick= rcv.split()[1]
            else:
                bad_nick = False
        else:
            print(nick)
            if any(i in nick for i in special_chars):
                print('1')
            if len(nick)==0 or len(nick)>10:
                print('2')
            if nick[0] in numbers:
                print('3')
            text =f":{serverName} 432 * {nick} :Erroneous Nickname\r\n"
            send_to_client(client, text)
            rcv = receive_from_client(client)
            #print(rcv)
            nick = rcv.split()[1]
    return nick


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

        # if CAP and NICK comes in different lines
        if "NICK" in first_chars:
            #socat connection doesn't send newlines, so it needs alternative code
            if rcv.find('\r\n',0,len(rcv)-4)!=-1:
                subs = rcv.split('\r\n')
                nick = subs[0][5:]  # set the nickname to everything following "NICK "
                nick = valid_nick(nick,client_socket)
                user = subs[1].split()[1]
                users.append(user)
                nicks.append(nick)  # add nickname to array
                log = nick + " " + subs[1].replace("USER ","")
                full_login.append(log)
                break
            else:
                subs = rcv.split(' ')
                nick = subs[1]  # set the nickname to everything following "NICK "
                nick = valid_nick(nick,client_socket)
                user = subs[3]
                users.append(user)
                nicks.append(nick)  # add nickname to array
                log = rcv.replace("USER ","")
                full_login.append(log)
                break

        # if CAP and NICK comes in one line
        elif "CAP" in first_chars and "NICK" in rcv:
            subs = rcv.split('\r\n')
            nick = subs[1][5:]  # set the nickname to everything following "NICK "
            #print("nick " + nick)
            nick = valid_nick(nick,client_socket)
            user = subs[2].split()[1]
            users.append(user)
            nicks.append(nick)
            log = nick + " " + subs[2].replace("USER ", "")
            #print(log)
            full_login.append(log)
            break

    clients.append(client_socket)  # add client instance to the array

    joinmsg_serv = "{0} joined the server!\r\n"
    joinmsg_client = "Welcome to the server {0}!\r\n"
    welcome=(
        f":{serverName} 001 {nick} :Welcome to IRC\r\n"
        f":{serverName} 002 {nick} :Your host is {serverName}\r\n"
        f":{serverName} 003 {nick} :This server was created in 2021\r\n"
        f":{serverName} 004 {nick} {serverName} group_5 server\r\n"
        f":{serverName} 256 {nick} :There are {len(clients)} clients on 1 server\r\n"
        #f":{serverName} 422 {nick} :MOTD File is missing\r\n"
              )

    #broadcast(joinmsg_serv.format(nick).encode('ascii'))
    client_socket.send(welcome.format(nick).encode('ascii'))
    print(f"[{address}] <- {str(bytes(welcome.encode()))}")
    # start a thread for handling the client comms
    thread = threading.Thread(target=handle_client, args=(client_socket, addr))
    threads.append(thread)
    thread.start()

def ping():
    while True:
        time.sleep(60)
        current_time = time.time()
        for client in clients:
            index = clients.index(client)
            if current_time-last_ping_time[index]>120:
                print(client.getpeername()[0] + " timed out")
                for channel in channels:
                    for member in channel.members:
                        if member.nick==nicks[index]:
                            channel.members.remove(member)
                last_ping_time.remove(last_ping_time[index])
                clients.remove(clients[index])
                nicks.remove(nicks[index])
                full_login.remove(full_login[index])
                client.close()
            else:
                text =f"PING {str(client.getpeername()[0])}:{str(client.getpeername()[1])}\r\n"
                send_to_client(client, text)
                time.sleep(3)


def main():
    print("[STARTING] Server is starting...")
    thread = threading.Thread(target=ping)
    thread.start()
    while True:
        client_socket, addr = server_socket.accept()  # open connection (error handling not present yet)
        try:
            recieve(client_socket, addr)
        except Exception:
            print(traceback.format_exc())
            print("No client detected")


main()
