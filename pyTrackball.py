import serial, math, asyncio, threading
from evdev import UInput, AbsInfo, ecodes as e
from time import sleep
from gpiozero import Button
from alsaaudio import Mixer
 
#Variables
serialInputDevice = '/dev/ttyUSB0'
timeToSleep = .01 # Time between loops
joystickDividend = 16.0 # tanh(x/joystickDividend) to convert pulses to axis
joystickStick = 3 #The number of loops it will hold a joystick value that is higher than current input
 
buttonA = Button(5)
buttonB = Button(6)
buttonC = Button(13)
buttonStart = Button(19)
buttonSelect = Button(26)
switchVolA = Button(20)
switchVolB = Button(21)
 
##########################################################################
# Definitions that shouldnt be changed
##########################################################################
packetStart = 127
packetDec = 63
 
def ConvertAxisData(data):
    dataValue = data
    if data > packetDec:
        return data-127
    return data
 
 
ser = serial.Serial(serialInputDevice,115200, serial.SEVENBITS)
 
def ReadTrackball():
    lengthOfBuffer = ser.in_waiting
    bytesRead = ser.read(lengthOfBuffer)
    deltaX = 0
    deltaY = 0
    deltaZ = 0
 
    iterator = 0
 
    while iterator+3 < lengthOfBuffer:
        #Somtimes we drop bytes, so we gotta make sure we got a full packet
        #this while loop iterates till it finds one. Most of the time it never
        #loops its just used to check.
        while bytesRead[iterator] != packetStart or bytesRead[iterator+1] == packetStart or bytesRead[iterator+2] == packetStart or bytesRead[iterator+3] == packetStart:
            iterator += 1
            if iterator+3 > lengthOfBuffer:
                return [deltaX,deltaY,deltaZ]
            continue
        deltaX += ConvertAxisData(bytesRead[iterator+1])
        deltaY += ConvertAxisData(bytesRead[iterator+2])
        deltaZ += ConvertAxisData(bytesRead[iterator+3])
       
        iterator+=4
    return [deltaX,deltaY,deltaZ]
 
mix = Mixer('PCM')
volumeLevel = -1
 
def VolumeControl():
    global volumeLevel
    if switchVolA.is_pressed:
        if volumeLevel != 0:
            volumeLevel = 0
            mix.setvolume(0)
    elif switchVolB.is_pressed:
        if volumeLevel != 2:
            volumeLevel = 2
            mix.setvolume(80)
    else:
        if volumeLevel != 1:
            volumeLevel = 1
            mix.setvolume(60)
 
mouse = {
    e.EV_KEY : [e.BTN_MOUSE, e.BTN_RIGHT, e.KEY_LEFTCTRL, e.KEY_Q, e.KEY_F5, e.KEY_ESC],
    e.EV_REL : [e.REL_X, e.REL_Y, e.REL_Z],
    e.EV_MSC : [e.MSC_SCAN]
}
 
joystick = {
    e.EV_KEY : [e.BTN_START, e.BTN_SELECT, e.BTN_A, e.BTN_B, e.BTN_C ],
    e.EV_ABS : [(e.ABS_X, AbsInfo(0, -32767, 32767, 0, 0, 0)),
                (e.ABS_Y, AbsInfo(0, -32767, 32767, 0, 0, 0)),
                (e.ABS_Z, AbsInfo(0, -32767, 32767, 0, 0, 0))]
}
uiMouse = UInput(mouse, name='A1UP-Trackball-Spinner', version = 0x3)
uiJoystick = UInput(joystick, name='A1UP-Centipede-Panel', version = 0x3)
 
def ReadButtons():
    return [buttonA.is_pressed, buttonB.is_pressed, buttonC.is_pressed, buttonSelect.is_pressed, buttonStart.is_pressed]
 
downA = False
downB = False
downC = False
downStart = False
downSelect = False
downModeSelect = False
joystickMode = True
accelerateMouse = False
 
