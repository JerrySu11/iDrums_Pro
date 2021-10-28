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
PP_ADDRESS = "http://192.168.43.1:8080"
PP_CHANNELS = ["accX", "accY", "accZ"]
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

# make one of them true at a time
isAnimate = False
isCollectData = True 


def getSensorData():
    url = PP_ADDRESS + "/get?" + ("&".join(PP_CHANNELS))
    data = requests.get(url=url).json()
    accX = data["buffer"][PP_CHANNELS[0]]["buffer"][0]
    accY = data["buffer"][PP_CHANNELS[1]]["buffer"][0]
    accZ = data["buffer"][PP_CHANNELS[2]]["buffer"][0]
    # print (accX, ' ', accY, ' ', accY)
    return [accX, accY, accZ]
    


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
    
def getData():
    [naccX, naccY, naccZ] = getSensorData() # get nth sample
    t = dt.datetime.now().strftime('%M:%S.%f') #%H:%M:%S.%f
    xs.append(t) 
    accX.append(naccX)
    accY.append(naccY)
    accZ.append(naccZ)
    return [t, naccX, naccY, naccZ]

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
    if second_average - first_average < 0:
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
    #SOUNDS ARE LOADED HERE
    filename = 'sounds/kick.wav'
    wave_obj = sa.WaveObject.from_wave_file(filename)
    if isAnimate == True:
        #interval in milliseconds
        ani = anim.FuncAnimation(fig, animate, fargs=(xs, accX, accY, accZ), interval=INTERVALS, repeat = True)
        plt.show()
    if isCollectData == True:
        flag = 0
        while True:
            [t, naccX, naccY, naccZ] = getData()
            print([t, naccX, naccY, naccZ])
            fillBuffer(t, naccX, naccY, naccZ)
        #SOUND IS PLAYED HERE
            if naccX != None:
                if naccX**2+naccY**2+naccZ**2 > 40 and flag == 0:
                    if meetsCritera():
                        play_obj = wave_obj.play()
                        play_obj.wait_done() 
                    flag = 1
                if naccX**2+naccY**2+naccZ**2 < 10:
                    flag = 0
            #time.sleep(INTERVAL/1000)   # Delays for INTERVALS seconds.



def the_gui():
    """
    Starts and executes the GUI
    Reads data from a Queue and displays the data to the window
    Returns when the user exits / closes the window
    """
    sg.theme('Light Brown 3')
    gui_queue = queue.Queue()  # queue used to communicate between the gui and the threads

    layout = [[sg.Text('Long task to perform example')],
              [sg.Output(size=(70, 12))],
              [sg.Text('Number of seconds your task will take'),
                  sg.Input(key='-SECONDS-', size=(5, 1)),
                  sg.Button('Do Long Task', bind_return_key=True)],
              [sg.Button('Click Me'), sg.Button('Exit')], ]

    window = sg.Window('Multithreaded Window', layout)

    # --------------------- EVENT LOOP ---------------------
    while True:
        event, values = window.read(timeout=100)
        if event in (None, 'Exit'):
            break
        elif event.startswith('Do'):
            try:
                seconds = int(values['-SECONDS-'])
                print('Thread ALIVE! Long work....sending value of {} seconds'.format(seconds))
                threading.Thread(target=main,
                                 args=(), daemon=True).start()
            except Exception as e:
                print('Error starting work thread. Bad seconds input: "%s"' %
                      values['-SECONDS-'])
        elif event == 'Click Me':
            print('Your GUI is alive and well')
        # --------------- Check for incoming messages from threads  ---------------
        try:
            message = gui_queue.get_nowait()
        except queue.Empty:             # get_nowait() will get exception when Queue is empty
            message = None              # break from the loop if no more messages are queued up

        # if message received from queue, display the message in the Window
        if message:
            print('Got a message back from the thread: ', message)

    # if user exits the window, then close the window and exit the GUI func
    window.close()

if __name__ == '__main__':
    the_gui()