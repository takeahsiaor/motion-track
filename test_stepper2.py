# from time import sleep
# import pigpio

# DIR = 17     # Direction GPIO Pin
# STEP = 27    # Step GPIO Pin
# #SWITCH = 16  # GPIO pin of switch

# # Connect to pigpiod daemon
# pi = pigpio.pi()

# # Set up pins as an output
# pi.set_mode(DIR, pigpio.OUTPUT)
# pi.set_mode(STEP, pigpio.OUTPUT)

# # Set up input switch
# #pi.set_mode(SWITCH, pigpio.INPUT)
# #pi.set_pull_up_down(SWITCH, pigpio.PUD_UP)

# # Set duty cycle and frequency
# pi.set_PWM_dutycycle(STEP, 128)  # PWM 1/2 On 1/2 Off
# pi.set_PWM_frequency(STEP, 2400)  # 500 pulses per second


# try:
#     while True:
#         pi.write(DIR, 1)  # Set direction
#         sleep(.1)

# except KeyboardInterrupt:
#     print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
# finally:
#     pi.set_PWM_dutycycle(STEP, 0)  # PWM off
#     pi.stop()

import pigpio
DIR = 17     # Direction GPIO Pin
STEP = 27    # Step GPIO Pin
# Connect to pigpiod daemon
pi = pigpio.pi()

# Set up pins as an output
pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)

# Set duty cycle and frequency
# pi.set_PWM_dutycycle(STEP, 128)  # PWM 1/2 On 1/2 Off
# pi.set_PWM_frequency(STEP, 2400)  # 500 pulses per second

def generate_ramp(ramp):
    """Generate ramp wave forms.
    ramp:  List of [Frequency, Steps]
    """
    pi.wave_clear()     # clear existing waves
    length = len(ramp)  # number of ramp levels
    wid = [-1] * length

    # Generate a wave per ramp level
    for i in range(length):
        frequency = ramp[i][0]
        micros = int(500000 / frequency)
        wf = []
        wf.append(pigpio.pulse(1 << STEP, 0, micros))  # pulse on
        wf.append(pigpio.pulse(0, 1 << STEP, micros))  # pulse off
        pi.wave_add_generic(wf)
        wid[i] = pi.wave_create()

    # Generate a chain of waves
    chain = []
    for i in range(length):
        steps = ramp[i][1]
        x = steps & 255
        y = steps >> 8
        chain += [255, 0, wid[i], 255, 1, x, y]

    pi.wave_chain(chain)  # Transmit chain

RAMP_UP = (
    (250, 50),
    (320, 100),
    (400, 150),
    (500, 200),
    (800, 300),
    (1000, 400),
    (1600, 600),
    (2000, 1000)
)

def move_stepper(total_steps, direction):
    pi.write(DIR, direction)

    ramp = []
    steps_left = total_steps / 2
    # Build acceleration
    for frequency, steps in RAMP_UP:
        if steps > steps_left:
            ramp.append((frequency, steps_left))
            steps_left = 0
            break
        else:
            ramp.append((frequency, steps))
            steps_left -= steps
    if steps_left:
        # Continue for the rest of the total steps at max speed
        ramp.append(RAMP_UP[-1][0], steps_left)

    # build deceleration
    full_ramp = list(ramp)
    while ramp:
        full_ramp.append(ramp.pop())

    generate_ramp(full_ramp)

move_stepper(2000, 1)
move_stepper(2000, 0)
