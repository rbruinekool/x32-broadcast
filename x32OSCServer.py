import threading
import time

try:
    import RPi.GPIO as GPIO
    GPIOActive = True
except ImportError:
    GPIOActive = False
    print "RPi.GPIO module not installed"

try:
    import OSC
except ImportError:
    print "pyOSC is not installed"

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

try:
    from x32broadcast import MixerChannel, DCAGroup, read_variables_from_csv
except ImportError:
    print "x32broadcast module is missing or not installed"

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

ChannelDict = read_variables_from_csv("x32CSGO.csv")

receive_address = ChannelDict["LOCAL IP"][0], 50006   # Local Address
send_address = ChannelDict["X32 IP"][0], 10023  # Remote Address

DCAObjectList = [None] * 8  # Preallocation
for i in range(0, 8):
    DCAObjectList[i] = DCAGroup()

ChannelNames = ChannelDict["Label"]
ChannelLabels = ChannelDict["Channel"]
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]

# Generating a list of indexes that point to which channel falls under each DCA. This list is formatted
# as follows: dcaindexlist[dca group number][indexes in ChannelDict which point to channel numbers that
# are a part of this dca group number]
dcaindexlist = [[], [], [], [], [], [], [], []]
for index, dca_group in enumerate(DCALabels):
    for dca_number in range(0, 8):
        if dca_group == dca_number + 1:
            dcaindexlist[dca_number].append(index)

for i in range(0, 8):
    if dcaindexlist[i]:
        DCAObjectList[i].channelindex = dcaindexlist[i]

ObjectList = [None] * len(ChannelLabels)
for i in range(0, len(ChannelLabels)):
    ObjectList[i] = MixerChannel(ChannelLabels[i])
    ObjectList[i].channelname = ChannelNames[i]
    ObjectList[i].setdcagroup(DCALabels[i])
    ObjectList[i].setledoutput(LEDChannels[i])
    ObjectList[i].setx32address(send_address)

NrofChannelInstances = MixerChannel._ids.next()
print "\nNumber of channel instances created =", NrofChannelInstances

#  These objects below are the subscribe messages that are sent periodically to the X32
OSCMessagelist = [None] * NrofChannelInstances  # Pre-allocation
for i in range(0, NrofChannelInstances):
    OSCMessagelist[i] = ObjectList[i].OSCChannelSubscribeMSG()

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

# adding OSC handles which make the server perform certain callback functions
# These handles are for all the channel faders and mutes that are defined in Channeldict
for i in range(0, NrofChannelInstances):
    CurrentInstance = ObjectList[i]
    s.addMsgHandler(CurrentInstance.mutepath, CurrentInstance.setmutebutton)
    s.addMsgHandler(CurrentInstance.faderpath, CurrentInstance.setfaderlevel)

# These handles are for all DCA faders and mutes (all are added regardless if they are in use or not)
for i in range(1, 9):
    s.addMsgHandler("/dca/%d/on" % i, DCAMute)
    s.addMsgHandler("/dca/%d/fader" % i, DCAFader)

# just checking which handlers we have addedD
print "\nRegistered Callback-functions are :"
for addr in sorted(s.getOSCAddressSpace()):
    print addr

###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
ChannelReport = PrettyTable()
ChannelReport.add_column("Name", ChannelDict["Label"])
ChannelReport.add_column("Channel", ChannelDict["Channel"])
ChannelReport.add_column("DCA Group", ChannelDict["DCA Group"])
ChannelReport.add_column("GPIO Channel", ChannelDict["LED Channels"])

print "\nOverview of selected channels which are being subscribed to"
print ChannelReport
print "Communicating with x32 at %s:%d" % (send_address[0], send_address[1])

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
        time.sleep(5)

except KeyboardInterrupt:
    print "\nClosing OSCServer."
    if GPIOActive:
        GPIO.cleanup()  # clears the used GPIO channels
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"
