import socketserver
import json
import configparser

from config import settings
import os
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


class FTPserverHendler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:

            client_data = self.request.recv(1024).strip()  # 自己接收数据了

            if client_data:
                client_data = json.loads(client_data.decode('utf-8'))
            # 因为数据传过来是json格式，使用json.loads来读取
            # json.loads 返回的是一个字典

            # print(client_data)
            # print(type(client_data))
            '''
                我们就当客户端发来的data是json信息
                {
                    "action":"auth"
                    "username":"zihao"
                    "passwd":"123"
                }
            '''
            if client_data.get('action'):
                if hasattr(self, client_data.get('action')):
                    # 类的反射!

                    func = getattr(self, client_data.get('action'))
                    func(**client_data)
                    # 将整个client_data 字典,都放到了类方法的参数里面去,所以使用**client_data传参数
                else:
                    print('Invalid action')
            else:
                print('用户端发送消息格式不正确,缺失action')

    def auth(self, **data):
        username = data['username']
        password = data['passwd']
        user = self.authenticate(username, password)
        if user:

            self.send_response(254)

        else:
            self.send_response(253)

    def authenticate(self, username, password):
        cfg = configparser.ConfigParser()
        cfg.read(settings.ACCOUNTS_FILE_PATH)
        print('cfg.sections():', cfg.sections())
        if username in cfg.sections():

            if cfg.get(username, 'Password') == password:
                #######认证完成后,取用户操作路径和用户名了#########
                self.user = username
                self.mainPath = os.path.join(
                    settings.BASE_DIR, 'home', self.user)
                self.userBasePath = os.path.join(
                    settings.BASE_DIR, 'home', self.user)

                print(username, ',passed authenticate')
                return username
                #######认证完成后,取用户操作路径和用户名了#########

    def send_response(self, state_code):
        response = {
            "status_code": state_code,
            'userBasePath': self.userBasePath}

        self.request.sendall(json.dumps(response).encode('utf-8'))

    def put(self, **data):
        print('data :', data)

        filename = data.get('filename')
        filesize = data.get('filesize')
        target_path = data.get('target_path')

        userPath = os.path.join(
            settings.BASE_DIR,
            'home',
            self.user,
            target_path)
        filePath = os.path.join(userPath, filename)
        has_esixted = os.path.exists(filePath)

        if not os.path.exists(userPath):
            os.makedirs(userPath)
        print(userPath, filePath, has_esixted)

        has_recveited = 0

        if has_esixted:
            # 文件是存在的
            file_has_size = os.stat(filePath).st_size
            if file_has_size < filesize:
                # 文件需要续传
                self.send_response(800)

                user_choice = self.request.recv(1024).decode('utf8')

                print(user_choice)

                if user_choice == 'Y':
                    # 决定续传
                    self.request.sendall(
                        str(file_has_size).encode('utf-8'))  # 发送了当前服务器存的文件的大小给客户端
                    has_recveited += file_has_size
                    f = open(filePath, 'ab')

                else:
                    # 决定不续传
                    f = open(filePath, 'wb')

            else:
                # 文件已经存在,不需要传输
                self.send_response(801)
                return

        else:
            # 文件是不存在的
            self.send_response(802)
            f = open(filePath, 'wb')

        while has_recveited < filesize:
            try:
                data = self.request.recv(1024)
            except Exception as e:
                print(e)
                break
            has_recveited = len(data) + has_recveited
            #print(has_recveited, filesize)
            f.write(data)
        f.close()

    def ls(self, **data):

        if os.path.exists(self.mainPath):
            file_list = os.listdir(self.mainPath)
        else:
            self.request.sendall(' 系统找不到指定的路径。'.encode('utf8'))
            return
        file_str = '\n'.join(file_list)
        print(file_str)
        if file_str == '':
            self.request.sendall('empty dir'.encode('utf8'))
        else:
            self.request.sendall(file_str.encode('utf8'))

    def cd(self, **data):

        target_dir = data['target_dir']

        if data['target_dir'] == '..':
            self.mainPath = os.path.dirname(self.mainPath)
            print(self.mainPath)
            self.request.sendall(self.mainPath.encode('utf8'))
        else:

            dirDoesexist = os.path.join(self.mainPath, target_dir)
            if os.path.exists(dirDoesexist):

                self.mainPath = os.path.join(self.mainPath, target_dir)

                self.request.sendall(self.mainPath.encode('utf8'))
            else:

                self.request.sendall('dir does not exist'.encode('utf8'))

    def mkdir(self, **data):
        print(type(data))
        dirname = data['dianame']

        try:
            os.makedirs(os.path.join(self.mainPath, dirname))
            self.request.sendall('Dir Created successfully'.encode('utf8'))
        except Exception as e:
            print(e)
            self.request.sendall('file is exist'.encode('utf8'))
