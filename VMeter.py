#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
::OUTPUT::

Touch position:
Ctrl #20.

On / Off:
Ctrl #17.
127 is sent when VMeter is first touched, 0 is sent when released.
Disabled by default.

Pressure:
Ctrl #18.
Pressure output is actually more a measure of contact area;
two fingers lightly touching will be the same as one heavy touch.
Disabled by default.

Echo test:
Ctrl #118.
Only chan 1.
Values sent to this controller are echoed back.

Pitch Wheel:
Disabled by default.
When enabled, it overrides the Touch Position output and LED Column Height input.
The pitch wheel acts like a spring-loaded keyboard pitch wheel. 
When a finger is released, the output snaps back to the center.

Cross Fader:
Pitch Wheel output without snapping back to center.

Noteout:
When touched, NoteOn messages sent via default pitch 64 and velocity 100 (changeable).
Disabled by default. NoteOff message sent on release.
Both the pitch and velocity can also be mapped to the position of touch,
see Noteout Pitch and Velocity modes below.

::INPUT::

LED Column Height:
Ctrl #20.

LED Brightness:
Ctrl #21.
17 unique levels including all the way off.

Echo response:
Ctrl #118.
Only chan 1.

Pitch Wheel:
for Pitch Wheel or Cross Fader mode.

Note On:
The note number (0-127) turns on a column of LEDs,
note Off turns all LEDs off.
Can be used in Sonar to make a visual metronome.

Individual LED control: 
Control uses the polyphonic aftertouch command on channels 14, 15 and 16.
LEDs 1-7: Polyphonic aftertouch on chan 14 (0xAD), data1 bits 0-6.
LEDs 8-14: status 0xAD, data2 bits 0-6.
LEDs 15-21: status 0xAE (polyphonic aftertouch on chan 15), data1 bits 0-6.
LEDs 22-28: status 0xAE, data2 bits 0-6.
LEDs 29-35: status 0xAF, data1 bits 0-6.
LEDs 36-38: status 0xAF, data2 bits 0-2.

