from flask import Flask, jsonify, url_for
app = Flask(__name__)

import paramiko, getpass, time, json

with open('dispositivos.json', 'r') as f:
    hosts = json.load(f)
    print("routers loaded:")
    print(hosts)


# max_buffer = 65535

# def clear_buffer(conexion):
#     if conexion.recv_ready():
#         return conexion.recv(max_buffer)

# # Iniciamos el ciclo para los dispositivos
# for host in hosts.keys(): 
#     nombreArchivo = host + '_salida.txt'
#     conexion = paramiko.SSHClient()
#     conexion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     conexion.connect(hosts[host]['ip'], username=usuario, password=password, look_for_keys=False, allow_agent=False)
#     nueva_conexion = conexion.invoke_shell()
#     salida = clear_buffer(nueva_conexion)
#     time.sleep(2)
#     nueva_conexion.send("terminal length 0\n")
#     salida = clear_buffer(nueva_conexion)
#     with open(nombreArchivo, 'wb') as f:
#         for comando in comandos:
#             nueva_conexion.send(comando)
#             time.sleep(2)
#             salida = nueva_conexion.recv(max_buffer)
#             print(salida)
#             f.write(salida)
    
#     nueva_conexion.close()
    

@app.route('/routers/<hostname>/interface/<int:num_interface>')
def dispositivo(hostname, num_interface):
    # usuario = input('Usuario: ')
    # password = getpass.getpass('Password: ')R5

    routers = ['R1', 'R2', 'R3','R5-tor','R6-edge']
    if hostname in routers:
        # return 'Lista de interfaces para %s' % hostname
        return jsonify(name=hostname, interface=num_interface)
    else: 
        return 'Hostname invalido'

    for router in routers: 
        with app.test_request_context():
            print(url_for('dispositivo', hostname=router, interface=num_interface))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


