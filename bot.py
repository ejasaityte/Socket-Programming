import socket
server = input("Enter a server that you want to connect to: ")
print( "Connecting to server : " ,server) ## ::1/6667
##should connect to the server using sockets(??)

#Creating a socket
##.AF_NET - connection type
##.SOCK_STREAM - establishing TCP connection
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

ser= '::1'
port= 6667

request="GET / HTTP/1.1\nHost:" +ser+"\n\n"

s.connect((ser, port))
s.send(request.encode())
result= s.recv(4096) ## 4096 - buffer
print(result)
##alternative
while(len(result)>0 ) :
    print(result)
    result = s.recv(4096)