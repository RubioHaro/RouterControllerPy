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
        return conexion.invoke_shell()
    except:
        print("An exception occurred: connection failed")
        return None

def executeCommand(command, router):
    connection = createConnection(
        host=router.host, usuario=router.user, password=router.password)
    if connection:
        output = clear_buffer(connection)
        time.sleep(2)
        connection.send("terminal length 0\n")
        output = clear_buffer(connection)

        connection.send(command)
        time.sleep(2)
        output = connection.recv(max_buffer)
        # print(output)

        connection.close()
        return output;
    else:
        return "Error al conectar con SSH"

class Commander:
    def __init__(self, router):
        self.router = router 

    def getInterfaceBrief(self):
        return executeCommand(command="sh ip int br",router=self.router)


class Router:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def __str__(self) -> str:
        return self.host+ "," + self.user + "," + self.password


@app.route('/routers/<hostname>/usuarios')
def dispositivo(hostname):
    routers = hosts

    result = [x for x in hosts if x["hostname"]==hostname]

    for i in range(len(routers)):
        if routers[i]["hostname"] == hostname:
            # print(f'R data: {routers[i]["data"]}')
         
            host = routers[i]["data"]["ip"]
            user = routers[i]["data"]["user"]
            password = routers[i]["data"]["password"]

            # print("creating new router....")
            
            selected_router = Router(host,user,password)

            cmder = Commander(selected_router)
            

            return jsonify(response=cmder.getInterfaceBrief())
    else:
        return 'Hostname invalido'

    for router in routers:
        with app.test_request_context():
            print(url_for('dispositivo', hostname=router, interface=num_interface))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


