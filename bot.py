import socket
import time
import random
import argparse
import threading
import atexit
import signal

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



def check_name_validity(name):
    special_chars =  "'!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}"
    if not any(i in name for i in special_chars) and len(name) > 0:
        return True
    return False

def disconnect():
    print('Disconnecting bot...')
    message = 'QUIT :Leaving\r\n'
    s.send(message.encode())
    s.close()

def log_in(username_arg):
    global nick, user, realname
    #Log in to IRC by specifying NICK and USERNAME
    mode=0 #should be increased for every single client joining the server ??
    in_use = True

    username_valid = False
    realname_valid = False
    nick_valid = False

    if username_arg:
        user=username_arg
        nick=username_arg
        realname=username_arg
        if check_name_validity(user) and user.find(' ')==-1:
            username_valid=True
            realname_valid = True
            nick_valid = True
        else:
            print("Erroneous name.")

    while not username_valid:
        user=input("Enter a username: ")
        if check_name_validity(user) and user.find(' ')==-1:            #checks if username doesn't contain an @ symbol or a space
            username_valid = True
        else:
            print("Erroneous username.")

    while not realname_valid:
        realname=input("Enter a real name (e.g. Name Surname): ")
        if check_name_validity(realname) and len(realname) > 0:
            realname_valid = True
        else:
            print("Erroneous real name.")

    mode_str=str(mode)
    nick_option = 0
    nicknames_list= [] #if first is in use , chooses others
    while in_use:
        if nick_option==0: # 3 nicks entered for the first time
            if nick_valid is False:
                    for x in range(3):
                        nick_valid=False
                        while not nick_valid:
                            nick1=input(f"Enter a nick name ({x+1} choice): ")
                            if len(nick1) < 10 and len(nick1) > 0 and not nick1[0].isdigit() and check_name_validity(nick1) and nick1.find(' ')==-1 and nick1 not in nicknames_list:  #checks nickname validity
                                nicknames_list.append(nick1)
                                nick_valid = True
                            else:
                                print("Nickname not valid (1-9 characters length, first character can't be - or a digit).")
            else:
                    #if command line args are used, it automatically picks some nicknames
                    nicknames_list.append(nick)
                    nicknames_list.append(nick + '_')
                    nicknames_list.append(nick + '__')
                    nicknames_list.append(nick + '___')
            request0="CAP LS 302\r\n"
            s.send(request0.encode())

            request="NICK "+nicknames_list[0]+"\r\nUSER "+user+" "+mode_str+" * :"+realname+"\r\n"

        else: #if 1st nick is not valid send this command only without users info
            request = "NICK " + nicknames_list[nick_option] + "\r\n"
        s.send(request.encode())
        result= s.recv(4096).decode() ## 4096 - buffer
        if "Nickname is already in use" in result:
            nick_option += 1
            if nick_option == 4:
                    nick_valid=False
                    nick_option=0
                    nicknames_list= []
        else:
            print(result)
            break
    return nicknames_list[nick_option]



def JOIN_channel(channel_arg):
    if channel_arg:
        channel_name=channel_arg
    else:
        channel_name = input("Enter chat name: #")
    request1="JOIN #"+channel_name+"\r\n"
    s.send(bytes(request1.encode()))

    result= str(bytes(s.recv(4096))) ## 4096 - buffer
    if("No topic is set" in result):
        print("Bot has joined the channel #"+channel_name)
        members_in_list = result.split(':')[7]
        members_in_list = members_in_list.replace("\\r\\n","")
        print(f"{members_in_list} in #{channel_name}")
    else:
        print("Bot was not able to join the channel #"+channel_name)
    return channel_name



#Responding to messages directed to the bot via the common chat or privately
def respond_to_PRIVMSG(server_msg, nick):

    substrings=server_msg.split() #e.g. sender PRIVMSG bot/#chat :message
    random_fact = random.choice(open("facts.txt").readlines()).strip('\n')
    sender = server_msg.split('!')[0]
    sender = sender.replace(":", "")
    #private message
    if server_msg.split()[2] == nick:
        print(f"From {sender} {server_msg.split(nick)[1]}")
        text=f"PRIVMSG {sender} {random_fact}\r\n"
        s.send(text.encode())
        
    #bot should only send random facts in private chat            
    #message from a channel

    elif "#" or "&" in server_msg.split()[2]:
        channel_n = server_msg.split()[2]
        print(f"{sender} in {channel_n} {server_msg.split(channel_n)[1]}")
        #text = f"PRIVMSG {server_msg.split()[2]}:{random_fact}\r\n"
        #s.send(text.encode())


