from bleak import BleakClient
import asyncio
import struct
import zmq
from squaternion import Quaternion

# Setup zmq TCP Sockets for UNITY visualisation
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('tcp://localhost:5555')

# Variables
global timestr, fieldnames, sensor_id
sensor_id = 0

# Returns base id of dot with new uuid matching functionality to access
def baseuuid(uuid):
    BASE_UUID = "1517xxxx-4947-11E9-8646-D663BD873D93"
    return BASE_UUID.replace("xxxx",uuid)

# Returns sensor id to keep track during output
def getID(address, addressNames):
    # Specifically analysis 5 sensors
    for ii in range(5):
        if(str(address) == str(addressNames[ii][0])):
            sensor_id = addressNames[ii][1]

    print("Starting connection with: "+str(address)+" || ID: "+str(sensor_id))
    return sensor_id

# Parses Incoming Quaternion Payload from xSens Sensor
def QuaternionData(rawData):
    data = DataReader(rawData)
    
    time_stamp = data.u32()
    w = (data.f32())[0]
    x = (data.f32())[0]
    y = (data.f32())[0]
    z = (data.f32())[0]
    quat_data = Quaternion(w, x, y, z)

    returnValue = {
        "timeStamp": time_stamp,
        "quaternionData": quat_data
    }
    return returnValue

# Class to change mode of xSens Dot
class ControlData:
    UUID = baseuuid('2001')

    def read(r):
        returnValue = ControlData()
        returnValue.Type = r.u8()
        returnValue.action = r.u8()
        returnValue.payload_mode = r.u8()

        return returnValue

    def parse(b):
        r = DataReader(b)
        return ControlData.read(r)

    def to_bytes(self):
        assert self.Type < 0xff
        assert self.action <= 1
        assert self.payload_mode <= 24

        b = bytes()
        b += bytes([self.Type])
        b += bytes([self.action])
        b += bytes([self.payload_mode])

        return b

# Class to access device information of xsens dot sensor
class DeviceInformation:
    UUID = baseuuid('1001')

    def readData(data):
        returnValue = DeviceInformation()

        return returnValue

    def parse(data):
        print(data)
        r = DataReader(data)
        return DeviceInformation.readData(r)

# Reads data from xSens Dot 
# Can break down bytes into required data
class DataReader:
    def b2i(b, signed=False):
        return int.from_bytes(b, "little", signed=False)
    
    def __init__(self, data):
        self.pos = 0
        self.data = data
    
    def raw(self, n):
        returnValue = self.data[self.pos:self.pos+n]
        self.pos += n
        return returnValue

    def u8(self):
        return DataReader.b2i(self.raw(1))

    def u32(self):
        return DataReader.b2i(self.raw(4))

    def f32(self):
        return struct.unpack('f', self.raw(4))

# Represents each IMU sensor 
# Contains bluetooth information and device characteristics
class IMU:
    def __init__(self, ble_device):
        self.dev = ble_device
        self.client = BleakClient(self.dev.address)
    
    async def __aenter__(self): # !!! Can we remove this?
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, value, traceback):
        await self.client.__aexit__(exc_type, value, traceback)

    async def enable_quaternions(self):
        resp = await self.client.read_gatt_char(ControlData.UUID)
        parsed = ControlData.parse(resp)

        parsed.action = 1
        parsed.payload_mode = 3

        msg = parsed.to_bytes()

        await self.client.write_gatt_char(ControlData.UUID, msg)
        
    async def disable_quaternions(self, dataObj):
        if dataObj.stream_control["shutdown"] == True:
            dataObj.stream_control["shutdown"] = False

            resp = await self.client.read_gatt_char(ControlData.UUID)
            parsed = ControlData.parse(resp)

            parsed.action = 0
            parsed.payload_mode = 5

            msg = parsed.to_bytes()

            await self.client.write_gatt_char(ControlData.UUID, msg)

            await asyncio.sleep(2)


    async def readMac(self): # Can we remove this? !!!
        response = await self.client.read_gatt_char(DeviceInformation.UUID)
        print(DeviceInformation.parse(response))

    async def reset_heading(self):
        msg = b'\x07\x00'
        await self.client.write_gatt_char(baseuuid('2006'), msg)
        resp = await self.client.read_gatt_char(baseuuid('2006'))
        # print(resp)

        # await asyncio.sleep(1)

        msg = b'\x01\x00'
        await self.client.write_gatt_char(baseuuid('2006'), msg)
        resp = await self.client.read_gatt_char(baseuuid('2006'))
        # print(resp)

        # await asyncio.sleep(1)

    async def start_notify_medium_payload(self, f):
        await self.client.start_notify(baseuuid('2003'), f)

# Callback function when xSens Dot returns data
# There will be n instances of Callback
class Callback:
    def __init__(self, constructData, initData, addressNames):
        self.sensor_id = getID(initData, addressNames)
        self.a = constructData

    def __call__(self, sender, data):
        sensorData = QuaternionData(data)

        # This is a list so it can be inserted into a CSV easier
        data = [
            sensorData["timeStamp"],
            int(self.sensor_id),
            sensorData["quaternionData"]]

        self.a.structappend(data)

        # Original data structure for C# & Unity
        data_unity = {
            'xq': sensorData["quaternionData"][1],
            'yq': sensorData["quaternionData"][2],
            'zq': sensorData["quaternionData"][3],
            'wq': sensorData["quaternionData"][0],
            'timestamp': sensorData["timeStamp"],
            'sensor':str(self.sensor_id)
        }

        # Parsing data to Unity Must be uncommented if the Unity app is not open
        socket.send_json(data_unity)

# Starts notifications on each individual IMU and sets mode
async def async_run(dot, dataObj, addressNames):
    async with IMU(dot) as d:
        await asyncio.sleep(dataObj.counter)
        dataObj.counter += 1

        await d.enable_quaternions()

        # await asyncio.sleep(1)

        await d.reset_heading()

        # await asyncio.sleep(4)

        h = Callback(dataObj, dot, addressNames)

        await d.start_notify_medium_payload(h)

        await d.disable_quaternions(dataObj)

        await asyncio.sleep(90000) # Change stream time

        print("Program Ended")