# Desarrollar un programa en Python que correrá en la máquina virtual MV y que sea capaz levantar
# los distintos métodos de enrutamiento indicados en las ramas de la topología y permitir que exista
# conectividad en toda la red.

# Paramiko
import paramiko
import time
import os


class RouterHandler:

    def __init__(self):
        self.routers = []

    def create_routers(self, array_routers, main_router=None):
        print('Configuring routers...')
        print('Enter the password for the routers. If you leave it blank, the default password will be used.')
        routers = {}
        for router in array_routers:
            password = input('Enter password for router ' + router + ': ')
            if(router == main_router):
                routers[router] = Router(
                    main_router, '', array_routers[router]['d_user'], password)
                continue

            if(password == ''):
                password = '123'

            routers[router] = Router(router,
                                     array_routers[router]['ip_r4'], array_routers[router]['d_user'], password)
        return routers


# class router
class Router:
    def __init__(self, name, ip, user, password, subnet=''):
        self.name = name
        self.ip = ip
        self.user = user
        self.password = password
        self.subnet = subnet

    def test_ping(self):
        return self.ping_test(self.ip)

    def ping_test(self, ip):
        response = os.system("ping -c 1 " + ip)
        if response == 0:
            return True
        else:
            return False

    def getConnection(self):
        connection = paramiko.SSHClient()
        # add aes128-ctr to the list of supported ciphers, ssh-rsa as HostKeyAlgorithms and PublickeyAuthentication, and the diffie-hellman-group1-sha1 key exchange algorithm
        connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #print('connection to '+ self.user+ '@' + self.ip)
        connection.connect(self.ip, username=self.user, password=self.password,
                           timeout=5, look_for_keys=False, allow_agent=False)
        return connection

    def __str__(self) -> str:
        if self.subnet == '':
            return 'Router ' + self.name + ' : ' + self.ip + ' ' + self.user + ' ' + self.password
        return 'Router ' + self.name + ' : ' + self.ip + ' ' + self.user + ' ' + self.password + '. Subnet: ' + self.subnet


