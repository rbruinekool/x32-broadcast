import OSC
import threading
import time

from x32channel import MixerChannel

receive_address = '127.0.0.1', 50006   # Local Address
send_address = '127.0.0.1', 10023  # Remote Address

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

C1 = MixerChannel(Caster1Channel)
C2 = MixerChannel(Caster2Channel)

#  These objects below are the subscribe messages that are sent periodically to the X32
SubscribemsgC1 = C1.OSCChannelSubscribeMSG()
SubscribemsgC2 = C2.OSCChannelSubscribeMSG()

ChannelSubscribeList = [Caster1Channel, Caster2Channel]
SubscribeFactor = 0

CastersDCA = 8
DCASubscribelist = [CastersDCA]

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
s.addMsgHandler("/dca/%d/on" %CastersDCA , CasterDCAMute)
s.addMsgHandler("/dca/%d/fader" %CastersDCA , CasterDCAFaderMute)



# just checking which handlers we have added
print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
    print addr

# Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread(target=s.serve_forever)
st.start()


# Loop while threads are running.
try:
    while 1:
        msg = OSC.OSCMessage()

        c.sendto(SubscribemsgC1, send_address)
        c.sendto(SubscribemsgC2, send_address)

        # for i in range(0, len(ChannelSubscribeList)):
        #     msg.setAddress("/subscribe")
        #     msg.append("/ch/%02d/mix/fader" % ChannelSubscribeList[i])
        #     msg.append(SubscribeFactor)
        #     c.sendto(msg, send_address)
        #     msg.clear()
        #
        # for j in range(0, len(DCASubscribelist)):
        #
        #     msg.setAddress("/subscribe")
        #     msg.append("/dca/%d/on" % DCASubscribelist[j])
        #     msg.append(SubscribeFactor)
        #     c.sendto(msg, send_address)
        #     msg.clear()
        #
        #     msg.setAddress("/subscribe")
        #     msg.append("/dca/%d/fader" % DCASubscribelist[j])
        #     msg.append(SubscribeFactor)
        #     c.sendto(msg, send_address)
        #     msg.clear()

        time.sleep(8)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"