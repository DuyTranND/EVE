import random
import signal
import time
import logging
from multiprocessing import Process
from threading import Thread

import RPi.GPIO as GPIO

from src.settings import settings
from src.domain import EXPRESSION_NAMES, Expression, RobotMode
from src.logging_config import configure_logging
from src.utilities.audio_playback import play_sound
from src.utilities.robot_behaviors import (
    follow_process,
    go_around_process,
    got_error,
    hi,
    low_battery,
    mumble,
    range_leg,
    save_friendly,
    sigh,
    touch_setup,
    vc_setup,
)
from src.runtime.state import (
    acting,
    battery,
    cam,
    com,
    err,
    express,
    friendly,
    lcd,
    look_around,
    low_battery_count,
    mqtt,
    rgb,
    running,
    state,
    initialize_hardware,
)

logger = logging.getLogger(__name__)


def request_shutdown(signum, frame):
    """Ask all workers to stop after SIGINT or SIGTERM."""
    running.clear()
        
def lcd_process():
    while running.is_set():
        try:
            if lcd.current_express in {"idle_optimus", "idle_optimus_alt"}:
                if lcd.current_index == 1:
                    lcd.fps = 10
                elif lcd.current_index == len(lcd.package[lcd.current_express]) - 1:
                    lcd.fps = 16

            expression = EXPRESSION_NAMES[express.value]
            lcd.show_expression(expression)

            if "idle_" in expression and lcd.current_index == len(lcd.package[lcd.current_express]) - 1:
                with express.get_lock():
                    express.value = Expression.IDLE

            if lcd.current_express == "idle_05" and lcd.current_index == 0:
                look_around.set()
                time.sleep(0.2)

            if express.value == Expression.BYE and lcd.current_index == len(lcd.package[lcd.current_express]) - 1:
                lcd.switch(on = False)

            if lcd.current_express == "paint_to_idle" and lcd.current_index == 14:
                time.sleep(10)

        except Exception:
            err.set()
            logger.exception("LCD worker failed")
        
def battery_process():
    while running.is_set():
        try:
            data = com.read_serial()
            if data != "":
                if "Battery" in data:
                    voltage = data.split(":")[-1]
                    voltage = float(voltage)
                    battery_percent = - 27.318 * voltage * voltage + 703.36 * voltage - 4428.1
                    with battery.get_lock():
                        battery.value = max(5, min(100, int(battery_percent)))

                    if battery.value <= 20:
                        with low_battery_count.get_lock():
                            low_battery_count.value = low_battery_count.value + 1
                    else:
                        with low_battery_count.get_lock():
                            low_battery_count.value = 0
        except Exception:
            err.set()
            logger.exception("Battery worker failed")

def upload_image_process():
    while running.is_set():
        try:
            if state.value in (RobotMode.GO_AROUND, RobotMode.FOLLOW):
                frame = cam.get_image()
                encoded_image = cam.encode_image(frame, quality = 60)
                mqtt.upload_image(encoded_image)
        except Exception:
            err.set()
            logger.exception("Camera upload worker failed")
        time.sleep(0.02)

def stop_holding_process():
    this_timer = time.perf_counter()
    stop_holding = True
    while running.is_set():
        try:
            if not acting.is_set():
                if stop_holding:
                    if time.perf_counter() - this_timer >= 0.25:
                        if com.ll.value == 0 and com.rl.value == 0 and com.le.value  == 0 and com.re.value == 0:
                            com.stop_all()
                            stop_holding = False
                        this_timer = time.perf_counter()
                else:
                    if time.perf_counter() - this_timer >= 3.0:
                        if com.ll.value == 0 and com.rl.value == 0 and com.le.value == 0 and com.re.value  == 0:
                            com.set_ear(0, 0)
                            com.set_leg(0, 0)
                            stop_holding = True
                        this_timer = time.perf_counter()
            else:
                stop_holding = True
                this_timer = time.perf_counter()

        except Exception:
            err.set()
            logger.exception("Servo holding worker failed")
        time.sleep(0.01)

