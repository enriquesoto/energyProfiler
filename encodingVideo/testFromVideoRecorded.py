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
    import pdb
    import urllib

    stream = urllib.urlopen('http://192.168.1.103:8080/cam.mjpg')

    with TwitchBufferedOutputStream(
            twitch_stream_key=streamkey,
            width=256,
            height=140,
            fps=30,
            verbose=True) as videostream:

        bytes = ''
        counter = 0
        while (True):
            #pdb.set_trace()
            #print("counter: "+str(counter))
            bytes+=stream.read(1024)

            varA = bytes.find('\xff\xd8')
            varB = bytes.find('\xff\xd9')
            if varA!=-1 and varB!=-1 and videostream.get_video_frame_buffer_state() < 30:
                jpg = bytes[varA:varB+2]
                bytes= bytes[varB+2:]
                img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                videostream.send_video_frame(imgRGB)
                #cv2.imshow('i',i)
                #cv2.imwrite("output/jejeje"+str(counter)+".jpg",i)
                if cv2.waitKey(1) ==27:
                    exit(0)
            counter +=1


class PytosEnergyTest(Thread):
  def __init__(self, pids, csvEnergyFile):
    Thread.__init__(self)
    self.pids = pids
    self.csvEnergyFile = csvEnergyFile
    self.command = "powerapi modules procfs-cpu-simple monitor --frequency 1000 --targets ffmpeg,"+pids+" --agg mean --console"

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


class MjpegServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            start_time=time()
            frameCounterFps=0
            frameCounter=0
            sumFrameSize=0
            while True:
                try:
                    rc,img = cap.read()
                    #resized_image = cv2.resize(img, (176, 140)) 
                    if  img is None:
                      print("termino de reproducirse el video")
                    if not rc:
                        continue
                    imgRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                    jpg = Image.fromarray(imgRGB)
                    tmpFile = StringIO.StringIO()
                    jpg.save(tmpFile,'JPEG',quality=95)
                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(tmpFile.len))
                    self.end_headers()
                    jpg.save(self.wfile,'JPEG',quality=95)
                    frameCounterFps += 1
                    frameCounter +=1
                    print("tamaño imagen en bytes:"+str(tmpFile.len))
                    sumFrameSize += int(tmpFile.len)
                    if time() - start_time>1 : 
                      start_time=time()
                      fps = frameCounterFps
                      averageFrameSPS = sumFrameSize
                      sumFrameSize = 0
                      frameCounterFps = 0
                      print("emiting at : "+str(fps)+"fps\nData Send/s:"+str(averageFrameSPS))
                    #sleep(0.01)
                except KeyboardInterrupt:
                    break
            return
        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="http://127.0.0.1:8080/cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return

class Offloading(Thread):
    def __init__(self,videoSource):
        Thread.__init__(self)
        global cap
        cap = cv2.VideoCapture(videoSource)
    def run(self):
        try:
            server = HTTPServer(('',8080),MjpegServer)
            server.serve_forever()
        except:
            cap.release()
            server.socket.close()


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
        file_size = os.path.getsize(self.videoPath)
        try: 
          httpServerThread = Offloading(self.videoPath)
          httpServerThread.start()
          pdb.set_trace()
          start_time=time()
          #encode_video("rtmp://a.rtmp.youtube.com/live2", "02ht-676q-csah-cpb3", "http://localhost:8080/cam.mjpg")
          end_time=time()
          total_time=end_time-start_time
          writer.writerow([file_size,total_time])
        except KeyboardInterrupt:
          end_time = time()
          total_time=end_time-start_time
          writer.writerow([file_size,total_time])
          cap.release()
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

