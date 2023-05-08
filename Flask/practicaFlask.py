import json
import time
import getpass
import paramiko
from Router import Router
from flask import Flask, jsonify, url_for, request, Response
app = Flask(__name__)


with open('dispositivos.json', 'r') as f:
    hosts = json.load(f)
    print("routers loaded:")
    print(hosts)


max_buffer = 65535


def clear_buffer(conexion):
    if conexion.recv_ready():
        return conexion.recv(max_buffer)


def createConnection(host, usuario, password):
    conexion = paramiko.SSHClient()
    conexion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        conexion.connect(host, username=usuario,
                         password=password, look_for_keys=False, allow_agent=False)
        print("new connection to" + host)
        return conexion
    except:
        print("An exception occurred: connection failed")
        return None


class Commander:
    def __init__(self, router):
        self.router = router

    def testRouter(self):
        return self.executeCommand(command="help")

    def getInterfaceBrief(self):
        return self.executeCommand(command="sh ip int br")

    def getUsersBrief(self):
        return self.executeCommand(command="sh run | i username")

    def deleteUser(self, user):
        connection = createConnection(
            host=self.router.host, usuario=self.router.user, password=self.router.password)
        if connection:
            shell = connection.invoke_shell()
            shell.send("config t\n")
            shell.send("no username " + user + "\n")
            shell.send("exit t\n")
            while not shell.recv_ready:
                time.sleep(1)
            console_out = shell.recv(65535)
            # print("executing: ", command, console_out)

            return str(console_out)
        else:
            return "Error al conectar con SSH"

    def setUser(self, user, password, priv):
        connection = createConnection(
            host=self.router.host, usuario=self.router.user, password=self.router.password)
        if connection:
            shell = connection.invoke_shell()
            shell.send("config t\n")
            shell.send("username " + user + " privilege " +
                       priv + " password " + password + "\n")
            shell.send("exit t\n")
            while not shell.recv_ready:
                time.sleep(1)
            console_out = shell.recv(65535)
            # print("executing: ", command, console_out)

            return str(console_out)
        else:
            return "Error al conectar con SSH"

        # command = "config terminal \nusername " + user + " privilege " + priv + " password " + password
        # return self.executeCommand(command)

    # todo: implement
    def executeCommands(self, commands):
        return None

    def executeCommand(self, command):
        connection = createConnection(
            host=self.router.host, usuario=self.router.user, password=self.router.password)
        if connection:
            (stdin, stdout, stderr) = connection.exec_command(command)
            console_out = stdout.read()
            print("executing: ", command, console_out)

            return str(console_out)
        else:
            return "Error al conectar con SSH"


def getRouter(hostname):
    routers = hosts

    for i in range(len(routers)):
        if routers[i]["hostname"] == hostname:
            print(f'R data: {routers[i]["data"]}')

            host = routers[i]["data"]["ip"]
            user = routers[i]["data"]["user"]
            password = routers[i]["data"]["password"]
            try:
                interfaces_list = routers[i]["interfaces"]
            except:
                interfaces_list = "None"
            return Router(hostname, host, user, password, interfaces_list)
    else:
        return None


def getRouters():
    routers = hosts
    routers_objects = []
    for i in range(len(routers)):
        hostname = routers[i]["hostname"]
        host = routers[i]["data"]["ip"]
        user = routers[i]["data"]["user"]
        password = routers[i]["data"]["password"]
        try:
            interfaces_list = routers[i]["interfaces"]
        except:
            interfaces_list = "None"

        routers_objects.append(Router(hostname, host, user, password, interfaces_list))
    return routers_objects


