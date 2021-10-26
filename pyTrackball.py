import serial, math
from evdev import UInput, AbsInfo, ecodes as e
from time import sleep
from gpiozero import Button
from alsaaudio import Mixer
 
#Variables
serialInputDevice = '/dev/ttyUSB0'
timeToSleep = .03333 # Time between loops
joystickDividend = 10.0 # tanh(x/joystickDividend) to convert pulses to axis
 
##########################################################################
# Definitions that shouldnt be changed
##########################################################################
def convertAxisData(data):
    if data == '\x01' :
        return 1
    elif data == '\x7e' :
        return -1
    return 0
 
mouse = {
    e.EV_KEY : [e.BTN_MOUSE],
    e.EV_REL : [e.REL_X, e.REL_Y, e.REL_Z],
    e.EV_MSC : [e.MSC_SCAN]
}
 
joystick = {
    e.EV_KEY : [e.BTN_START, e.BTN_SELECT, e.BTN_A, e.BTN_B, e.BTN_C ],
    e.EV_ABS : [(e.ABS_X, AbsInfo(0, -32767, 32767, 0, 0, 0)),
                (e.ABS_Y, AbsInfo(0, -32767, 32767, 0, 0, 0)),
                (e.ABS_Z, AbsInfo(0, -32767, 32767, 0, 0, 0))]
}
 
downA = False
downB = False
downC = False
downStart = False
downSelect = False
downModeSelect = False
joystickMode = True
volumeLevel = -1
###########################################################################
mix = Mixer('PCM')
ser = serial.Serial(serialInputDevice,100000, serial.SEVENBITS)
uiMouse = UInput(mouse, name='A1UP-Trackball-Spinner', version = 0x3)
uiJoystick = UInput(joystick, name='A1UP-Centipede-Panel', version = 0x3)
 
buttonA = Button(5)
buttonB = Button(6)
buttonC = Button(13)
buttonStart = Button(19)
buttonSelect = Button(26)
switchVolA = Button(20)
switchVolB = Button(21)
 
while 1:
    #K, let's check buttons. Start with mode change
    if buttonSelect.is_pressed and buttonA.is_pressed:
        if not downModeSelect:
            downModeSelect = True
            joystickMode = not joystickMode
    else:
        downModeSelect = False
 
    if buttonA.is_pressed and not downModeSelect:
        if not downA:
            downA = True
            if joystickMode:
                uiJoystick.write(e.EV_KEY, e.BTN_A,1)
                uiMouse.write(e.EV_KEY, e.BTN_MOUSE,0)
            else:
                uiMouse.write(e.EV_KEY, e.BTN_MOUSE,1)
                uiJoystick.write(e.EV_KEY, e.BTN_A,0)
    elif downA:
        downA = False
        uiMouse.write(e.EV_KEY, e.BTN_MOUSE,0)
        uiJoystick.write(e.EV_KEY,e.BTN_A,0)
 
    if buttonB.is_pressed:
        if not downB:
            downB = True
            uiJoystick.write(e.EV_KEY, e.BTN_B,1)
    elif downB:
        downB = False
        uiJoystick.write(e.EV_KEY,e.BTN_B,0)
 
    if buttonC.is_pressed:
        if not downC:
            downC = True
            uiJoystick.write(e.EV_KEY, e.BTN_C, 1)
    elif downC:
        downC = False
        uiJoystick.write(e.EV_KEY,e.BTN_C,0)
 
    if buttonStart.is_pressed:
        if not downStart:
            downStart = True
            uiJoystick.write(e.EV_KEY, e.BTN_START, 1)
    elif downStart:
        downStart = False
        uiJoystick.write(e.EV_KEY, e.BTN_START, 0)
 
    if buttonSelect.is_pressed:
        if not downSelect:
            downSelect = True
            uiJoystick.write(e.EV_KEY, e.BTN_SELECT, 1)
    elif downSelect:
        downSelect = False
        uiJoystick.write(e.EV_KEY, e.BTN_SELECT, 0)
 
    if switchVolA.is_pressed:
        if volumeLevel != 0:
            volumeLevel = 0
            mix.setvolume(0)
    elif switchVolB.is_pressed:
        if volumeLevel != 2:
            volumeLevel = 2
            mix.setvolume(90)
    else:
        if volumeLevel != 1:
            volumeLevel = 1
            mix.setvolume(60)
 
    # Now do the trackball stuff
    lengthOfBuffer = ser.in_waiting
    bytesRead = ser.read(lengthOfBuffer)
    deltaX = 0
    deltaY = 0
    deltaZ = 0
 
    iterator = 0
    loopTimes = math.floor(lengthOfBuffer/4)
    #buffer should always be a multiple of 4, but sometimes we drop bytes.
    #if that happens, we don't want a fraction on the loop.
    while iterator < loopTimes :
        if bytesRead[iterator*4] != '\x7f':
            #The 4 byte packet always starts with 0x7F, if we dropped some bytes
            #and it's no longer in sync. It's easier to just quit.
            break
        deltaX += convertAxisData(bytesRead[iterator*4+1])
        deltaY += convertAxisData(bytesRead[iterator*4+2])
        deltaZ += convertAxisData(bytesRead[iterator*4+3])
        
        iterator+=1
 
    #We use the deltas to simulate the mouse/joystick!
    if joystickMode:
        uiJoystick.write(e.EV_ABS, e.ABS_X, int(math.tanh(deltaX/joystickDividend)*32767))
        uiJoystick.write(e.EV_ABS, e.ABS_Y, int(math.tanh(deltaY/joystickDividend)*32767))
        uiJoystick.write(e.EV_ABS, e.ABS_Z, int(math.tanh(deltaZ/joystickDividend)*32767))
        uiMouse.write(e.EV_REL, e.REL_X, 0)
        uiMouse.write(e.EV_REL, e.REL_Y, 0)
        uiMouse.write(e.EV_REL, e.REL_Z, 0)
    else:
        uiMouse.write(e.EV_REL,e.REL_X, deltaX)
        uiMouse.write(e.EV_REL,e.REL_Y, deltaY)
        uiMouse.write(e.EV_REL,e.REL_Z, deltaZ)
        uiJoystick.write(e.EV_ABS, e.ABS_X, 0)
        uiJoystick.write(e.EV_ABS, e.ABS_Y, 0)
        uiJoystick.write(e.EV_ABS, e.ABS_Z, 0)
    #Sync our fake inputs
    uiMouse.syn()
    uiJoystick.syn()
 
    sleep(timeToSleep)