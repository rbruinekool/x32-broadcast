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

Caster1Channel = 9
Caster2Channel = 10
CasterDCAGroup = 1

C1 = MixerChannel(Caster1Channel, CasterDCAGroup)
C2 = MixerChannel(Caster2Channel, CasterDCAGroup)


NrofChannelInstances = (MixerChannel._ids).next()
print "Number of channel instances created =", NrofChannelInstances

#  These objects below are the subscribe messages that are sent periodically to the X32
C1MessageList = C1.OSCChannelSubscribeMSG()
C2MessageList = C2.OSCChannelSubscribeMSG()

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

def C1ChannelMute(addr, tags, msg, source):
    C1.setmutebutton(msg[0])

def C2ChannelMute(addr, tags, msg, source):
    C2.setmutebutton(msg[0])

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
s.addMsgHandler("/ch/%02d/mix/on" %Caster1Channel , C1ChannelMute)
s.addMsgHandler("/ch/%02d/mix/on" %Caster2Channel , C2ChannelMute)
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
# TODO: Find some way to make a good name or list for 'C1Messagelist' as it is too specific
try:
    while 1:
        for i in range(0, NrofChannelInstances):
            CurrentChannel = ("C%dMessageList[j]" % (i+1))
            for j in range(0, len(C1MessageList)):
                c.sendto(eval(CurrentChannel), send_address)

        time.sleep(8)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"