#import threading
import time

from pylgbst import get_connection_auto
from pylgbst.messages import *
from pylgbst.peripherals import *
#from pylgbst.utilities import queue
from pylgbst.utilities import str2hex, usbyte, ushort

#log = logging.getLogger('hub')

PERIPHERAL_TYPES = {
    MsgHubAttachedIO.DEV_MOTOR: Motor,
    MsgHubAttachedIO.DEV_MOTOR_EXTERNAL_TACHO: EncodedMotor,
    MsgHubAttachedIO.DEV_MOTOR_INTERNAL_TACHO: EncodedMotor,
    MsgHubAttachedIO.DEV_VISION_SENSOR: VisionSensor,
    MsgHubAttachedIO.DEV_RGB_LIGHT: LEDRGB,
    MsgHubAttachedIO.DEV_TILT_EXTERNAL: TiltSensor,
    MsgHubAttachedIO.DEV_TILT_INTERNAL: TiltSensor,
    MsgHubAttachedIO.DEV_CURRENT: Current,
    MsgHubAttachedIO.DEV_VOLTAGE: Voltage,
}


class Hub(object):
    """
    :type connection: pylgbst.comms.Connection
    :type peripherals: dict[int,Peripheral]
    """
    HUB_HARDWARE_HANDLE = 0x0E

    def __init__(self, connection=None):
        self._msg_handlers = []
        self.peripherals = {}
        self._sync_request = None
        self._sync_replies = None

        self.add_message_handler(MsgHubAttachedIO, self._handle_device_change)
        self.add_message_handler(MsgPortValueSingle, self._handle_sensor_data)
        self.add_message_handler(MsgPortValueCombined, self._handle_sensor_data)
        self.add_message_handler(MsgGenericError, self._handle_error)
        self.add_message_handler(MsgHubAction, self._handle_action)

        if not connection:
            connection = get_connection_auto()  # TODO: how to identify the hub?
        self.connection = connection
        self.connection.set_notify_handler(self._notify)
        #if self.connection.is_alive() == False:
        #print("Wait for 2 seconds!")
        time.sleep(2) # WORKAROUND
        self.connection.enable_notifications()

    def __del__(self):
        if self.connection and self.connection.is_alive():
            print("Disconnecting ...")
            self.connection.disconnect()

    def add_message_handler(self, classname, callback):
        self._msg_handlers.append((classname, callback))

    def send(self, msg):
        """
        :type msg: pylgbst.messages.DownstreamMsg
        :rtype: pylgbst.messages.UpstreamMsg
        """
        #log.debug("Send message: %r", msg)
        msgbytes = msg.bytes()
        if msg.needs_reply == True:
            self._sync_request = msg
            self.connection.write(self.HUB_HARDWARE_HANDLE, msgbytes)

            while self._sync_replies == None:
                time.sleep(0.1)
            resp = self._sync_replies
            self._sync_replies = None;
            #print("Fetched sync reply: %r", resp)
            if isinstance(resp, MsgGenericError):
                raise RuntimeError(resp.message())
            return resp
        else:
            self.connection.write(self.HUB_HARDWARE_HANDLE, msgbytes)
            print("Message w/o reply sent")
            return None

    def _notify(self, handle, data):
        #print("Notification on", handle ,"with data: ", str2hex(data))
        
        msg = self._get_upstream_msg(data)

        if self._sync_request:
            if self._sync_request.is_reply(msg):
                print("Found matching upstream msg")
                self._sync_replies = msg
                self._sync_request = None

        for msg_class, handler in self._msg_handlers:
            if isinstance(msg, msg_class):
                #print("Handling msg with %s: %r", handler, msg)
                handler(msg)

    def _get_upstream_msg(self, data):
        msg_type = usbyte(data, 2)
        #print("Message Type: ",msg_type)
        msg = None
        for msg_kind in UPSTREAM_MSGS:
            if msg_type == msg_kind.TYPE:
                msg = msg_kind.decode(msg_kind,data)
                #print("Decoded message: %r", msg)
                break
        assert msg
        return msg

    def _handle_error(self, msg):
        #log.warning("Command error: %s", msg.message())
        if self._sync_request:
            self._sync_request = None
            self._sync_replies = msg

    def _handle_action(self, msg):
        """
        :type msg: MsgHubAction
        """
        if msg.action == MsgHubAction.UPSTREAM_DISCONNECT:
            #log.warning("Hub disconnects")
            self.connection.disconnect()
        elif msg.action == MsgHubAction.UPSTREAM_SHUTDOWN:
            #log.warning("Hub switches off")
            self.connection.disconnect()

    def _handle_device_change(self, msg):
        if msg.event == MsgHubAttachedIO.EVENT_DETACHED:
            #log.debug("Detaching peripheral: %s", self.peripherals[msg.port])
            self.peripherals.pop(msg.port)
            return

        assert msg.event in (msg.EVENT_ATTACHED, msg.EVENT_ATTACHED_VIRTUAL)
        port = msg.port
        dev_type = ushort(msg.payload, 0)
        #print("port: ", port, "device: ",dev_type)

        if dev_type in PERIPHERAL_TYPES:
            self.peripherals[port] = PERIPHERAL_TYPES[dev_type](self, port)
        else:
            print("Have not dedicated class for peripheral type %x on port %x", dev_type, port)
            self.peripherals[port] = Peripheral(self, port)

        print("Attached peripheral: ", self.peripherals[msg.port])

        if msg.event == msg.EVENT_ATTACHED:
            hw_revision = reversed([usbyte(msg.payload, x) for x in range(2, 6)])
            sw_revision = reversed([usbyte(msg.payload, x) for x in range(6, 10)])
            # what to do with this info? it's useless, I guess
            del hw_revision, sw_revision
        elif msg.event == msg.EVENT_ATTACHED_VIRTUAL:
            self.peripherals[port].virtual_ports = (usbyte(msg.payload, 2), usbyte(msg.payload, 3))

    def _handle_sensor_data(self, msg):
        assert isinstance(msg, (MsgPortValueSingle, MsgPortValueCombined))
        if msg.port not in self.peripherals:
            print("Notification on port with no device: ", msg.port)
            return
        device = self.peripherals[msg.port]
        device.queue_port_data(msg)

    def disconnect(self):
        self.send(MsgHubAction(MsgHubAction.DISCONNECT))

    def switch_off(self):
        self.send(MsgHubAction(MsgHubAction.SWITCH_OFF))