def CommonButtonPresses(buttonList):
    global downSelect, downStart, downB, downC
    if buttonList[3]:
        if not downSelect:
            downSelect = True
            uiJoystick.write(e.EV_KEY, e.BTN_SELECT, 1)
    elif downSelect:
        downSelect = False
        uiJoystick.write(e.EV_KEY, e.BTN_SELECT, 0)
 
    if buttonList[4]:
        if not downStart:
            downStart = True
            uiJoystick.write(e.EV_KEY, e.BTN_START, 1)
    elif downStart:
        downStart = False
        uiJoystick.write(e.EV_KEY, e.BTN_START, 0)
 
    if buttonList[1]:
        if not downB:
            downB = True
            uiJoystick.write(e.EV_KEY, e.BTN_B, 1)
    elif downB:
        downB = False
        uiJoystick.write(e.EV_KEY, e.BTN_B, 0)
 
    if buttonList[2]:
        if not downC:
            downC = True
            uiJoystick.write(e.EV_KEY, e.BTN_C, 1)
    elif downC:
        downC = False
        uiJoystick.write(e.EV_KEY, e.BTN_C, 0)
 
lastJoystickDis = 0
lastJoysticCount = 0
 
def JoystickMode(axisList, buttonList):
    global downA, lastJoysticCount, lastJoystickDis
    CommonButtonPresses(buttonList)
 
    if buttonList[0]:
        if not downA:
            downA = True
            uiJoystick.write(e.EV_KEY, e.BTN_A, 1)
    elif downA:
        downA = False
        uiJoystick.write(e.EV_KEY, e.BTN_A, 0)
    dis = axisData[0]+axisData[1]+axisData[2]
    lastJoysticCount = lastJoysticCount + 1
    if dis > lastJoystickDis or lastJoysticCount > joystickStick:
        lastJoystickDis = dis
        lastJoysticCount = 0
        uiJoystick.write(e.EV_ABS, e.ABS_X, int(math.tanh(axisData[0]/joystickDividend)*32767))
        uiJoystick.write(e.EV_ABS, e.ABS_Y, int(math.tanh(axisData[1]/joystickDividend)*32767))
        uiJoystick.write(e.EV_ABS, e.ABS_Z, int(math.tanh(axisData[2]/joystickDividend)*32767))
 
def MouseMode(axisList, buttonList):
    global downA
    CommonButtonPresses(buttonList)
 
    if buttonList[0]:
        if not downA:
            downA = True
            uiMouse.write(e.EV_KEY, e.BTN_MOUSE, 1)
    elif downA:
        downA = False
        uiMouse.write(e.EV_KEY, e.BTN_MOUSE, 0)
    uiMouse.write(e.EV_REL,e.REL_X, axisList[0])
    uiMouse.write(e.EV_REL,e.REL_Y, axisList[1])
    uiMouse.write(e.EV_REL,e.REL_Z, axisList[2])
 
def AccelerateAxis(axisValue):
    if axisValue > 10:
        axisValue = int(axisValue * 1.5)
    elif axisValue > 20:
        axisValue = axisValue * 2
    return axisValue
 
