#!/usr/bin/env python3
from cmd import Cmd
from time import sleep
import DbusCommunication
import configparser
import tqdm
import argparse

class main:
    
    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("action",help='The action to take (e.g. read, write)',type=str, choices=["read","write"])
        parser.add_argument("--debug",help='Debug the Tool',type=int, choices=[0, 1], default=0)
        parser.add_argument("file",help='File')
        parser.add_argument("--comport",help='ComPort to use(e.g COM1)',default="COM1")
        args = parser.parse_args()
        self.dbusComm = DbusCommunication.DbusCommunication(args.comport,int(args.debug))
        self.typ = self.dbusComm.getTypeByName("eeprom")
        self.filename = args.file
        self.memory_size = 0x1FF
        self.memory_start = 0x0
        
        if(args.action=="read"):
            self.readDump()
            pass
        elif(args.action=="write"):
            self.writeDump()
        print("Finished!")  
        
    def readDump(self):
        self.CHUNK_SIZE = 4
        progress = tqdm.tqdm(total=self.memory_size)
        with open(self.filename, "wb") as f:
            for i in range(0, self.memory_size, self.CHUNK_SIZE):
                memory_address = self.memory_start + i
                returnBytes = int(self.CHUNK_SIZE / 2)
                databyte = self.dbusComm.readCmd(self.typ,memory_address,returnBytes)
                if(len(databyte) != self.CHUNK_SIZE):
                    #print(databyte)
                    raise Exception("Problem with Returned Bytes. Expected: "+ str(self.CHUNK_SIZE) +". Got: "+ str(len(databyte)))
                f.write(databyte)
                f.flush()
                progress.update(self.CHUNK_SIZE)
            progress.close()
        
    def writeDump(self):
        self.CHUNK_SIZE = 8
        progress = tqdm.tqdm(total=self.memory_size)
        with open(self.filename, "rb") as f:
            for i in range(0, self.memory_size, self.CHUNK_SIZE):
                memory_content = f.read(self.CHUNK_SIZE)
                memory_address = self.memory_start + i
                try:
                    self.dbusComm.writeCmd(self.typ,memory_address,memory_content)
                except DbusCommunication.InvalidParameter:
                    if(memory_address < 0x10):
                        pass
                    else:
                        raise Exception("Problem while writing")
                    pass
                progress.update(self.CHUNK_SIZE)
            progress.close()
        
        
if __name__ == "__main__":
    m = main()
    m.run()
      
        

    
    
    