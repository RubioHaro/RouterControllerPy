import json
import time
import getpass
import paramiko
import graphviz
import platform 
import subprocess

from Router import Router
from Conector import Conector

from flask import Flask, jsonify, request
app = Flask(__name__)


with open('dispositivos.json', 'r') as f:
    hosts = json.load(f)
    print("routers loaded:")
    print(hosts)


max_buffer = 65535


def clear_buffer(connection):
    if connection.recv_ready():
        return connection.recv(max_buffer)


def createConnection(host, usuario, password):
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connection.connect(host, username=usuario,
                         password=password, look_for_keys=False, allow_agent=False, timeout=5)
        print("new connection to" + host)
        return connection
    except:
        print("An exception occurred: connection failed at: " + host)
        return None

class Commander:
    def __init__(self, router):
        self.router = router

    def pingInterface(interface):
        return pingHost(interface)
    
    def isAlive(self):
        r_list  = self.router.interfaces_list
        for i in range(len(r_list)):
            host = r_list[i]["ip"]
            # print("ping host:" +str(host))
            param = '-n' if platform.system().lower()=='windows' else '-c'
            command = ['ping', param, '1', host]
            self.router.alive = subprocess.call(command) == 0
        return self.router

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
            (stdin, stdout, stderr) = connection.exec_command(command=command)
            console_out = stdout.read()
            # print("executing: ", command, console_out)

            return str(console_out)
        else:
            return "Error al conectar con SSH"

def graficar(routers_objects):
    nodos = []
    conectores = []
    for i in range(len(routers_objects)):
        if(int(routers_objects[i].alive) == 1 and len(routers_objects[i].interfaces_list) > 0):
            nodos.append(routers_objects[i].name)
        for j in range(len(routers_objects[i].interfaces_list)):    
            for n in range(len(routers_objects)):
                for m in range(len(routers_objects[n].interfaces_list)):
                    try: 
                        ipInicio = str(routers_objects[i].interfaces_list[j]["ip"])
                        ipI = ipInicio.split(".")
                        if ( (int(ipI[3])%2) == 1):
                            ipI[3] = int(ipI[3])+1
                            ipD = f'{str(ipI[0])}.{str(ipI[1])}.{str(ipI[2])}.{str(ipI[3])}'
                            if str(routers_objects[n].interfaces_list[m]["ip"]) == ipD:
                                conectores.append(Conector(routers_objects[i].name,routers_objects[n].name))
                    except:
                        print(" ")

    red = graphviz.Digraph(comment='Red', node_attr={'color': 'lightblue2', 'style': 'filled'})
    red.attr(label=r'\nTopología de la red\n')

    for i in range(len(nodos)):
        red.attr('node', shape='ellipse')
        red.node( nodos[i] , label= nodos[i])
        if nodos[i] == "TOR-1":
            red.attr('node', shape='box')
            red.node('SME',label= 'SME')
            red.edge('TOR-1','SME',arrowhead='none')
   
    for i in range(len(conectores)):
        if conectores[i].inicio in nodos:
            if conectores[i].destino in nodos:
                red.edge(conectores[i].inicio , conectores[i].destino, arrowhead='none')
    
    print(red.source)
    red.render(directory='output', view=True) 

def getRouter(hostname):
    routers = hosts
    print("SEARCHING: "+ hostname)
    for i in range(len(routers)):
        if routers[i]["hostname"] == hostname:
            print(f'R data: {routers[i]["data"]}')

            host = routers[i]["data"]["ip"]
            user = routers[i]["data"]["user"]
            so = routers[i]["data"]["so"]
            ip_lookback = routers[i]["data"]["ip_lookback"]
            password = routers[i]["data"]["password"]
            try:
                interfaces_list = routers[i]["interfaces"]
            except:
                interfaces_list = "None"
            return Router(hostname, host, user, password, interfaces_list, ip_lookback, so)
        
    return None


def getRouters():
    routers = hosts
    routers_objects = []
    for i in range(len(routers)):
        hostname = routers[i]["hostname"]
        host = routers[i]["data"]["ip"]
        user = routers[i]["data"]["user"]
        so = routers[i]["data"]["so"]
        ip_lookback = routers[i]["data"]["ip_lookback"]
        password = routers[i]["data"]["password"]
        try:
            interfaces_list = routers[i]["interfaces"]
        except:
            interfaces_list = "None"

        r = Router(hostname, host, user, password, interfaces_list, so, ip_lookback)
        try:
           print("geting alive: ")
           r = Commander(r).isAlive()
        except:
            continue
        routers_objects.append(r)

    return routers_objects


