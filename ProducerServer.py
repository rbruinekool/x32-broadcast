import logging
import sys

from x32broadcast import read_variables_from_csv, PhysicalButton, getChannelData

try:
    import pygame.midi
except ImportError:
    logging.warning("pygame.midi not found. Make sure to run this script on a raspberry pi with pygame.midi installed")
    sys.exit()

try:
    from prettytable import PrettyTable
except ImportError:
    print "prettytable module not installed"

# Variables
userInputPhase = True;
print "Do you want me to read channel data from the local x32ChannelSheet.csv?"
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
DCALabels = ChannelDict["DCA Group"]
LEDChannels = ChannelDict["LED Channels"]
ProducerHearsOnPress = ChannelDict["ProducerHearsOnPress"]

try:
    x32ipaddress = ChannelDict["X32 IP"][0]
    hostbus = ChannelDict["Host Bus"][0]
    panelbus = ChannelDict["Panel Bus"][0]
    caster1bus = ChannelDict["Caster 1 Bus"][0]
    caster2bus = ChannelDict["Caster 2 Bus"][0]
    stagehostbus = ChannelDict["Stagehost Bus"][0]
    reporterbus = ChannelDict["Reporter Bus"][0]
    producerHB = ChannelDict["Producer HB Bus"][0]
    producerpgmbus = ChannelDict["Producer PGM Bus"][0]
except ValueError:
    print "Bus names in the CSV file are wrongly formatted"

x32address = (x32ipaddress, 10023)

try:
    host_index = ChannelNames.index("Host")
    panel1_index = ChannelNames.index("Panel 1")
    panel2_index = ChannelNames.index("Panel 2")
    panel3_index = ChannelNames.index("Panel 3")
    caster1_index = ChannelNames.index("Caster 1")
    caster2_index = ChannelNames.index("Caster 2")
    stagehost_index = ChannelNames.index("Stagehost")
    reporter_index = ChannelNames.index("Reporter")
except ValueError:
    print "The channelnames are not in the correct format. " \
          "Use Host, Panel 1, Panel 2, Caster 1, Caster 2, Stagehost and Reporter"

hostchannel = ChannelLabels[host_index]
panel1channel = ChannelLabels[panel1_index]
panel2channel = ChannelLabels[panel2_index]
panel3channel = ChannelLabels[panel3_index]
caster1channel = ChannelLabels[caster1_index]
caster2channel = ChannelLabels[caster2_index]
stagehostchannel = ChannelLabels[stagehost_index]
reporterchannel = ChannelLabels[reporter_index]

#  If any of the below statements are filled in with anything other than '' it will cause a press of the button by the
#  to also hear the person(s) he is talking to as long as he holds the button (useful if the talent does not have
#  talkback buttons. Filling any value in the 'ProducerHearsOnPress' row in x32ChannelSheet.csv file will cause this
#  to happen.
ProducerHearsOnPress_Host = ProducerHearsOnPress[host_index].lower()
ProducerHearsOnPress_Panel1 = ProducerHearsOnPress[panel1_index].lower()
ProducerHearsOnPress_Panel2 = ProducerHearsOnPress[panel2_index].lower()
ProducerHearsOnPress_Panel3 = ProducerHearsOnPress[panel3_index].lower()
ProducerHearsOnPress_Caster1 = ProducerHearsOnPress[caster1_index].lower()
ProducerHearsOnPress_Caster2 = ProducerHearsOnPress[caster2_index].lower()
ProducerHearsOnPress_Stagehost = ProducerHearsOnPress[stagehost_index].lower()
ProducerHearsOnPress_Reporter = ProducerHearsOnPress[reporter_index].lower()

###########################################################
# Reporting of the subscribed OSC handles in a pretty way #
###########################################################
BusReport = PrettyTable()
BusReport._set_field_names(["Bus Name", "Bus Number"])
BusReport.add_row(["Host Bus", hostbus])
BusReport.add_row(["Panel Bus", panelbus])
BusReport.add_row(["Caster 1 Bus", caster1bus])
BusReport.add_row(["Caster 2 Bus", caster2bus])
BusReport.add_row(["Stagehost Bus", stagehostbus])
BusReport.add_row(["Reporter Bus", reporterbus])
BusReport.add_row(["Producer Hearback", producerHB])
BusReport.add_row(["Producer PGM", producerpgmbus])

