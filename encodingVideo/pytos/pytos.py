import constants,inspect,time,requests,pdb,os,csv,datetime,os
import Pyro4
import rpyc
from StringIO import StringIO
from cStringIO import StringIO
import numpy as np
import os
import inspect
import pytosdb
import time
from utils import Utils
import sys
import marshal

class Offloading:
    func = None
    args = None
    task = None
    args = None
    kwargs = None
    result = None
    execTime = None
    def __init__(self,func,args,kwargs,resources):
        self.func=func
        self.args=args
        self.kwargs=kwargs
        self.resources = resources
    def prepare(self):
        #os.system('python pytos/pytos_daemon.py --debug true&')
        #db = pytosdb.PytosDB() #create initial DB
        pass
    def decision(self):
        conn = rpyc.connect("localhost", 22345)
        c = conn.root
        argsSize = Utils.getArgsSize(self.args)
        methodSignature = self.func.__name__
        methodBody = inspect.getsource(self.func)
        methodWeight = sys.getsizeof(methodBody)

        offload = c.getOffloadingDesicion(methodSignature,methodWeight,argsSize)
        #pdb.set_trace()
        #offload = False
        offload = True
        print offload
        if not offload:
            startTime = time.time()
            self.result = self.func(*self.args,**self.kwargs)
            endTime = time.time()
            timeLocally = endTime - startTime
            #paralelize create a new thread
            aTask = pytosdb.Task(self.func,timeLocally,self.args)
            #aTask.initFromFunc(self.func,timeLocally,self.args)  
            #pdb.set_trace()
            asyncThreadProfiler = pytosdb.TaskWriterThread(aTask,self.func,self.args)
            asyncThreadProfiler.start() #async task
            #asyncThreadProfiler.join()
        else:
            Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
            Pyro4.config.SERIALIZER="pickle"
            #remoteCall = Pyro4.Proxy("PYRONAME:pytos.remoteCall")
            remoteCall = Pyro4.Proxy(c.getUri())
            #remoteServer = rpyc.connect("localhost",12345, config = {"allow_all_attrs" : True})
            #c = remoteServer.root
            #functionSource = inspect.getsource(self.func)
            funcEncoded = marshal.dumps(self.func.func_code)
            #pdb.set_trace()
            response = remoteCall.callRemoteMethod(funcEncoded,methodSignature,self.args)
            self.result = response["result"]
            self.execTime = response["time"]

    def start(self):
        self.prepare()
        self.decision()

def offload(resources={}):
  def wrapper(func):
    def inner(*args,**kwargs):
      Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
      Pyro4.config.SERIALIZER = "pickle"
      offloading = Offloading(func,args,kwargs,resources)
      offloading.start()
      #modified for statistics purposes
      #return offloading.result
      return offloading
    return inner
  return wrapper

