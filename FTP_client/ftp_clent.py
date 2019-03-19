
import socket
import optparse
import json
import os
import sys

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",
    800: "the file exist,but not enough ,is continue? ",
    801: "the file exist !",
    802: " ready to receive datas",
    900: "md5 valdate success"

}


class ClientHandler:

    def __init__(self):

        self.op = optparse.OptionParser()

        self.op.add_option('-s', '--server', dest='server')
        self.op.add_option('-P', '--port', dest='port')
        self.op.add_option('-u', '--username', dest='username')
        self.op.add_option('-p', '--passwd', dest='passwd')
        # python ftp_clent.py -u zihao -P 8080 -s 127.0.0.1 -p 123
        # put 12.bz2 im
        self.options, self.args = self.op.parse_args()
        print(self.options)
        # print(self.args)
        self.verify_args(self.options, self.args)
        self.make_connection()

        self.mainPATH = os.path.dirname(os.path.abspath(__file__))

        self.interA = True
        # 这里等于是找到了FTP_client的绝对路径了

    def verify_args(self, options, args):
        server = options.server
        port = options.port
        # passwd = options.passwd
        # username = options.username
        if 0 < int(port) < 65535:
            return True
        else:
            exit('Invalid port ')

    def make_connection(self):
        self.sk = socket.socket()
        self.sk.connect((self.options.server, int(self.options.port)))

    def interactive(self):
        if self.authenticate():
            print('authenticate pass!')
            print('begin to interactive')
            while self.interA:
                # input 的是一个这样的字符串: put xxx.png xxx
                cmd_info = input('[%s]:' % self.currdir).strip()
                cmd_info_list = cmd_info.split()
                # print(cmd_info_list)
                if hasattr(self, cmd_info_list[0]):
                    func = getattr(self, cmd_info_list[0])
                    func(*cmd_info_list)

    def put(self, *put_info_list):
        # put xxx.png  目标目录
        action, local_path, target_path = put_info_list
        local_path = os.path.join(self.mainPATH, local_path)
        file_name = os.path.basename(local_path)

        file_size = os.stat(local_path).st_size
        print(file_name, file_size, local_path)

        data = {
            "action": 'put',
            "filename": file_name,
            "filesize": file_size,
            "target_path": target_path

        }
        self.sk.send(json.dumps(data).encode('utf8'))
        responds = self.response()  # 回传的状态码
        ###########################################

        has_sent = 0

        if responds['status_code'] == 800:
            # 文件不完整,需要断点续传
            pass
            choice = input('the file exist,but not enough ,is continue? [Y/N]')
            if choice.upper() == 'Y':
                # 决定续传
                self.sk.sendall('Y'.encode('utf8'))
                # 收到了当前服务器存的文件的大小给客户端
                continue_position = self.sk.recv(1024).decode('utf8')
                has_sent = int(continue_position)

                f = open(local_path, 'rb')
                f.seek(has_sent)

            else:
                # 决定不续传

                self.sk.sendall('N'.encode('utf8'))

        elif responds['status_code'] == 801:
            # 文件完全存在
            return

        else:  # 那就是等于802,文件在服务器不存在,直接全部文件传过去

            f = open(local_path, 'rb')

        while has_sent < file_size:
            data = f.read(1024)
            self.sk.sendall(data)
            has_sent += len(data)
            self.show_processbar(has_sent, file_size)
        f.close()
        print('put success')

    def ls(self, *cmd_info_list):
        data = {
            "action": 'ls',
        }
        self.sk.sendall(json.dumps(data).encode('utf8'))
        ls_result = self.sk.recv(1024).decode('utf8')
        print(ls_result)

    def cd(self, *cmd_info_list):
        # cd xxx/xxx
        data = {
            "action": 'cd',
            "target_dir": cmd_info_list[1]

        }
        self.sk.sendall(json.dumps(data).encode('utf8'))
        # 进入的result

        cd_result = self.sk.recv(1024).decode('utf8')
        if cd_result == 'dir does not exist':
            print('dir does not exist')
        else:
            print(cd_result)
            self.currdir = cd_result.replace(self.userBasePath, self.user)
            # self.currdir=os.path.basename(cd_result)
            print(self.currdir)

    def mkdir(self, *cmd_info_list):
        data = {
            "action": 'mkdir',
            "dianame": cmd_info_list[1]
        }
        self.sk.sendall(json.dumps(data).encode('utf8'))
        # mkdir
        cdmkdir_result = self.sk.recv(1024).decode('utf8')
        print(cdmkdir_result)

    def show_processbar(self, has_sent, file_size):
        precent = int((has_sent / file_size) * 100)
        well_num = precent // 2 * '#'
        s1 = "[%s %% %s ]" % (precent, well_num)
        print(s1, flush=True)


    def quit(self, *quit_info_list):

        self.sk.close()
        self.interA = False

    def authenticate(self):
        if self.options.username is None or self.options.passwd is None:
            username = input('username:')
            passwd = input('password:')
            return self.get_auth_result(username, passwd)
        else:
            return self.get_auth_result(
                self.options.username, self.options.passwd)

    def get_auth_result(self, user, psw):
        data = {

            "action": "auth",
            "username": user,
            "passwd": psw

        }

        self.sk.send(json.dumps(data).encode('utf-8'))
        responds = self.response()
        print(responds['status_code'])
        if responds['status_code'] == 254:
            self.user = user
            self.currdir = user
            self.userBasePath = responds['userBasePath']
            print(self.userBasePath)

            print(STATUS_CODE[254])
            return True
        else:
            print(STATUS_CODE[responds['status_code']])

    def response(self):

        data = self.sk.recv(1024).decode('utf-8')
        data = json.loads(data)

        return data


if __name__ == '__main__':

    ch = ClientHandler()

    ch.interactive()
