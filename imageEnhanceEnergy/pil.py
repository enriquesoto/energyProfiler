from scavenger import Scavenger, shutdown, scavenge
from StringIO import StringIO

from time import sleep
import os
from PIL import Image
import pdb

# Sleep for a little while to allow surrogates to be discovered.
print "Sleeping for a little while...",
sleep(1.2)
print "done"
print "Found", len(Scavenger.get_peers()), "surrogates"

path_input = "imgs/"
path_output = "output/"

listing = os.listdir(path_input)
for file in listing:
  file_path =path_input+file
  tmpImgFilebasename = os.path.basename(file_path)
  img = Image.open(file_path)
  sio = StringIO()
  img.save(sio,"JPEG",quality = 95)
  send = sio.getvalue()
  factor = 1.0
  #pdb.set_trace()
  '''
  result = Scavenger.scavenge('pil.test.sharpness16', [send,factor], """
def perform(img,factor):
  from PIL import ImageEnhance as IE,Image
  from StringIO import StringIO
  sio = StringIO(img)
  pil_image = Image.open(sio)
  new_image = IE.Sharpness(pil_image).enhance(1.0 + factor)
  sio = StringIO()
  #new_image.save("pruebita.jpg","JPEG")
  new_image.save(sio,"JPEG", quality=95)
  return sio.getvalue()
""")
  '''
  result = Scavenger.scavenge('pil.test.sharpness16', [send,factor])
  #pdb.set_trace()
  #sio = StringIO(result)
  #pil_image = Image.open(sio)
  #pil_image.save("output/"+tmpImgFilebasename+".jpg","JPEG",quality = 95)

shutdown()
    

