import numpy as np
from cStringIO import StringIO
import cStringIO
import constants
import sys
import cv2
import os
import numbers
import decimal
from pythonwifi.iwlibs import Wireless
#dev
import pdb

class Utils:

  @staticmethod
  def getSizeInBytes(var):
    response = 0
    if type(var).__module__ == np.__name__:
      cstringvar = Utils.numpyArrayToStringIO(var)
      #if isinstance(var, cStringIO.InputType):
      cstringvar.seek(0, os.SEEK_END)
      response = cstringvar.tell()
      cstringvar.seek(0)
    elif isinstance(var,numbers.Number):
      response = var
    elif isinstance(var,basestring):
      response = len(var)
    else:
      response = sys.getsizeof(var)
    return response

  @staticmethod
  def getArgsSize(var):
    size = 0
    for k in var:
      #s1 = Utils.getSizeInBytes(k) 
      size = size + Utils.getSizeInBytes(k)
    return size
  
  @staticmethod
  def numpyArrayToStringIO(numpyArray):
    if len(numpyArray) == 0:
      return StringIO('')
    img_str = cv2.imencode('.jpg', numpyArray)[1].tostring()
    response = StringIO(img_str)
    return response
  
  @staticmethod
  def getSSID():
    wifi = Wireless('wlan0')
    return wifi.getEssid()
