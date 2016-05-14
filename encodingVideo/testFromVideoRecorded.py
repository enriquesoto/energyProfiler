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
import time
from threading import Thread
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

class MjpegServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                try:
                    rc,img = cap.read()
                    if not rc:
                        continue
                    imgRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                    jpg = Image.fromarray(imgRGB)
                    tmpFile = StringIO.StringIO()
                    jpg.save(tmpFile,'JPEG')
                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(tmpFile.len))
                    self.end_headers()
                    jpg.save(self.wfile,'JPEG')
                    time.sleep(0.05)
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
    def __init__(self, ):
        Thread.__init__(self)
    def run(self):
        try:
            server = HTTPServer(('',8080),MjpegServer)
            server.serve_forever()
        except:
            cap.release()
            server.socket.close()


@offload(resources={})
def encode_video(rtmp_server,streamkey,videoSource):
    
    from twitchstream.outputvideo import TwitchBufferedOutputStream
    import numpy as np
    import cv2
    import pdb 
    import urllib

    stream = urllib.urlopen('http://localhost:8080/cam.mjpg')

    with TwitchBufferedOutputStream(
            twitch_stream_key=streamkey,
            width=640,
            height=480,
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

             

if __name__ == "__main__":
    global cap
    parser = argparse.ArgumentParser(description=__doc__)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-s', '--streamkey',
                          help='twitch streamkey',
                          required=True)
    #pdb.set_trace()
    args = parser.parse_args()
    cap = cv2.VideoCapture(0)
    #cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320);
    #cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240);
    try:
        httpServerThread = Offloading()
        httpServerThread.start()
        encode_video("rtmp://a.rtmp.youtube.com/live2", "02ht-676q-csah-cpb3", "http://localhost:8080/cam.mjpg")
    except KeyboardInterrupt:
        cap.release()
        server.socket.close()
