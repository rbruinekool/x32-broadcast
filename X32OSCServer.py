import socket, OSC, re, time, threading
from x32channel import MixerChannel

receive_address = '10.75.255.74', 50006   # Local Address
send_address = '10.75.255.75', 10023  # Remote Address

##########################
# Channel Variables
##########################

Caster1Channel = 9
Caster2Channel = 10

ChannelSubscribeList = [Caster1Channel, Caster2Channel]
SubscribeFactor = 0

CastersDCA = 8
DCASubscribelist = [CastersDCA]

Caster1LedChannel = 7
Caster2LedChannel = 11

C1 = MixerChannel(Caster1Channel)
C2 = MixerChannel(Caster2Channel)
#############################################

class PiException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

##########################
# OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)
c = OSC.OSCClient()
c.setServer(s)

s.addDefaultHandlers()

# define a message-handler function for the server to call.

def X32Renewed(addr, tags, stuff, source):
    dummy = 1

def C1ChannelMute(addr, tags, stuff, source):
    C1.setmutebutton(stuff[0])

def C2ChannelMute(addr, tags, stuff, source):
    C2.setmutebutton(stuff[0])

def C1FaderMute(addr, tags, stuff, source):
    C1.setfaderlevel(stuff[0])

def C2FaderMute(addr, tags, stuff, source):
    C2.setfaderlevel(stuff[0])

def CasterDCAMute(addr, tags, stuff, source):
    C1.setdcamutebutton(stuff[0])
    C2.setdcamutebutton(stuff[0])

def CasterDCAFaderMute(addr, tags, stuff, source):
    C1.setdcafaderlevel(stuff[0])
    C2.setdcafaderlevel(stuff[0])


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

        for i in range(0, len(ChannelSubscribeList)):
            msg.setAddress("/subscribe")
            msg.append("/ch/%02d/mix/on" % ChannelSubscribeList[i])
            msg.append(SubscribeFactor)
            c.sendto(msg, send_address)
            # print "Sent message:", msg
            msg.clear()

            msg.setAddress("/subscribe")
            msg.append("/ch/%02d/mix/fader" % ChannelSubscribeList[i])
            msg.append(SubscribeFactor)
            c.sendto(msg, send_address)
            # print "Sent message:", msg
            msg.clear()

        for j in range(0, len(DCASubscribelist)):

            msg.setAddress("/subscribe")
            msg.append("/dca/%d/on" % DCASubscribelist[j])
            msg.append(SubscribeFactor)
            c.sendto(msg, send_address)
            # print "Sent message:", msg
            msg.clear()

            msg.setAddress("/subscribe")
            msg.append("/dca/%d/fader" % DCASubscribelist[j])
            msg.append(SubscribeFactor)
            c.sendto(msg, send_address)
            # print "Sent message:", msg
            msg.clear()

        time.sleep(8)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"