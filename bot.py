import socket
import time
##server ::1/6667
server = input("Enter a server: ") # '::1'
port = input("Enter a port: ")
port = int(port) #6667

#Creating a socket
##.AF_NET - connection type
##.SOCK_STREAM - establishing TCP connection

s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.connect((server, port))

#Log in to IRC by specifying NICK and USERNAME
mode=0 #should be increased for every single client joining the server
nick=input("Enter a nick name: ")
user=input("Enter a user name: ")
realname=input("Enter a real name (e.g. Name Surname): ")
mode_str=str(mode)

request="NICK "+nick+"\r\nUSER "+user+" "+mode_str+" * :"+realname+"\r\n"
s.send(request.encode())
result= s.recv(4096) ## 4096 - buffer
print(result)

#JOIN the chat
chat_name = input("Enter chat name: ")
request1="JOIN #"+chat_name+"\r\n"
s.send(request1.encode())
result= s.recv(4096) ## 4096 - buffer
print(result)



while True:
    server_msg = s.recv(4096).decode()
    print(server_msg) #display everything that server sends to bot
    #if(server_msg.find("PRVMSG" )==0): #if a private message was sent to bot




#time.sleep(10)
#s.close()