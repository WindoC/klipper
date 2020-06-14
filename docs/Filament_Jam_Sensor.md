This document describes Filament Jam Sensor module. Hardware used for developing this module is based on optical endstop or encoder(1 line) count the filament usage within one LOW/HIGH cycle. You can find designs at [thingiverse.com](https://www.thingiverse.com/thing:3067904)

## How does it work?
Filaments spins the wheel in the sensor, the sensor goes LOW to HIGH. The module calculates the filament usage between a LOW/HIGH cycle compare with base line(setting base_usage) usage.
If the usage reached base_usage (mm) and no signal from PIN within timer (s) will trigger the jam/pause action.

## Configuration
    # Pause/Resume module must define
    [pause_resume]
    #recover_velocity: 50.
    #
    # on/off / encoder(user only 1 line) Filament Jam Sensor
    [filament_jam_sensor jamsensor]
    pin: ar22
    timer: 1.0
    # timer ; in sec ; setup how often the system check the usage ; default = 1.0
    extruder: extruder
    # name of extruder ( , extruder1 , extruder2 or etc ... )
    base_usage: 3.85
    # base_usage ; in mm (must define) for one up/down cycle
    # detect in Jam or filament run out and will trigger PAUSE & jam_gcode
    jam_gcode: M300
    # gcode that will run at jam_usage triggered

## Commands
  - `SET_FILAMENT_JAM_SENSOR SENSOR=<sensor name> [TIMER=<sec>] [BASE_USAGE=<mm>]
    [ACTION=<0|1>] [ENABLE=<0|1>] [DEBUG=<0|1>]
    `:  Configures the [filament_jam_sensor] module. TIMER, BASE_USAGE, 
	correspond to same name in configuration.
    ACTION default is 1 and set to 0 will bypass the action of slow down/speed up,
    pause and gcode execute defined in the config. ENABLE default is 1 and set to 0
    will disable the checking logic of this module. DEBUG default is 0 and set to 1
    will output the information for debug.