def ScummMode(axisList, buttonList):
    global downA, downB, downC, downSelect, downStart
 
    if buttonList[0]:
        if not downA:
            downA = True
            uiMouse.write(e.EV_KEY, e.BTN_MOUSE, 1)
    elif downA:
        downA = False
        uiMouse.write(e.EV_KEY, e.BTN_MOUSE, 0)
 
    if buttonList[1]:
        if not downB:
            downB = True
            uiMouse.write(e.EV_KEY, e.BTN_RIGHT, 1)
    elif downB:
        downB = False
        uiMouse.write(e.EV_KEY, e.BTN_RIGHT, 0)
 
    if buttonList[2]:
        if not downC:
            downC = True
            uiMouse.write(e.EV_KEY, e.KEY_ESC, 1)
    elif downC:
        downC = False
        uiMouse.write(e.EV_KEY, e.KEY_ESC, 0)
 
    if buttonList[3]: #select
        if not downSelect:
            if buttonList[4]: #start
                if not downStart:
                    downStart = True
                    uiMouse.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
                    uiMouse.write(e.EV_KEY, e.KEY_Q, 1)
            elif downStart:
                downStart = False
                uiMouse.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
                uiMouse.write(e.EV_KEY, e.KEY_Q, 0)
    else:
        if downSelect:
            downSelect = False
            uiMouse.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
            uiMouse.write(e.EV_KEY, e.KEY_Q, 0)
        if buttonList[4]:
            if not downStart:
                downStart = True
                uiMouse.write(e.EV_KEY, e.KEY_F5, 1)
        elif downStart:
            downStart = False
            uiMouse.write(e.EV_KEY, e.KEY_F5, 0)
    
 
    uiMouse.write(e.EV_REL, e.REL_X, AccelerateAxis(axisList[0]))
    uiMouse.write(e.EV_REL, e.REL_Y, AccelerateAxis(axisList[1]))
    uiMouse.write(e.EV_REL, e.REL_Z, axisList[2])
 
currentMode = 0 #0 is joystick    2 is Scumm
nextMode = 0    #1 is trackball
changeMode = False
 
def ClearInput() :
    global lastJoysticCount, lastJoystickDis
    if currentMode > 0 and nextMode == 0:
        uiMouse.write(e.EV_REL, e.REL_X, 0)
        uiMouse.write(e.EV_REL, e.REL_Y, 0)
        uiMouse.write(e.EV_REL, e.REL_Z, 0)
        uiMouse.write(e.EV_KEY, e.BTN_MOUSE, 0)
    if currentMode == 0 and nextMode > 0:
        uiJoystick.write(e.EV_ABS, e.ABS_X, 0)
        uiJoystick.write(e.EV_ABS, e.ABS_Y, 0)
        uiJoystick.write(e.EV_ABS, e.ABS_Z, 0)
        uiJoystick.write(e.EV_KEY, e.BTN_A, 0)
        lastJoysticCount = 0
        lastJoystickDis = 0
    if currentMode == 2:
        uiMouse.write(e.EV_KEY, e.KEY_F5, 0)
        uiMouse.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
        uiMouse.write(e.EV_KEY, e.KEY_Q, 0)
        uiMouse.write(e.EV_KEY, e.KEY_ESC, 0)
        uiMouse.write(e.EV_KEY, e.BTN_RIGHT, 0)    
 
async def ChangeModeServer(reader, writer):
    global changeMode
    global nextMode
    while True:
        data = await reader.read(10)
        if not data:
            break
        if data[0] >= 48 and data[0] <= 50:
            nextMode = data[0] - 48
        changeMode = True
        writer.close()
        sleep(0)
###########################################################################
 
server = asyncio.get_event_loop()
server.create_task(asyncio.start_server(ChangeModeServer, 'localhost', 5269))
thread = threading.Thread(target = server.run_forever)
thread.start()
                            
while 1:
    VolumeControl()
 
    if changeMode:
        ClearInput()
        currentMode = nextMode
        if currentMode == 0:
            print("Joystick mode activated")
        elif currentMode == 1:
            print("Trackball mode activated")
        elif currentMode == 2:
            print("Scummvm mode activated")
        changeMode = False
    
    buttonsPressed = ReadButtons()
 
    axisData = ReadTrackball()
 
    #We use the deltas to simulate the mouse/joystick!
    if currentMode == 0:
       JoystickMode(axisData,buttonsPressed)
    elif currentMode == 1:
        MouseMode(axisData, buttonsPressed)
    elif currentMode == 2:
        ScummMode(axisData, buttonsPressed)
    #Sync our fake inputs
    uiMouse.syn()
    uiJoystick.syn()
 
    sleep(timeToSleep)