class RouterCLIMenu:

    def __init__(self, routerList_toParse, mainRouter):
        handler = RouterHandler()
        routers = handler.create_routers(routerList_toParse, mainRouter)

        self.routerList = routers
        self.mainRouter = self.routerList[mainRouter]
        self.selected = None

    def show_menu(self):
        print('Select a router: ')
        for router in self.routerList:
            if router == self.mainRouter:
                continue
            print(router)
        print('0. Exit')
        option = input('Enter option: ')
        if(option == '0'):
            return
        else:
            # check if is a number
            if(option.isnumeric()):
                option = 'R' + str(option)

            if(option not in self.routerList):
                # clear the console
                os.system('cls' if os.name == 'nt' else 'clear')
                print('Invalid option')
                self.show_menu()
                return

            # clear the console
            os.system('cls' if os.name == 'nt' else 'clear')
            print('Main router: ' + str(self.mainRouter))
            print('Selected router: ' + option)
            self.selected = self.routerList[option]
            self.show_menu_options()

    def show_menu_options(self):

        print("Connecting to router...")
        # Start SSH connection
        try:
            connection = self.mainRouter.getConnection()
            print("Connected to router " + self.selected.name)
            connection.close()
        except Exception as e:
            print("Connection error: " + str(e))
            self.show_menu()
            return

        if(self.selected == None):
            return
        else:
            print('Select the option: ')
            print('1. Show Interfaces')
            print('2. Show Routing Table')
            print('3. Complete Backbone')
            print('6. Test Connectivity (ping)')
            print('0. Select another router')
            option = input('Enter option: ')
            if(option == '0'):
                # clear the console
                os.system('cls' if os.name == 'nt' else 'clear')
                self.show_menu()
            elif(option == '1'):
                self.show_interfaces()
            elif(option == '2'):
                self.show_routing_table()
            elif(option == '3'):
                self.complete_backbone()
            elif(option == '4'):
                print('Testing connectivity...')
                if(self.selected.test_ping()):
                    print('Connectivity OK')
                else:
                    print('Connectivity FAIL')
                time.sleep(2)
                # clear the console
                os.system('cls' if os.name == 'nt' else 'clear')
                self.show_menu_options()
            elif(option == '7'):
                self.complete_backbone()

            else:
                print('Invalid option')
                self.show_menu_options()

    # Option 1
    def show_interfaces(self):
        print('show interfaces')

        print("Connecting to router...")
        # Start SSH connection
        try:
            connection = self.mainRouter.getConnection()
            print("Connected to router " + self.mainRouter.name)

            stdin, stdout, stderr = connection.exec_command('show interfaces')
            print(stdout.read().decode('utf-8'))

            connection.close()
        except Exception as e:
            print("Connection error: " + str(e))
            self.show_menu()
            return

    # Option 2
    def show_routing_table(self):
        print('show routing table')
        print("Connecting to router...")
        # Start SSH connection
        try:
            connection = self.mainRouter.getConnection()
            print("Connected to router " + self.mainRouter.name)

            stdin, stdout, stderr = connection.exec_command('show ip route')
            print(stdout.read().decode('utf-8'))

            connection.close()
        except Exception as e:
            print("Connection error: " + str(e))
            self.show_menu()
            return

    def configure_rip(self):
        print('configure rip')
        print("Connecting to router...")
        # Start SSH connection
        try:
            connection = self.mainRouter.getConnection()
            stdin, stdout, stderr = connection.exec_command(
                'configure terminal')
            stdin, stdout, stderr = connection.exec_command('router rip')
            stdin, stdout, stderr = connection.exec_command('version 2')
            stdin, stdout, stderr = connection.exec_command(
                'network ' + self.selected.subnet)
            stdin, stdout, stderr = connection.exec_command('end')
            print(stdout.read().decode('utf-8'))

            connection.close()
        except Exception as e:
            print("Connection error: " + str(e))
            self.show_menu()
            return

        print("Connected to router " + self.mainRouter.name)

    def complete_backbone(self):
        commands = [
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
            'show ip route']
        
        print("Connecting to router...")
        # Start SSH connection
        try:
            connection = self.mainRouter.getConnection()
            print("Connected to router " + self.mainRouter.name)

            for command in commands:
                stdin, stdout, stderr = connection.exec_command(command)
                print(stdout.read().decode('utf-8'))

            connection.close()
        except Exception as e:
            print("Connection error: " + str(e))
            self.show_menu()
            return
        

    # def configure_ospf(self):
    #     print('configure ospf')
    #     print("Connecting to router...")
    #     # Start SSH connection
    #     try:
    #         connection = self.mainRouter.getConnection()
    #         stdin, stdout, stderr = connection.exec_command(
    #             'configure terminal')
    #         stdin, stdout, stderr = connection.exec_command('router ospf 1')
    #         stdin, stdout, stderr = connection.exec_command(
    #             'network ' + self.selected.subnet + ' area 0')
    #         stdin, stdout, stderr = connection.exec_command('end')
    #         print(stdout.read().decode('utf-8'))

    #         connection.close()
    #     except Exception as e:
    #         print("Connection error: " + str(e))
    #         self.show_menu()
    #         return

    #     print("Connected to router " + self.mainRouter.name)

    # def configure_static_routes(self):
    #     print('configure static routes')
    #     print("Connecting to router...")
    #     # Start SSH connection
    #     try:
    #         connection = self.mainRouter.getConnection()
    #         print("Connected to router " + self.mainRouter.name)

    #         stdin, stdout, stderr = connection.exec_command(
    #             'configure terminal')
    #         stdin, stdout, stderr = connection.exec_command(
    #             'ip route ' + self.selected.subnet + ' ' + self.selected.ip_r4)
    #         stdin, stdout, stderr = connection.exec_command('end')
    #         print(stdout.read().decode('utf-8'))

    #         connection.close()
    #     except Exception as e:
    #         print("Connection error: " + str(e))
    #         self.show_menu()
    #         return


def main():
    array_routers = {
        'R1': {
            'subnet': '10.0.5.0/24',
            'ip_r4': '10.0.2.1',
            'd_user': 'roy',
        },
        'R2': {
            'subnet': '10.0.6.0/24',
            'ip_r4': '10.0.2.5',
            'd_user': 'roy',
        },
        'R3': {
            'subnet': '10.0.7.0/24',
            'ip_r4': '10.0.2.9',
            'd_user': 'roy',
        },
        'R4': {
            'subnet': '10.0.1.0/24',
            'ip_r4': '10.0.1.1',
            'd_user': 'roy',
        }
    }

    # For the main router the ip_r4 is used as the ip VM interface connected to the router. To use the ssh connection.
    menu = RouterCLIMenu(array_routers, 'R4')
    menu.show_menu()

main()