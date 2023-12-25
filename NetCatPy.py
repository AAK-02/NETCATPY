import socket
import shlex
import threading
import argparse
import subprocess
import sys
import textwrap


class NetCat:
    def __init__(self,ARGS,BUFFER=None):
        self.ARGS=ARGS
        self.BUFFER=BUFFER

        #SET UP THE SOCKET TO IP4 AND TCP TYPE CONNECTION
        self.SOCK=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        #allow other server to connect to same port sol(socket level) so_reuseaddr(Allows the socket to be bound to an address that is already in use)
        self.SOCK.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

    #RUN METHODE CHECK IF WE RUN A LISTENER OR NOT 
    def RUN(self):
        try:
            if self.ARGS.listen:
                self.listen()
            else:
                self.send()
        except Exception as ex:
            print(ex)        
    
    #SEND METHOD THAT ALOW TO SEND AND RCV DATA FROM TARGET 
    def SEND(self):
        self.SOCK.connect((self.ARGS.target,self.ARGS.port))
        if self.BUFFER:
            self.SOCK.send(self.BUFFER)
        # RCV DATA FROM TARGET IF THERE IS NO MORE DATA WE BRAEK OUT OF THE LOOP.
        try:
            while True:
                RCV_LEN=1
                RESP=""
                while RCV_LEN:
                    DATA=self.SOCK.recv(4096)
                    RCV_LEN=len(DATA)
                    RESP+=DATA.decode()
                    if RCV_LEN <4096:
                        break
                #WE PRINT THE RESPONSE DATA AND PAUSE TO GET INTERACTIVE INPUT , AND SEND THAT INPUT
                if RESP:
                    print(RESP)
                    BUFFER=input(">> ")
                    BUFFER+="\n"
                    self.SOCK.send(BUFFER.encode())
        # BREAK THE LOOP IF THE USER CLOSE IT (CNTRL-C)
        except KeyboardInterrupt:
            print("CONNECTION CLOSED ")
            self.SOCK.close()
            sys.exit()

    #LISTEN METHOD THAT ALOW US TO START LISTEN AND GET CONNECTION WHITH THE TARGET  AND START IT AS SINGLE THREAD 
    def listen(self):
        try:
            self.SOCK.bind((self.ARGS.target,self.ARGS.port))
            self.SOCK.listen(5)  

            while True:
                CLIE_SOCK,_=self.SOCK.accept()
                CLIE_THREAD=threading.Thread(target=self.HANDLE,args=(CLIE_SOCK,))
                CLIE_THREAD.start()
        except Exception as EX:
            print(EX)


    def HANDLE(self,CLIE_SOCK):
        if self.ARGS.execute:
            OUT=EXECUTE(self.ARGS.execute)
            CLIE_SOCK.send(OUT.encode())

        elif self.ARGS.upload:
            FILE_BUFFER=b""
            while True:
                DATA=CLIE_SOCK.recv(4096)
                if DATA:
                    FILE_BUFFER+=DATA
                else:
                    break

            with open(self.ARGS.upload,"wb") as file:
                 file.write(FILE_BUFFER)
            MESS=f"SAVED {self.ARGS.upload}"
            CLIE_SOCK.send(MESS.encode())


        elif self.ARGS.command:
            CMD_BUFF=b""
            while True:
                try:

                    CLIE_SOCK.send(b'AKA: #> ')
                    while '\n' not in CMD_BUFF.decode():
                        CMD_BUFF+=CLIE_SOCK.recv(128)
                    RES=EXECUTE(CMD_BUFF.decode())
                    if RES:
                        CLIE_SOCK.send(RES.encode())
                    CMD_BUFF=b""

                except Exception as EX:
                    print('SISSION SOPTED')
                    self.SOCK.close()
                    sys.exit()
                    
                            

        




#<--------------------------------------------------------->
def EXECUTE(COMMAND):
    
    COMMAND=COMMAND.strip()
    if not COMMAND:
        return
    OUTPUT=subprocess.check_output(shlex.split(COMMAND),stderr=subprocess.STDOUT)
    return OUTPUT.decode()

if __name__ == "__main__":
    try:
        if len(sys.argv)<2:
            print('[+]: python3 scriptname.py --help')
            sys.exit()
        PARSER= argparse.ArgumentParser(
        description="PY NETCATPRO",
        formatter_class=argparse.RawDescriptionHelpFormatter,epilog=textwrap.dedent('''EXAMPLE:
        NetCatPro.py -t x.x.x.x -p 1234 -l -c (COMMAND SHELL)
        NetCatPro.py -t x.x.x.x -p 1234 -l -u=FILE.TXT (UPLOAD FILE)
        NetCatPro.py -t x.x.x.x -p 1234 -l -e=\" cat /etc/passwd\" (EXC COMMAND)
        NetCatPro.py -t x.x.x.x -p 1234 -l -c (COMMAND SHELL)
        echo 'ACK' | ./NetCatPro.py -t X.X.X.X -p 1234 (ECHO TO SERVER)
        NetCatPro.py -t x.x.x.x -p 1234 (CONNECT TO SERVER)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        )
        '''))

        PARSER.add_argument('-c','--command',action='store_true',help='command shell')
        PARSER.add_argument('-e','--execute',help=' execute specified command')
        PARSER.add_argument('-l','--listen',action='store_true',help=' listen')
        PARSER.add_argument('-p','--port',type=int,default='1234',help='specified port')
        PARSER.add_argument('-t','--target',default='192.168.1.252',help='specified IP')
        PARSER.add_argument('-u','--upload',help='upload file')

        ARGS=PARSER.parse_args()
        try:
            if ARGS.listen:
                BUFFER=""
            else:
                BUFFER=sys.stdin.read()
        except Exception as ex:
            print(ex)

        NC=NetCat(ARGS,BUFFER.encode())
        NC.RUN()
    except Exception as ex:
        print(ex)                                                                                    
