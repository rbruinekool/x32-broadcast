from itertools import count
import OSC
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    global GPIOActive
    GPIOActive = True
    print "GPIO set to Board-Mode"
except:
    print "WARNING: No GPIO functionality found on this device"
    global GPIOActive
    GPIOActive = False


class MixerChannel(object):
    _ids = count(0)

    def __init__(self, channelnumber, dcagroup = None, gpo_channel = None,
                 x32ipaddress = "127.0.0.1"):
        self.id = self._ids.next()  # id number to keep track of the amount of instances made in a script

        self.mute_button = None
        self.mute_fader = None
        self.mute_dcafader = None
        self.mute_dcabutton = None
        self.mutestatus = None
        self.channelnumber = channelnumber
        self.dcagroup = dcagroup
        self.mutepath = "/ch/%02d/mix/on" % channelnumber
        self.faderpath = "/ch/%02d/mix/fader" % channelnumber
        self.channelname = "No channel name assigned, use self.channelname"
        if type(self.dcagroup) is int:
            self.dcamutepath = "/dca/%d/on" % dcagroup
            self.dcafaderpath = "/dca/%d/fader" % dcagroup

        # connecting to x32 and creating an OSCMessage instance to prevent
        # having to do this repeatedly inside a loop
        self.x32address = (x32ipaddress, 10023)
        self.x32 = OSC.OSCClient()
        self.x32.connect(self.x32address)
        self.msg = OSC.OSCMessage()

        # Sets how fast the X32 will send subscribe messages (0 is fastest)
        self.subscribefactor = 0

        # GPIO Related attributes are assigned here
        self.gpo_channel = gpo_channel
        if GPIOActive and self.gpo_channel is not None:
            GPIO.setup(self.gpo_channel, GPIO.OUT)

    #########################################################################
    # Methods that involve registering the actual state of M/X32 channels   #
    # into the MixerChannel instances are here                              #
    #########################################################################

    def setfaderlevel(self, addr, tags, msg, source):
        fadermsg = msg[0]
        self.faderlevel = fadermsg

        # Set the mute_button property if the channel fader is below 10%
        if fadermsg <= 0.1:
            self.mute_fader = True
        else:
            self.mute_fader = False

        self.check_mute_status()

    def setmutebutton(self, addr, tags, msg, source):
        buttonmsg = msg[0]
        self.channel_on = buttonmsg

        # Set the mute_button property True if the channel is muted by the mute button
        if buttonmsg == 0:
            self.mute_button = True
        else:
            self.mute_button = False

        self.check_mute_status()

    def setdcafaderlevel(self, msg):
        dcafadermsg = msg[0]
        self.DCAfader = dcafadermsg

        # Set the mute_dcafader property to True if the DCA fader is below 10%
        if dcafadermsg <= 0.1:
            self.mute_dcafader = True
        else:
            self.mute_dcafader = False

        self.check_mute_status()

    def setdcamutebutton(self, msg):
        dcabuttonmsg = msg[0]
        self.dcaon = dcabuttonmsg

        if dcabuttonmsg == 0:
            self.mute_dcabutton = True
        else:
            self.mute_dcabutton = False

        self.check_mute_status()

    def check_mute_status(self):

        mutestatus = self.mute_button or self.mute_fader or self.mute_dcabutton or self.mute_dcafader

        # Activate a change in GPIO only if the mutestatus has actually changed
        if self.mutestatus != mutestatus:
            if GPIOActive:
                GPIO.output(self.gpo_channel, not(mutestatus))
            #print "Set mutestatus to", mutestatus, "for", self.channelname , "(channel", self.channelnumber,")"

        self.mutestatus = mutestatus

        return self.mutestatus

    def OSCChannelSubscribeMSG(self):

        # Format the OSC message to subscribe to the channel mute button
        mutemsg = OSC.OSCMessage()
        mutemsg.setAddress("/subscribe")
        mutemsg.append("/ch/%02d/mix/on" % self.channelnumber)
        mutemsg.append(self.subscribefactor)

        # Format the OSC message to subscribe to the channel fader
        fadermsg = OSC.OSCMessage()
        fadermsg.setAddress("/subscribe")
        fadermsg.append("/ch/%02d/mix/fader" % self.channelnumber)
        fadermsg.append(self.subscribefactor)

        # The DCA group is an optional integer property, so we only want to formate these osc messages if it was
        # actually assigned in creation of the instance
        if type(self.dcagroup) is int:
            # Format the OSC message to subscribe to the DCA mute
            dcamutemsg = OSC.OSCMessage()
            dcamutemsg.setAddress("/subscribe")
            dcamutemsg.append("/dca/%d/on" % self.dcagroup)
            dcamutemsg.append(self.subscribefactor)

            # Format the OSC message to subscribe to the DCA fader
            dcafadermsg = OSC.OSCMessage()
            dcafadermsg.setAddress("/subscribe")
            dcafadermsg.append("/dca/%d/fader" % self.dcagroup)
            dcafadermsg.append(self.subscribefactor)

            return [mutemsg, fadermsg, dcamutemsg, dcafadermsg]
        else:
            #TODO change this print into an actual proper way of reporting an exception
            print "Warning: non integer DCA group has been assigned"

            return [mutemsg, fadermsg]

    #########################################################################
    # Methods that involve setting the state of M/X32 channels go here      #
    # (e.g. methods that use OSC to mute a channel on an actual X32 when    #
    #########################################################################

    def set_mute(self, mute):
        self.msg.clear(self.mutepath)
        self.msg.append(mute)
        self.send_osc()

    def set_fader(self, fader):
        self.msg.clear(self.faderpath)
        self.msg.append(fader)
        self.send_osc()

    def send_osc(self):
        self.x32.send(self.msg)

