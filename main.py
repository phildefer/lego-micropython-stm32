import time
from time import sleep

from pylgbst import *
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor, Current, Voltage, COLORS, COLOR_BLACK

log = logging.getLogger("demo")

def demo_led_colors(movehub):
    # LED colors demo
    log.info("LED colors demo")

    # We get a response with payload and port, not x and y here...
    def colour_callback(named):
        log.info("LED Color callback: %s", named)

    movehub.led.subscribe(colour_callback)
    for color in list(COLORS.keys())[1:] + [COLOR_BLACK]:
        log.info("Setting LED color to: %s", COLORS[color])
        movehub.led.set_color(color)
        sleep(1)

    #movehub.led.unsubscribe(colour_callback)

def demo_motors_timed(movehub):
    log.info("Motors movement demo: timed")
    for level in range(0, 101, 10):
        level /= 100.0
        log.info("Speed level: %s%%", level * 100)
        movehub.motor_A.timed(0.2, level)
        movehub.motor_B.timed(0.2, -level)
    movehub.motor_AB.timed(1.5, -0.2, 0.2)
    movehub.motor_AB.timed(0.5, 1)
    movehub.motor_AB.timed(0.5, -1)

def demo_voltage(movehub):
    def callback1(value):
        log.info("Amperage: %s", value)

    def callback2(value):
        log.info("Voltage: %s", value)

    movehub.current.subscribe(callback1, mode=Current.CURRENT_L, granularity=0)
    movehub.current.subscribe(callback1, mode=Current.CURRENT_L, granularity=1)

    movehub.voltage.subscribe(callback2, mode=Voltage.VOLTAGE_L, granularity=0)
    movehub.voltage.subscribe(callback2, mode=Voltage.VOLTAGE_L, granularity=1)
    time.sleep(5)
    movehub.current.unsubscribe(callback1)
    movehub.voltage.unsubscribe(callback2)

def demo_color_sensor(movehub):
    log.info("Color sensor test: wave your hand in front of it")
    count = 0
    limit = 20

    def callback(color):
        log.info("Color: %s",color[0])

    movehub.vision_sensor.subscribe(callback)
    while count < limit:
        count+=1
        time.sleep(1)

    movehub.vision_sensor.unsubscribe(callback)

def demo_tilt_sensor_precise(movehub):
    log.info("Tilt sensor precise test. Turn device in different ways.")
    cnt = 0
    limit = 10

    def callback(Mylist): 
        log.info("Tilt:%s, %s, %s",Mylist[0],Mylist[1],Mylist[2] )

    movehub.tilt_sensor.subscribe(callback, mode=TiltSensor.MODE_3AXIS_ACCEL)
    while cnt < limit:
        cnt += 1
        time.sleep(0,1)

    movehub.tilt_sensor.unsubscribe(callback)

def demo_tilt_sensor_simple(movehub):
    log.info("Tilt sensor simple test. Turn device in different ways.")
    cnt = 0
    limit = 10

    def callback(state):
        log.info("Tilt: %s=%s", TiltSensor.TRI_STATES[state[0]], state[0])

    movehub.tilt_sensor.subscribe(callback, mode=TiltSensor.MODE_3AXIS_SIMPLE)
    while cnt < limit:
        cnt += 1
        time.sleep(1)

    movehub.tilt_sensor.unsubscribe(callback)



def demo_port_cd_motor(movehub):
    motor = None
    if isinstance(movehub.port_D, EncodedMotor):
        log.info("Rotation motor is on port D")
        motor = movehub.port_D
    elif isinstance(movehub.port_C, EncodedMotor):
        log.info("Rotation motor is on port C")
        motor = movehub.port_C
    else:
        log.info("Motor not found on ports C or D")

    if motor:
        motor.angled(20, 0.2)
        sleep(3)
        motor.angled(20, -0.2)
        sleep(1)

        motor.angled(20, -0.1)
        sleep(2)
        motor.angled(20, 0.1)
        sleep(1)



if __name__ == '__main__':
    parameters = {}  
    hub = MoveHub(**parameters)
    demo_led_colors(hub)
    demo_voltage(hub)
    demo_motors_timed(hub)
    demo_color_sensor(hub)
    demo_port_cd_motor(hub)
    demo_tilt_sensor_precise(hub)
    demo_tilt_sensor_simple(hub)
    #


    