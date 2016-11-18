"""
This script is to be run at the caster desk.
It enables the on-air LEDS and mute/talkback buttons


"""
import pygame, pygame.midi
import RPi.GPIO as GPIO
from x32broadcast import MixerChannel, PhysicalButton, read_variables_from_csv

ButtonMode = "GPI" # Fill in "MIDI" if a MIDI pad is used and "GPI" if GPI's are used

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

###########################################################
#     Reading channels and ip adress from a CSV file      #
# Make sure that the correct CSV file is pointed to below #
###########################################################

ChannelDict = read_variables_from_csv("x32ChannelSheet.csv")

ChannelNames = ChannelDict["Label"]
ChannelLabels = ChannelDict["Channel"]
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]
x32ipaddress = ChannelDict["X32 IP"][0]

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

producerHB = 6

Hostchannel = ChannelLabels[host_index]
caster1channel = ChannelLabels[caster1_index]
caster2channel = ChannelLabels[caster2_index]

c1mutebutton = PhysicalButton()
c1talkbutton = PhysicalButton()
c2mutebutton = PhysicalButton()
c2talkbutton = PhysicalButton()

c1mutebutton.setgpichannel(36)
c1talkbutton.setgpichannel(37)
c2mutebutton.setgpichannel(38)
c2talkbutton.setgpichannel(40)

c1mutebutton.setx32address(x32address)
c1talkbutton.setx32address(x32address)
c2mutebutton.setx32address(x32address)
c2talkbutton.setx32address(x32address)

c1mutebutton.addmutemsg(caster1channel)

c1talkbutton.addmutemsg(caster1channel)
c1talkbutton.addmutemsg(caster1channel, "mute_on_release", destinationbus=producerHB)

c2mutebutton.addmutemsg(caster2channel)

c2talkbutton.addmutemsg(caster2channel)
c2talkbutton.addmutemsg(caster2channel, "mute_on_release", destinationbus=producerHB)

###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
ChannelReport = PrettyTable()
ChannelReport.add_column("Name", ChannelDict["Label"])
ChannelReport.add_column("Channel", ChannelDict["Channel"])
ChannelReport.add_column("DCA Group", ChannelDict["DCA Group"])
ChannelReport.add_column("GPO LED Pin", ChannelDict["LED Channels"])
print "\nOverview of selected channels which are being subscribed to"
print ChannelReport
print "Communicating with x32 at %s:%d" % x32address

print "\nCaster 1 Mute button set to GPI pin %d. It has the following registered OSC Paths:" % c1mutebutton.gpichannel
for i in range(0, len(c1mutebutton.mutemsglist)):
    print "\t", c1mutebutton.mutemsglist[i]
print "Caster 1 Talkback button set to GPI pin %d. It has the following registered OSC Paths:" % c1talkbutton.gpichannel
for i in range(0, len(c1talkbutton.mutemsglist)):
    print "\t", c1talkbutton.mutemsglist[i]
print "\nCaster 2 Mute button set to GPI pin %d. It has the following registered OSC Paths:" % c2mutebutton.gpichannel
for i in range(0, len(c2mutebutton.mutemsglist)):
    print "\t", c2mutebutton.mutemsglist[i]
print "Caster 2 Talkback button set to GPI pin %d. It has the following registered OSC Paths:" % c2talkbutton.gpichannel
for i in range(0, len(c2talkbutton.mutemsglist)):
    print "\t", c2talkbutton.mutemsglist[i]

"""
MIDI Stuff
"""
verbose = False  # Verbose being true allows you to see what MIDI messages are being registered
pygame.init()
pygame.midi.init()

if ButtonMode is "MIDI":
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
                    if note_number == 36:  # Mute button for caster 2
                        caster2.set_mute(0)
                    elif note_number == 37:  # Talkback button for caster 2
                        caster2.open_communications(6)
                        caster2.set_mute(0)
                    elif note_number == 39:  # Mute button for caster 1
                        caster1.set_mute(0)
                    elif note_number == 38:  # Talkback button for caster 1
                        caster1.open_communications(6)
                        caster1.set_mute(0)

                # CC Note OFF (activate when a MIDI pad is released)
                elif status_byte == 128:
                    if note_number == 36:
                        caster2.set_mute(1)
                    elif note_number == 37:
                        caster2.close_communications(6)
                        caster2.set_mute(1)
                    elif note_number == 39:
                        caster1.set_mute(1)
                    elif note_number == 38:
                        caster1.close_communications(6)
                        caster1.set_mute(1)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop."
        print "Done"

if ButtonMode is "GPI":
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(c1mutebutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c1talkbutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c2mutebutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c2talkbutton.gpichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    Caster1MuteButton = GPIO.input(c1mutebutton.gpichannel)
    Caster1TalkButton = GPIO.input(c1talkbutton.gpichannel)
    Caster2MuteButton = GPIO.input(c2mutebutton.gpichannel)
    Caster2TalkButton = GPIO.input(c2talkbutton.gpichannel)

    try:
        while 1:
            # Caster 1 MUTE button
            if GPIO.input(c1mutebutton.gpichannel) != Caster1MuteButton:
                if GPIO.input(c1mutebutton.gpichannel) == 1:
                    c1mutebutton.sendoscmessages(1)
                    Caster1MuteButton = GPIO.input(c1mutebutton.gpichannel)

                if GPIO.input(c1mutebutton.gpichannel) == 0:
                    c1mutebutton.sendoscmessages(0)
                    Caster1MuteButton = GPIO.input(c1mutebutton.gpichannel)

            # Caster 1 TALK button
            if GPIO.input(c1talkbutton.gpichannel) != Caster1TalkButton:
                if GPIO.input(c1talkbutton.gpichannel) == 1:
                    c1talkbutton.sendoscmessages(1)
                    Caster1TalkButton = GPIO.input(c1talkbutton.gpichannel)

                if GPIO.input(c1talkbutton.gpichannel) == 0:
                    c1talkbutton.sendoscmessages(0)
                    Caster1TalkButton = GPIO.input(c1talkbutton.gpichannel)

            # Caster 2 MUTE button
            if GPIO.input(c2mutebutton.gpichannel) != Caster2MuteButton:
                if GPIO.input(c2mutebutton.gpichannel) == 1:
                    c2mutebutton.sendoscmessages(1)
                    Caster2MuteButton = GPIO.input(c2mutebutton.gpichannel)

                if GPIO.input(c2mutebutton.gpichannel) == 0:
                    c2mutebutton.sendoscmessages(0)
                    Caster2MuteButton = GPIO.input(c2mutebutton.gpichannel)

            # Caster2 TALK button
            if GPIO.input(c2talkbutton.gpichannel) != Caster2TalkButton:
                if GPIO.input(c2talkbutton.gpichannel) == 1:
                    c2talkbutton.sendoscmessages(1)
                    Caster2TalkButton = GPIO.input(c2talkbutton.gpichannel)

                if GPIO.input(c2talkbutton.gpichannel) == 0:
                    c2talkbutton.sendoscmessages(0)
                    Caster2TalkButton = GPIO.input(c2talkbutton.gpichannel)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop."
        print "Done"
