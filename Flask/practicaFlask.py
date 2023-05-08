import json
import time
import getpass
import paramiko
from flask import Flask, jsonify, url_for, request
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


class Router:
    def __init__(self, name, host, user, password):
        self.name = name
        self.host = host
        self.user = user
        self.password = password

    def __str__(self) -> str:
        return self.host + "," + self.user + "," + self.password


def getRouter(hostname):
    routers = hosts

    for i in range(len(routers)):
        if routers[i]["hostname"] == hostname:
            print(f'R data: {routers[i]["data"]}')

            host = routers[i]["data"]["ip"]
            user = routers[i]["data"]["user"]
            password = routers[i]["data"]["password"]
            return Router(hostname, host, user, password)
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
        routers_objects.append(Router(hostname, host, user, password))
    return routers_objects


@app.route('/usuarios', methods=['GET', 'POST', 'DELETE', 'PUT'])
def usuarios():
    if request.method == 'GET':
        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            JSONResposes.append("router=" +router.name + ", "+  "response=" + cmder.getUsersBrief())

        return jsonify(JSONResposes)
    elif request.method == 'POST':
        data = request.json

        user = data.get('user')
        if user == None or user == "":
            return "user is required"

        password = data.get('password')
        if password == None or password == "":
            return "password is required"

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
            JSONResposes.append("router=" +router.name + ", "+  "response=" + cmder.setUser(
                user=user, password=password, priv=priv))

        return jsonify(JSONResposes)
    elif request.method == 'PUT':
        return "put method"
    elif request.method == 'DELETE':
        user = "test_user"
        password = "test_pass"
        priv = "15"

        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            JSONResposes.append(
                jsonify(router=router.name, response=cmder.deleteUser(user=user)))
        return jsonify(JSONResposes)

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
