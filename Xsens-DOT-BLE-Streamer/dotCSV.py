import time
import csv
from squaternion import Quaternion

# CSV Column labels
fieldnames = [
    "TIMESTAMP", "S1_Arm_Left_w", "S1_Arm_Left_x", "S1_Arm_Left_y", "S1_Arm_Left_z",
                 "S2_Arm_Right_w", "S2_Arm_Right_x", "S2_Arm_Right_y", "S2_Arm_Right_z",
                 "S3_Leg_Left_w", "S3_Leg_Left_x", "S3_Leg_Left_y", "S3_Leg_Left_z",
                 "S4_Leg_Right_w", "S4_Leg_Right_x", "S4_Leg_Right_y", "S4_Leg_Right_z",
                 "S5_Head_w", "S5_Head_x", "S5_Head_y", "S5_Head_z"]

positions = {
    "A": "Lying on back. Hands on sides",
    "B": "Lying on back. Hands under head",
    "C": "Lying on front. Hands on sides",
    "D": "Lying on front. Hands under head",
    "E": "Lying on left. Hands on under head",
    "F": "Lying on left. Right hand on tummy",
    "G": "Lying on right. Hands on under head",
    "H": "Lying on right. Left hand on tummy",
    "I": "Standing",
}

# Print CSV
def printCSV(quat_data, fileName, stream_control):
    quat_data_round = [round(num, 3) for num in quat_data]

    with open(f'data/{fileName}.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if stream_control["new_name"] == True:
            stream_control["new_name"] = False
            writer.writerow(fieldnames)
        writer.writerow(quat_data_round)

# Classification
def make_classify(classifier, window_2, live_data):
    flat_list = [[item for sublist in live_data for item in sublist]]
    
    prediction_random_forrest = (classifier.predict(flat_list))[0]

    result = f"{prediction_random_forrest}: {positions[prediction_random_forrest]}"

    window_2["-CLASSIFY-"].Update(values=[result])

# Construct data
class constructData:
    def __init__(self, classifier, window_2):
        self.data_list = [[], [], [], [], []]
        self.data_list_offset = [[], [], [], [], []]
        self.sensorTrackList = [0]*5
        self.stream_control = {
            "start_stop": True, 
            "new_name": True, 
            "new_heading": True, 
            "euler_quaternion": True, 
            "shutdown": False
            }
        self.fileName = time.strftime("Dot_Data_%H_%M_%S_%d_%m_%Y")
        self.time_prev = time.time()
        self.time_flag = True
        self.first_run = True
        self.classifier = classifier
        self.window_2 = window_2
        self.counter = 0

    def structappend(self, data):
        quat_data_list_with_offset = [[], [], [], [], []]
        
        # Grabbing sensor ID for sensor monitoring
        sensorID = data[1]

        # Checking if data should be appended to list
        if(sum(self.sensorTrackList) <= 5):
            if(self.sensorTrackList[(sensorID - 1)] == 0):
                self.sensorTrackList[(sensorID - 1)] = 1

                # Appending the new data
                for ii in range(len(self.data_list)):
                    self.data_list[(sensorID-1)] = data[2]

        # Checking whether data frequency is within tolerances
        sensor_track(self.sensorTrackList)

        # Once all the sensor data is accounted for post data into CSV
        if(sum(self.sensorTrackList) == 5):
            # heading correction------------------------------------------------
            if self.stream_control["new_heading"] == True:
                # Postponing the update for 5s
                if self.time_flag == True:
                    self.time_prev = time.time()
                    self.time_flag = False
                    print("WARNING: New heading set in 5 seconds")
                
                if (((time.time() - self.time_prev) > 5) or (self.first_run == True)):
                    self.stream_control["new_heading"] = False
                    self.time_flag = True
                    self.first_run = False

                    print("WARNING: New heading set")
                    self.data_list_offset = quat_data_offset(self.data_list)

            quat_data_list_with_offset = quat_with_offset(self.data_list, self.data_list_offset)
            
            # GUI control
            if self.stream_control["start_stop"] == True:
                # Creating a new CSV file with the fieldnames
                if self.stream_control["new_name"] == True:
                    self.fileName = time.strftime("Dot_Data_%H_%M_%S_%d_%m_%Y")

                # CSV name handling---------------------------------------------
                # Creating appropriate formating for CSV
                CSV_data = [item for sublist in quat_data_list_with_offset for item in sublist]
                CSV_data.insert(0, data[0])

                # printing data
                printCSV(CSV_data, self.fileName, self.stream_control)
                print_data(quat_data_list_with_offset, self.stream_control["euler_quaternion"])
                make_classify(self.classifier, self.window_2, quat_data_list_with_offset)

            # Resetting sensor tracking list
            self.data_list = [[], [], [], [], []]
            self.sensorTrackList = [0]*5

# Flagging when sensors respond outside of parameters
def sensor_track(sensorTrackList):
    global time_prev, unresponsive
    
    try: time_prev
    except NameError:
        time_prev = time.time()
        unresponsive = 0

    # DEBUG Uncomment to view sensor update data for debugging
    # print(sensorTrackList)

    if( ((time.time() - time_prev) > 4) & (unresponsive == 0) ):
        time_prev = time.time()
        unresponsive = 1

        for ii in range(5):
            if(sensorTrackList[ii] == 0):
                print("WARNING: Sensor not responding: "+str(ii+1))

    if(sum(sensorTrackList) == 5):
        unresponsive = 0
        time_prev = time.time()

# Defining the offset
def quat_data_offset(data_list):
    data_list_offset = [[], [], [], [], []]

    for ii in range(len(data_list)):
        data_list_offset[ii] = Quaternion(data_list[ii][0], -data_list[ii][1], -data_list[ii][2], -data_list[ii][3])

    return data_list_offset

# Mutliplying the offset
def quat_with_offset(data_list, data_list_offset):
    quat_data_list_with_offset = [[], [], [], [], []]

    for ii in range(len(data_list)):
        quat_data_list_with_offset[ii] = data_list_offset[ii] * data_list[ii]
    
    return quat_data_list_with_offset

# Printing to the Terminal. Creating a nice format, Euler form and rounding the data
def print_data(quat_data_list_with_offset, euler_quaternion):
    euler_data_list_with_offset = [[], [], [], [], []]

    # Converting to a list of lists from a list of quaternions
    for ii in range(len(quat_data_list_with_offset)):
        q = Quaternion(quat_data_list_with_offset[ii][0], quat_data_list_with_offset[ii][1], quat_data_list_with_offset[ii][2], quat_data_list_with_offset[ii][3]).to_euler(degrees = True)
        euler_data_list_with_offset[ii] = [int(round(num, 1)) for num in q]
        
    # Printing the raw data
    if euler_quaternion == True:
        print(f'S1:{euler_data_list_with_offset[0]}  |  S2:{euler_data_list_with_offset[1]}  |  S3:{euler_data_list_with_offset[2]}  |  S4:{euler_data_list_with_offset[3]}  |  S5:{euler_data_list_with_offset[4]}')
    else:
        for ii in range(len(quat_data_list_with_offset)):
            print(f'S{ii+1}:', end = ' ')
            for jj in range(4):
                print(f'{round(quat_data_list_with_offset[ii][jj], 1)},', end = ' ')
            print("|", end = ' ')
        print("")