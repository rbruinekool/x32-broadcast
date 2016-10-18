import threading
import time

import OSC

from x32channel import MixerChannel

receive_address = '10.75.255.74', 50006   # Local Address
send_address = '10.75.255.75', 10023  # Remote Address

#############################################

class PiException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

##########################
# Channel Variables
##########################

Caster1Channel = 5
Caster2Channel = 6
HostChannel = 1

CasterDCAGroup = 2
PanelDCAGroup = 1

C1 = MixerChannel(Caster1Channel, CasterDCAGroup)
C2 = MixerChannel(Caster2Channel, CasterDCAGroup)
# C3 = MixerChannel(HostChannel, PanelDCAGroup)

NrofChannelInstances = MixerChannel._ids.next()
print "Number of channel instances created =", NrofChannelInstances

OSCMessagelist = [None] * NrofChannelInstances  # Pre-allocation

#  These objects below are the subscribe messages that are sent periodically to the X32
for i in range(0, NrofChannelInstances):
    CurrentChannelMethod = "C%d.OSCChannelSubscribeMSG()" % (i + 1)
    OSCMessagelist[i] = eval(CurrentChannelMethod)

del i

ChannelSubscribeList = [Caster1Channel, Caster2Channel]
SubscribeFactor = 0

Caster1LedChannel = 7
Caster2LedChannel = 11


##########################
# OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)
c = OSC.OSCClient()
c.setServer(s)

s.addDefaultHandlers()

# define a message-handler function for the server to call.

def X32Renewed(addr, tags, msg, source):
    dummy = 1

# Callback functions are being integrated into the MixerChannel object, so these will be removed soon
# def C1ChannelMute(addr, tags, msg, source):
#     C1.setmutebutton(msg[0])

# def C2ChannelMute(addr, tags, msg, source):
#     C2.setmutebutton(msg[0])

def C1FaderMute(addr, tags, msg, source):
    C1.setfaderlevel(msg[0])

def C2FaderMute(addr, tags, msg, source):
    C2.setfaderlevel(msg[0])

def CasterDCAMute(addr, tags, msg, source):
    C1.setdcamutebutton(msg[0])
    C2.setdcamutebutton(msg[0])

def CasterDCAFaderMute(addr, tags, msg, source):
    C1.setdcafaderlevel(msg[0])
    C2.setdcafaderlevel(msg[0])


# adding OSC handles
s.addMsgHandler("/renew", X32Renewed)
s.addMsgHandler("/ch/%02d/mix/on" %Caster1Channel , C1.setmutebutton)
s.addMsgHandler("/ch/%02d/mix/on" %Caster2Channel , C2.setmutebutton)
s.addMsgHandler("/ch/%02d/mix/fader" %Caster1Channel , C1FaderMute)
s.addMsgHandler("/ch/%02d/mix/fader" %Caster2Channel , C2FaderMute)
s.addMsgHandler("/dca/%d/on" %CasterDCAGroup , CasterDCAMute)
s.addMsgHandler("/dca/%d/fader" %CasterDCAGroup , CasterDCAFaderMute)


# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
    print addr

# Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread(target=s.serve_forever)
st.start()


# Loop while threads are running.
# OSCMessageList is a list in which each entry is another list that contains all the OSC Messages to which the Server
# will subscribe. For example OSCMessageList could look like this:
# [ ["/ch/01/mix/on" , "/ch/01/mix/fader"] , ["/ch/02/mix/on" , "/ch/02/mix/fader"]]
# I.e. the first index of the list points to a specific instance of the MixerChannel object
# The second index points to a specific OSC message that is a part of that MixerChannel object

try:
    while 1:
        for i in range(0, NrofChannelInstances):
            CurrentChannel = ("OSCMessagelist[%d][j]" % (i))
            for j in range(0, len(OSCMessagelist[i])):
                c.sendto(eval(CurrentChannel), send_address)
        time.sleep(8)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"