class MoveHub(Hub):
    """
    Class implementing Lego Boost's MoveHub specifics

    :type led: LEDRGB
    :type tilt_sensor: TiltSensor
    :type button: Button
    :type current: Current
    :type voltage: Voltage
    :type vision_sensor: pylgbst.peripherals.VisionSensor
    :type port_C: Peripheral
    :type port_D: Peripheral
    :type motor_A: EncodedMotor
    :type motor_B: EncodedMotor
    :type motor_AB: EncodedMotor
    :type motor_external: EncodedMotor
    """

    DEFAULT_NAME = "LEGO Move Hub"

    # PORTS
    PORT_A = 0x00
    PORT_B = 0x01
    PORT_C = 0x02
    PORT_D = 0x03
    PORT_AB = 0x10
    PORT_LED = 0x32
    PORT_TILT_SENSOR = 0x3A
    PORT_CURRENT = 0x3B
    PORT_VOLTAGE = 0x3C

    # noinspection PyTypeChecker
    def __init__(self, connection=None):
        self._comm_lock = None #threading.RLock()
        if connection is None:
            connection = get_connection_auto(hub_name=self.DEFAULT_NAME)

        super(MoveHub, self).__init__(connection)
        self.info = {}

        # shorthand fields
        self.button = Button(self)
        self.led = None
        self.current = None
        self.voltage = None
        self.motor_A = None
        self.motor_B = None
        self.motor_AB = None
        self.vision_sensor = None
        self.tilt_sensor = None
        self.motor_external = None
        self.port_C = None
        self.port_D = None

        self._wait_for_devices()
        self._report_status()

    def _wait_for_devices(self, get_dev_set=None):
        if not get_dev_set:
            get_dev_set = lambda: (self.motor_A, self.motor_B, self.motor_AB, self.led, self.tilt_sensor,
                                   self.current, self.voltage)
        for num in range(0, 100):
            devices = get_dev_set()
            if all(devices):
                print("All devices are present: %s", devices)
                return
            #print("Waiting for builtin devices to appear: %s", devices)
            time.sleep(0.1)
        print("Got only these devices: %s", get_dev_set())

    def _report_status(self):
        # maybe add firmware version
        name = self.send(MsgHubProperties(MsgHubProperties.ADVERTISE_NAME, MsgHubProperties.UPD_REQUEST))
        #time.sleep(1)
        mac = self.send(MsgHubProperties(MsgHubProperties.PRIMARY_MAC, MsgHubProperties.UPD_REQUEST))
        #print("%s on %s", name.payload, str2hex(mac.payload))
        #time.sleep(1)

        voltage = self.send(MsgHubProperties(MsgHubProperties.VOLTAGE_PERC, MsgHubProperties.UPD_REQUEST))
        assert isinstance(voltage, MsgHubProperties)
        #print("Voltage: %s%%", usbyte(voltage.parameters, 0))
        #time.sleep(1)

        voltage = self.send(MsgHubAlert(MsgHubAlert.LOW_VOLTAGE, MsgHubAlert.UPD_REQUEST))
        #time.sleep(1)
        #print("Hello :", voltage)
        assert isinstance(voltage, MsgHubAlert)
        if voltage != None:
            if not voltage.is_ok():
                print("Low voltage, check power source (maybe replace battery)")

    # noinspection PyTypeChecker
    def _handle_device_change(self, msg):
        if self._comm_lock == None:
            super(MoveHub, self)._handle_device_change(msg)
            if isinstance(msg, MsgHubAttachedIO) and msg.event != MsgHubAttachedIO.EVENT_DETACHED:
                port = msg.port
                if port == self.PORT_A:
                    self.motor_A = self.peripherals[port]
                elif port == self.PORT_B:
                    self.motor_B = self.peripherals[port]
                elif port == self.PORT_AB:
                    self.motor_AB = self.peripherals[port]
                elif port == self.PORT_C:
                    self.port_C = self.peripherals[port]
                elif port == self.PORT_D:
                    self.port_D = self.peripherals[port]
                elif port == self.PORT_LED:
                    self.led = self.peripherals[port]
                elif port == self.PORT_TILT_SENSOR:
                    self.tilt_sensor = self.peripherals[port]
                elif port == self.PORT_CURRENT:
                    self.current = self.peripherals[port]
                elif port == self.PORT_VOLTAGE:
                    self.voltage = self.peripherals[port]

                if type(self.peripherals[port]) == VisionSensor:
                    self.vision_sensor = self.peripherals[port]
                elif type(self.peripherals[port]) == EncodedMotor \
                        and port not in (self.PORT_A, self.PORT_B, self.PORT_AB):
                    self.motor_external = self.peripherals[port]


class TrainHub(Hub):
    DEFAULT_NAME = 'TrainHub'

    def __init__(self, connection=None):
        if connection is None:
            connection = get_connection_auto(hub_name=self.DEFAULT_NAME)
        super(TrainHub, self).__init__(connection)