#displays if a user left the channel
def PART_response(msg):
    leaver = msg.split('!')[0]
    leaver = leaver.replace(":", "")
    print(f"{leaver} left the channel  {msg.split()[2]}")

def someone_JOINS_channel(msg):
    joinning_user = msg.split('!')[0]
    joinning_user = joinning_user.replace(":", "")
    print(f"{joinning_user} joined {msg.split()[2]}")


def PONG_response(msg):
    text = msg.split()[1]
    msg=f"PONG {text}\r\n"
    s.send(msg.encode())

def respond_to_commands(split_server_msg, channel_name):
    response_message = ''
    friend_nick = split_server_msg[0].split('!')[0][1:] #gets the nickname of the user who sent the command
    if split_server_msg[3] == ':!hello\r\n' or split_server_msg[3] == '!hello\r\n':
        if split_server_msg[2] == "#" + channel_name:
            response_message = "PRIVMSG #"+channel_name + " :" + friend_nick + " :Hello to you too, " + friend_nick + ".\r\n"
        else:
            response_message="PRIVMSG "+friend_nick+" :Hello to you too, " + friend_nick + ".\r\n"
    elif split_server_msg[3] == ':!slap\r\n' or split_server_msg[3] == ':!slap':
        query="NAMES #"+channel_name+"\r\n" #requests names of all the users in channel
        s.send(query.encode())
        n_server_msg = s.recv(4096).decode()
        nick_string = n_server_msg.split('\r\n')[0]
        nick_arr = nick_string.split(':')[2]
        nick_arr = nick_arr.split(' ')    #puts names of all users in channel in a list
        if '' in nick_arr:
                nick_arr.remove('')
        if split_server_msg[3] == ':!slap\r\n' or split_server_msg[3] == '!slap\r\n':
            if len(nick_arr)>2:
                rand_nick = random.choice(nick_arr) #gets random user from user list
                while rand_nick==nick or rand_nick == friend_nick: #if random user is bot or the user who sent the command, try again
                    rand_nick = random.choice(nick_arr)
                response_message = "PRIVMSG #" + channel_name + " :" + rand_nick + " :You've been slapped with a trout!\r\n"
            else:
                response_message = "PRIVMSG #" + channel_name + " :" + friend_nick + " :Not enough users to slap :(\r\n"
        else:
            if split_server_msg[4].strip() in nick_arr: #checks if user is in user list
                response_message = "PRIVMSG #" + channel_name + " :" + split_server_msg[4].strip() + " :You've been slapped with a trout!\r\n"
            else:
                response_message = "PRIVMSG #" + channel_name + " :" + friend_nick + " :Couldn't find user to slap :(\r\n"
    s.send(response_message.encode())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='Server address')
    parser.add_argument('--port', type=int, help='Port number')
    parser.add_argument('--name', help='Nick, username, and real name of the bot')
    parser.add_argument('--channel', help='Channel the bot should join')
    args = parser.parse_args()
    atexit.register(disconnect)
    connection_success = False
    try_num = 0
    while not connection_success:
        if args.host:
            server = args.host
        else:
            server = input("Enter a server: ")  # '::1'

        if args.port:
            port = args.port
        else:
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
        if (connection_success==0):
            try_num+=1
        if try_num>3:
            print('Server unavailable.')
            exit()

    nick = log_in(args.name)
    channel_n=JOIN_channel(args.channel) #getting channel name
    while True:
        server_msg = s.recv(1024).decode()
        split_server_msg = server_msg.split(' ') #splits server message by spaces
        if split_server_msg[0] == 'PING':
                PONG_response(server_msg)
        elif len(server_msg) == 0:
                print('Server disconnected.')
                exit()
        elif split_server_msg[1] == 'PRIVMSG' and (split_server_msg[3] == ':!hello\r\n' or split_server_msg[3] == ':!slap\r\n' or split_server_msg[3] == ':!slap' or split_server_msg[3] == '!hello\r\n' or split_server_msg[3] == '!slap\r\n' or split_server_msg[3] == '!slap'):
                respond_to_commands(split_server_msg, channel_n)
        elif split_server_msg[1] == 'PRIVMSG' :
                print("Message received")
                #print(split_server_msg)
                respond_to_PRIVMSG(server_msg, nick)
        elif split_server_msg[1] == 'PART':
                PART_response(server_msg)
        elif split_server_msg[1] == 'JOIN':
                someone_JOINS_channel(server_msg)
main()
