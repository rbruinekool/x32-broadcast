import csv
import os
import socket
import ssl
import time
import urllib2

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

from itertools import count

import OSC

global GPIOActive
GPIOActive = False

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIOActive = True
    #print "GPIO set to Board-Mode"
except:
    print "WARNING: No GPIO functionality found on this device\n"


class MixerChannel(object):
    _ids = count(0)

    def __init__(self, channelnumber):
        self.id = self._ids.next()  # id number to keep track of the amount of instances made in a script

        self.mute_button = None
        self.mute_fader = None
        self.mute_dcafader = False
        self.mute_dcabutton = False
        self.mutestatus = None
        self.channelnumber = channelnumber
        self.dcagroup = None
        self.dcamutepath = None
        self.dcafaderpath = None
        self.mutepath = "/ch/%02d/mix/on" % channelnumber
        self.faderpath = "/ch/%02d/mix/fader" % channelnumber
        self.channelname = "No channel name assigned, use self.channelname"

        # Creating an OSCMessage instance to prevent
        # having to do this repeatedly inside a loop
        self.msg = OSC.OSCMessage()

        # Sets how fast the X32 will send subscribe messages (0 is fastest)
        self.subscribefactor = 0

        # GPIO Related attributes are assigned here
        self.gpo_channel = ''  # an empty string '' is needed to filter the instances that have no GPIO functionality

    #########################################################################
    # Methods that initialize the object in certain ways go here            #
    #########################################################################

    def setdcagroup(self, dcagroup):
        """
        Sets the dcagroup for a MixerChannel instance
        """
        self.dcagroup = dcagroup
        if type(self.dcagroup) is int:
            self.dcamutepath = "/dca/%d/on" % dcagroup
            self.dcafaderpath = "/dca/%d/fader" % dcagroup

    def setledoutput(self, gpo_channel):
        self.gpo_channel = gpo_channel
        try:
            GPIO.setup(self.gpo_channel, GPIO.OUT)
            print "GPIO %d for channel %d set to OUT mode" % (self.gpo_channel, self.channelnumber)
        except NameError:
            print "Warning: No GPIO can be assigned because RPi GPIO is not available"
        except ValueError:
            pass

    def setx32address(self, x32address, **kwargs):
        """
        Connects a MixerChannel instance to an X32 in the network, this must be done if the MixerChannel is to send
        messags to an X32 (e.g. setting mutes using the below set_mute method)
        :param x32address: The network adress of the x32 as a tuple, e.g. ('10.75.10.75', 10023)
        :return: Nothing
        """
        self.x32address = x32address
        self.x32 = OSC.OSCClient()
        self.x32.connect(self.x32address)

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
            if GPIOActive and type(self.gpo_channel) is int:
                GPIO.output(self.gpo_channel, not(mutestatus))
            # print "Set mutestatus to", mutestatus, "for", self.channelname , "(channel %d)" % self.channelnumber

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

    def open_communications(self, mixbus):
        self.talkpath = "/ch/%02d/mix/%02d/on" % (self.channelnumber, mixbus)
        self.msg.clear(self.talkpath)
        self.msg.append(1)
        self.send_osc()

    def close_communications(self, mixbus):
        self.talkpath = "/ch/%02d/mix/%02d/on" % (self.channelnumber, mixbus)
        self.msg.clear(self.talkpath)
        self.msg.append(0)
        self.send_osc()

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

