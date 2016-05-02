import time
import rpyc
import sys
import constants
import argparse
from tendo import singleton
from rpyc.utils.server import ThreadedServer
from threading import Thread
import pytosdb
import cStringIO
import cv2
import numpy as np
from cStringIO import StringIO
import os
from utils import Utils
import pytosDebug
import requests
import Pyro4
#development
import pdb

class Global():
  debug = True
  offloading=True
  uriCloudlet = None
  idleTime=0
  ssid = None
  weight =None
  bandwidth = 0
  ipl = {}

class PytosDaemon():
  mainGlobals = None
  cloudlet = None
  def __init__(self,main):
    db = pytosdb.PytosDB()
    self.debug = pytosDebug.Debug(main.debug,False)
    self.mainGlobals = main
  def discover(self):
    try:
      self.debug.printLog("asking for cloudlet to "+ constants.URI_DISCOVERY_ENDPOINT)
      response = requests.get(constants.URI_DISCOVERY_ENDPOINT+self.mainGlobals.ssid)
      code = response.status_code
      if code is 200:
        main.uriCloudlet = str(response.json()["cloudlet"]["uri"])
        self.debug.printLog("cloudlet found"+main.uriCloudlet)
      else:
        self.debug.printLog("cloudlet not available")
        main.uriCloudlet = None
    except requests.exceptions.ConnectionError as e:
      main.uriCloudlet = None
      self.debug.printLog("connection error when asking for cloudlet")
      #print "Connection error({0}): {1}".format(e.errno, e.strerror)
    except:
      self.debug.printLog("unknown error :/")
      main.uriCloudlet = None
      raise

  def profile(self):
    try:
      if self.mainGlobals.uriCloudlet is not None:
        remoteCall = Pyro4.Proxy(self.mainGlobals.uriCloudlet)
        weight2send = Utils.getSizeInBytes(self.mainGlobals.weight)
        self.debug.printLog("transfering "+str(weight2send)+ "bytes")
        start_time = time.time()
        ans = remoteCall.measureBandwidth(self.mainGlobals.weight)
        total_time = time.time()-start_time
        self.debug.printLog("Time used:"+str(total_time) + "seconds")
        self.mainGlobals.bandwidth = weight2send*2/total_time/1000
        self.debug.printLog("bandwidth speed: %.2f kb/s "%self.mainGlobals.bandwidth)
      #pdb.set_trace()
      tasks = pytosdb.TaskDAO.getAllTasks()
      if len(tasks) > 0:
        #pdb.set_trace()
        for task in tasks:
          result = pytosdb.TaskDAO.getExecutionsTimes(str(task[0]),task[1])
          if len(result) >0 and len(result)>=10:
            ans = np.array(result) #fx
            self.mainGlobals.ipl[str(task[0])+str(task[1])+"_local"] = np.polyfit(ans[:,0],ans[:,1],1)
            self.mainGlobals.ipl[str(task[0])+str(task[1])+"_remote"] =  np.polyfit(ans[:,0],ans[:,2],1)
    except Pyro4.errors.CommunicationError as e:
      self.mainGlobals.uriCloudlet = None
      self.debug.printLog("unknown error when using cloudlet")

  def solve(self, methodSignature, methodWeight, argsSize):
    #pdb.set_trace()
    #return True
    uid = methodSignature+str(methodWeight)
    ipl = self.mainGlobals.ipl
    #if self.mainGlobals.uriCloudlet is not None and len(self.mainGlobals.ipl)>0:
    if self.mainGlobals.uriCloudlet is not None and uid+"_local" in ipl and uid+"_remote" in ipl:
      localPoly = self.mainGlobals.ipl[uid+"_local"]
      remotePoly = self.mainGlobals.ipl[uid+"_remote"]
      localTimeForecast = localPoly[0]*argsSize+localPoly[1]
      remoteTimeForecast = remotePoly[0]*argsSize+remotePoly[1]+argsSize/self.mainGlobals.bandwidth
      if (remoteTimeForecast < localTimeForecast):
        return True
    return False

  def start(self):
    self.discover()
    self.profile()

class MyService(rpyc.Service):
  def exposed_getOffloadingDesicion(self,methodSignature, methodWeight, argsSize):
    main.iddleTime=0
    return pytosDaemon.solve(methodSignature, methodWeight, argsSize)
  def exposed_getUri(self):
    return main.uriCloudlet
  def exposed_getBandwidth(self):
    return main.bandwidth

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Pytos\' gather  daemon')
  parser.add_argument('--debug',help='shows debug information in the console')
  arguments = parser.parse_args()
  main = Global()

  if arguments.debug.lower() == "false"  or arguments is None:
    main.debug=False

  me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running
  Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
  Pyro4.config.SERIALIZER="pickle"
  server = ThreadedServer(MyService, port = 22345)
  t = Thread(target = server.start)
  # the main logica
  main.weight = cv2.imread(constants.WEIGHT_FILE)
  pytosDaemon = PytosDaemon(main)
  t.daemon = True
  t.start()

  while True:
    if main.idleTime >= constants.KILLING_TIME: #if its iddle by killingTime constants, pytos daemon is killed
      sys.exit()
    main.idleTime += constants.TIMEGAP
    main.ssid = Utils.getSSID()
    pytosDaemon.start()
    time.sleep(constants.TIMEGAP)

