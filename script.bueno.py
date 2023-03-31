# Paramiko
import paramiko
import time
import os


connection = paramiko.SSHClient()
# add aes128-ctr to the list of supported ciphers, ssh-rsa as HostKeyAlgorithms and PublickeyAuthentication, and the diffie-hellman-group1-sha1 key exchange algorithm
connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#print('connection to '+ self.user+ '@' + self.ip)
connection.connect('10.0.1.1', username='roy', password='123',
                   timeout=5, look_for_keys=False, allow_agent=False)

commands = [
      '\n',
      'config t',
        'ip route 10.0.5.0 255.255.255.0 10.0.2.1',
        'router rip',
        'version 2',
        'network 10.0.6.0',
        'network 10.0.2.4',
        'exit',
        'router ospf 15',
        'network 10.0.7.0 0.0.0.255 area 1',
        'network 10.0.2.8 0.0.0.3 area 1',
        'network 10.0.1.0 0.0.0.255 area 1',
        'end ',
        'show ip route'
      ]

for command in commands:
    print(command)
    stdin, stdout, stderr = connection.exec_command(command)
    time.sleep(2)
    print(stdout.read().decode('utf-8'))

connection.close()