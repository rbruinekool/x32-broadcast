"""
This script is to be run at the caster desk.
It enables the on-air LEDS and mute/talkback buttons


"""
import pygame, pygame.midi
import RPi.GPIO as GPIO
from x32broadcast import MixerChannel, read_variables_from_csv

ButtonMode = "GPI" # Fill in "MIDI" if a MIDI pad is used and "GPI" if GPI's are used

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

###########################################################
#     Reading channels and ip adress from a CSV file      #
# Make sure that the correct CSV file is pointed to below #
###########################################################

ChannelDict = read_variables_from_csv("x32CSGO.csv")

ChannelNames = ChannelDict["Label"]
ChannelLabels = ChannelDict["Channel"]
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]
x32ipaddress = ChannelDict["X32 IP"][0]

x32address = (x32ipaddress, 10023)

if x32ipaddress is '':
    print "ip adress field in csv is empty make sure the ip adress is located in the right spot"
try:
    caster1_index = ChannelNames.index("Caster 1")
    caster2_index = ChannelNames.index("Caster 2")
except ValueError:
    print "The channelnames are not in the correct format. Use Caster 1 and Caster 2"

# Here the caster MixerChannel objects are created. These objects have methods that allow the script
# to change paramaters of the channel (e.g. mute them) based on incoming MIDI messages
caster1 = MixerChannel(ChannelLabels[caster1_index])
caster1.setdcagroup(DCALabels[caster1_index])
caster1.setx32address(x32address)

caster2 = MixerChannel(ChannelLabels[caster2_index])
caster2.setdcagroup(DCALabels[caster2_index])
caster2.setx32address(x32address)

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
print "Communicating with x32 at %s:%d" % x32address


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

if ButtonMode is "MIDI":
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

    Caster1GPI_Mute = 36
    Caster2GPI_Mute = 37
    Caster1GPI_Talk = 38
    Caster2GPI_Talk = 40

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(Caster1GPI_Mute, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(Caster2GPI_Mute, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.setup(Caster1GPI_Talk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(Caster2GPI_Talk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    Caster1MuteButton = GPIO.input(Caster1GPI_Mute)
    Caster2MuteButton = GPIO.input(Caster2GPI_Mute)
    Caster1TalkButton = GPIO.input(Caster1GPI_Talk)
    Caster2TalkButton = GPIO.input(Caster2GPI_Talk)

    try:
        while 1:
            # Caster 2 MUTE button
            if GPIO.input(Caster1GPI_Mute) != Caster1MuteButton:
                if GPIO.input(Caster1GPI_Mute) == 1:
                    caster1.set_mute(0)
                    Caster1MuteButton = GPIO.input(Caster1GPI_Mute)

                if GPIO.input(Caster1GPI_Mute) == 0:
                    caster1.set_mute(1)
                    Caster1MuteButton = GPIO.input(Caster1GPI_Mute)

            # Caster 1 TALK button
            if GPIO.input(Caster1GPI_Talk) != Caster1TalkButton:
                if GPIO.input(Caster1GPI_Talk) == 1:
                    caster1.set_mute(0)
                    caster1.open_communications(6)
                    Caster1TalkButton = GPIO.input(Caster1GPI_Talk)

                if GPIO.input(Caster1GPI_Talk) == 0:
                    caster1.set_mute(1)
                    caster1.close_communications(6)
                    Caster1TalkButton = GPIO.input(Caster1GPI_Talk)

            # Check if the Caster 2 mute button status has changed
            if GPIO.input(Caster2GPI_Mute) != Caster2MuteButton:
                if GPIO.input(Caster2GPI_Mute) == 1:
                    caster2.set_mute(0)
                    Caster2MuteButton = GPIO.input(Caster2GPI_Mute)

                if GPIO.input(Caster2GPI_Mute) == 0:
                    caster2.set_mute(1)
                    Caster2MuteButton = GPIO.input(Caster2GPI_Mute)

            # Caster 1 TALK button
            if GPIO.input(Caster2GPI_Talk) != Caster2TalkButton:
                if GPIO.input(Caster2GPI_Talk) == 1:
                    caster2.set_mute(0)
                    caster2.open_communications(6)
                    Caster2TalkButton = GPIO.input(Caster2GPI_Talk)

                if GPIO.input(Caster2GPI_Talk) == 0:
                    caster2.set_mute(1)
                    caster2.close_communications(6)
                    Caster2TalkButton = GPIO.input(Caster2GPI_Talk)

    except KeyboardInterrupt:
        print "\nClosing MIDI Listening Loop."
        print "Done"