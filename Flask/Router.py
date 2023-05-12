class Router:
    def __init__(self, name, host, user, password):
        self.name = name
        self.host = host
        self.user = user
        self.password = password

    def __init__(self, name, host, user, password, interfaces_list):
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.interfaces_list = interfaces_list

    def __init__(self, name, host, user, password, interfaces_list, ip_lookback,os,alive=True):
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.interfaces_list = interfaces_list
        self.ip_lookback = ip_lookback
        self.os = os
        self.alive = alive

    def __str__(self) -> str:
        return self.host + "," + self.user + "," + self.password
    
    