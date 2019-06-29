# Usage:
#
# $socks5ping.py www.baidu.com
# Connected to www.baidu.com[:80]: seq=1 time=1.47s
# Connected to www.baidu.com[:80]: seq=2 time=1.27s
# Connected to www.baidu.com[:80]: seq=3 time=1.18s
# Connected to www.baidu.com[:80]: seq=4 time=1.15s
#
# $socks5ping.py -h
# usage: socks5ping.py [-h] [-s SOCKS5HOST] [-o SOCKS5PORT] [-p PORT]
#                      [-r REPEAT] [-l] [-v]
#                      tg
#
# positional arguments:
#   tg                    Target host you want to ping.
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -s SOCKS5HOST, --socks5host SOCKS5HOST
#                         Socks5 host address, default localhost.
#   -o SOCKS5PORT, --socks5port SOCKS5PORT
#                         Socks5 port, default 1080.
#   -p PORT, --port PORT  Target port you want to ping. default 80.
#   -r REPEAT, --repeat REPEAT
#                         The times you want to repeat. default 4.
#   -l, --use-ssl         Whether use ssl for socks5. default False.
#   -v, --verbose         Print more information.


import socket
import time
import ssl
import argparse
import logging



def create_greating(methods: list=None):
    if methods is None:
        methods = [0]

    return b'\x05' + bytes([len(methods)]) + bytes(methods)

def create_connection_request(dest: str, port_num: int):
    dest = dest.encode('utf-8')
                # CMD        # ADDR TYPE
    return b'\x05\x01\x00' + b'\x03' + bytes([len(dest)]) + dest + int.to_bytes(port_num, 2, "big")

def socks5ping(socks5host: str,
               socks5port: int,
               target_host: str,
               target_port: int,
               use_ssl: bool,
               data: bytes):
    try:
        result = {}

        t1 = time.perf_counter()
        sock = socket.create_connection((socks5host, socks5port))
        if use_ssl:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.verify_mode = ssl.CERT_NONE
            sock = ssl_context.wrap_socket(sock)

        sock.sendall(create_greating())
        sock.recv(4096)  # To simulate browser waiting for socks5 response
        t2 = time.perf_counter()
        result["socks_delay_1"] = t2 - t1

        t1 = time.perf_counter()
        sock.sendall(create_connection_request(target_host, target_port))
        sock.recv(4096)  # To simulate browser waiting for connection status
        t2 = time.perf_counter()
        result["socks_delay_2"] = t2 - t1

        t1 = time.perf_counter()
        sock.sendall(data)
        tg_data = sock.recv(1400)
        t2 = time.perf_counter()
        result["tcp_delay_1"] = t2 - t1

        if len(tg_data) == 0:
            logging.warning("Got empty reply, failed! ")

        logging.info(("Got data from target: %r" % tg_data)[0:80] + "...")

        return result
    finally:
        sock.close()

def fake_http_request(host: str):
    get_request = ("""
    
GET / HTTP/1.1
Host: %s
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8

    """ % host).strip().encode("utf-8").replace(b'\n', b'\r\n') + b'\r\n\r\n'
    return get_request

def run_ping(socks5host: str,
             socks5port: int,
             target_host: str,
             target_port: int,
             repeat: int,
             use_ssl: bool):
    for i in range(1, repeat+1):
        t1 = time.perf_counter()
        result = socks5ping(socks5host=socks5host,
                            socks5port=socks5port,
                            target_host=target_host,
                            target_port=target_port,
                            use_ssl=use_ssl,
                            data=fake_http_request(host=target_host))
        t2 = time.perf_counter()
        print("Connected to %s[:%d]: seq=%d time=%.2fs" % (target_host, target_port, i, t2 - t1))
        logging.info(result)
        time.sleep(max(0.5, 0.5 - (t2 - t1)))



parser = argparse.ArgumentParser()
parser.add_argument("-s", "--socks5host", type=str, help="Socks5 host address, default localhost. ", default="localhost")
parser.add_argument("-o", "--socks5port", type=int, help="Socks5 port, default 1080. ", default=1080)
parser.add_argument("tg", type=str, help="Target host you want to ping. ")
parser.add_argument("-p", "--port", type=int, help="Target port you want to ping. default 80. ", default=80)
parser.add_argument("-r", "--repeat", type=int, help="The times you want to repeat. default 4. ", default=4)
parser.add_argument("-l", "--use-ssl", action="store_true", help="Whether use ssl for socks5. default False. ", default=False)
parser.add_argument("-v", "--verbose", action="store_true", help="Print more information. ", default=False)

args = parser.parse_args()

socks5host: str = args.socks5host
socks5port: int = args.socks5port
target_host: str = args.tg
target_port: int = args.port
repeat: int = args.repeat
use_ssl: bool = args.use_ssl
verbose: bool = args.verbose

if not verbose:
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

run_ping(socks5host=socks5host,
         socks5port=socks5port,
         target_host=target_host,
         target_port=target_port,
         repeat=repeat,
         use_ssl=use_ssl)

