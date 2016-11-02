"""
This script is to be run at the caster desk.
It enables the on-air LEDS and talkback buttons
"""

import pygame, pygame.midi, OSC
from x32broadcast import MixerChannel

# OSC Declarations
x32ipaddress = "10.75.255.75"

# Channel Declarations
ChannelDict = {
    "label": ["Host", "Panel 1", "Panel 2", "Panel 3" "Caster 1", "Caster 2", "Stagehost"],
    "Channel": [1, 2, 3, 4, 5, 6, 7],
    "DCA Group": [1, 1, 1, 1, 2, 2, 3],
}

ChannelNames = ChannelDict["label"]
ChannelLabels = ChannelDict["Channel"]
DCALabels = ChannelDict["DCA Group"]

caster1 = MixerChannel(4, 2, None, x32ipaddress)
caster2 = MixerChannel(5, 2, None, x32ipaddress)

"""
MIDI Stuff
"""
verbose = True # Verbose being true allows you to see what MIDI messages are being registered
pygame.init()
pygame.midi.init()

# list all midi devices
for x in range( 0, pygame.midi.get_count() ):
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

            #print MIDIeventlist
            if verbose:
                print "Status Byte= %d" % status_byte
                print "Note Number= %d" % note_number
                print "Velocity= %d" % velocity

except KeyboardInterrupt:
    print "\nClosing MIDI Listening Loop."
    print "Waiting for Server-thread to finish"
    print "Done"