"""
This script is to be run at the caster desk.
It enables the on-air LEDS and mute/talkback buttons


"""
import logging
import socket
import sys
import time

import requests

try:
    DiagnosticMode = False
    import RPi.GPIO as GPIO
    # import pygame.midi
except ImportError:
    logging.warning("No GPIO or Pygame found - running in diagnostic mode")
    DiagnosticMode = True

from x32broadcast import PhysicalButton, sendondetect, getChannelData, getMuteBoxData, getMyIp

ButtonMode = "GPI"  # Fill in "MIDI" if a MIDI pad is used and "GPI" if GPI's are used

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

# # Checking for an internet connection
# internetActive = False
# while not(internetActive):
#     try:
#         urllib2.urlopen('http://google.com', timeout=1)
#         internetActive = True
#     except urllib2.URLError as err:
#         print "No connection to internet, trying again in 5 seconds"
#         time.sleep(5)

myIp = getMyIp()
fohExist = False

# Getting info about all muteboxes from google sheets
muteBoxData = getMuteBoxData()

hostName = socket.gethostname()
if hostName.split("-")[0] == "mutebox":
    thisPi = hostName
    #thisPi = hostName.split("-")[1]
    print "\nRunning script as " + hostName + " which is currently registered to " + muteBoxData[thisPi][0]
else:
    thisPi = "mutebox-test"
    print "\nDevice hostname is not set to mutebox, running script in testmode as " + thisPi


#############################################################
#     Reading channels and ip adress from the google sheet  #
# Make sure that the correct CSV file is pointed to below   #
#############################################################
try:
    ChannelDict = getChannelData(muteBoxData[thisPi][0])
except KeyError:
    r = requests.post("https://script.google.com/macros/s/AKfycbzB3Tig-5MJp3eLhVInG-IGOx7cwVqvfDBjdByuVfHBKkxMvpw/exec",
                      data={"muteboxName": thisPi, "muteboxIp": myIp})
    raise ValueError("This mutebox is not registered in the online X32ChannelSheets. A report has been emailed to bob.bruinekool@dreamhack.se")


ChannelNames = ChannelDict["Label"]
Channels = ChannelDict["Channel"]
PAChannels = ChannelDict["PAChannel"]
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]
x32ipaddress = ChannelDict["X32 IP"][0]
x32fohipaddress = ChannelDict["X32 FOH IP"][0]
producerHB = ChannelDict["Producer HB Bus"][0]

channelNumbers = {}.fromkeys(ChannelNames, "")
for x in range(0, len(Channels)):
    channelNumbers[ChannelNames[x]] = Channels[x]
    channelNumbers[ChannelNames[x] + "_PA"] = PAChannels[x]

channelNumbers["Producer HB Bus"] = producerHB

x32address = (x32ipaddress, 10023)
x32fohaddress = (x32fohipaddress, 10023)

if x32ipaddress is '':
    print "ip adress field in sheet is empty make sure the ip adress is located in the right spot"

try:
    x32fohipaddress != ''
    fohExist=True
except socket.error:
    print "No FOH ip address available, running only with stream mixer"

# PhysicalButton stuff
leftRedButton = PhysicalButton()
leftBlackButton = PhysicalButton()
rightRedButton = PhysicalButton()
rightBlackButton = PhysicalButton()

leftRedButton.setgpichannel(36)
leftBlackButton.setgpichannel(37)
rightRedButton.setgpichannel(38)
rightBlackButton.setgpichannel(40)

leftRedButton.setx32address(x32address)
leftBlackButton.setx32address(x32address)
rightRedButton.setx32address(x32address)
rightBlackButton.setx32address(x32address)

if fohExist:
    leftRedButton.setx32address(x32address, fohipaddress=x32fohaddress)
    leftBlackButton.setx32address(x32address, fohipaddress=x32fohaddress)
    rightRedButton.setx32address(x32address, fohipaddress=x32fohaddress)
    rightBlackButton.setx32address(x32address, fohipaddress=x32fohaddress)

####################################################################################
#                      Set button osc messages here                                #
####################################################################################

leftRedButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][1])
leftBlackButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][2])
rightRedButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][3])
rightBlackButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][4])

if fohExist:
    leftRedButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][1], tofoh=True)
    leftBlackButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][2], tofoh=True)
    rightRedButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][3], tofoh=True)
    rightBlackButton.setButtonTemplate(channelNumbers, muteBoxData[thisPi][4], tofoh=True)


###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
ChannelReport = PrettyTable()
ChannelReport.add_column("Name", ChannelDict["Label"])
ChannelReport.add_column("Channel", ChannelDict["Channel"])
ChannelReport.add_column("PA Channel", ChannelDict["PAChannel"])
ChannelReport.add_column("DCA Group", ChannelDict["DCA Group"])
ChannelReport.add_column("GPO LED Pin", ChannelDict["LED Channels"])
print "\nOverview of selected channels which are being subscribed to"
print ChannelReport
print "Communicating with x32 at %s:%d" % x32address
if fohExist:
    print "Communicating with x32 FOH at %s:%d" % x32fohaddress

print "\nLeft red button is registered as %s. It has the following registered OSC Paths:" % leftRedButton.description
for i in range(0, len(leftRedButton.mutemsglist)):
    print "\t", leftRedButton.mutemsglist[i]
for i in range(0, len(leftRedButton.fadermsglist)):
    print "\t", leftRedButton.fadermsglist[i]
print "Left black button is registered as %s. It has the following registered OSC Paths:" % leftBlackButton.description
for i in range(0, len(leftBlackButton.mutemsglist)):
    print "\t", leftBlackButton.mutemsglist[i]
for i in range(0, len(leftBlackButton.fadermsglist)):
    print "\t", leftBlackButton.fadermsglist[i]
