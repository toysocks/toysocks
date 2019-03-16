# toysocks

## Remote

### Configuration
```
{
        "ip": "0.0.0.0",
        "port": [12345, 65535],
        "password": "password"
}
```
+ The configuration file should be `/root/toysocks.json`
+ `ip` is the server address binded to.
+ `port` is a list that the server listens to.
+ `password` should be secured and shared between the server and client.

### Run
+ Dependency: Python3.5.2+, Ubuntu

```
cd toysocks/
python3 server.py # or nohup python3 server.py &
```

## Client

### Overview

The client implements part of a SOCKS5 protocol, mainly to connect with the browser. It relays the SOCK5 requests and responses with the remote server in an encrypted manner.

### Configuration
```
{
	"local_ip": "127.0.0.1",
	"local_port": 1234,
	"remote_ip": "1.2.3.4",
	"remote_port": [12345, 65535],
	"password": "password"
}
```
+ The configuration file should be `C:\Users\Your Name\toysocks.json`
+ `(local_ip, local_port)` is the client server binded to.
+ `remote_ip` is the ip of remote server
+ `remote_port` is the ports of remote server. If it is an integer, client only connects to it;
  If it is a list of integers, client selects a random port each time. This is believed to
  increase robustness.

### Run
+ Dependency: Python3.5.2+, only tested on Windows 10

```
cd toysocks/
python3 client.py
```

If you want to user Chrome with the proxy, you should figure out how to use [SwitchyOmega](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif).