@app.route('/usuarios', methods=['GET', 'POST', 'DELETE', 'PUT'])
def usuarios():
    if request.method == 'GET':
        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            console_out = cmder.getUsersBrief()
            
            splitted_out_by_user = console_out.split("username")
            user_list = []
            for unformated_user in splitted_out_by_user:
                splited_unformated_user = unformated_user.split(" ")
                cant_users = 0
                if len(splited_unformated_user)>1:
                    cant_users = cant_users + 1
                    user = splited_unformated_user[1]
                    if splited_unformated_user[2] == "privilege":
                        privilege = splited_unformated_user[3]
                        password_type = splited_unformated_user[4]
                    else:
                        privilege = "None"
                        password_type = splited_unformated_user[2]
                    user_json = {
                        "user": user,
                        "privilege": privilege,
                        "password_type": password_type
                    }
                    user_list.append(user_json)  

            print(user_list)

            router_result = {
                "router": router.name,
                "usuarios": cant_users,
                "user_list": user_list,
                "original_ouput": console_out
            }

            JSONResposes.append(router_result)

        response_json = {
            "results": JSONResposes
        }
        return jsonify(response_json)
    elif request.method == 'POST':
        data = request.json

        user = data.get('user')
        if user == None or user == "":
            return "user is required"

        password = data.get('password')
        if password == None or password == "":
            return "password is required"

        priv = data.get('privilege')
        if priv == "" or priv ==None:
            priv = "1"
        if priv not in ["1", "15"]:
            return "privilege must be 1 or 15"

        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            JSONResposes.append("router=" + router.name + ", " + "response=" + cmder.setUser(
                user=user, password=password, priv=priv))
        
        response_json = {
        "data" : {
            "user": user,
            "password": password,
            "privilege": priv
        },
        "result": JSONResposes
        }

        return jsonify(response_json)
    elif request.method == 'PUT':
        data = request.json
        new_user = data.get('new_user')
        user = data.get('user')
        if user == None or user == "":
            return "user is required"

        password = data.get('password')
        if password == "" or password == None:
            return "password cannot be emṕty"

        priv = data.get('privilege')
        if priv == None:
            return "privilege is required"
        if priv == "":
            priv = "1"
        if priv not in ["1", "15"]:
            return "privilege must be 1 or 15"

        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            cmder.deleteUser(user=user)
            JSONResposes.append("router=" + str(router.name) + ", " + "response=" + cmder.setUser(
                user=new_user, password=password, priv=priv))

        response_json = {
        "data" : {
            "new_user": new_user,
            "old_user": user,
            "password": password,
            "privilege": priv
        },
        "result": JSONResposes
        }
        return jsonify(response_json)
    elif request.method == 'DELETE':
        data = request.json
        user = data.get('user')
        if user == None or user == "":
            return "user is required"

        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            JSONResposes.append("router=" + router.name +
                                ", " + "response=" + cmder.deleteUser(user=user))
        response_json = {
        "data" : {
            "user": user
        },
        "result": JSONResposes
        }
        return jsonify(response_json)

    else:
        return 404


@app.route('/routers/<hostname>/setUser')
def setUser(hostname):
    user = "test_user"
    password = "test_pass"
    priv = "15"
    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        cmder.setUser(user, password=password, priv=priv)
        return jsonify(response=cmder.getUsersBrief())
    else:
        return 'Hostname invalido', 400


@app.route('/routers/<hostname>/deleteUser')
def delelteUser(hostname):
    user = "test_user"
    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        cmder.deleteUser(user)
        return jsonify(response=cmder.getUsersBrief())
    else:
        return 'Hostname invalido', 400

@app.route('/routers')
def routersList():
    response = []
    routerList = getRouters()


    for router in routerList: 
        # response.append(str(router))
        # a Python object (dict):
        interfaces = "None"
        if hasattr(router, "interfaces_list") and router.interfaces_list != "" and router.interfaces_list != "":
            interfaces = router.interfaces_list
        router_json = {
        "hostname": router.name,
        "data" : {
            "ip": router.host,
            "admin_user": router.user,
            "admin_password": router.password
        },
        "interfaces": interfaces
        }

        response.append(router_json)

        
    return jsonify(result=response) 


@app.route('/routers/<hostname>/usuarios')
def users(hostname):

    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        return jsonify(response=cmder.getUsersBrief())
    else:
        return 'Hostname invalido', 400


@app.route('/routers/<hostname>/interfaces')
def interfaces(hostname):

    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        return jsonify(response=cmder.getInterfaceBrief())
    else:
        return 'Hostname invalido', 400


@app.route('/routers/<hostname>/')
def ping(hostname):

    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        return jsonify(response=cmder.testRouter())
    else:
        return 'Hostname invalido', 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