print "\nRight red button is registered to %s. It has the following registered OSC Paths:" % rightRedButton.description
for i in range(0, len(rightRedButton.mutemsglist)):
    print "\t", rightRedButton.mutemsglist[i]
for i in range(0, len(rightRedButton.fadermsglist)):
    print "\t", rightRedButton.fadermsglist[i]
print "Right black button is registered to %s. It has the following registered OSC Paths:" % rightBlackButton.description
for i in range(0, len(rightBlackButton.mutemsglist)):
    print "\t", rightBlackButton.mutemsglist[i]
for i in range(0, len(rightBlackButton.fadermsglist)):
    print "\t", rightBlackButton.fadermsglist[i]

# Check in with google apps scripts
r = requests.post("https://script.google.com/macros/s/AKfycbzB3Tig-5MJp3eLhVInG-IGOx7cwVqvfDBjdByuVfHBKkxMvpw/exec",
                  data = {"deviceType": "mutebox","deviceName": thisPi, "muteboxIp": myIp})


#################################################################
#                       Diagnostic Mode                         #
#################################################################

if DiagnosticMode is True:
    print "\nDiagnostic Mode started\nPossible buttons to choose from are: "
    print "leftRedButton, leftBlackButton, rightRedButton, rightBlackButton, exit"

while DiagnosticMode is True:
    ChosenButton = raw_input("Please enter the name of the button you wish to simulate a press on: ")
    if ChosenButton is "exit":
        sys.exit()
    ChosenStatus = input("Press (1) or release (0): ")

    buttonmutelist = "%s.mutemsglist" % ChosenButton
    buttonfaderlist = "%s.fadermsglist" % ChosenButton

    try:
        MessageList = eval(buttonmutelist)
        FaderList = eval(buttonfaderlist)
        sendondetect(eval(ChosenButton), pinstatus=ChosenStatus)
    except NameError:
        logging.warning("invalid button name or status")

# if ButtonMode is "MIDI":
#     """
#     MIDI Stuff
#     """
#     verbose = False  # Verbose being true allows you to see what MIDI messages are being registered
#     pygame.init()
#     pygame.midi.init()
#
#     # list all midi devices
#     for x in range(0, pygame.midi.get_count()):
#        print pygame.midi.get_device_info(x)
#
#     # open a specific midi device
#     MIDIdevice = 3
#     inp = pygame.midi.Input(MIDIdevice)
#
#     try:
#         while 1:
#             if inp.poll():
#                 # no way to find number of messages in queue
#                 # so we just specify a high max value
#
#                 MIDIeventlist = inp.read(1000)
#
#                 # 144 is note on, 128 is note off, 176 is a CC
#                 status_byte = MIDIeventlist[0][0][0]
#
#                 # pad 1 - 8 are note numbers 36-44
#                 # encoder 1 - 8 are note numbers 1 through 8
#                 note_number = MIDIeventlist[0][0][1]
#
#                 velocity = MIDIeventlist[0][0][2]
#
#                 # print MIDIeventlist
#                 if verbose:
#                     print "Status Byte= %d" % status_byte
#                     print "Note Number= %d" % note_number
#                     print "Velocity= %d" % velocity
#
#                 # CC Note ON (activate when a MIDI pad is pressed)
#                 if status_byte == 144:
#                     if note_number == 36:  # Mute button for caster 2
#                         rightRedButton.sendoscmessages(1)
#                     elif note_number == 37:  # Talkback button for caster 2
#                         rightBlackButton.sendoscmessages(1)
#                     elif note_number == 39:  # Mute button for caster 1
#                         leftRedButton.sendoscmessages(1)
#                     elif note_number == 38:  # Talkback button for caster 1
#                         leftBlackButton.sendoscmessages(1)
#
#                 # CC Note OFF (activate when a MIDI pad is released)
#                 elif status_byte == 128:
#                     if note_number == 36:
#                         rightRedButton.sendoscmessages(0)
#                     elif note_number == 37:
#                         rightBlackButton.sendoscmessages(0)
#                     elif note_number == 39:
#                         leftRedButton.sendoscmessages(0)
#                     elif note_number == 38:
#                         leftBlackButton.sendoscmessages(0)
#
#     except KeyboardInterrupt:
#         print "\nClosing MIDI Listening Loop."
#         print "Done"

if ButtonMode is "GPI":
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(leftRedButton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(leftBlackButton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(rightRedButton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(rightBlackButton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    Caster1MuteButton = GPIO.input(leftRedButton.gpichannel)
    Caster1TalkButton = GPIO.input(leftBlackButton.gpichannel)
    Caster2MuteButton = GPIO.input(rightRedButton.gpichannel)
    Caster2TalkButton = GPIO.input(rightBlackButton.gpichannel)

    bouncetime = 5

    GPIO.add_event_detect(leftRedButton.gpichannel, GPIO.BOTH)
    GPIO.add_event_detect(leftBlackButton.gpichannel, GPIO.BOTH)
    GPIO.add_event_detect(rightRedButton.gpichannel, GPIO.BOTH)
    GPIO.add_event_detect(rightBlackButton.gpichannel, GPIO.BOTH)

    try:
        while 1:

            # Caster 1 mute
            if GPIO.event_detected(leftRedButton.gpichannel):
                sendondetect(leftRedButton)

            # Caster 1 Talkback
            if GPIO.event_detected(leftBlackButton.gpichannel):
                sendondetect(leftBlackButton)

            # Caster 2 Mute
            if GPIO.event_detected(rightRedButton.gpichannel):
                sendondetect(rightRedButton)

            # Caster 2 Talkback
            if GPIO.event_detected(rightBlackButton.gpichannel):
                sendondetect(rightBlackButton)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop and GPIO ports."
        GPIO.cleanup()
        print "Done"
