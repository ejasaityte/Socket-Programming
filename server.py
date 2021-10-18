import socket
import threading

HEADER = 1024 #standard accepted header size in bytes. saves faffing with numbers in the code
PORT = 6667 #hard coded port
SERVER = "::1" #hard coded IP
ADDR = (SERVER, PORT) #tuple for connecting to server

# server boot up
# need to add error handling for a failed connection (should be fine tho)
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
#print(socket.getaddrinfo('localhost', PORT)[0][4][0])
    # SERVER = socket.getaddrinfo('localhost',PORT)[0][4][0]   #getting ipv6
server_socket.bind(ADDR)
server_socket.listen()
print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")

#class for Channels
class Channel():
    name = ''
    members = []

    def __init__(self, name):
        self.name = name
        print(name)

#class for Clients
#currently just used for storing clients in channels
class Client():
    nick = ''
    connection = None

    def __init__(self, nick, connection):
        self.nick = nick
        self.connection = connection


clients = [] #stores the connection instances for all clients
nicks = [] #stores the nicknames of all clients
users = [] #stores the username of all clients
channels = [] # stores the channels on the server

# send message to all clients
# no idea if this is neccessary but nice to have
def broadcast(message):
    for client in clients:  # messy implementation but it does the job
        client.send(message)

def print_total_clients():
    if (len(clients) ==1):
        print(str(len(clients))+" client on the server")
    else:
        print(str(len(clients))+" clients on the server")


# handle the clients messages that are sent
def handle_client(client, addr):
    while True:
        i = clients.index(client)
        try:
            msg = client.recv(HEADER).decode('ascii')
            print(msg)

            broadcast(f"[{nicks[i]}]: {msg}".encode('ascii'))
            
            #handles commands
            #handles private message command
            if (msg.split()[0] == "PRIVMSG"):
                #get the server name from the message
                target = msg.split()[1]
                #find the searched for channel
                for channel in channels:
                    if target == channel.name:
                        #send the message to each member of the channel
                        for member in channel.members:
                            member.connection.send(msg.encode('ascii'))
                        #stop the loop
                        break
            #handles join command
            elif (msg.split()[0] == "JOIN"):
                #get the channel name from the message
                channelName = msg.split()[1]
                #temporary channel variable
                tempChannel = None
                #check if channel exists
                for channel in channels:
                    #if the channel is found
                    if (channel.name == channelName):
                        #store the channel
                        tempChannel = channel
                        #add the client to the channel
                        channel.members.append(Client(nicks[i], client))
                        #stop the loop
                        break
                #if the channel doesn't exist
                if (tempChannel == None):
                    #create the channel
                    channel = Channel(channelName)
                    #add the client to the channel
                    channel.members.append(Client(nicks[i], client))
                    #store the channel
                    tempChannel = channel
                    #add the channel to the list
                    channels.append(channel)
                
                #get the hostmask
                hostmask = f"{users[i]}@{addr[0]}"
                #get the server name
                serverName = socket.gethostname()

                #create the response for the client
                reply = ''
                reply += f":{nicks[i]}!{hostmask} JOIN {channelName}\r\n"
                reply += f":{serverName} 331 {nicks[i]} {channelName} :No topic is set\r\n"
                reply += f":{serverName} 353 {nicks[i]} = {channelName}:{nicks[i]}\r\n"
                namesList = ""
                members = tempChannel.members
                for member in members:
                    namesList += member.nick
                    namesList += " "
                reply += f":{serverName} 366 {namesList} {channelName} :End of NAMES list\r\n"

                #send the reply
                client.send(reply.encode('ascii'))
            
                
            
        except:
            clients.remove(client)
            client.close()
            break

# handle first communication from clients
def recieve(client_socket, addr):

        print(f"Connected with {str(addr)}")

        # for the first 2 recieved comms
        for x in range(2):
            rcv = client_socket.recv(HEADER).decode('ascii')  # decode the bytes into words
            print(rcv)
            first_chars = rcv[0:4]  # take the first 4 characters of the message
            # this will be where the command is e.g. NICK,
            # JOIN, etc. if some wise guy decides to call them-
            # -self "NICK" to mess up the system, this counters that

            if "NICK" in first_chars:  # handling NICK command

                subs = rcv.split('\n')  # NICK command also contains the USER part
                # but we don't want that, so we split around the
                # new line
                nick = subs[0][5:]  # set the nickname to everything following "NICK "
                user = subs[1].split()[1]
                
                users.append(user)
                nicks.append(nick)

                joinmsg_serv = "{0} joined the server!\r\n"
                joinmsg_client = "Welcome to the server {0}!\r\n"
                broadcast(joinmsg_serv.format(nick).encode('ascii'))
                client_socket.send(joinmsg_client.format(nick).encode('ascii'))

            elif "JOIN" in first_chars:  # handling JOIN command
                # TODO: handle this
                break

        clients.append(client_socket)  # add client instance to the array
        nicks.append(nick)  # add nickname to array

        # start a thread for handling the client comms
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
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