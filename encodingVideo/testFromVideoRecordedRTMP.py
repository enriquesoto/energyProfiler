#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which creates a twitch stream to connect with
and changes the color of the video according to the colors provided in
the chat.
"""
from __future__ import print_function
from pytos.pytos import offload
from pytos.utils import Utils
import urllib
import argparse
import numpy as np
import pdb
import cv2
import Image
import StringIO
from time import sleep,time
import os
import sys
import rpyc
import csv
import subprocess
import re
from datetime import date
from threading import Thread
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

@offload(resources={})
def encode_video(rtmp_server,streamkey,videoSource):

    from twitchstream.outputvideo import TwitchBufferedOutputStream
    import numpy as np
    import cv2
    from time import sleep

    cap = cv2.VideoCapture(videoSource)


    with TwitchBufferedOutputStream(
            twitch_stream_key=streamkey,
            width=640,
            height=480,
            fps=30,
            verbose=True) as videostream:

        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        if int(major_ver)  < 3 :
              fpsFromStream = cap.get(cv2.cv.CV_CAP_PROP_FPS)
              #print "Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fpsFromStream)
        else :
              fpsFromStream = cap.get(cv2.CAP_PROP_FPS)
              #print "Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fpsFromStream)

        while (True):
            state = videostream.get_video_frame_buffer_state()
            #cv2.imshow("jeje",img)
            if videostream.get_video_frame_buffer_state() < 30:
                
                rc,img = cap.read()
                #imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                videostream.send_video_frame(img)
                #if time() - start_time > 1:
                #    fps = frameCounterFps
                #    frameCounterFps = 0
                #    start_time=time()
                #if cv2.waitKey(1) ==27:
                #    exit(0)
            if cv2.waitKey(1) & 0xFF == ord('q'):
              break
            #sleep(0.03)


class PytosEnergyTest(Thread):
  def __init__(self, pids, csvEnergyFile):
    Thread.__init__(self)
    self.pids = pids
    self.csvEnergyFile = csvEnergyFile
    self.command = "powerapi modules procfs-cpu-simple monitor --frequency 1000 --targets ffmpeg,nginx"+pids+" --agg mean --console"

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
          print("medicion actual"+nonProcessed[0])
          print("acumulado : ")
          writer.writerow(["medicion actual "+nonProcessed[0]])
          energy += float(nonProcessed[0])
          print("acumulado : " + str(energy))
          writer.writerow(["medicion acumulada "+str(energy)])
          #sys.stdout.write("medicion acumulada :"+str(energy)+"\n")
          #sys.stdout.flush()
    output = process.communcate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
      return output
    else:
      raise ProcessException(command, exitCode, output)


class PytosTimeTest():

  def __init__(self,csvFile, videoPath):
      self.csvFile = csvFile
      self.videoPath = videoPath
      self.conn = rpyc.connect("localhost", 22345)
      self.c = self.conn.root

  def start(self):
      day = date.today().day
      month = date.today().month
      with open("log/"+self.csvFile+"-"+str(day)+"-"+str(month)+"-times.csv","wb") as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        #file_size = os.path.getsize(self.videoPath)
        try: 
          pdb.set_trace()
          start_time=time()
          encode_video("rtmp://a.rtmp.youtube.com/live2", "02ht-676q-csah-cpb3",self.videoPath)
          end_time=time()
          total_time=end_time-start_time
          writer.writerow([total_time])
        except:
          end_time = time()
          total_time=end_time-start_time
          writer.writerow([total_time])
          server.socket.close()
        
class PytosPerformance(object):

  def __init__(self, csvFile, videoPath, pids):

    self.pytosTimeTest = PytosTimeTest(csvFile,videoPath)
    myPid = os.getpid()
    if pids != -1:
      self.pids = pids+","+str(myPid)
    else:
      self.pids = myPid

    self.pytosEnergyTest = PytosEnergyTest(self.pids,csvFile)

  def start(self):
    try:
      #self.pytosEnergyTest.start()
      self.pytosTimeTest.start()
    except KeyboardInterrupt:
      cap.release()

global cap

if __name__ == "__main__":
    if len(sys.argv) != 4:
      print("you must enter 3 arguments: csvfile name, video source path")
      sys.exit()
    if len(sys.argv) == 4:
      pytosPerformance = PytosPerformance(csvFile=sys.argv[1],videoPath=sys.argv[2],pids=sys.argv[3])
      pytosPerformance.start()

