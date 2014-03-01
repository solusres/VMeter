import VMeter

v = VMeter.VMeter()
v.set_output_on_off(True)
v.set_output_touch_position(True)
v.set_output_pressure(True)

def start():
	print "Touch Start"

def end():
	print "Touch End"

def pressure(data):
	print "Pressure: %s (%s)" % ("#"*(int(data)/2), data)

def position(data):
	print "Position: %s (%s)" % ("*"*(int(data)/2), data)

v.on_touch_start(start)
v.on_touch_end(end)
v.on_pressure(pressure)
v.on_touch(position)