print "\nOverview of selected busses:"
print BusReport

ChannelReport = PrettyTable()
ChannelReport.add_column("Channel Name", ChannelDict["Label"])
ChannelReport.add_column("Channel Number", ChannelDict["Channel"])
ChannelReport.add_column("Producer Hears on Press", ChannelDict["ProducerHearsOnPress"])

print"\nOverview of selected channels, and whether producer hears them whilst talking to them:"
print ChannelReport
print "Communicating with x32 at %s:%d\n" % x32address

def create_MIDI_button(MIDIcc, ipaddress):
        MIDIbutton = PhysicalButton()
        MIDIbutton.setMIDIcc(MIDIcc)
        MIDIbutton.setx32address(ipaddress)
        return MIDIbutton

# Generating list of midi button PhysicalButton instances
MIDIbuttonlist = []
MIDICClist = []
for i in range(0, 8):
    MIDICClist.append(36 + i)
    MIDIbuttonlist.append(create_MIDI_button(MIDICClist[i], x32address))

# Generating list of midi encoder PhysicalButton instances
MIDIencoderlist = []
MIDIencoderCClist = []
for i in range(0, 8):
    MIDIencoderCClist.append(1 + i)
    MIDIencoderlist.append(create_MIDI_button(MIDIencoderCClist[i], x32address))

#########################################################################################
##                            Change PAD functions here                                ##
#########################################################################################

# Pad 5 - Talk to Host
MIDIbuttonlist[4].addtalk2bus(hostbus)
if ProducerHearsOnPress_Host == 'yes':
    MIDIbuttonlist[4].addmutemsg(hostchannel, mutemode="mute_on_release", destinationbus=producerHB)
                             
# Pad 6 - Talk to Panel

MIDIbuttonlist[5].addtalk2bus([hostbus, panelbus])
if ProducerHearsOnPress_Host == 'yes':
    MIDIbuttonlist[5].addmutemsg(hostchannel, mutemode="mute_on_release", destinationbus=producerHB)
if ProducerHearsOnPress_Panel1 == 'yes':
    MIDIbuttonlist[5].addmutemsg(panel1channel, mutemode="mute_on_release", destinationbus=producerHB)
if ProducerHearsOnPress_Panel2 == 'yes':
    MIDIbuttonlist[5].addmutemsg(panel2channel, mutemode="mute_on_release", destinationbus=producerHB)
