from bleak import BleakScanner

# Returns scanned sensors
async def scanSensors(addressNames, ready_to_stream, auto_run):
    # List of sensors for program and converted version
    sensors = [[], ([""]*len(addressNames))]

    # Scanning for Dots
    print("Scanning for Dots!")
    ble_devices = await BleakScanner.discover()
    
    # DEBUG Uncomment for scan results
    # print(ble_devices)

    # Checking for Dots in ble_devices
    for ble_device in ble_devices:

        # Fixes issue with a ble device with no name
        if(ble_device.name is None):
            continue

        if "xsens" in ble_device.name.lower():
            sensors[0].append(ble_device)

            # Placing the sensors in the correct order post scan. Only for GUI
            for ii in range(len(addressNames)):
                if(str(ble_device) == str(addressNames[ii][0])):
                    sensors[1][(addressNames[ii][1]) - 1] = addressNames[ii][2]
    if len(sensors[0]) == len(addressNames):
        ready_to_stream["stream_status"] = True
        print("All sensors found!")
    else:
        auto_run["scan"] = True
    print("Finished scanning!")
    return sensors