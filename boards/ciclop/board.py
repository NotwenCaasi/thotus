# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2016 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import time
import serial
import threading

import logging
logger = logging.getLogger(__name__)

from thotus import settings

class WrongFirmware(Exception):

    def __init__(self):
        Exception.__init__(self, "Wrong Firmware")

class BoardNotConnected(Exception):

    def __init__(self):
        Exception.__init__(self, "Board Not Connected")

class OldFirmware(Exception):

    def __init__(self):
        Exception.__init__(self, "Old Firmware")

class Board(object):

    """Board class. For accessing to the scanner board

    Gcode commands:

        G1 Fnnn : feed rate
        G1 Xnnn : move motor
        G50     : reset origin position

        M70 Tn  : switch off laser n
        M71 Tn  : switch on laser n

        M50 Tn  : read ldr sensor
    """

    def __init__(self, parent=None, serial_name='/dev/ttyUSB0', baud_rate=19200):
        self.parent = parent
        self.serial_name = serial_name
        self.baud_rate = baud_rate
        self.unplug_callback = None

        self._serial_port = None
        self._is_connected = False
        self._motor_enabled = False
        self._motor_position = 0
        self._motor_speed = 0
        self._motor_acceleration = 0
        self._motor_direction = 1
        self._laser_number = 2
        self._laser_enabled = self._laser_number * [False]
        self._tries = 0  # Check if command fails

    def connect(self):
        """Open serial port and perform handshake"""
        logger.info("Connecting board {0} {1}".format(self.serial_name, self.baud_rate))
        self._is_connected = False
        try:
            print('0a')
            print(self.serial_name)
            print(self.baud_rate)
            self._serial_port = serial.Serial(self.serial_name, self.baud_rate, timeout=2)
            print('0b')
            if self._serial_port.isOpen():
                print('1a')
                self._reset()  # Force Reset and flush
                print('1b')
                version = self._serial_port.readline()
                print('1c')
                if b"Horus 0.1 ['$' for help]" in version:
                    print('1d')
                    raise OldFirmware()
                elif b"Horus 0.2 ['$' for help]" in version:
                    print('1e1')
                    self.motor_speed(1)
                    print('1e2')
                    self._serial_port.timeout = 0.05
                    print('1e3')
                    self._is_connected = True
                    print('1e4')
                    # Set current position as origin
                    print('1e5')
                    self.motor_reset_origin()
                    print('1e6')
                    logger.info(" Done")
                else:
                    print('1f')
                    raise WrongFirmware()
            else:
                print('2a')
                raise BoardNotConnected()
        except Exception as exception:
            print('3a')
            if self.serial_name == None:
                logger.error("No board detected!\n")
            else:
                logger.error("Error opening the port {0}\n".format(self.serial_name))
            self._serial_port = None
            raise exception

    def disconnect(self):
        """Close serial port"""
        if self._is_connected:
            logger.info("Disconnecting board {0}".format(self.serial_name))
            try:
                if self._serial_port is not None:
                    self.lasers_off()
                    self.motor_disable()
                    self._is_connected = False
                    self._serial_port.close()
                    del self._serial_port
            except serial.SerialException:
                logger.error("Error closing the port {0}\n".format(self.serial_name))
            logger.info(" Done")

    def motor_speed(self, value):
        if self._is_connected:
            if self._motor_speed != value:
                self._motor_speed = value
                self._send_command("G1F{0}".format(value))

    def motor_acceleration(self, value):
        if self._is_connected:
            if self._motor_acceleration != value:
                self._motor_acceleration = value
                self._send_command("$120={0}".format(value))

    def motor_enable(self):
        if self._is_connected:
            if not self._motor_enabled:
                self._motor_enabled = True
                # Save current speed value
                speed = self._motor_speed
                self.motor_speed(1)
                # Enable stepper motor
                self._send_command("M17")
                time.sleep(1)
                # Restore speed value
                self.motor_speed(speed)

    def motor_disable(self):
        if self._is_connected:
            if self._motor_enabled:
                self._motor_enabled = False
                self._send_command("M18")

    def motor_reset_origin(self):
        if self._is_connected:
            self._send_command("G50")
            self._motor_position = 0

    def motor_move(self, step=0, nonblocking=False, callback=None):
        if self._is_connected:
            self._motor_position += step * self._motor_direction
            self.send_command("G1X{0}".format(self._motor_position), nonblocking, callback)

    def laser_on(self, index):
        if self._is_connected:
            if not self._laser_enabled[index]:
                self._laser_enabled[index] = True
                self._send_command("M71T" + str(index + 1))

    def laser_off(self, index):
        if self._is_connected:
            if self._laser_enabled[index]:
                self._laser_enabled[index] = False
                self._send_command("M70T" + str(index + 1))

    def lasers_on(self):
        for i in settings.get_laser_range():
            self.laser_on(i)

    def lasers_off(self):
        for i in range(self._laser_number):
            self.laser_off(i)

    def send_command(self, req, nonblocking=False, callback=None, read_lines=False):
        if nonblocking:
            threading.Thread(target=self._send_command,
                             args=(req, callback, read_lines)).start()
        else:
            self._send_command(req, callback, read_lines)

    def _send_command(self, req, callback=None, read_lines=False):
        """Sends the request and returns the response"""
        ret = ''
        req = req.encode('ascii')
        if self._is_connected and req != '':
            if self._serial_port is not None and self._serial_port.isOpen():
                try:
                    self._serial_port.flushInput()
                    self._serial_port.flushOutput()
                    self._serial_port.write(req + b"\r\n")
                    while req != b'~' and req != b'!' and ret == b'':
                        ret = self.read(read_lines)
                        time.sleep(0.01)
                    self._success()
                except:
                    if hasattr(self, '_serial_port'):
                        if callback is not None:
                            callback(ret.decode('ascii'))
                        self._fail()
        if callback is not None:
            callback(ret)
        return ret

    def read(self, read_lines=False):
        if read_lines:
            return ''.join(self._serial_port.readlines())
        else:
            return ''.join(self._serial_port.readline())

    def _success(self):
        self._tries = 0

    def _fail(self):
        if self._is_connected:
            logger.debug("Board fail")
            self._tries += 1
            if self._tries >= 3:
                self._tries = 0
                if self.unplug_callback is not None and \
                   self.parent is not None and \
                   not self.parent.unplugged:
                    self.parent.unplugged = True
                    self.unplug_callback()

    def _reset(self):
        self._serial_port.flushInput()
        self._serial_port.flushOutput()
        self._serial_port.write(b"\x18\r\n")  # Ctrl-x
        self._serial_port.readline()

