from pytos.pytos import offload
from pytos.utils import Utils
from StringIO import StringIO
from datetime import date
import rpyc 
from time import sleep,time
import os
import sys
from PIL import Image
import csv
from threading import Thread
import os
import subprocess
import re
#dev
import pdb
# Sleep for a little while to allow surrogates to be discovered.

class PytosTest():

  def __init__(self,csvFile, imgPath, imgOutput):
    self.csvFile = csvFile
    self.imgPath = imgPath
    self.imgOutput = imgOutput
    self.conn = rpyc.connect("localhost", 22345)
    self.c = self.conn.root
    self.listing = os.listdir(self.imgPath)
    self.enhanceFactor =2
    

  def start(self):
    pdb.set_trace()
    day = date.today().day
    month = date.today().month
    with open("log/"+self.csvFile+"-"+str(day)+"-"+str(month)+"-times.csv","wb") as csvfile:
      writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      for file in self.listing:
        filePath = self.imgPath+file
        filebasename = os.path.basename(filePath)
        img = Image.open(filePath)
        sio = StringIO()
        img.save(sio,"JPEG",quality = 95)
        send = sio.getvalue()
        bandwidth = self.c.getBandwidth()
        #pdb.set_trace()
        argSize = Utils.getArgsSize({send,self.enhanceFactor})
        start_time = time()
        resultado = self.imageEnhance(send,self.enhanceFactor)
        end_time = time()
        imgReturnedSize=Utils.getArgsSize({resultado.result})
        writer.writerow([bandwidth,file,argSize,imgReturnedSize,resultado.execTime,end_time - start_time])
        sio = StringIO(resultado.result)
        pil_image = Image.open(sio)
        #pil_image.save(self.imgOutput+filebasename+".jpg","JPEG",quality = 95)
      print "terminnooo"
  @staticmethod
  @offload(resources={})
  def imageEnhance(img,factor):
    from PIL import ImageEnhance as IE,Image
    from StringIO import StringIO
    sio = StringIO(img)
    pil_image = Image.open(sio)
    new_image = IE.Sharpness(pil_image).enhance(1.0 + factor)
    sio = StringIO()
    new_image.save(sio,"JPEG", quality=95)
    return sio.getvalue()


class TaskEnergyProfiler(Thread):
  def __init__(self, pids, csvEnergyFile):
    Thread.__init__(self)
    self.pids = pids
    self.csvEnergyFile = csvEnergyFile
    self.command = "powerapi modules procfs-cpu-simple monitor --frequency 1000 --targets "+pids+" --agg mean --console"

  def run(self):
    process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    energy=0
    day = date.today().day
    month = date.today().month
    with open("log/"+self.csvEnergyFile+"-"+str(day)+"-"+str(month)+"-energy.csv","wb") as csvfile:
      writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() != None:
          break
        nonProcessed =  re.findall("\d+\.\d+", nextline)
        if nonProcessed:
          #sys.stdout.write("medicion actual"+nonProcessed[0]+"\n")
          print "medicion actual"+nonProcessed[0]
          print "acumulado : "
          writer.writerow(["medicion actual "+nonProcessed[0]])
          energy += float(nonProcessed[0])
          print "acumulado : " + str(energy)
          writer.writerow(["medicion acumulada "+str(energy)])
          #sys.stdout.write("medicion acumulada :"+str(energy)+"\n")
          #sys.stdout.flush()
    output = process.communcate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
      return output
    else:
      raise ProcessException(command, exitCode, output)

      
class EnergyTestPytos(object):

  def __init__(self, csvFile, imgPath, imgOutput, pids):

    self.pytosTest = PytosTest(csvFile,imgPath,imgOutput)
    myPid = os.getpid()
    if pids != -1:
      self.pids = pids+","+str(myPid)
    else:
      self.pids = myPid

    self.energyProfiler = TaskEnergyProfiler(self.pids,csvFile)

  def start(self):
    self.energyProfiler.start()
    self.pytosTest.start()


if __name__ == "__main__":
    if len(sys.argv) != 5:
      print " you must enter 4 arguments: csvfile name, image source path, image output folder "
      sys.exit()
    if len(sys.argv) == 5:
      pytosEnergy = EnergyTestPytos(csvFile=sys.argv[1],imgPath=sys.argv[2],imgOutput=sys.argv[3],pids=sys.argv[4])
      pytosEnergy.start()

