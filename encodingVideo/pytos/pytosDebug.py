#dev 
import pdb

class Debug:
    def __init__(self,debug=True,log2File=False):
        self.debug = debug
        self.log2File=log2File
    def printLog(self, string):
        if self.debug:
            print string

