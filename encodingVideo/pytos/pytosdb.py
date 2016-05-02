import sqlite3
import constants
import os
import uuid
import inspect
import sys
#from pytos_daemon import Solver
from threading import Thread
from utils import Utils
import marshal
import Pyro4
import rpyc
#dev
import pdb

class TaskWriterThread(Thread):
  def __init__(self, task, func, args):
    Thread.__init__(self)
    self.task = task
    self.func = func
    self.args = args
  def run(self):
    tasksRows = TaskDAO.getTasksByProperties(self.task.methodDeclaration,self.task.methodWeight)
    #functionBody = inspect.getsource(self.func)
    #pdb.set_trace()
    if TaskDAO.getLocalCalls(tasksRows) < constants.N_MIN_LOCAL_CALLS:
      taskDAO = TaskDAO(self.task)
    if TaskDAO.getRemoteCalls(tasksRows) < constants.N_MIN_REMOTE_CALLS:
      Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
      Pyro4.config.SERIALIZER="pickle"
      #pdb.set_trace()
      conn = rpyc.connect("localhost", 22345)
      c = conn.root
      remoteCall = Pyro4.Proxy(c.getUri())
      funcEncoded = marshal.dumps(self.func.func_code)
      response = remoteCall.callRemoteMethod(funcEncoded,self.task.methodDeclaration,self.args)
      timeExecution = response["time"]
      print "enviando a cloudlet con fines estadisticos"
      #if TaskDAO.getLocalCalls(tasksRows) < constants.N_MIN_LOCAL_CALLS:
      print "logging for stats"
      self.task.timeRemotelly = timeExecution
      #argument= self.args[1] 
      #argsSize = Utils.getArgsSize(self.args)
      #task = pytosdb.Task(self.func.__name__,methodWeight,argsSize,timeLocally,functionBody)
      taskDAO = TaskDAO(self.task)

class Task:
  id = ''
  methodDeclaration =''
  methodWeight = 0
  argsSize = 0
  timeLocally = 0
  timeRemotelly=0
  returnWeight='' #optional field :S
  methodBody= ''
  def __init__(self,func,timeLocally,args):
    u = uuid.uuid1()
    self.id=u.hex
    self.methodDeclaration = func.__name__
    self.methodBody = inspect.getsource(func)
    self.methodWeight = sys.getsizeof(self.methodBody)
    self.timeLocally = timeLocally
    self.argsSize = Utils.getArgsSize(args)
  def initialize(self,row):
    self.id,self.methodDeclaration,self.methodWeight, self.argsSize, self.timeLocally,self.timeRemotelly, self.returnWeight, self.methodBody= row

class TaskDAO:
  def __init__(self,task):
    #print "Inserting task"
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      cursor = conn.cursor()
      query = "insert into task (id, method_declaration, method_weight, args_size, time_locally, time_remotelly, function_body) values (:id,:method_declaration,:method_weight,:args_size, :time_locally, :time_remotelly, :function_body)"
      cursor.execute(query, {'id':task.id,'method_declaration':task.methodDeclaration, 'method_weight':task.methodWeight, 'args_size':task.argsSize, 'time_locally':task.timeLocally,'time_remotelly':task.timeRemotelly, 'function_body':task.methodBody})
  
  def updateTask(self,task):
    #print "Updating Task"
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      cursor = conn.cursor()
      query = "update task set method_declaration =:method_declaration, method_weight =: method_weight, argsSize =:argsSize, time_locally = :time_locally, time_remotelly =:time_remotelly, return_weight =:return_weight, function_body =:function_body where id = :id"
      cursor.execute(query, {'method_declaration':task.methodDeclaration,'method_weight':task.methodWeight, 'argsSize':task.argsSize, 'time_locally':task.timeLocally,'time_remotelly':task.timeRemotelly,'return_weight':task.returnWeight,'function_body':task.methodBody, 'id':task.id})

  @staticmethod
  def getTasksByProperties(methodDeclaration,methodWeight):
    #print "getting a task by properties "
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      cursor = conn.cursor()
      query = "select * from task where method_declaration =:method_declaration AND method_weight =:method_weight"
      cursor.execute(query, {'method_declaration':methodDeclaration,'method_weight':methodWeight})
      answers = cursor.fetchall()
      return answers

  @staticmethod
  def getAllTasks():
    #print "getting all tasks that may be offloaded "
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      cursor = conn.cursor()
      query = "select distinct method_declaration,method_weight from task"
      cursor.execute(query)
      answers = cursor.fetchall()
      return answers


  @staticmethod
  def getExecutionsTimes(methodSignature,methodWeight):
    #print "getting executions times for forecasting"
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      cursor = conn.cursor()
      query = "select args_size, time_locally, time_remotelly  from task where method_declaration =:method_declaration AND method_weight =:method_weight  AND time_remotelly >0 AND time_locally >0"
      cursor.execute(query,{'method_declaration':methodSignature,'method_weight':methodWeight})
      answers = cursor.fetchall()
      return answers


  @staticmethod
  def getRemoteCalls(nTasksRows):
    #print "getting n remote calls"
    #pdb.set_trace()
    nRemoteCalls = 0
    for task in nTasksRows:
      if task[constants.TIME_REMOTELLY_FIELD] is not None and task[constants.TIME_REMOTELLY_FIELD]>0:
        nRemoteCalls +=1
        #reurn constants.N_MIN_REMOTE_CALLS-nRemoteCalls
    return nRemoteCalls

  @staticmethod
  def getLocalCalls(nTasksRows):
    #print "getting n local calls"
    nLocalCalls = 0
    for task in nTasksRows:
      if task[constants.TIME_LOCALLY_FIELD] is not None:
        nLocalCalls +=1
    return nLocalCalls
        
class PytosDB:
  conn = None
  def __init__(self):
    pdb.set_trace()
    #self.db_filename = 'pytos/stats.db'
    db_exits = os.path.exists(constants.ROOT_DIR+constants.DB_FILENAME)
    with sqlite3.connect(constants.ROOT_DIR+constants.DB_FILENAME) as conn:
      if not db_exits:
        #print 'Creating schema'
        conn.execute('''create table task (id text, method_declaration text not null, method_weight not null, args_size integer,  time_locally real not null, time_remotelly real, return_weight integer, function_body text not null);''')
        #print "Table Created!"
        #conn.close() #can not operate on a closed db
