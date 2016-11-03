import threading, time
from x32broadcast import MIDIDevice

akai = MIDIDevice(3)
t = threading.Thread(target = akai.observe)

t.start()
try:
   while 1:
       time.sleep(0.1)
except KeyboardInterrupt:
    print "Closing MIDI device observing"
    akai.stopobserving()
    t.join()