def main():
    configure_logging()
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    initialize_hardware()
    acting.set()

    # Create a process for battery calculation
    battery_instance = Process(target = battery_process)
    battery_instance.start()

    # Create a process for image capturing
    upload_image_instance = Thread(target = upload_image_process)
    upload_image_instance.start()

    # Create a process for the lcd display
    lcd_instance = Process(target = lcd_process)

    touch_setup()
    vc_setup()

    com.send_motor_speed(0, 0)
    com.set_ear(0, 0)
    com.set_leg(0, 0)

    # Mumble timing
    sound_timing = time.perf_counter()
    sound_waiting = random.randint(180, 240)

    do_hi = False
    do_sigh = False

    friendly_value = friendly.value
    if friendly_value < 30:
        do_sigh = True
    elif friendly_value < 50:
        do_sigh = random.choices([True, False], [0.3, 0.7])[0]
    else:
        do_sigh = False
    
    if do_sigh:
        sigh()
        lcd_instance.start()
        for i in range(100, -1, -1):
            rgb.light = i
            rgb.set_battery()
            time.sleep(0.04)
        
    else:
        do_hi = random.choices([True, False], [0.5, 0.5])[0]
        hi()
        lcd_instance.start()
    
    rgb.light = 100
    rgb.set_battery()

    if do_hi:
        which_leg = random.choice([1, -1])
        range_leg(0, 15 * which_leg, 0 , -15 * which_leg, 100, 0.6)
        time.sleep(2)
        range_leg(15 * which_leg, 0 , -15 * which_leg, 0, 100, 0.6)

    acting.clear()

    # Stop holding process
    stop_holding_instance = Process(target = stop_holding_process)
    stop_holding_instance.start()

    try:  
        while running.is_set():
            if look_around.is_set():
                acting.set()
                play_sound(settings.paths.sounds / "look_around.wav", wait=True)
                look_around.clear()
                acting.clear()

            if low_battery_count.value >= 8:
                if not acting.is_set():
                    low_battery()

                    with low_battery_count.get_lock():
                        low_battery_count.value = 0
                else:
                    with low_battery_count.get_lock():
                        low_battery_count.value = 4

            if battery.value != rgb.light:
                rgb.light = battery.value 
                if not acting.is_set():
                    rgb.set_battery()

            if state.value == RobotMode.STAND_STILL:
                # Mumble
                if time.perf_counter() - sound_timing >= sound_waiting:
                    if not acting.is_set():
                        acting.set()
                        sound_timing = time.perf_counter()
                        sound_waiting = random.randint(180, 240)

                        friendly_value = friendly.value
                        if friendly_value < 30:
                            sigh()
                        else:
                            mumble()
                        acting.clear()
                    else:
                        sound_timing = time.perf_counter()

            elif state.value == RobotMode.FOLLOW:
                ee, rr = mqtt.track
                if ee == -999 or rr == -999:
                    with express.get_lock():
                        express.value = Expression.SAD
                else:
                    follow_process(ee, rr)
            elif state.value == RobotMode.GO_AROUND:
                ll, ff, rr = mqtt.depth
                if ll != -1.0 and ff != -1.0 and rr != -1.0:
                    go_around_process(ll, ff, rr)

            if com.error:
                pass
                # err.set()

            if err.is_set():
                got_error()

            time.sleep(0.01)

    except Exception:
        logger.exception("Unhandled error in the EVE control loop")
        err.set()
        got_error()
        
    finally:
        com.send_motor_speed(0, 0)
        # com.stop_ear()
        # com.stop_leg()

        save_friendly()
        running.clear()
        
        lcd_instance.join()
        battery_instance.join()
        upload_image_instance.join()
        stop_holding_instance.join()
        # mpu_instance.join()
        
        lcd.switch(on = False)
        rgb.stop()
        cam.stop_camera()
        mqtt.disconnect()
        GPIO.cleanup()

        # sys.exit(0)
        
if __name__ == "__main__":
    main()
