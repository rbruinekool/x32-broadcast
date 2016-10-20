from itertools import count

import OSC


class MixerChannel(object):
    _ids = count(0)

    def __init__(self, channelnumber, dcagroup = None):
        self.id = self._ids.next()  #id number to keep track of the amount of instances made in a script

        self.mute_button = None
        self.mute_fader = None
        self.mute_dcafader = None
        self.mute_dcabutton = None
        self.mutestatus = None
        self.channelnumber = channelnumber
        self.dcagroup = dcagroup
        self.mutepath = "/ch/%02d/mix/on" % channelnumber
        self.faderpath = "/ch/%02d/mix/fader" % channelnumber
        if type(self.dcagroup) is int:
            self.dcamutepath = "/dca/%d/on" % dcagroup
            self.dcafaderpath = "/dca/%d/fader" % dcagroup

        self.subscribefactor = 0  # Sets how fast the X32 will send subscribe messages (0 is fastest)

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
            print "Set mutestatus to", mutestatus, "for channel", self.channelnumber

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

def list_duplicates(seq):
    seen = set()
    seen_add = seen.add
    # adds all elements it doesn't know yet to seen and all other to seen_twice
    seen_twice = set( x for x in seq if x in seen or seen_add(x) )
    # turn the set into a list (as requested)
    return list( seen_twice )
