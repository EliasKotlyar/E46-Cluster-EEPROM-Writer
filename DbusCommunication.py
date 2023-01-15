import serial
import time

MOTRONIC = 0x12
AUTOMATIC_TRANSMISSION = 0x32
IKE = 0x80
LCM = 0xD0


class DbusCommunication(object):
    def __init__(self,comport,debug):
        self.debug = debug
        if self.debug == 0:
            self._device = serial.Serial(comport, 9600, parity=serial.PARITY_EVEN)

    def _execute(self, address, payload_str):
        payload = bytes.fromhex(payload_str)

        self._write(address, payload)
        echo = self._read()
        self._device.timeout = 5
        time.sleep(0.10)
        reply = self._read()
        if reply is None:
            raise InvalidAddress("invalid address")
        sender, payload = reply
        self._device.timeout = None
        if sender != address:
            raise ProtocolError("unexpected sender")
        status = payload[0]
        
        #0xA0	OKAY
        #0xA1	BUSY
        #0xA2	ERROR_ECU_REJECTED
        #0xB0	ERROR_ECU_PARAMETER
        #0xB1	ERROR_ECU_FUNCTION
        #0xB2	ERROR_ECU_NUMBER
        #0xFF	ERROR_ECU_NACK
        
        if status == 0xa0:
            return payload[1:]
        elif status == 0xa1:
            raise ComputerBusy("computer busy")
        elif status == 0xa2:
            raise InvalidParameter("invalid parameter")
        elif status == 0xff:
            raise InvalidCommand("invalid command")
        elif status == 0xB0:
            raise InvalidParameter("invalid parameter")
        else:
            #raise ProtocolError("unknown status")
            #print("Error")
            self._device.close()
            time.sleep(1)
            self._device.open()
            
            return bytes.fromhex("EEEEEE")

    def _write(self, address, payload):
        size = 2 + len(payload) + 1
        message = bytes([address, size]) + payload
        buf = message + bytes([self._checksum(message)])
        #print(buf.hex())
        self._device.write(buf)

    def _read(self):
        try:
            address = self._device.read(1)[0]
        except IndexError:
            #print("index error")
            return None
        size = self._device.read(1)[0]
        remaining = size - 3
        if remaining > 0:
            payload = self._device.read(remaining)
        else:
            payload = bytes([])
        expected_checksum = self._checksum(bytes([address, size]) + payload)
        actual_checksum = self._device.read(1)[0]
        if actual_checksum != expected_checksum:
            raise ProtocolError("invalid checksum")
            pass
        self._device.reset_input_buffer()
        #print(address,payload)
        return (address, payload)

    def _checksum(self, message):
        result = 0
        for b in message:
            result ^= b
        return result

    def setAnalog(self, input, value):
        hexStr = "0c"
        hexStr += "0" + input
        hexStr += format(value, '04x')
        print(hexStr)
        self._execute(IKE, hexStr)
        pass

    def setKilometer(self, kmh):
        self.setAnalog("a", kmh)

    def setRpm(self, rpm):
        rpm = rpm / 1000
        rpm = rpm * 316
        rpm = int(round(rpm, 0))
        self.setAnalog("b", rpm)

    def setFuel(self, fuel):
        self.setAnalog("c", fuel)

    def setCoolant(self, temperature):
        self.setAnalog("d", temperature)

    def setOil(self, temperature):
        self.setAnalog("e", temperature)

    def setLamps(self,value):
        hexStr = "0c"
        hexStr += "09"
        hexStr += format(value, '02x')
        #for x in range(6):
        #    hexStr += "00"
        self._execute(IKE, hexStr)

    def acticateTest(self):
        hexStr = "30"
        hexStr += "b4"
        self._execute(IKE, hexStr)

    def deactivateTest(self):
        hexStr = "9f"
        hexStr += "1b"
        self._execute(IKE, hexStr)
        
    def readCmd(self,memory_type,address,mem_size = 1):
        hexStr = "06" 
        hexStr += format(memory_type, '02x')
        # Address:
        hexStr += address.to_bytes(3, byteorder='big').hex()
        # How much to read
        hexStr += format(mem_size, '02x')
        #print(hexStr)
        return self._execute(IKE, hexStr)
    def writeCmd(self,memory_type,address,memoryContent):
        hexStr = "07" 
        hexStr += format(memory_type, '02x')
        # Address:
        hexStr += address.to_bytes(3, byteorder='big').hex()
        # How much to write
        memory_len = int(len(memoryContent) / 2)
        hexStr += format(memory_len, '02x')
        hexStr += memoryContent.hex()
        #print(hexStr)
        return self._execute(IKE, hexStr)
        
        
    def getTypeByName(self,typ):
        if(typ == "eeprom"):
            memory_type = 0x03
        elif (typ == "rom"):
            memory_type = 0x01
        elif(typ == "dpram"):
            memory_type = 0x0a
        elif(typ == "internalram"):
            memory_type = 0x04
        elif(typ == "externalram"):
            memory_type = 0x05
        else:
            pass
        return memory_type

class ProtocolError(Exception):
    pass


class ComputerBusy(Exception):
    pass


class InvalidAddress(Exception):
    pass


class InvalidCommand(Exception):
    pass

class InvalidParameter(Exception):
    pass
