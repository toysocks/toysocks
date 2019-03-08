from typing import *
import selectors
import heapq
import time

_selector = selectors.DefaultSelector()
_event_count = 0
_sleep = []

def sleep(interval : float, cb : Callable):
  heapq.heappush(_sleep, (time.time() + interval, cb))

def register(fileno, events, cb):
  global _event_count
  _event_count += 1
  _selector.register(fileno, events, cb)

def register_write(fileno, cb):
  register(fileno, events=selectors.EVENT_WRITE, cb=cb)

def register_read(fileno, cb):
  register(fileno, events=selectors.EVENT_READ, cb=cb)

def register_read_write(fileno, cb):
  register(fileno, events=selectors.EVENT_READ | selectors.EVENT_WRITE, cb=cb)

def unregister(fileno):
  global _event_count
  _event_count -= 1
  _selector.unregister(fileno)

class Future:

  def __init__(self):
    self.result = None
    self.callbacks : List[Callable] = []
    pass

  def add_callback(self, callback : Callable):
    self.callbacks.append(callback)
    return self

  def set_result(self, result : Any):
    self.result = result
    for cb in self.callbacks:
      cb(self)
    return self

class Task:

  def __init__(self, coroutine : Generator):
    self.coroutine = coroutine
    f = Future()
    self.step(f)

  def step(self, future : Future):
    try:
      f : Future = self.coroutine.send(future.result)
      if f is None:
        return
      f.add_callback(self.step)
    except StopIteration as e:
      pass

class AsyncFunc:

  @property
  def coroutine(self):
    raise NotImplementedError()

class EventLoop:

  def __init__(self, funcs : List[AsyncFunc] = None):
    if funcs:
      [Task(f.coroutine) for f in funcs]

  def run_forever(self):
    while _event_count > 0 or len(_sleep) > 0:

      if len(_sleep) > 0:
        t, callback = _sleep[0]
        while t <= time.time():
          heapq.heappop(_sleep)
          callback()
          if len(_sleep) > 0:
            t, callback = _sleep[0]
          else:
            break

      results = _selector.select(0.01)
      for event_key, event_mask in results:
        callback = event_key.data
        callback(event_key, event_mask)

  def add_event(self, coroutine):
    Task(coroutine)