"""

from pygame import pypm
import time
import threading

NUM_LEDS = 38

# constants used when listing MIDI devices
_INPUT, _OUTPUT, _BOTH = range(3)

CONTROL = 0xB0

TOUCH_POS = 20

def get_devices():
    for i in range(pypm.CountDevices()):
        yield pypm.GetDeviceInfo(i)

def print_devices(InOrOut=None):
    for i, (interf,name,inp,outp,opened) in enumerate(get_devices()):
        if ((InOrOut == _INPUT) and (inp == 1) or
            (InOrOut == _OUTPUT) and (outp == 1) or
            (InOrOut == None)):
            print i, name, "\t",
            if (inp == 1):
                print "(input) \t",
            else:
                print "(output)\t",
            if (opened == 1):
                print "(opened)"
            else:
                print "(unopened)"
    print

class VMeter(object):
    """Class used to communicate with a VMeter.

    NOTE: this class may not behave correctly if more than one VMeter is connected.
    """
    _in = None
    _out = None

    def __init__(self, input_device=None, output_device=None):
        pypm.Initialize()
        
        self.connect(input_device, output_device)

        self.handlers = {}

        self.reader = IntervalThread(self.dispatch, interval=.001)
        self.reader.start()

    #
    # CONNECTION
    #

    def connect(self, input_device=None, output_device=None):
        self._in = self.connectInput(device=input_device)
        self._out = self.connectOutput(device=output_device)

    def connectInput(self, device=None):
        """
        Connect input to receive data from VMeter.
        If no device number is specified, attempts to connect
        to the first unopened input device with "VMeter" in the name.
        """
        if device is None:
            a = [i for (i, (_, name, inp, outp, opened))
                in enumerate(get_devices())
                if inp==1 and opened == 0 and "VMeter" in name]
            if len(a) > 0:
                device = a[0]
            else:
                raise Exception("No unopened VMeter input devices found!")

        return pypm.Input(device) 

    def connectOutput(self, device=None):
        """
        Connect output to send data to VMeter.
        If no device number is specified, attempts to connect
        to the first unopened output device with "VMeter" in the name.
        """
        if device is None:
            a = [i for (i, (_, name, inp, outp, opened))
                in enumerate(get_devices())
                if outp==1 and opened == 0 and "VMeter" in name]
            if len(a) > 0:
                device = a[0]
            else:
                raise Exception("No unopened VMeter output devices found!")

        return pypm.Output(device)

    def close(self):
        self.closeInput()
        self.closeOutput()

    def closeInput(self):
        if (self._in is not None):
            self._in.Close()

    def closeOutput(self):
        if (self._out is not None):
            self._out.Close()

    #
    # SETTINGS
    #

    def set_upside_down_mode(self, which):
        """
        When enabled, VMeter will draw LED column from the top rather than the bottom.
        MIDI controller outputs are also referenced from the bottom.
        Useful if you want all the USB cables to go away from you rather than towards.
        """
        self.send_config(125 if which else 126)

    def recalibrate_touch_sensor(self):
        """
        Issues a recalibration, which normally shouldn’t be necessary,
        but might if the environment changes too much, or it gets in an erroneous state.
        For instance, moving it next to a large metal object can sometimes cause this.
        In general, the VMeter is contantly recalibrating itself to the environment,
        and this shouldn't be necessary.
        """
        self.send_config(112)

    def set_LEDs_ignore_touch(self, which):
        """
        When enabled, VMeter LEDs will NOT respond to touch--only MIDI input.
        MIDI commands will still be sent.
        Useful if you don’t want the LED pattern being controlled by MIDI to be
        overridden by touch.
        """
        self.send_config(107 if which else 106)

    def set_on_off_output(self, which):
        """
        When enabled, VMeter will send 127 via ctrl #17 when touched, 0 when released.
        """
        self.send_config(120 if which else 119)

    def set_touch_position_output(self, which):
        """
        When enabled, VMeter will output touch position.
        Disabling this is useful when setting up mappings.
        """
        self.send_config(124 if which else 123)

    def set_pressure_output(self, which):
        """
        When enabled, VMeter will output pressure intensity.
        """
        self.send_config(122 if which else 121)

    def set_note_on_off_messages(self, which):
        """
        When enabled, VMeter will output note on/off messages.
        """
        self.send_config(117 if which else 116)

    def set_pitch_wheel_mode(self, which):
        """
        When enabled, VMeter will behave as a pitch wheel.
        This overrides the lights.
        """
        self.send_config(115 if which else 114)

    def set_cross_fader_mode(self, which):
        """
        When enabled, VMetter will behave as a cross fader.
        Output is same as pitch wheel without snapping back to center.
        This overrides the lights.
        """
        self.send_config(105 if which else 104)

    def read_current_settings(self):
        """
        Reads VMeter's current settings.
        Used to update the configuration utility interface.
        """
        self.send_config(113)

    def set_noteout_velocity_mode(self, which):
        """
        When enabled, velocity of note-outs is based on position.
        When disabled, note-outs use preset velocity. (Default 100)
        """
        self.send_config(111 if which else 110)

    def set_noteout_pitch_mode(self, which):
        """
        When enabled, pitch of note-outs is based on position.
        When disabled, note-outs use preset pitch. (Default 64)
        """
        self.send_config(109 if which else 108)

    def get_version(self):
        """
        Returns the 4 digit version as ASCII via controller number 109.
        """
        self.send_config(103)

    def store_settings(self):
        """
        Stores settings so they will be retained after power is removed.
        Saves:
        - upside-down mode
        - enable touch position output
        - enable pressure output
        - enable on/off output
        - midi channel
        - position output controller #
        - on/off output controller #
        - pressure output controller #
        - light input controller #
        - brightness input controller #
        - enable note-on/off signals
        - note pitch
        - note pitch mode
        - note velocity
        - note velocity mode
        - pitch wheel enable
        - brightness
        - LEDs ignore touch mode
        - pitch wheel enable
        - cross fade mode enable
        """
        self.send_config(118)

    def set_MIDI_channel(self, value):
        """
        Changes the channel over which Input and Output messages are sent.
        Note: all config changes are always sent over channel 1.

        value 1-16
        """
        self._out.WriteShort(CONTROL, 117, value)

    def set_position_output_ctrl_num(self, value):
        """
        Changes the controller number over which touch output messages are sent.

        value 0-100
        """
        self._out.WriteShort(CONTROL, 116, value)

    def set_on_off_output_ctrl_num(self, value):
        """
        Changes the controller number over which on/off output messages are sent.

        value 0-100
        """
        self._out.WriteShort(CONTROL, 115, value)

    def set_pressure_output_ctrl_num(self, value):
        """
        Changes the controller number over which pressure output messages are sent.

        value 0-100
        """
        self._out.WriteShort(CONTROL, 114, value)

    def set_light_input_ctrl_num(self, value):
        """
        Changes the controller number over which light input messages are sent.

        value 0-100
        """
        self._out.WriteShort(CONTROL, 113, value)

    def set_brightness_input_ctrl_num(self, value):
        """
        Changes the controller number over which brightness input messages are sent.

        value 0-100
        """
        self._out.WriteShort(CONTROL, 112, value)

    def set_noteout_number(self, value):
        """
        Changes the default value for noteout number.

        value 0-127
        """
        self._out.WriteShort(CONTROL, 111, value)

    def set_noteout_velocity(self, value):
        """
        Changes the default value for noteout velocity.

        value 0-127
        """
        self._out.WriteShort(CONTROL, 110, value)

    def set_brightness(self, value):
        """
        Changes brightness of LEDs.

        value 0-16 (0 = off)
        """
        vals = [0, 7, 15, 23, 31, 39, 47, 55, 63, 71, 79, 87, 95, 103, 111, 119, 127]
        self._out.WriteShort(CONTROL, 21, vals[value])

    #
    # SENDING DATA
    #

    def echo(self, value):
        """
        Sends value to be echoed back.
        Works only on channel 1.
        """
        self._out.WriteShort(CONTROL, 118, value)

    def send_config(self, value):
        """
        Sends value over Ctrl #119.
        Helper function for setting config values.
        """
        self._out.WriteShort(CONTROL, 119, value)

    def send_array(self, array):
        """
        Sends an array of 1's and 0's as LED on/off data.
        Assumes length 38 array.
        """
        
        # Need to split array into (6) 7-bit chunks
        # Individual LED control is sent to the aftertouch MIDI command and
        # channels 14, 15 and 16.
        # Each of the data bytes transmit 7 LED states.

        bytes = [0,0,0,0,0,0]
        bytes[0] =  array[0] |  array[1]<<1 |  array[2]<<2 |  array[3]<<3 |  array[4]<<4 |  array[5]<<5 |  array[6]<<6
        bytes[1] =  array[7] |  array[8]<<1 |  array[9]<<2 | array[10]<<3 | array[11]<<4 | array[12]<<5 | array[13]<<6
        bytes[2] = array[14] | array[15]<<1 | array[16]<<2 | array[17]<<3 | array[18]<<4 | array[19]<<5 | array[20]<<6
        bytes[3] = array[21] | array[22]<<1 | array[23]<<2 | array[24]<<3 | array[25]<<4 | array[26]<<5 | array[27]<<6
        bytes[4] = array[28] | array[29]<<1 | array[30]<<2 | array[31]<<3 | array[32]<<4 | array[33]<<5 | array[34]<<6
        bytes[5] = array[35] | array[36]<<1 | array[37]<<2
        self._out.WriteShort(0xAD,bytes[0],bytes[1])
        self._out.WriteShort(0xAE,bytes[2],bytes[3])
        self._out.WriteShort(0xAF,bytes[4],bytes[5])

    def send_column(self, height):
        """
        Send a column of height from 0 to 127.
        """
        self._out.WriteShort(CONTROL,20,height)

    def clear(self):
        self.send_column(0)

    #
    # RECEIVING DATA
    #

    def read(self):
        if self._in.Poll():
            return self._in.Read(1)[0][0]

        return None

    def read_touch_position(self):
        midi_data = self.read()

        if midi_data is not None:
            if midi_data[0] == CONTROL:
                if midi_data[1] == TOUCH_POS:
                    return int(midi_data[2])

        return None

    #
    # EVENTING
    #

    def dispatch(self):
        midi_data = self.read()

        if midi_data is not None:
            if midi_data[0] == CONTROL:
                self.handle(midi_data[1], int(midi_data[2]))

    def register(self, ctrl, function):
        try:
            control = self.handlers[ctrl]
        except KeyError:
            control = self.handlers[ctrl] = []

        control.append(function)

    def handle(self, ctrl, data):
        print ctrl, data
        
        if ctrl in self.handlers:
            for f in self.handlers[ctrl]:
                f(data)

    #
    # MACROS
    #

    def draw_bar(self, position, size):
        """
        Draws a bar of given size (0-38),
        centered at given position (0-127)
        """
        leds = [0]*NUM_LEDS
        cursor_pos = int(float(position) / 127.0 * 37.0)
        
        lower_limit = cursor_pos - size / 2
        if lower_limit < 0:
            lower_limit = 0
        
        upper_limit = cursor_pos + size / 2
        if upper_limit > (NUM_LEDS-1):
            upper_limit = NUM_LEDS-1
        
        i = lower_limit
        while i <= upper_limit:
            leds[i] = 1
            i = i + 1
        self.send_array(leds)

    def sweep_from_center(self, delay=.05):
        """
        Draws a sweep from the center, with delay (in sec) between each step
        """
        self.clear()

        leds = [0]*NUM_LEDS

        for i in range(NUM_LEDS/2,NUM_LEDS):
            leds[i] = 1
            leds[NUM_LEDS-1-i] = 1
            self.send_array(leds)
            time.sleep(delay)

class IntervalThread(threading.Thread):
    def __init__(self, function, interval, name="Interval"):
        threading.Thread.__init__(self)
        self.name = name
        self.setDaemon(True)
        self.killed = False
        self.function = function
        self.interval = interval

    def run(self):
        while not self.killed:
            time.sleep(self.interval)
            self.function()
            
    def stop(self):
        self.killed = True