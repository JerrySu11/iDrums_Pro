import requests
import time
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import simpleaudio as sa
import PySimpleGUI as sg
import threading
import queue
import time
#phyphox configuration
PP_ADDRESS = "http://192.168.86.23:80"
PP_CHANNELS = ["accX", "accY", "accZ"]
PP_CHANNELS2 = ["magX", "magY", "magZ"]
sampling_rate = 100

#animation and data collection config
PREV_SAMPLE = 50
INTERVALS = 1000/sampling_rate

#sets up buffer
samples_taken = 10
buffer_length = 0
buffer = [[] for x in range(samples_taken)]

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

#global var to save timestamp
xs = []

# global array to save acceleration
accX =[]
accY = []
accZ = []

magX =[]
magY = []
magZ = []

# make one of them true at a time
isAnimate = False
isCollectData = True 

STOPTHREAD = True

def getSensorData():
    url = PP_ADDRESS + "/get?" + ("&".join(PP_CHANNELS))
    data = requests.get(url=url).json()
    accX = data["buffer"][PP_CHANNELS[0]]["buffer"][0]
    accY = data["buffer"][PP_CHANNELS[1]]["buffer"][0]
    accZ = data["buffer"][PP_CHANNELS[2]]["buffer"][0]
    # print (accX, ' ', accY, ' ', accY)
    return [accX, accY, accZ]

def getSensorData2():
    url = PP_ADDRESS + "/get?" + ("&".join(PP_CHANNELS2))
    data = requests.get(url=url).json()
    magX = data["buffer"][PP_CHANNELS2[0]]["buffer"][0]
    magY = data["buffer"][PP_CHANNELS2[1]]["buffer"][0]
    magZ = data["buffer"][PP_CHANNELS2[2]]["buffer"][0]

    return [magX, magY, magZ]


# In[11]:


# This function is called periodically from FuncAnimation
def animate(i, xs, accX, accY, accZ):
    [naccX, naccY, naccZ] = getSensorData()


    xs.append(dt.datetime.now().strftime('%S.%f')) #%H:%M:%S.%f

    accX.append(naccX)
    accY.append(naccY)
    accZ.append(naccZ)

     #plot only the 50 (PREV_SAMPLE) previous smaples
    _accX = accX[-PREV_SAMPLE:]
    _accY = accY[-PREV_SAMPLE:]
    _accZ = accZ[-PREV_SAMPLE:]


    xs = xs[-PREV_SAMPLE:]

    ax.clear()
   
    ax.plot(xs, _accX, label='AX')
    ax.plot(xs, _accY, label='AY')
    ax.plot(xs, _accZ, label='AZ')
        

    ax.legend(loc = 'upper left')
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
##JERRY's code
import osascript
THRESHOLD_VALUE = 40
LARGEST_ACC = 100
def makeSound(acc_data,mag_data):
    if math.abs(acc_data)>=THRESHOLD_VALUE:
        file = sound_based_on_direction(mag_data) #need implemented
        changeVolume((acc_data-THRESHOLD_VALUE)/(LARGEST_ACC-THRESHOLD_VALUE)*100) # scale to 0-100
        wav_file = sa.WaveObject.from_wave_file(file) #sa => simpleaudio module
        play_obj = wav_file.play()
        play_obj.wait_done()

#call this method after reaching the swing threshold and before invoking the sound file
def changeVolume(strength): #strength is scaled from 0 to 100
    osascript.osascript("set volume output volume "+str(strength))      
##End of Jerry's code
def getData():
    [naccX, naccY, naccZ] = getSensorData() # get nth sample
    t = dt.datetime.now().strftime('%M:%S.%f') #%H:%M:%S.%f
    xs.append(t) 
    accX.append(naccX)
    accY.append(naccY)
    accZ.append(naccZ)
    return [t, naccX, naccY, naccZ]

def getData2():
    [nmagX, nmagY, nmagZ] = getSensorData2() # get nth sample
    t = dt.datetime.now().strftime('%M:%S.%f') #%H:%M:%S.%f
    xs.append(t) 
    magX.append(nmagX)
    magY.append(nmagY)
    magZ.append(nmagZ)
    return [t, nmagX, nmagY, nmagZ]

def meetsCritera():
    global buffer_length, samples_taken
    if buffer_length >= samples_taken and recognizeZspike():
        return True
    return False