if ProducerHearsOnPress_Panel3 == 'yes':
    MIDIbuttonlist[5].addmutemsg(panel3channel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 1 - Talk to Caster 1
MIDIbuttonlist[0].addtalk2bus(caster1bus)
if ProducerHearsOnPress_Caster1 == 'yes':
    MIDIbuttonlist[0].addmutemsg(caster1channel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 3 - Talk to Caster 2
MIDIbuttonlist[2].addtalk2bus(caster2bus)
if ProducerHearsOnPress_Caster2 == 'yes':
    MIDIbuttonlist[2].addmutemsg(caster2channel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 2 - Talk to Caster 1 and Caster 2
MIDIbuttonlist[1].addtalk2bus([caster1bus, caster2bus])
if ProducerHearsOnPress_Caster1 == 'yes':
    MIDIbuttonlist[1].addmutemsg(caster1channel, mutemode="mute_on_release", destinationbus=producerHB)
if ProducerHearsOnPress_Caster2 == 'yes':
    MIDIbuttonlist[1].addmutemsg(caster2channel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 7 - Talk to Reporter
MIDIbuttonlist[6].addtalk2bus(reporterbus)
if ProducerHearsOnPress_Reporter == 'yes':
    MIDIbuttonlist[6].addmutemsg(reporterchannel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 8 - Talk to Stagehost
MIDIbuttonlist[7].addtalk2bus(stagehostbus)
if ProducerHearsOnPress_Stagehost == 'yes':
    MIDIbuttonlist[7].addmutemsg(stagehostchannel, mutemode="mute_on_release", destinationbus=producerHB)

# Pad 4 - Talk to ALL
talk2BusList = [hostbus, panelbus, caster1bus, caster2bus, stagehostbus, reporterbus]
MIDIbuttonlist[3].addtalk2bus(talk2BusList)
MIDIbuttonlist[3].addmutemsg(hostchannel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(panel1channel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(panel2channel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(panel3channel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(caster1channel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(caster2channel, mutemode="mute_on_release", destinationbus=producerHB)
MIDIbuttonlist[3].addmutemsg(stagehostchannel, mutemode="mute_on_release", destinationbus=producerHB)

#########################################################################################
##                            Change encoder functions here                            ##
#########################################################################################

# Encoder 1 - Set host level to producer hb bus
MIDIencoderlist[0].addfadermsg(hostchannel, producerHB)

# Encoder 2 - Set panel level to producer hb bus
MIDIencoderlist[1].addfadermsg([panel1channel, panel2channel, panel3channel], producerHB)

# Encoder 5- Set caster1 level to producer hb bus
MIDIencoderlist[4].addfadermsg(caster1channel, producerHB)

# Encoder 6 - Set caster2 level to producer hb bus
MIDIencoderlist[5].addfadermsg(caster2channel, producerHB)

# Encoder 3 - Set caster2 level to producer hb bus
MIDIencoderlist[2].addfadermsg(stagehostchannel, producerHB)

# Encoder 8 - Set producer PGM level
MIDIencoderlist[7].addbusfadermsg(producerpgmbus)

verbose = False #Only use for diagnostics, it really slows the program

# set up pygame
pygame.init()
pygame.midi.init()

# list all midi devices
#for x in range( 0, pygame.midi.get_count()):
#    print pygame.midi.get_device_info(x)

# open a specific midi device

MIDIDeviceNamePC = 'LPD8'    #The name of the midi Device as detected by pygame.midi.get_device_info()
MIDIDeviceNamePi = 'LPD8 MIDI 1'  #The name on a raspberry Pi

# list all midi devices
for x in range( 0, pygame.midi.get_count()):
    currentMIDIdevice = pygame.midi.get_device_info(x)
    #print x,': ', currentMIDIdevice
    if currentMIDIdevice[2] == 1 and (currentMIDIdevice[1] == MIDIDeviceNamePC or currentMIDIdevice[1] == MIDIDeviceNamePi):
        device = x

# open a specific midi device

try:
    print 'Found and selected %s as device number %d' %(MIDIDeviceNamePC, device)
except NameError:
    print("The MIDI device (with name %s) has not been found. Make sure it plugged in with USB and rerun the script") % MIDIDeviceNamePC
    sys.exit(1)

# device = 2#input('Please type MIDI input device number: ')

inp = pygame.midi.Input(device)

# run the event loop
run = True
print "\nNow listening for MIDI commands"
while run:
##    print PadCount
    if inp.poll():
        # no way to find number of messages in queue
        # so we just specify a high max value

        # print inp.read(1000)
        MIDIeventlist = inp.read(1000)
        #print MIDIeventlist

        # 144 is note on, 128 is note off, 176 is a CC
        status_byte = MIDIeventlist[0][0][0]

        # pad 1 - 8 are note numbers 36-44
        # encoder 1 - 8 are note numbers 1 through 8
        note_number = MIDIeventlist[0][0][1]
        velocity = MIDIeventlist[0][0][2]

        if verbose:
            print "Status Byte= %d" % status_byte
            print "Note Number= %d" % note_number
            print "Velocity= %d" % velocity

##### PAD SECTION #####
        if status_byte == 144:
            buttonstate = 1
        elif status_byte == 128:
            buttonstate = 0

        ##### Sending all osc PAD messages based on the MIDICClist #####
        if 36 <= note_number <= 43:
            try:
                currentbuttonindex = MIDICClist.index(note_number)
                MIDIbuttonlist[currentbuttonindex].sendoscmessages(buttonstate)
                #  print "Received midi note %d. sending these osc talk messages" %note_number
                #  print MIDIbuttonlist[currentbuttonindex].talk2buslist
            except ValueError:
                print "MIDI Note %d is not registered" % note_number

        ##### Sending all osc encoder messages based on the MIDIencoderCClist #####
        elif 1 <= note_number <= 8:
            try:
                currentencoderindex = MIDIencoderCClist.index(note_number)
                MIDIencoderlist[currentencoderindex].sendfaderoscmessages(velocity)
            except ValueError:
                print "MIDI Note %d is not registered" % note_number



