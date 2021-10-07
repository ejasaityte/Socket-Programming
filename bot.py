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
realname=input("Enter a real name (name and surname): ")
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

time.sleep(10)
s.close()
"""
request2="USER guest 0 * :TOT BOT"
s.send(request2.encode())
result2= s.recv(4096) ## 4096 - buffer
print(result2)
"""
#nick=input("Enter a nickname:  ")
#s.send(("NICK " + nick ).encode())
#data = s.recv(1024)
#print('Received', repr(data))


"""
#user=input("USER ")
nick="NICK "+nick
#user="USER "+user
s.send(nick)
#s.sendall('USER ')
data = s.recv(1024)
print('Received', repr(data))
"""
"""
try:

    # Send data
    message = b'This is our message. It is very long but will only be transmitted in chunks of 16 at a time'
    print('sending {!r}'.format(message))
    sock.sendall(message)

    # Look for the response
    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += len(data)
        print('received {!r}'.format(data))

finally:
    print('closing socket')
    sock.close()
"""
#request="GET / HTTP/1.1\nHost:" +server+"\n\n"

#s.connect((server, port))
#s.send(request.encode())
#result= s.recv(4096) ## 4096 - buffer
#print(result)
##alternative
#while(len(result)>0 ) :
#    print(result)
#    result = s.recv(4096)

