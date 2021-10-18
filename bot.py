import socket
import time
import random
import argparse
import atexit

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

"""
Logging in/registering using IRC protocol
"""
##Error handling needed to check:
#   1)if nic, usern, realn have acceptable characters, format, length
#   2)if username is in use (is it included in IRC?)
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
	while in_use:
		while not nick_valid:
			nick=input("Enter a nickname: ")
			if len(nick) < 10 and len(nick) > 0 and not nick[0].isdigit() and check_name_validity(nick) and nick.find(' ')==-1:  #checks nickname validity
				nick_valid = True
			else:
				print("Nickname not valid (1-9 characters length, first character can't be - or a digit).")
		request="NICK "+nick+"\r\nUSER "+user+" "+mode_str+" * :"+realname+"\r\n"
		s.send(request.encode())
		result= s.recv(4096).decode() ## 4096 - buffer
		nick_inuse_text = "Nickname is already in use" #migh need to be adjusted based on the message sent by a server when a nickname already in use
		if nick_inuse_text in result:
			print("Nickname is already in use choose another one")
			nick_valid=False
		else:
			print("Bot was successfully registered")
			in_use=False




##Error handling needed to check:
#   1) if bot joins a non-existing channel
def JOIN_channel(channel_arg):
	if channel_arg:
		channel_name=channel_arg
	else:
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

	random_fact = random.choice(open("facts").readlines())

	#if the message was sent via a public channel(e.g. #test) and directed to the bot
	if(server_msg.find(channel_name) !=-1):
		random_fact = "PRIVMSG #"+channel_name +" :"+ receiver1[0] + " :"+random_fact+"\r\n"
	else:
		# if the message was sent privately and directed to the bot
		random_fact="PRIVMSG "+receiver1[0]+" :"+random_fact+"\r\n"

	s.send(random_fact.encode())

def PONG_response():
	msg="PONG bot is still alive"
	s.send(msg.encode())

def respond_to_commands(split_server_msg, channel_name):
	friend_nick = split_server_msg[0].split('!')[0][1:] #gets the nickname of the user who sent the command
	if split_server_msg[3] == ':!hello\r\n':
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
		nick_arr = nick_arr.split(' ')	#puts names of all users in channel in a list
		if split_server_msg[3] == ':!slap\r\n':
			if len(nick_arr)>2:
				rand_nick = random.choice(nick_arr) #gets random user from user list
				while rand_nick==nick or rand_nick == friend_nick: #if random user is bot or the user who sent the command, try again
					rand_nick = random.choice(nick_arr)
				response_message = "PRIVMSG #" + channel_name + " :" + rand_nick + " :You've been slapped with a trout!\r\n"
			else:
				response_message = "PRIVMSG #" + channel_name + " :" + friend_nick + " :Not enough users to slap :(\r\n"
		else:
			if split_server_msg[4].strip() in nick_arr: #checks if user is in user list (doesn't work yet)
				response_message = "PRIVMSG #" + channel_name + " :" + split_server_msg[4].strip() + " :You've been slapped with a trout!\r\n"
				print("opt 1" + response_message)
			else:
				response_message = "PRIVMSG #" + channel_name + " :" + friend_nick + " :Couldn't find user to slap :(\r\n"
				print("opt 2" + response_message)
	s.send(response_message.encode())

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--host', help='Server address')
	parser.add_argument('--port', type=int, help='Port number')
	parser.add_argument('--name', help='Nick, username, and real name of the bot')
	parser.add_argument('--channel', help='Channel the bot should join')
	args = parser.parse_args()

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

	log_in(args.name)
	channel_n=JOIN_channel(args.channel) #getting channel name
	while True:
		server_msg = s.recv(4096).decode()
		print(server_msg)
		split_server_msg = server_msg.split(' ') #splits server message by spaces
		#print(split_server_msg)
		if split_server_msg[0] == 'PING':
			PONG_response()
		elif len(server_msg) == 0:
			print('Server disconnected.')
			exit()
		elif split_server_msg[1] == 'PRIVMSG' and split_server_msg[2] == nick:
			print("Private message received")
			respond_to_PRIVMSG(server_msg, channel_n)
		elif split_server_msg[1] == 'PRIVMSG' and (split_server_msg[3] == ':!hello\r\n' or split_server_msg[3] == ':!slap\r\n' or split_server_msg[3] == ':!slap'):
			respond_to_commands(split_server_msg, channel_n)

	atexit.register(disconnect)
	#time.sleep(10)
	#s.close()


main()