class PhysicalButton(object):

    def __init__(self):
        self.gpichannel = ''
        self.MIDIcc = ''
        self.mutemsglist = [] #This list will be sent to X32 production.
        self.mutemsglistPa = [] #This list will be sent to X32 FOH if available
        self.mutemsgmodelist = []
        self.talk2buslist = []
        self.talk2destmap = None
        self.fadermsglist = []
        self.oscmsg = OSC.OSCMessage()
        self.description = ""

    def setx32address(self, x32address, **kwargs):
        """
        Connects a MixerChannel instance to an X32 in the network, this must be done if the MixerChannel is to send
        messags to an X32 (e.g. setting mutes using the below set_mute method)
        :param x32address: The network adress of the x32 as a tuple, e.g. ('10.75.10.75', 10023)
        :return: Nothing
        """

        try:
            x32fohaddress = kwargs['fohipaddress']
        except KeyError:
            x32fohaddress = ''

        self.x32address = x32address
        self.x32fohaddress = x32fohaddress
        self.x32 = OSC.OSCClient()
        self.x32.connect(self.x32address)
        #self.x32.connect(self.x32fohaddress)

    def setgpichannel(self, gpichannel):
        self.gpichannel = gpichannel

    def setMIDIcc(self, MIDIcc):
        self.MIDIcc = MIDIcc

    def addmutemsg(self, sourcechannel, mutemode='mute_on_press', tofoh=False, **kwargs):
        """
        Adds an OSC mute message to the list that will be sent to the production X32 when the button is pressed
        :param sourcechannel: The channel that will be the main focus of the mute message
        :param mutemode: decides whether the channel is muted on press ('mute_on_press') or on release ("mute_on_release")
        :param kwargs: a destination bus can be added to change the mute message to a bus mute
        """
        try:
            destbus = kwargs['destinationbus']
        except KeyError:
            destbus = ''

        if 0 < sourcechannel < 33:  #Checking if the channel is actually in the legal range of 1-32
            if destbus is '':
                mutemsg = "/ch/%02d/mix/on" % sourcechannel
            else:
                mutemsg = "/ch/%02d/mix/%02d/on" % (sourcechannel, destbus)
        else:
            return

        if tofoh:
            self.mutemsglistPa.append(mutemsg)
        else:
            self.mutemsglist.append(mutemsg)

        if mutemode is 'mute_on_press':
            self.mutemsgmodelist.append(0)
        elif mutemode is 'mute_on_release':
            self.mutemsgmodelist.append(1)
        else:
            raise NameError("mutemode must be either 'mute_on_press' or 'mute_on_release'")

    def addfadermsg(self, channelnumber, busnumber=''):

        try:
            for i in range(0, len(channelnumber)):
                if type(channelnumber[i]) is int:
                    if busnumber is '':
                        self.fadermsglist.append("/ch/%02d/mix/fader" % channelnumber[i])
                    else:
                        self.fadermsglist.append("/ch/%02d/mix/%02d/level" % (channelnumber[i], busnumber))
                elif channelnumber[i] is '':
                    pass
                else:
                    print "illegal busnumber entered in CSV. Use only an integer or an empty field"
        except TypeError:
            if type(channelnumber) is int:
                if busnumber is '':
                    self.fadermsglist.append("/ch/%02d/mix/fader" % channelnumber)
                else:
                    self.fadermsglist.append("/ch/%02d/mix/%02d/level" % (channelnumber, busnumber))
            elif channelnumber is '':
                pass
            else:
                print "illegal busnumber entered in CSV. Use only an integer or an empty field"

    def addbusfadermsg(self, busnumber):
        try:
            for i in range(0, len(busnumber)):
                if type(busnumber[i]) is int:
                    fadermsg = "/bus/%02d/mix/fader" % (busnumber[i])
                    self.fadermsglist.append(fadermsg)
                elif busnumber is '':
                    pass
                else:
                    print "illegal busnumber entered in CSV. Use only an integer or an empty field"
        except TypeError:
            if type(busnumber) is int:
                fadermsg = "/bus/%02d/mix/fader" % (busnumber)
                self.fadermsglist.append(fadermsg)
            elif busnumber is '':
                pass
            else:
                print "illegal busnumber entered in CSV. Use only an integer or an empty field"

    def addtalk2bus(self, busnumber):
        if self.talk2destmap is None:
            self.talk2destmap = 0
        try:
            busnumber = list(set(busnumber)) #This statement prevents adding busses twice
            for i in range(0, len(busnumber)):
                if type(busnumber[i]) is int and 0 < busnumber[i] < 17:  # To prevent adding non integer busses
                    self.talk2buslist.append(busnumber[i])
                    self.talk2destmap += 2 ** (busnumber[i] - 1)
                elif busnumber[i] is '':
                    pass
                else:
                    raise ValueError("Busnumbers must be given in the range of 1-16.\n "
                                     "Leave the field blank in the x32ChannelSheet.csv if you do not want to use the bus")
                    #print "Warning, non integer busnumbers are being used. Use only integer values in the range of 1-16 or empty fields"

        except TypeError:
            if type(busnumber) is int and 0 < busnumber < 17:  # To prevent adding non integer busses
                self.talk2buslist.append(busnumber)
                self.talk2destmap = self.talk2destmap + 2 ** (busnumber - 1)
            elif busnumber is '':
                pass
            else:
                raise ValueError("Busnumbers must be given in the range of 1-16.\n "
                                 "Leave the field blank in the x32ChannelSheet.csv if you do not want to use the bus")

    def removetalk2bus(self, busnumber):
        self.talk2destmap = self.talk2destmap - 2 ** (busnumber - 1)

    def setButtonTemplate(self, channelNumbers, buttonTemplate, tofoh=False, **kwargs):

        if buttonTemplate:
            splitTemplate = buttonTemplate.split(":")

            if len(splitTemplate) == 2:
                channelName = buttonTemplate.split(":")[0]
                actionType = buttonTemplate.split(":")[1]
                self.description = channelName + " " + actionType
            else:
                raise ValueError("The button template (e.g. Host:mute) is not being provided in the correct format")
        else:
            return

        if actionType == "mute":
            self.addmutemsg(channelNumbers[channelName])
            self.addmutemsg(channelNumbers[channelName + "_PA"], tofoh=True)
        elif actionType == "talk":
            self.addfadermsg(channelNumbers[channelName])
            self.addmutemsg(channelNumbers[channelName], "mute_on_release", destinationbus=channelNumbers["Producer HB Bus"])
            self.addmutemsg(channelNumbers[channelName + "_PA"], tofoh=True)

    def sendoscmessages(self, buttonstate):

        try:
                # Mutemessages will be sent here
            mutestatus = []
            if buttonstate is 1:
                mutestatus = self.mutemsgmodelist
            elif buttonstate is 0:
                mutestatus = [not i for i in self.mutemsgmodelist]

            for i in range(0, len(self.mutemsglist)):
                self.oscmsg.clear()
                self.oscmsg.setAddress(self.mutemsglist[i])
                self.oscmsg.append(int(mutestatus[i]))
                self.x32.send(self.oscmsg)

            for i in range(0, len(self.mutemsglistPa)):
                self.oscmsg.clear()
                self.oscmsg.setAddress(self.mutemsglistPa[i])
                self.oscmsg.append(int(mutestatus[i]))
                self.x32.send(self.oscmsg)

            # Talk2bus messages will be sent here
            if self.talk2destmap:
                if buttonstate is 1:
                    self.oscmsg.clear()
                    self.oscmsg.setAddress("/config/talk/A/destmap")
                    self.oscmsg.append(self.talk2destmap)
                    self.x32.send(self.oscmsg)
                elif buttonstate is 0:
                    self.oscmsg.clear()
                    self.oscmsg.setAddress("/config/talk/A/destmap")
                    self.oscmsg.append(0)
                    self.x32.send(self.oscmsg)
        except OSC.OSCClientError:
            print ("Couldnt send mute message because the network connection is lost, waiting for network")

    def sendfaderoscmessages(self, encoderMIDIvalue):
        try:
            oscvalue = float(encoderMIDIvalue) / 127.0  # Convert 127 step msg into msg from 0 to 1
            for i in range(0, len(self.fadermsglist)):
                self.oscmsg.clear()
                self.oscmsg.setAddress(self.fadermsglist[i])
                self.oscmsg.append(oscvalue)
                self.x32.send(self.oscmsg)
        except OSC.OSCClientError:
            print ("Couldnt send fader message because the network connection is lost, waiting for network")


