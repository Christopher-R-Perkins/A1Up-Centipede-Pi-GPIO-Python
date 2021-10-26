### Updating trackball script to auto change modes
## Arcade1Up script upgrade
### What's new?
I decided to change from Python 2 to Python 3 between when the script was first made and when the upgrade was made. So, to use this version of the script you will need to install the Python 3 versions of

 - pySerial
 - pyalsaaudio
 - gpiozero
 - evdev
These are easily installed via pip3. Besides that, the /etc/rc.local file needs a different line to run the script due to changing python versions:

    python3 /home/pi/pyTrackball.py &

Finally, we need another file to communicate with our pyTrackball script when we change games via RetroPie. In /opt/retropie/configs/all you can add runcommand-onstart.sh and make it executable. This file is run whenever you start a game and thus our file will check if it's a game we want to change modes on and send the mode via port 5269. We also need runcommand-onend.sh to tell it to change back to the default mode when exiting a game.

### Problems
Due to how slow the python script is and our wait time to not hurt performance too much, large amounts of movement on the trackball causes all kinds of unintentional effects. The future involves me offloading it from the Raspberry Pi and using a seperate microcontroller to translate the controls for an interface device. 
