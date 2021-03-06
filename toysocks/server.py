from toysocks.eventloop import AsyncFunc, Future, EventLoop, register_read, register_write, \
  register_read_write, unregister
from selectors import EVENT_WRITE, EVENT_READ
from toysocks.utils import sock_callback, reg_socket_future_read, reg_socket_future_write,\
  close_if, reg_multi_sockets_future_read
from toysocks.socks5 import decode_greating, decode_connection_request, \
  encode_connection_repsonse
from toysocks.utils import SocketFailure, check_socket, bytes_to_port_num
from toysocks.encrypt import Encryptor, XOREncryptor, Plain, TaggedXOREncryptor
from toysocks.relay import relay
from toysocks.socks5 import decode_sock5_addr, bytes_ip_to_string

from typing import *
import socket
import logging

class SSServer(AsyncFunc):

  def __init__(self,
               loop: EventLoop,
               remote_addr: Tuple[str, List[int]],
               encryptor : Encryptor):
    self.remote_ip, self.remote_ports = remote_addr
    self.encryptor = encryptor
    self.loop = loop

  @property
  def coroutine(self):
    return self.run()

  def run(self):
    remote_socks = []
    for port in self.remote_ports:
      remote_sock = socket.socket()
      remote_sock.setblocking(False)
      remote_sock.bind((self.remote_ip, port))
      remote_sock.listen()
      remote_socks.append(remote_sock)

    for s in remote_socks:
      logging.info("Listening at %s:%s" % (s.getsockname()))

    try:
      while True:
        yield from self.wait_client_connection(remote_socks)
    finally:
      for s in remote_socks:
        s.close()

  def wait_client_connection(self, remote_socks: List[socket.socket]):
    future = Future()
    reg_multi_sockets_future_read(future, remote_socks)
    remote_sock = yield future
    local_sock, local_addr = remote_sock.accept()
    local_sock.setblocking(False)

    logging.info("Connection from %s:%d to %s:%d" % (local_addr + remote_sock.getsockname()))
    self.loop.add_event(self.local_handle(local_sock, local_addr))

  def local_handle(self, local_sock : socket.socket, local_addr : Tuple[str, int]):
    try:
      yield from self.server_relay(local_sock, local_addr)
    except ValueError as e:
      logging.error(str(e))
    except SocketFailure as e:
      logging.error(str(e))
    except ConnectionAbortedError as e:
      logging.error(str(e))
    except OSError as e:
      logging.error(str(e))
    finally:
      if local_sock.fileno() != -1:
        local_sock.close()

  def server_relay(self, local_sock, local_addr):

    server_sock = socket.socket()
    server_sock.setblocking(False)

    def local_data_to_server_data(data : bytes, offset : int):
      decoded_data = self.encryptor.decode(data, offset)
      if offset == 0:
        addr_type, dest_addr, port = decode_sock5_addr(decoded_data)
        if addr_type == 1:
          real_addr = dest_addr
          server_dest = bytes_ip_to_string(real_addr), bytes_to_port_num(port)
        elif addr_type == 3:
          real_addr = dest_addr[1:]
          server_dest = real_addr.decode('utf-8'), bytes_to_port_num(port)
        else:
          logging.error("Sorry, not implemented for ipv6. ")
          raise ValueError("Unimplemented addr_type: %d" % addr_type)

        try:
          logging.info("%s:%d reaching for %s:%d" % (local_addr + server_dest))
          server_sock.connect(server_dest)
        except BlockingIOError:
          pass

        return decoded_data[1 + len(dest_addr) + len(port):], 0
      else:
        return decoded_data, 0

    def server_to_local_data(data : bytes, offset : int):
      encoded = self.encryptor.encode(data, offset)
      #logging.debug("data get from server (%d, %d):\n%s" % (offset, len(data), data))
      return encoded, 0

    yield from relay(local_sock, server_sock, local_data_to_server_data, server_to_local_data)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)

  ver, length, methods = decode_greating(bytes([0, 1, 2, 3]))
  print(methods)

  encryptor = TaggedXOREncryptor("fuckyouleatherman")
  #encryptor = Plain()

  event_loop = EventLoop()
  ss_local = SSServer(event_loop, ('127.0.0.1', [3456, 2888, 7999]), encryptor)
  event_loop.add_event(ss_local.coroutine)
  event_loop.run_forever()