class DCAGroup(object):

    def __init__(self):
        self.channellist = [None]
        self.channelindex = [None]

    def addchannel(self, channel):
        if type(channel) is int:
            if self.channellist[0] is None:
                self.channellist[0] = channel
            else:
                self.channellist.append(channel)
        if type(channel) is list:
            if self.channellist[0] is None:
                self.channellist = channel
            else:
                self.channellist = self.channellist + channel


#For easy programming of the osc messages all the messages will be compiled with these functions
#to import them use the import function (e.g. 'from X32OSCFunctions import MuteChannel2Bus')

# Set up the osc adress
import OSC

def SendOscList(path,message,ipadress,port):
    """
    This function sends the value 'message' to the OSC path 'path' at the
    ip adress 'ipadress' to port 'port'.
    Path and Message can be lists of indefinite length. The function will
    send an osc message for every index of the lists. Do note that the path
    and message lists must be the same length in this case

    Path must be a string (e.g. '/ch/01/mix/on'
    message can be an integer, floating point or string
    ipadress must be a string (e.g. '10.75.255.74)
    port must be an integer (e.g. 10023)
    """

    if len(path) != len(message):
        print('''Error :Path and Message are not the same length
                (the function will still send osc messages, but only for the
                 length of the path list''')

    send_adress = ipadress , port

    c = OSC.OSCClient()
    c.connect(send_adress)
    msg = OSC.OSCMessage()

##    msg.setAddress(path)
##    msg.append(message)
##    c.send(msg)

    for i in range(len(path)):
        msg.setAddress(path[i])
        msg.append(message[i])
        c.send(msg)
        del msg[-1]
    return


