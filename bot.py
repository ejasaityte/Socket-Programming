import socket
import time


def connecting_to_socket(server, port):
    global s
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.connect((server, port))
        print("Bot has successfully connected to the server")
        return 1
    except:
        print("Failed to connect to the server")
        return 0



"""
Logging in/registering using IRC protocol
"""
##Error handling needed to check:
#   1)if nic, usern, realn have acceptable characters, format, length
#   2)if username is in use (is it included in IRC?)
def log_in():
    global nick, user, realname
    #Log in to IRC by specifying NICK and USERNAME
    mode=0 #should be increased for every single client joining the server ??
    in_use = True

    username_valid = False

    while not username_valid:
        user=input("Enter a username: ")
        if user.find('@') != -1 and user.find(' ') != -1 and len(user) > 0:            #checks if username doesn't contain an @ symbol or a space
            username_valid = True
        else:
            print("Username cannot start with @ or space.")

    realname_valid = False

    while not realname_valid:
        realname=input("Enter a real name (e.g. Name Surname): ")
        if len(realname) > 0:
            realname_valid = True
        else:
            print("Name too short.")

    mode_str=str(mode)
    while in_use:
        nick_valid = False
        while not nick_valid:
            nick=input("Enter a nickname: ")
            if len(nick) < 10 and len(nick) > 0 and not nick[0].isdigit() and nick[0] != '-':  #checks nickname validity
                nick_valid = True
            else:
                print("Nickname not valid (1-9 characters length, first character can't be - or a digit).")
        request="NICK "+nick+"\r\nUSER "+user+" "+mode_str+" * :"+realname+"\r\n"
        s.send(request.encode())
        result= s.recv(4096).decode() ## 4096 - buffer
        nick_inuse_text = "Nickname is already in use" #migh need to be adjusted based on the message sent by a server when a nickname already in use
        if nick_inuse_text in result:
            print("Nickname is already in use choose another one")
        else:
            print("Bot was successfully registered")
            in_use=False

##Error handling needed to check:
#   1) if bot joins a non-existing channel
def JOIN_channel():
    channel_name = input("Enter chat name: ")
    request1="JOIN #"+channel_name+"\r\n"
    s.send(request1.encode())
    result= s.recv(4096).decode() ## 4096 - buffer
    if(result!=""):  ## not sure what 'result' should display when bot doesn't join  the channel
        print("Bot has joined the channel #"+channel_name)
    else:
        print("Bot was not able to join the channel #"+channel_name)
    return channel_name


"""
Responding to messages directed to the bot via the common chat or privately
NOTE: more random facts should be added , now it only responds with the same sentence
"""
def respond_to_PRIVMSG(server_msg, channel_name):
    substrings=server_msg.split(':')
    receiver = substrings[1]
    receiver1 = receiver.split('!')

    #if the message was sent via a public channel(e.g. #test) and directed to the bot
    if(server_msg.find(channel_name) !=-1):
        random_fact = "PRIVMSG #"+channel_name +" :"+ receiver1[0] + " :Today is a beautiful day! :)\r\n"
    else:
        # if the message was sent privately and directed to the bot
        random_fact="PRIVMSG "+receiver1[0]+" :Today is a beautiful day! :)\r\n"

    s.send(random_fact.encode())

def PONG_response():
    msg="PONG bot is still alive"
    s.send(msg.encode())

def respond_to_commands(server_msg, channel_name):
    pass

def main():

    connection_success = False
    while not connection_success:
        server = input("Enter a server: ")  # '::1'

        port_valid = False
        while not port_valid:
            port_str = input("Enter a port: ")
            if port_str.isdigit():
                port = int(port_str)                # 6667    connect_to_socket(server_port[0], server_port[1])
                if port > 0 and port < 65536:       # checks if port number is valid
                    port_valid = True
                else:
                    print('Port number invalid.')
            else:
                print('Port should be an integer.')

        connection_success = connecting_to_socket(server,port) #updates the global socket obj - s also it

    log_in()
    channel_n=JOIN_channel() #getting channel name

    while True:
        server_msg = s.recv(4096).decode()
        # print(server_msg) #display everything that server sends to bot
        if ((server_msg.find("PRIVMSG") != -1) and ((server_msg.find(nick) != -1) or (server_msg.find(user) != -1)
        or (server_msg.find(realname) != -1))):  # if a private message was directed to bot
            print("Private message received")
            respond_to_PRIVMSG(server_msg, channel_n)
        elif(server_msg.find("PING")!=-1):
            PONG_response()
    #time.sleep(10)
    #s.close()


main()