"""
This script is to be run at the caster desk.
It enables the on-air LEDS and mute/talkback buttons
"""

import pygame, pygame.midi
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

caster1 = MixerChannel(9, 5, None, x32ipaddress)
caster2 = MixerChannel(10, 5, None, x32ipaddress)

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

            print MIDIeventlist
            if verbose:
                print "Status Byte= %d" % status_byte
                print "Note Number= %d" % note_number
                print "Velocity= %d" % velocity

            if status_byte == 144:  # CC Note ON
                if note_number == 36:
                    caster2.set_mute(0)
                elif note_number == 37:
                    caster2.open_communications(6)
                    caster2.set_mute(0)
                elif note_number == 39:
                    caster1.set_mute(0)
                elif note_number == 38:
                    caster1.open_communications(6)
                    caster1.set_mute(0)

            elif status_byte == 128:  # CC Note OFF
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
