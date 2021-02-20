import time
from time import sleep

from pylgbst import *
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor, Current, Voltage, COLORS, COLOR_BLACK


def demo_led_colors(movehub):
    # LED colors demo
    print("LED colors demo")

    # We get a response with payload and port, not x and y here...
    def colour_callback(named):
        print("LED Color callback: ", named)

    movehub.led.subscribe(colour_callback)
    while True:
        for color in list(COLORS.keys())[1:] + [COLOR_BLACK]:
            print("Setting LED color to: %s", COLORS[color])
            movehub.led.set_color(color)
            sleep(1)


def demo_motors_timed(movehub):
    print("Motors movement demo: timed")
    for level in range(0, 101, 10):
        level /= 100.0
        print("Speed level: ", level * 100)
        movehub.motor_A.timed(0.2, level)
        movehub.motor_B.timed(0.2, -level)
    movehub.motor_AB.timed(1.5, -0.2, 0.2)
    movehub.motor_AB.timed(0.5, 1)
    movehub.motor_AB.timed(0.5, -1)

def demo_voltage(movehub):
    def callback1(value):
        print("Amperage: ", value)

    def callback2(value):
        print("Voltage: ", value)

    print("Callback: ",callback1)
    #movehub.current.subscribe(callback1, mode=Current.CURRENT_L, granularity=0)
    movehub.current.subscribe(callback1, mode=Current.CURRENT_L, granularity=0)

    #movehub.voltage.subscribe(callback2, mode=Voltage.VOLTAGE_L, granularity=0)
    movehub.voltage.subscribe(callback2, mode=Voltage.VOLTAGE_L, granularity=1)
    time.sleep(5)
    movehub.current.unsubscribe(callback1)
    movehub.voltage.unsubscribe(callback2)

def demo_color_sensor(movehub):
    print("Color sensor test: wave your hand in front of it")
    count = 0
    limit = 20

    def callback(color):
        print("Color: ",color)

    movehub.vision_sensor.subscribe(callback)
    while count < limit:
        count+=1
        time.sleep(1)

    movehub.vision_sensor.unsubscribe(callback)

def demo_tilt_sensor_precise(movehub):
    print("Tilt sensor precise test. Turn device in different ways.")
    cnt = 0
    limit = 50

    def callback(pitch, roll, yaw):
        cnt += 1
        print("Tilt #%s of %s: roll:%s pitch:%s yaw:%s", cnt, limit, pitch, roll, yaw)

    movehub.tilt_sensor.subscribe(callback, mode=TiltSensor.MODE_3AXIS_ACCEL)
    while cnt < limit:
        time.sleep(1)

    movehub.tilt_sensor.unsubscribe(callback)

if __name__ == '__main__':
    parameters = {}  
    hub = MoveHub(**parameters)
    #demo_led_colors(hub)
    #demo_voltage(hub)
    #demo_motors_timed(hub)
    demo_color_sensor(hub)
    #demo_tilt_sensor_precise(hub)

    