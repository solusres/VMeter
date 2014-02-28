#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# DEMOS
#

from VMeter import VMeter
from pygame import pypm
from datetime import datetime

vMeter = VMeter()

def binary_clock():
    """
    Binary clock display.
    Each digit is displayed over 4 LEDs.
    Marker LEDs blink every half second to indicate the position of the digits.
    It displays hours, minutes and seconds, where hours are 24 hour format.
    """
    last_cycle_time = 0
    led_array = [0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0]
    update_time = 0
    while True:
        if pypm.Time() - last_cycle_time > 500:
            last_cycle_time = pypm.Time()
            led_array[11] = update_time # marker for minutes, just blinks with seconds
            led_array[16] = update_time # marker for minutes, just blinks with seconds
            led_array[26] = update_time # marker for hours, just blinks with seconds
            led_array[31] = update_time # marker for hours, just blinks with seconds
            
            if update_time == 0:
                update_time = 1
            
            else:
                update_time = 0
                ##            print "cycle"
                seconds = datetime.now().strftime('%S')
                seconds_first_digit = int(seconds[0])
                seconds_second_digit = int(seconds[1])
                
                minutes = datetime.now().strftime('%M')
                minutes_first_digit = int(minutes[0])
                minutes_second_digit = int(minutes[1])
                
                hours = datetime.now().strftime('%H')
                hours_first_digit = int(hours[0])
                hours_seconds_digit = int(hours[1])
                
             
                temp_counter = seconds_second_digit
                for i in range(4):
                    led_array[i] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1
                
                temp_counter = seconds_first_digit
                for i in range(4):
                    led_array[i+4] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1
                
                        
                temp_counter = minutes_second_digit
                for i in range(4):
                    led_array[i+12] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1
                
                temp_counter = minutes_first_digit
                for i in range(4):
                    led_array[i+17] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1
                
                
                temp_counter = hours_seconds_digit
                for i in range(4):
                    led_array[i+27] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1
                
                temp_counter = hours_first_digit
                for i in range(4):
                    led_array[i+32] = 0x01 & temp_counter
                    temp_counter = temp_counter >> 1

                print hours, minutes, seconds
            vMeter.send_array(led_array)

def binary_counter():
    """
    A simple binary counter display.
    """
    last_cycle_time = 0
    counter = 0
    led_array = [0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0,0,0,
                 0,0,0,0,0,0,0,0]
    
    while True:
        if pypm.Time() - last_cycle_time > 30:
            ##            print "cycle"
            last_cycle_time = pypm.Time()
            temp_counter = counter
            counter = counter + 1
            for i in range(20):
                led_array[i] = 0x01 & temp_counter
                temp_counter = temp_counter >> 1
                
            vMeter.send_array(led_array)