@app.route('/usuarios', methods=['GET', 'POST', 'DELETE', 'PUT'])
def usuarios():
    if request.method == 'GET':
        data = request.json

        if data == None:
            request_mode = "default"
        else:
            request_mode = data.get('mode')


        routerList = getRouters()
        JSONResposes = []
        # Iterate every router
        for router in routerList:
            cmder = Commander(router)
            console_out = cmder.getUsersBrief()

            if "Error" in console_out:
                router_result = {
                    "router": router.name,
                    "usuarios": 0,
                    "original_ouput": console_out
                }
            else:
                splitted_out_by_user = console_out.split("username")
                user_list = []
                cant_users = 0
                for unformated_user in splitted_out_by_user:
                    splited_unformated_user = unformated_user.split(" ")
                    if len(splited_unformated_user) > 1:
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

                # print(user_list)

                router_result = {
                    "router": router.name,
                    "usuarios": cant_users,
                    "user_list": user_list,
                    "original_ouput": console_out
                }

            JSONResposes.append(router_result)

        if request_mode == "by_user":
            # group user and show the routers where the user is
            user_list = []
            for router_result in JSONResposes:
                try:
                    for user in router_result["user_list"]:
                        user_list.append(user["user"])
                except:
                    continue
            user_list = list(set(user_list))
            # print(user_list)

            user_list_with_routers = []
            for user in user_list:
                routers_where_user_is = []
                links_routers_where_user_is = []
                for router_result in JSONResposes:
                    try:
                        for user_in_router in router_result["user_list"]:
                            if user_in_router["user"] == user:
                                routers_where_user_is.append(
                                    router_result["router"])
                                links_routers_where_user_is.append(
                                    "http://localhost:8080/routers/"+router_result["router"])
                    except:
                        continue
                user_list_with_routers.append({
                    "user": user,
                    "routers": routers_where_user_is,
                    "routers, links:": links_routers_where_user_is
                })
           
            JSONResposes = user_list_with_routers

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
        if priv == "" or priv == None:
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
            "data": {
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
            "data": {
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
            "data": {
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
            links_interfaces = []
            for i in range(len(interfaces)):
                ip_addr = interfaces[i]["ip"]
                links_interfaces.append("http://localhost:8080/routers/" + router.name + "/interfaces/" + ip_addr) 
                
            # for interface in interfaces:
        router_json = {
            "hostname": router.name,
            "data": {
                "admin_ip": router.host,
                "ip_lookback": router.ip_lookback,
                "admin_user": router.user,
                "admin_password": router.password,
                "os": router.os
            },
            "interfaces": interfaces,
            "links-interfaces:": links_interfaces,
        }

        response.append(router_json)

    return jsonify(result=response)


@app.route('/routers/<hostname>/usuarios', methods=['GET', 'POST', 'DELETE', 'PUT'])
def users(hostname):
    selected_router = getRouter(hostname)
    if selected_router:
        if request.method == 'GET':
            cmder = Commander(selected_router)
            return jsonify(response=cmder.getUsersBrief())
            
        if request.method == 'POST':
            data = request.json

            user = data.get('user')
            if user == None or user == "":
                return "user is required"

            password = data.get('password')
            if password == None or password == "":
                return "password is required"

            priv = data.get('privilege')
            if priv == "" or priv == None:
                priv = "1"
            if priv not in ["1", "15"]:
                return "privilege must be 1 or 15"

            JSONResposes = []
            cmder = Commander(selected_router)
            JSONResposes.append("router=" + selected_router.name + ", " + "response=" + cmder.setUser(user=user, password=password, priv=priv))
            
            response_json = {
                "data": {
                    "user": user,
                    "password": password,
                    "privilege": priv
                },
                "result": JSONResposes
            }

            return jsonify(response_json)
        if request.method == 'PUT':
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

            
            cmder = Commander(selected_router)
            cmder.deleteUser(user=user)
            JSONResposes=[]
            JSONResposes.append("router=" + str(selected_router.name) + ", " + "response=" + cmder.setUser(user=new_user, password=password, priv=priv))

            response_json = {
                "data": {
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
            
            cmder = Commander(selected_router)
            JSONResposes.append("router=" + selected_router.name +", " + "response=" + cmder.deleteUser(user=user))
            response_json = {
                "data": {
                    "user": user
                },
                "result": JSONResposes
            }
            return jsonify(response_json)
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


def pingHost(host):
    print("searching for " + host)
    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, '1', host]
    res = subprocess.call(command) == 0
    return str(res)

@app.route('/topologias/grafica')
def graph():

    routers = getRouters()
    graficar(routers_objects=routers)
    return 'Mostrando Grafica', 200


@app.route('/routers/<hostname>/')
def ping(hostname):

    selected_router = getRouter(hostname)

    if selected_router:
        cmder = Commander(selected_router)
        isAlive = 0
        out = cmder.testRouter()
        if len(out) > 25:
            isAlive = 1
        router = selected_router

        interfaces = "None"
        if hasattr(router, "interfaces_list") and router.interfaces_list != "" and router.interfaces_list != "None":
            interfaces = router.interfaces_list

        response = {
            "hostname": router.name,
            "data": {
                "ip": router.host,
                "ip_lookback": router.ip_lookback,
                "admin_user": router.user,
                "admin_password": router.password,
                "os": router.os
            },
            "interfaces": interfaces,
            "is_alive": isAlive
        }
        return jsonify(response)
    else:
        return 'Hostname invalido', 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
