# Generic Filament Jam Sensor Module
#
# Copyright (C) 2020 Antonio Cheong <windo.ac@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging


class JamSensor:
    def __init__(self, config):
        self.mname = config.get_name().split()[0]
        self.name = config.get_name().split()[1]
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.reactor = self.printer.get_reactor()
        self.buttons = self.printer.load_object(config, "buttons")
        self.buttons.register_buttons( [config.get("pin")], self._signal_handler )
        self.timer = config.getfloat( "timer", 1.0, above=0.0 )
        self.extruder_name = config.get("extruder", None)
        self.extruder = None
        self.base_usage = config.getfloat( "base_usage", None, above=0.0)
        self.jam_gcode = config.get("jam_gcode", None)
        self.filament_usage_last = 0.0
        self.timer_usage_last = 0.0
        self.pause_resume = None
        self.enable = False
        self.debug = False
        self.action = True
        self.jam_triggered = False
        self.cmd_SET_FILAMENT_JAM_SENSOR_help = "Set param of FILAMENT_JAM_SENSOR"
        self.gcode.register_mux_command( "SET_FILAMENT_JAM_SENSOR", "SENSOR", self.name, self.cmd_SET_FILAMENT_JAM_SENSOR, desc=self.cmd_SET_FILAMENT_JAM_SENSOR_help, )
        self.printer.register_event_handler( "klippy:ready", self._handle_ready )

    def _handle_ready(self):
        self.extruder = self.printer.lookup_object( self.extruder_name )
        if self.base_usage is None:
            logging.exception("base_usage must defined")
            self.enable = False
        else:
            self.filament_usage_last = self.get_filament_usage()
            self.pause_resume = self.printer.lookup_object( "pause_resume", None )
            if self.pause_resume is None:
                logging.exception( "pause_resume must define" )
                self.enable = False
            else:
                self.enable = True
                self.reactor.register_timer( self._timer_handler, self.reactor.NOW )
                logging.info( "%s(%s): ready to use", self.mname, self.name, )

    def _signal_handler(self, eventtime, state):
        if self.enable and state == 1:
            new_usage = self.get_filament_usage()
            delta_usage = new_usage - self.filament_usage_last
            self.filament_usage_last = new_usage
            if self.debug:
                self.gcode.respond_info( "%s(%s): %.2f %% ( %.2f / %.2f )" % ( self.mname, self.name, delta_usage / self.base_usage * 100.0, delta_usage, self.base_usage, ) )
                logging.debug( "%s(%s): _signal_handler triggered | delta_usage = %s", self.mname, self.name, delta_usage, )
            if self.jam_triggered:
                self.jam_triggered = False  # reset jam_triggered if it moving
                if self.debug:
                    self.gcode.respond_info( "%s(%s): jam_triggered = False" % ( self.mname, self.name, ) )

    def _timer_handler(self, eventtime):
        if self.enable:
            new_usage = self.get_filament_usage()
            delta_usage = new_usage - self.filament_usage_last
            if self.jam_triggered and self.timer_usage_last != new_usage:   # ignore when it's not move
                if self.debug:
                    self.gcode.respond_info( "%s(%s): detect jam | %.2f %% ( %.2f / %.2f )" % ( self.mname, self.name, delta_usage / self.base_usage * 100.0, delta_usage, self.base_usage, ) )
                self.gcode.respond_info( "%s(%s): detect jam" % (self.mname, self.name) )
                if self.action:
                    # self.pause_resume.send_pause_command()
                    # self._exec_gcode("PAUSE")
                    if self.jam_gcode:
                        self._exec_gcode(self.jam_gcode)
                self.filament_usage_last = new_usage  # reset the filament_usage_last to avoide repeat trigger
                self.jam_triggered = False
            else:
                if self.debug:
                    logging.debug( "%s(%s): _timer_handler triggered | delta_usage = %s", self.mname, self.name, delta_usage, )
                if ( delta_usage > ( self.base_usage * 1.5 ) and self.timer_usage_last != new_usage ):  # ignore when it's not move
                    self.jam_triggered = True
                    if self.debug:
                        self.gcode.respond_info( "%s(%s): jam_triggered = True | %.2f %% ( %.2f / %.2f )" % ( self.mname, self.name, delta_usage / self.base_usage * 100.0, delta_usage, self.base_usage, ) )
            self.timer_usage_last = new_usage
        return eventtime + self.timer

    def get_filament_usage(self):
        theout = 0.0
        if self.extruder:
            theout = self.extruder.stepper.get_commanded_position()
        return float(theout)

    def _exec_gcode(self, script):
        try:
            self.gcode.run_script(script)
        except Exception:
            logging.exception("Script running error")

    def cmd_SET_FILAMENT_JAM_SENSOR(self, gcmd):
        self.timer = gcmd.get_float( "TIMER", self.timer, minval=0.0 )
        self.base_usage = gcmd.get_float( "BASE_USAGE", self.base_usage, minval=0.0, )
        self.enable = True if gcmd.get_int( "ENABLE", 1 if self.enable else 0 ) == 1 else False
        self.debug = True if gcmd.get_int( "DEBUG", 1 if self.debug else 0 ) == 1 else False
        self.action = True if gcmd.get_int( "ACTION", 1 if self.action else 0 ) == 1 else False
        gcmd.respond_info( "%s(%s): timer = %.2f | base_usage = %.2f | enable = %s | debug = %s | action = %s"
            % ( self.mname, self.name, self.timer, self.base_usage, self.enable, self.debug, self.action, ) )
        # reset some counter
        self.timer_usage_last = self.filament_usage_last = self.get_filament_usage()


def load_config_prefix(config):
    return JamSensor(config)
