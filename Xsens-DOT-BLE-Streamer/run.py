import dotCSV
import dotMain
import dotClassify
import PySimpleGUI as sg
import threading

# Dot identification & ordering for program to find Dots
global addressNames
addressNames = [
    ["D4:22:CD:00:2E:F5: Xsens DOT", 1, "Xsens Dot 1: Left Arm"],
    ["D4:22:CD:00:2E:F7: Xsens DOT", 2, "Xsens Dot 2: Right Arm"],
    ["D4:22:CD:00:2E:F8: Xsens DOT", 3, "Xsens Dot 3: Left Leg"],
    ["D4:22:CD:00:2E:F9: Xsens DOT", 4, "Xsens Dot 4: Right Leg"],
    ["D4:22:CD:00:2E:FA: Xsens DOT", 5, "Xsens Dot 5: Head"]]

read_me_BLE_scan = "Scanning for DOTs will commence automatically\nMake sure the DOTs are all blinking orange (pairing mode) otherwise\nconnection will likely be unsucessful.\n\nTo fix, sync and de-sync the sensors in the Xsens DOT app"
read_me_stream = "Enabling streaming mode can take up to 5 seconds.\nFrequency is approximately 20Hz.\nCSV input will likely stop due to Dot not being in streaming mode."

# ---------------Layouts---------------
line_length = 40
line_length_2 = 130

layout_BLE = [
    [sg.Text(
    "XSENS Dot Quaternion Data to CSV Data Streamer",
    size = (45, 1),
    font=("Helvetica", 13),
    text_color = "White",)],

    [sg.Text(
    read_me_BLE_scan,
    size = (50, 5),
    font=("Helvetica", 10),
    text_color = "White",)],

    [sg.Text("_" * line_length, size=(line_length, 1))],

    [sg.Text(
        "BLE Search Results",
        size = (20, 1),
        font=("Helvetica", 15),
        text_color = "White")],
    
    [sg.Listbox(values = ["Searching..."],enable_events = True, size = (55, 10), key = "-SENSOR LIST-")],
    
    [sg.Text("_" * line_length, size = (line_length, 1))],
    
    [sg.Checkbox("Auto Run", change_submits = True, enable_events = True, default = True, key = '-AUTO RUN-'),
    sg.Slider(
        range=(1, 7),
        orientation="h",
        size=(25, 20),
        default_value=5,)],
    
    [sg.Button(button_text = 'Scan',size = (22,2), key = '-SCAN-'),
    sg.Button(button_text = 'Stream',size = (22,2), key = '-RUN-'),]
]

layout_stream = [
    [sg.Text(
        "XSENS Dot Quaternion Data to CSV Data Streamer",
        size = (60, 1),
        font=("Helvetica", 15),
        text_color = "White",)],

    [sg.Text(
        read_me_stream,
        size = (60, 3),
        font=("Helvetica", 10),
        text_color = "White",)],

    [sg.Text("_" * line_length_2, size=(line_length_2, 1))],

    [sg.Text(
        "Data Stream",
        size = (20, 1),
        font=("Helvetica", 15),
        text_color = "White")],
    
    [sg.Output(size=(105, 15), font=("Helvetica", 13))],

    [sg.Text("_" * line_length_2, size=(line_length_2, 1))],

    [sg.Text(
        "Classification",
        size = (20, 1),
        font=("Helvetica", 15),
        text_color = "White")],

    [sg.Listbox(values = [""],enable_events = True, size = (42, 1), font=("Helvetica", 30), key = "-CLASSIFY-")],
    
    [sg.Text("_" * line_length_2, size=(line_length_2, 1))],
    
    [sg.Text(
        "Data Representation",
        size = (20, 1),
        font=("Helvetica", 15),
        text_color = "White")],

    [sg.Radio("Euler", "RADIO1", enable_events = True, default=True, key='-DATA TYPE TRUE-'),
        sg.Radio("Quaternion", "RADIO1", enable_events = True, key='-DATA TYPE FALSE-')],
    
    [sg.Button(button_text='Start',size=(17,2), key='-START-'),
    sg.Button(button_text='Stop',size=(17,2), key='-STOP-'),
    sg.Button(button_text='Reset Heading',size=(17,2), key='-HEADING-'),
    sg.Button(button_text='Close',size=(17,2), key='-CLOSE-')]
]

WINDOWS = set()

# ---------------GUIs---------------
def BLE_scanner():
    form = sg.FlexForm(
    "xSens Dot Bluetooth", 
    auto_size_text = True, 
    default_element_size = (20, 1))
    window_1 = form.Layout(layout_BLE)

    sensors = []
    ready_to_stream = {"stream_status": False}
    auto_run = {"scan": True, "run": True}
    
    while True:
        #Autoscan
        if auto_run["scan"] == True:
            auto_run["scan"] = False
            threading.Thread(target = dotMain.run_scan_sensors, args = (window_1, ready_to_stream, addressNames, sensors, auto_run,), daemon = True).start()

        event, value = window_1.read()
        # Force Scan
        if event == '-SCAN-':
            auto_run["scan"] = True
        # Streaming
        elif event == '-RUN-':
            if ready_to_stream["stream_status"] == True:
                # Opens the BLE Streaming window
                print("Closing BLE Window")
                print("Opening Streaming Window")
                window_1.close()
                BLE_streamer(sensors[0])
            break
        # Auto run button
        elif event == '-AUTO RUN-':
            auto_run["run"] = not auto_run["run"]
            print(f'Auto: {auto_run["run"]}')
        
        # Exit
        elif event == "__TIMEOUT__":
            continue
        elif event == "Exit" or event == None:
            break
    window_1.close()

def BLE_streamer(sensors):
    form = sg.FlexForm(
    "XSENS Dot to PC Quaternion Streaming", 
    auto_size_text = True, 
    default_element_size = (40, 1))
    window_2 = form.Layout(layout_stream)

    # Training classification model
    classify_class = dotClassify.classify([1, 2, 3, 4, 5])
    classify_class.make_model("")

    # Streaming
    dataObj = dotCSV.constructData(classify_class.the_classifier, window_2)
    
    threading.Thread(target = dotMain.run_quaternions, args = (sensors, addressNames, dataObj,), daemon = True).start()
    print("Starting Stream...")

    while True:
        event_2, values = window_2.read()
        # Force Scan
        if event_2 == '-START-':
            dataObj.stream_control["start_stop"] = True
            dataObj.stream_control["new_name"] = True
        # Streaming
        elif event_2 == '-STOP-':
            dataObj.stream_control["start_stop"] = False
        # Heading reset
        elif event_2 == '-HEADING-':
            dataObj.stream_control["new_heading"] = True
        # Euler vs Quaternion
        elif event_2 == '-DATA TYPE TRUE-':
            dataObj.stream_control["euler_quaternion"] = True
        elif event_2 == '-DATA TYPE FALSE-':
            dataObj.stream_control["euler_quaternion"] = False
        # Close
        elif event_2 == '-CLOSE-':
            dataObj.stream_control["shutdown"] = True
            print("Turning off sensors")
            break
        # Timeout
        elif event_2 == "__TIMEOUT__":
            continue
        # Exit
        elif event_2 == "Exit" or event_2 == None:
            break
    window_2.close()
    print("Closing Streaming Window")

# ---------------Main---------------
if __name__ == '__main__':
    BLE_scanner()
    print("Exiting Program")