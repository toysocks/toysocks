from toysocks.eventloop import EventLoop, Future, register_read_write, unregister
from toysocks.encrypt import Encryptor
from toysocks.utils import check_socket

import socket
import logging
import errno
from selectors import EVENT_READ, EVENT_WRITE

def relay(sock1 : socket.socket,
          sock2 : socket.socket,
          sock1_data_to_sock2_data = lambda x, offset : (x, 0),
          sock2_data_to_sock1_data = lambda x, head, offset : (x, 0),):

  def relay_callback(source_sock, tg_sock, event_key, event_mask):
    future.set_result((source_sock, tg_sock, event_key, event_mask))

  data_queues = {
    sock1.fileno(): [],
    sock2.fileno(): []
  }

  data_offset = {
    sock1.fileno(): 0,
    sock2.fileno(): 0
  }

  try:
    while True:
      future = Future()

      register_read_write(sock1, lambda k, m: relay_callback(sock1, sock2, k, m))
      register_read_write(sock2, lambda k, m: relay_callback(sock2, sock1, k, m))

      source_sock, tg_sock, event_key, event_mask = yield future
      unregister(sock1)
      unregister(sock2)

      try:

        if event_mask & EVENT_WRITE != 0:
          # If a write is ready, write the corresponding data to it
          if len(data_queues[source_sock.fileno()]) > 0:
            data = data_queues[source_sock.fileno()][0]
            check_socket(source_sock)
            sent = source_sock.send(data)
            if source_sock.fileno() == sock2.fileno():
              logging.debug("data sent to sock2 (%d):\n%s" % (sent, data[0 : sent]))

            if sent < len(data):
              data_queues[source_sock.fileno()][0] = data[sent:]
            else:
              data_queues[source_sock.fileno()].pop(0)
            #logging.debug("sent %d" % len(data))
        if event_mask & EVENT_READ != 0:
          check_socket(source_sock)

          data = source_sock.recv(4096)
          if len(data) == 0:
            break
          if tg_sock.fileno() == sock2.fileno():
            encoded_data, adjust = sock1_data_to_sock2_data(data, data_offset[sock1.fileno()])
            data_offset[sock1.fileno()] += len(data) + adjust
          else:
            encoded_data, adjust = sock2_data_to_sock1_data(data, data_offset[sock2.fileno()])
            data_offset[sock2.fileno()] += len(data) + adjust

          data_queues[tg_sock.fileno()].append(encoded_data)

      except IOError as e:
        if e.errno == errno.EWOULDBLOCK:
          pass

  finally:
    check_socket(sock1)
    check_socket(sock2)

    sock2.close()