"""
This script is to be run at the caster desk.
It enables the mute/talkback buttons


"""
import logging
import sys
import time

try:
    DiagnosticMode = False
    import RPi.GPIO as GPIO
    import pygame.midi
except ImportError:
    logging.warning("No GPIO or Pygame found - running in diagnostic mode")
    DiagnosticMode = True

from x32broadcast import PhysicalButton, read_variables_from_csv, sendondetect, getChannelData

ButtonMode = "GPI" # Fill in "MIDI" if a MIDI pad is used and "GPI" if GPI's are used

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

###########################################################
#     Reading channels and ip adress from a CSV file      #
# Make sure that the correct CSV file is pointed to below #
###########################################################

userInputPhase = True
while userInputPhase:
    dataMode = raw_input("Type 'local' or 'l' if you want me to read the x32ChannelSheet.csv\n"
                         "Type 'online' or 'o' if you want me to read from the google spreadsheet\n")
    if dataMode == 'local' or dataMode == 'l':
        ChannelDict = read_variables_from_csv("x32ChannelSheet.csv")
        userInputPhase = False
    elif dataMode == 'online' or dataMode == 'o':
        userName = raw_input("please input your username in lower case letters.\n")
        ChannelDict = getChannelData(userName)
        userInputPhase = False
    else:
        print "%s is not a recognized command" % dataMode

ChannelNames = ChannelDict["Label"]
ChannelLabels = ChannelDict["Channel"]
PALabels = ChannelDict["PAChannel"]
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]
x32ipaddress = ChannelDict["X32 IP"][0]
producerHB = ChannelDict["Producer HB Bus"][0]

x32address = (x32ipaddress, 10023)

if x32ipaddress is '':
    print "ip adress field in csv is empty make sure the ip adress is located in the right spot"
try:
    host_index = ChannelNames.index("Host")
    caster1_index = ChannelNames.index("Caster 1")
    caster2_index = ChannelNames.index("Caster 2")
except ValueError:
    print "The channelnames are not in the correct format. Use Host, Caster 1 and Caster 2"

#### PhysicalButton stuff

hostchannel = ChannelLabels[host_index]
caster1channel = ChannelLabels[caster1_index]
caster2channel = ChannelLabels[caster2_index]

caster1channel_PA = PALabels[caster1_index]            # PA Channels Here
caster2channel_PA = PALabels[caster2_index]
Hostchannel_PA = PALabels[host_index]

hostmutebutton = PhysicalButton()
hosttalkbutton = PhysicalButton()

hostmutebutton.setgpichannel(38)
hosttalkbutton.setgpichannel(40)

hostmutebutton.setx32address(x32address)
hosttalkbutton.setx32address(x32address)

hostmutebutton.addmutemsg(hostchannel)

hosttalkbutton.addfadermsg(hostchannel)
hosttalkbutton.addmutemsg(hostchannel, "mute_on_release", destinationbus=producerHB)

if Hostchannel_PA:
    hostmutebutton.addmutemsg(Hostchannel_PA)
    hosttalkbutton.addmutemsg(Hostchannel_PA)


###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
ChannelReport = PrettyTable()
ChannelReport.add_column("Name", ChannelDict["Label"])
ChannelReport.add_column("Channel", ChannelDict["Channel"])
ChannelReport.add_column("DCA Group", ChannelDict["DCA Group"])
ChannelReport.add_column("PA Channel", ChannelDict["PAChannel"])
ChannelReport.add_column("GPO LED Pin", ChannelDict["LED Channels"])
print "\nOverview of selected channels which are being subscribed to"
print ChannelReport
print "Communicating with x32 at %s:%d" % x32address

print "\nHost Mute button set to GPI pin %d. It has the following registered OSC Paths:" % hostmutebutton.gpichannel
for i in range(0, len(hostmutebutton.mutemsglist)):
    print "\t", hostmutebutton.mutemsglist[i]
for i in range(0, len(hostmutebutton.fadermsglist)):
    print "\t", hostmutebutton.fadermsglist[i]
print "Host Talkback button set to GPI pin %d. It has the following registered OSC Paths:" % hosttalkbutton.gpichannel
for i in range(0, len(hosttalkbutton.mutemsglist)):
    print "\t", hosttalkbutton.mutemsglist[i]
for i in range(0, len(hosttalkbutton.fadermsglist)):
    print "\t", hosttalkbutton.fadermsglist[i]

#################################################################
#                       Diagnostic Mode                         #
#################################################################

if DiagnosticMode is True:
    print "\nDiagnostic Mode started\nPossible buttons to choose from are: hostmutebutton, hosttalkbutton, exit"

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
        logging.warning("invalid button name")


if ButtonMode is "MIDI":
    """
    MIDI Stuff
    """
    verbose = False  # Verbose being true allows you to see what MIDI messages are being registered
    pygame.init()
    pygame.midi.init()
    # list all midi devices
    for x in range(0, pygame.midi.get_count()):
       print pygame.midi.get_device_info(x)

    # open a specific midi device
    MIDIdevice = 3
    inp = pygame.midi.Input(MIDIdevice)

    try:
        while 1:
            if inp.poll():
                # no way to find number of messages in queue
                # so we just specify a high max value

                MIDIeventlist = inp.read(1000)

                # 144 is note on, 128 is note off, 176 is a CC
                status_byte = MIDIeventlist[0][0][0]

                # pad 1 - 8 are note numbers 36-44
                # encoder 1 - 8 are note numbers 1 through 8
                note_number = MIDIeventlist[0][0][1]

                velocity = MIDIeventlist[0][0][2]

                # print MIDIeventlist
                if verbose:
                    print "Status Byte= %d" % status_byte
                    print "Note Number= %d" % note_number
                    print "Velocity= %d" % velocity

                # CC Note ON (activate when a MIDI pad is pressed)
                if status_byte == 144:
                    if note_number == 36:  # Mute button for Host
                        hostmutebutton.sendoscmessages(1)
                    elif note_number == 37:  # Talkback button for Host
                        hosttalkbutton.sendoscmessages(1)

                # CC Note OFF (activate when a MIDI pad is released)
                elif status_byte == 128:
                    if note_number == 36:
                        hostmutebutton.sendoscmessages(0)
                    elif note_number == 37:
                        hosttalkbutton.sendoscmessages(0)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop."
        print "Done"

if ButtonMode is "GPI":
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(hostmutebutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(hosttalkbutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    bouncetime = 5

    GPIO.add_event_detect(hostmutebutton.gpichannel, GPIO.BOTH)
    GPIO.add_event_detect(hosttalkbutton.gpichannel, GPIO.BOTH)

    try:
        while 1:

            # Host mute
            if GPIO.event_detected(hostmutebutton.gpichannel):
                sendondetect(hostmutebutton)

            # Host Talkback
            if GPIO.event_detected(hosttalkbutton.gpichannel):
                sendondetect(hosttalkbutton)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop and GPIO ports."
        GPIO.cleanup()
        print "Done"