#########################################################################
#                   Random other functions go here                      #
#########################################################################

def read_variables_from_csv(filename):
    """
    This functions reads a CSV file that contains the channel labels, numbers, DCA group assignments and LED channels
    :param filename: a string that points to the CSV file that is to be read, e.g. "X32CSGO.csv"
    :return: The function returns a channel dictionary like it is used in the X32OSCServer
    """
    ChannelDict = {}
    with open(filename, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            key = row[0]
            if key in ChannelDict:
                pass
            ChannelDict[key] = row[1:]

    ChannelDictKeyList = ChannelDict.keys()
    for i in range(0, len(ChannelDictKeyList)):
        for j in range(0, len(ChannelDict["Label"])):
            try:
                ChannelDict[ChannelDictKeyList[i]][j] = int(ChannelDict[ChannelDictKeyList[i]][j])
            except ValueError:
                pass
    return ChannelDict

# Generic sending function which is called in the loop below:
def sendondetect(button, **kwargs):
    time.sleep(0.02)
    try:
        pinstatus = kwargs['pinstatus']
    except KeyError:
        pinstatus = int(not (GPIO.input(button.gpichannel)))
    button.sendoscmessages(pinstatus)
    if pinstatus == 1:
        button.sendfaderoscmessages(0.0)
    else:
        button.sendfaderoscmessages(98)
    time.sleep(0.02)
    print "sent messages for %s. Pin state = %d " % (button.description, pinstatus)

def callbackdata(data):
    return data

def getChannelData(userName):
    sheetId = "1xCvYdmH13sQg41dOZfgAiYZLI1JzmML7IhTW7QzNktg"
    url = "http://spreadsheets.google.com/tq?tqx=responseHandler:callbackdata&key=" + sheetId + "&sheet=" + userName

    rawResponse = urllib2.urlopen(url).read()
    response = rawResponse.splitlines()[1].replace(';','').replace('null','{}')
    response = response.replace('"v":{}', '') #This one is put on a separate row because it might be a bit risky
    responseDict = eval(response)
    allRows = responseDict["table"]['rows'];

    currentRow = []
    channelDict = {}

    for i in range(0, len(allRows)):
        for j in range(1, len(allRows[i]['c'])):
            if len(allRows[i]['c'][j].values()) > 0:
                if type(allRows[i]['c'][j].values()[0]) == str:
                    currentRow.append(allRows[i]['c'][j].values()[0])
                    try:
                        currentRow[j - 1] = int(currentRow[j - 1])
                    except ValueError:
                        pass
            else:
                currentRow.append("")

        channelDict[allRows[i]['c'][0]['v']] = currentRow
        currentRow = []

    return channelDict


def getMuteBoxData():
    sheetId = "1xCvYdmH13sQg41dOZfgAiYZLI1JzmML7IhTW7QzNktg"
    url = "http://spreadsheets.google.com/tq?tqx=responseHandler:callbackdata&key=" + sheetId + "&sheet=muteboxes"

    rawResponse = urllib2.urlopen(url).read()
    response = rawResponse.splitlines()[1].replace(';','').replace('null','{}')
    response = response.replace('"v":{}', '') #This one is put on a separate row because it might be a bit risky
    responseDict = eval(response)
    allRows = responseDict["table"]['rows'];

    currentRow = []
    channelDict = {}

    for i in range(0, len(allRows)):
        for j in range(1, len(allRows[i]['c'])):
            if len(allRows[i]['c'][j].values()) > 0:
                if type(allRows[i]['c'][j].values()[0]) == str:
                    currentRow.append(allRows[i]['c'][j].values()[0])
                    try:
                        currentRow[j - 1] = int(currentRow[j - 1])
                    except ValueError:
                        pass
            else:
                currentRow.append("")

        channelDict[allRows[i]['c'][0]['v']] = currentRow
        currentRow = []

    return channelDict

def getMyIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    myIp = s.getsockname()[0]
    s.close()
    return myIp


