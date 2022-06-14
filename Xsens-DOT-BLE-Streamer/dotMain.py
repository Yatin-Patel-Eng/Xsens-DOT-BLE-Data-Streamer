import dotScan
import dotRun
import asyncio

# Data streaming
def run_quaternions(sensors, addressNames, dataObj):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    tasks = asyncio.gather(*((dotRun.async_run(dot, dataObj, addressNames)) for dot in sensors))
        
    loop.run_until_complete(tasks)
    loop.close()

# Dot scan
def run_scan_sensors(window_1, ready_to_stream, addressNames, sensors, auto_scan):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sensors[:] = loop.run_until_complete(dotScan.scanSensors(addressNames, ready_to_stream, auto_scan))
    window_1["-SENSOR LIST-"].Update(values=sensors[1])
    loop.close()