def recognizeZspike(): #The Z acceleration sharply increases then decreases when the phone is pulled back and sharply decreases then increases when pushed forward
    z_values = []
    for data in buffer:
        z_values.append(data[2])
    first = z_values[:len(z_values)//2]
    second = z_values[len(z_values)//2:]
    first_average = sum(first)/len(first)
    second_average = sum(second)/len(second)
    print(first)
    print(second)
    print(first_average)
    print(second_average)
    if second_average - first_average > 0:
        return True
    return False
def fillBuffer(t, naccX, naccY, naccZ):
    global buffer_length, samples_taken
    if buffer_length < samples_taken:
        buffer[buffer_length] = [naccX, naccY, naccZ]
        buffer_length += 1
    else:
        shiftDown(buffer)
        buffer[buffer_length-1] = [naccX, naccY, naccZ]
def shiftDown(buffer):
    for x in range(1, len(buffer)):
        buffer[x-1] = buffer[x]

def main():
    global STOPTHREAD
    #SOUNDS ARE LOADED HERE

    filename = 'sounds/kick.wav'
    filename2 = 'sounds/snare.wav'
    filename3 = 'sounds/hat.wav'
    left_obj = sa.WaveObject.from_wave_file(filename)
    middle_obj = sa.WaveObject.from_wave_file(filename2)
    right_obj = sa.WaveObject.from_wave_file(filename3)

    if isAnimate == True:
        #interval in milliseconds
        ani = anim.FuncAnimation(fig, animate, fargs=(xs, accX, accY, accZ), interval=INTERVALS, repeat = True)
        plt.show()
    if isCollectData == True:
        flag = 0
        while True:
            if STOPTHREAD == True:
                break
            [t, naccX, naccY, naccZ] = getData()
            [t, nmagX, nmagY, nmagZ] = getData2()
            print([t, nmagX, nmagY, nmagZ])
            
            fillBuffer(t, naccX, naccY, naccZ)
        #SOUND IS PLAYED HERE
            if naccX != None and nmagX != None:
                if naccX**2+naccY**2+naccZ**2 > 400 and flag == 0:
                    if meetsCritera():
                        #left- kick
                        if(nmagY > 0):
                            play_obj = left_obj.play()
                            play_obj.wait_done()
                            flag = 1
                            
                        #middle- snare
                        elif(nmagZ < -20):
                            play_obj = middle_obj.play()
                            play_obj.wait_done()
                            flag = 1
                            
                        #right- hat (nmagX > 0 and nmagY < -20)
                        elif(nmagX > 0):
                            play_obj = right_obj.play()
                            play_obj.wait_done()
                            flag = 1

                if naccX**2+naccY**2+naccZ**2 < 200:
                    flag = 0
            #time.sleep(INTERVAL/1000)   # Delays for INTERVALS seconds.



def test(file1, file2, file3): #we will pass main instead
        print(file1 + ", " + file2 + ", " + file3)


'''
our main function will look as it does, but we will pass the above params in, 
we just need to modify "sa.WaveObject.from_wave_file()" to take these params
'''

def the_gui():
    """
    Starts and executes the GUI
    Reads data from a Queue and displays the data to the window
    Returns when the user exits / closes the window
    """
    global STOPTHREAD
    sg.theme('Material 1')
    gui_queue = queue.Queue()  # queue used to communicate between the gui and the threads

    layout = [[sg.Text('Debug Console')],
            [sg.Output(size=(70, 12))],
            [sg.Text('Press to toggle swings'),
                sg.Button('On/Off', bind_return_key=True)],
            [sg.Input(key='-FILE1-', size=(7, 1)),
                sg.Button('Change File 1', bind_return_key=True),
                sg.Input(key='-FILE2-', size=(7, 1)),
                sg.Button('Change File 2', bind_return_key=True),
                sg.Input(key='-FILE3-', size=(7, 1)),
                sg.Button('Change File 3', bind_return_key=True)],
            [sg.Button('Exit')], ]

    window = sg.Window('iDrums Pro Visual Interface', layout)


    file1 = 'sounds/kick.wav'
    file2 = 'undef'
    file3 = 'undef'

    flag = False



    while True:
        event, values = window.read(timeout=100)
        if event in (None, 'Exit'):
            break
        elif event.startswith('On'):
            print(flag) #debugging
            if STOPTHREAD == True:   
                STOPTHREAD = False
                try:
                    currVal1 = values['-FILE1-']
                    currVal2 = values['-FILE1-']
                    currVal3 = values['-FILE1-']

                    drums = threading.Thread(
                        target=main,
                        args=[], 
                        daemon=True)
                    drums.start()
            
                except Exception as e:
                    print('Something went wrong with the main() call')
            else: 
                STOPTHREAD = True
                drums.join()

        elif event == 'Change File 1':
            file1 = values['-FILE1-']
        elif event == 'Change File 2':
            file2 = values['-FILE2-']
        elif event == 'Change File 3':
            file3 = values['-FILE3-']



        # --------------- Not sure if we need this code but I'll leave it  ---------------
        try:
            message = gui_queue.get_nowait()
        except queue.Empty:             # get_nowait() will get exception when Queue is empty
            message = None              # break from the loop if no more messages are queued up

        # if message received from queue, display the message in the Window
        if message:
            print('Got a message back from the thread: ', message)

    # if user exits the window, then close the window and exit the GUI func
    window.close()


if __name__  == '__main__':
    the_gui()