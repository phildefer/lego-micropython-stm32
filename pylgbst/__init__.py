#import logging
#import traceback

#from pylgbst.comms import DebugServer

#log = logging.getLogger('pylgbst')


def get_connection_bluegiga(controller=None, hub_mac=None, hub_name=None):
    del controller  # to prevent code analysis warning
    from pylgbst.comms.cpygatt import BlueGigaConnection

    return BlueGigaConnection().connect(hub_mac, hub_name)


def get_connection_gattool(controller='hci0', hub_mac=None, hub_name=None):
    from pylgbst.comms.cpygatt import GattoolConnection

    return GattoolConnection(controller).connect(hub_mac, hub_name)


def get_connection_gatt(controller='hci0', hub_mac=None, hub_name=None):
    from pylgbst.comms.cgatt import GattConnection

    return GattConnection(controller).connect(hub_mac, hub_name)


def get_connection_gattlib(controller='hci0', hub_mac=None, hub_name=None):
    from pylgbst.comms.cgattlib import GattLibConnection

    return GattLibConnection(controller).connect(hub_mac, hub_name)


def get_connection_bluepy(controller='hci0', hub_mac=None, hub_name=None):
    from pylgbst.comms.cbluepy import BluepyConnection

    return BluepyConnection(controller).connect(hub_mac, hub_name)

def get_connection_stm32(controller='hci0', hub_mac=None, hub_name=None):
    from pylgbst.comms.ble_sensor import STM32Connection
    conn = STM32Connection(controller)
    if conn is None:
        print("Unable to initialize STM32WB55 Connection")
        return None
    conn.connect()
    return conn


def get_connection_bleak(controller='hci0', hub_mac=None, hub_name=None):
    """
    Return connection based with Bleak API as an endpoint.

    :param controller: Not used, kept for compatibility with others.
    :param hub_mac: Optional Lego HUB MAC to connect to.
    :return: Driver object.
    """
    del controller  # to prevent code analysis warning
    from pylgbst.comms.cbleak import BleakDriver

    return BleakDriver(hub_mac, hub_name)


def get_connection_auto(controller='hci0', hub_mac=None, hub_name=None):
    fns = [
        get_connection_bluepy,
        get_connection_bluegiga,
        get_connection_gatt,
        get_connection_bleak,
        get_connection_gattool,
        get_connection_gattlib,
        get_connection_stm32,
    ]

    conn = None
    """
    for fn in fns:
        try:
            print("Trying %s", fn.__name__)
            conn = fn(controller, hub_mac, hub_name)
        except KeyboardInterrupt:
            raise
        except BaseException:
            print("Failed")
    """
    conn = get_connection_stm32(controller, hub_mac, hub_name)
    if conn is None:
        print("Failed to autodetect connection, make sure you have installed prerequisites")

    print("Succeeded with %s", conn.__class__.__name__)
    return conn