#This function mutes or unmutes a variable channel to a variable bus
def MuteChannel2Bus(ChannelNumber,BusNumber,state,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function mutes or unmutes a variable channel to a variable bus

    ChannelNumber - This is the channel that you want to be (un)muted [1..32]
    BusNumber - This is the destination bus that you want the channel to be (un)muted to [1..16]
    Fill in ChannelNumber and Busnumber as integer values without padded 0's (e.g 1 or 14)

    state - a list of mutes or unmutes, choose 1 for unmuting and 0 for muting
    """
    NrOfMessages = len(ChannelNumber)
    OSCPath = [None]*NrOfMessages

    for i in range(NrOfMessages):
        OSCPath[i] = "/ch/%02d/mix/%02d/on" %(ChannelNumber[i],BusNumber)

    SendOscList(OSCPath,state,adress,port)

    return

def SetLevel2Bus(ChannelList,BusNumber,FaderValue,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function changes the send level of a list of channels to a variable bus

    ChannelList - This is the channel list of integer values that you want to change send levels for [1..32]
    BusNumber - This is the destination bus that you want the channels to be changed for [1..16]
    Fill in ChannelNumber and Busnumber as integer values without padded 0's (e.g 1 or 14)

    state - choose 1 for unmuting and 0 for muting
    """
    NrOfMessages = len(ChannelList)
    OSCPath = [None]*NrOfMessages
    value = [None]*NrOfMessages

    for i in range(NrOfMessages):
        OSCPath[i] = "/ch/%02d/mix/%02d/level" %(ChannelList[i],BusNumber)
        value[i] = FaderValue

    SendOscList(OSCPath,value,adress,port)

    return

def SetBusLevel(BusNumber,FaderValue,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function changes the send level of a mixbus

    BusNumber - This is list of busnumbers you want to change the level for [1..16]
    Fill in Busnumber as integer values without padded 0's (e.g 1 or 14)

    """
    NrOfMessages = len(BusNumber)
    OSCPath = [None]*NrOfMessages
    value = [None]*NrOfMessages

    for i in range(NrOfMessages):
        OSCPath[i] = "/bus/%02d/mix/fader" %(BusNumber[i])
        value[i] = FaderValue

    SendOscList(OSCPath,value,adress,port)

    return

def MuteBus(BusNumber,state,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function mutes or unmutes a mixbus

    BusNumber - This is list of busnumbers you want to mute/unmute [1..16]
    Fill in Busnumber as integer values without padded 0's (e.g 1 or 14)
    Fill in state as a list of integer values (0 is mute, 1 is unmute)

    """
    NrOfMessages = len(BusNumber)
    OSCPath = [None]*NrOfMessages

    for i in range(NrOfMessages):
        OSCPath[i] = "/bus/%02d/mix/on" %(BusNumber[i])

    SendOscList(OSCPath,state,adress,port)

    return

def Talk2Busses(BusList,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function routes the talkback input to the list of busses given in BusList

    BusList - This is list of busnumbers you want to route Talkback to [1..16]
    Fill in Busnumber as a list of integer values without padded 0's (e.g 1 or 14)

    """
    NrOfBusses = len(BusList)
    destmap = 0

    OSCPath = ["/config/talk/A/destmap"]
    for i in range(NrOfBusses):
        destmap = destmap + 2**(BusList[i]-1)

    destmap = [destmap]
    SendOscList(OSCPath,destmap,adress,port)

    return

def ConvBusNumber2DestMap(BusList):
    NrOfBusses = len(BusList)
    destmap = 0

    for i in range(NrOfBusses):
        destmap = destmap + 2**(BusList[i]-1)

    return destmap

def SendDestMap(DestMap,adress,port):
    """
    """

    OSCPath = ["/config/talk/A/destmap"]

    SendOscList(OSCPath,[DestMap],adress,port)

    return

def SetTalkLevelA(FaderValue,adress,port):
    """
    This function is valid for the X32 or the M32 sound desk
    This function sets the level of talkback A

    FaderValue should be entered as a float
    adress is the ip adress where the osc message is sent
    port is the port number at which osc message will be directed

    """
    OSCPath = ["/config/talk/A/level"]
    SendOscList(OSCPath,[FaderValue],adress,port)

    return

def SendOscMessage(path, message, ipadress, port):

    send_adress = ipadress , port

    c = OSC.OSCClient()
    c.connect(send_adress)
    msg = OSC.OSCMessage()

    msg.setAddress(path)
    msg.append(message)
    c.send(msg)

    return
