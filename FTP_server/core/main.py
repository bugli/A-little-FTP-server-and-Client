import optparse
import socketserver
from core import server
from config import  settings

class ArgvHandler():
    def __init__(self):
        self.op=optparse.OptionParser()
        # self.op.add_option("-P","--port",dest="port")
        # self.op.add_option("-s","--server",dest="server")
        option , args = self.op.parse_args()
        # print(option)
        # print(args)
        self.verify_args(option,args)


    def verify_args(self,option,args):
        cmd = args[0]
        #print(args)
        if hasattr(self,cmd):    #知识点，类的反射
            func = getattr(self,cmd)
            func()


    def start (self):
        print('the server is working')
        s = socketserver.ThreadingTCPServer((settings.IP, settings.PORT), server.FTPserverHendler)
        s.serve_forever()

    def help(self):
        print('help')