class MixerChannel(object):

    def __init__(self):
        print "New channel instance created"
        self.mute_button = None
        self.mute_fader = None
        self.mutestatus = None

    def setfaderlevel(self, fadermsg):
        self.faderlevel = fadermsg

        # Set the mute_button property if the channel fader is below 10%
        if fadermsg <= 0.1:
            self.mute_fader = True
        else:
            self.mute_fader = False

        self.check_mute_status()

    def setmutebutton(self, buttonmsg):
        self.channel_on = buttonmsg

        # Set the mute_button property True if the channel is muted by the mute button
        if buttonmsg == 0:
            self.mute_button = True
        else:
            self.mute_button = False

        self.check_mute_status()

    def check_mute_status(self):

        mutestatus = self.mute_button or self.mute_fader

        # Activate a change in GPIO only if the mutestatus has actually changed
        if self.mutestatus != mutestatus:
            print "reference to GPIO class here, should probably be a function"

        self.mutestatus = mutestatus

        return self.mutestatus
