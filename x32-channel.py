class MixerChannel(object):

    def __init__(self, mute_button, mute_fader):
        print "New channel instance created"
        self.mute_button = mute_button
        self.mute_fader = mute_fader

    def mutebutton_check(self, buttonmsg):
        if buttonmsg == 0:                      # Returns True if the channel is Muted
            self.mute_button = True
        else:
            self.mute_button = False

    def fader_check(self, fadermsg):
        if fadermsg <= 0.1:                     # Returns True if the channel fader is below 10%
            self.mute_fader = True
        else:
            self.mute_fader = False

    def mute_status(self):

        mutestatus = self.mute_button or self.mute_fader
        return mutestatus
