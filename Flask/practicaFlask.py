import json
import time
import getpass
import paramiko
from flask import Flask, jsonify, url_for
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

    def executeCommand(self, command):
        connection = createConnection(
            host=self.router.host, usuario=self.router.user, password=self.router.password)
        if connection:
            (stdin, stdout, stderr) = connection.exec_command(command)
            console_out = stdout.read()
            print("executing: ", command, console_out)
            
            return str(console_out);
        else:
            return "Error al conectar con SSH"



class Router:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def __str__(self) -> str:
        return self.host+ "," + self.user + "," + self.password


def getRouter(hostname):
    routers = hosts

    for i in range(len(routers)):
        if routers[i]["hostname"] == hostname:
            print(f'R data: {routers[i]["data"]}')
         
            host = routers[i]["data"]["ip"]
            user = routers[i]["data"]["user"]
            password = routers[i]["data"]["password"]
            return Router(host,user,password) 
    else:
        return None


@app.route('/routers/<hostname>/usuarios')
def dispositivo(hostname):

    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        return jsonify(response=cmder.getInterfaceBrief())
    else:
        return 'Hostname invalido'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


