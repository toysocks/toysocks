import time
from typing import *
import random

class PortSelector:
  def __init__(self):
    pass

  def select(self, ports: List[int]):
    raise NotImplementedError()

class TimedPortSelector(PortSelector):

  def __init__(self, interval):
    self.interval = interval
    self.last_switch = int(time.time())
    self.choice = random.randint(0, 65535)

    super().__init__()

  def select(self, ports: List[int]):
    now = int(time.time())
    if now - self.last_switch > self.interval:
      self.choice = random.randint(0, 65535)
    return ports[self.choice % len(ports)]