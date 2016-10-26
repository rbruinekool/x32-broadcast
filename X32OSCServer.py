import threading
import time

import OSC
from prettytable import PrettyTable

from x32broadcast import MixerChannel, DCAGroup

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

SubscribeFactor = 0

ChannelDict = {
    "label": ["Caster 1", "Caster 2", "Host"],
    "Channel": ["5", "6", "1"],
    "DCA Group": ["2", "2", "1"],
}
DCA1 = DCAGroup()
DCA2 = DCAGroup()

DCAObjectList = [DCA1, DCA2]
DCA1.channelindex = [2]
DCA2.channelindex = [0, 1]

ChannelLabels = ChannelDict["Channel"]
DCALabels = ChannelDict["DCA Group"]

ObjectList = [None] * len(ChannelLabels)
for i in range(0, len(ChannelLabels)):
    ObjectList[i] = MixerChannel(eval(ChannelLabels[i]), eval(DCALabels[i]))
del i

NrofChannelInstances = MixerChannel._ids.next()
print "Number of channel instances created =", NrofChannelInstances

#  These objects below are the subscribe messages that are sent periodically to the X32
OSCMessagelist = [None] * NrofChannelInstances  # Pre-allocation
for i in range(0, NrofChannelInstances):
    OSCMessagelist[i] = ObjectList[i].OSCChannelSubscribeMSG()
del i

###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
ChannelReport = PrettyTable()
ChannelReport.add_column("Name", ChannelDict["label"])
ChannelReport.add_column("Channel #", ChannelDict["Channel"])
ChannelReport.add_column("DCA Group", ChannelDict["DCA Group"])

print "Reporting to subscribe and receive OSC messages from the following channels:"
print ChannelReport
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

def DCAMute(addr, tags, msg, source):
        CurrentDCA = DCAObjectList[eval(addr[5])-1]
        for j in range(0, len(CurrentDCA.channelindex)):
            CurrentChannel = ObjectList[CurrentDCA.channelindex[j]]
            CurrentChannel.setdcamutebutton(msg)

def DCAFader(addr, tags, msg, source):
    CurrentDCA = DCAObjectList[eval(addr[5]) - 1]
    for j in range(0, len(CurrentDCA.channelindex)):
        CurrentChannel = ObjectList[CurrentDCA.channelindex[j]]
        CurrentChannel.setdcafaderlevel(msg)

# adding OSC handles

for i in range(0, NrofChannelInstances):
    CurrentInstance = ObjectList[i]
    s.addMsgHandler(CurrentInstance.mutepath, CurrentInstance.setmutebutton)
    s.addMsgHandler(CurrentInstance.faderpath, CurrentInstance.setfaderlevel)
    # s.addMsgHandler(CurrentInstance.dcamutepath, CurrentInstance.setdcamutebutton)
    # s.addMsgHandler(CurrentInstance.dcafaderpath, CurrentInstance.setdcafaderlevel)

s.addMsgHandler("/dca/2/on", DCAMute)
s.addMsgHandler("/dca/2/fader", DCAFader)
s.addMsgHandler("/dca/1/on", DCAMute)
s.addMsgHandler("/dca/1/fader",DCAFader)


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
# will subscribe. For example the string parts of OSCMessageList could look like this:
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