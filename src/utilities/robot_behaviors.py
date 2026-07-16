import ast
import time
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread

from src.runtime.state import (
    acting,
    animal_dictionary,
    cam,
    chatting,
    com,
    express,
    friendly,
    fuz,
    halucination,
    internet,
    lcd,
    length,
    mic,
    mqtt,
    opi,
    radius,
    rgb,
    state,
    w_m_max,
)
from src.settings import settings
from src.domain import Expression, RobotMode

import random
import re
import subprocess
import numpy as np
import cv2
import socket
import base64
from src.utilities.audio_playback import play_sound
from src.utilities.friendliness import save_friendliness
from src.utilities.image_processing import merge_image
from src.utilities.kinematics import differential_wheel_speeds

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

SOUND_DIR = settings.paths.sounds
OPENAI_DIR = settings.paths.openai_data
EXPRESSION_DIR = settings.paths.expressions
LATEST_CAMERA_IMAGE = settings.paths.latest_camera_image

def save_friendly():
    save_friendliness(settings.paths.friendliness, friendly.value)

def gain_friendly(value):
    with friendly.get_lock():
        friendly.value = min(max(friendly.value + value, 0), 100)

    save_friendly()

def reset_friendly():
    with friendly.get_lock():
        friendly.value = 70.0

    save_friendly()

def check_internet(host="8.8.8.8", port=53, timeout = 1):
    """
    Check if there is an internet connection by attempting to connect to a host.
    
    :param host: Host to connect to (default is Google's public DNS server).
    :param port: Port to connect to (default is 53).
    :param timeout: Timeout for the connection attempt in seconds (default is 3 seconds).
    :return: True if the connection is successful, False otherwise.
    """
    try:
        # Set default timeout for the socket
        socket.setdefaulttimeout(timeout)
        
        # Create and connect the socket using the 'with' statement for proper resource management
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            internet.set()
            return True
    except (socket.timeout, socket.error):
        # Log the exception if needed, e.g., print(f"Error: {ex}")
        internet.clear()
        return False

def check_server():
    mqtt.upload_state("check")
    time.sleep(0.1)
    if mqtt.status == "OK":
        mqtt.status = ""
        return True
    else:
        return False

def encode_image(img, quality = 20):
    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    encoded = base64.b64encode(buffer).decode('utf-8')
    return encoded

                                                            ################
                                                            ### VC - 02  ###
                                                            ################

def range_ear(start_left, stop_left, start_right, stop_right, step, duration):
    lefts = np.linspace(start_left, stop_left, step)
    rights = np.linspace(start_right, stop_right, step)

    for i in range(step):
        left = round(lefts[i], 2)
        right = round(rights[i], 2)
        com.set_ear(left, right)
        time.sleep(round(duration / step, 4))

def range_leg(start_left, stop_left, start_right, stop_right, step, duration):
    lefts = np.linspace(start_left, stop_left, step)
    rights = np.linspace(start_right, stop_right, step)

    for i in range(step):
        left = round(lefts[i], 2)
        right = round(rights[i], 2)
        com.set_leg(left, right)
        time.sleep(round(duration / step, 4))

def range_all(start_left_ear, stop_left_ear, start_right_ear, stop_right_ear, start_left_leg, stop_left_leg, start_right_leg, stop_right_leg, step, duration):
    ear_lefts = np.linspace(start_left_ear, stop_left_ear, step)
    ear_rights = np.linspace(start_right_ear, stop_right_ear, step)

    leg_lefts = np.linspace(start_left_leg, stop_left_leg, step)
    leg_rights = np.linspace(start_right_leg, stop_right_leg, step)

    for i in range(step):
        el = round(ear_lefts[i], 2)
        er = round(ear_rights[i], 2)
        ll = round(leg_lefts[i], 2)
        lr = round(leg_rights[i], 2)
        com.set_ear(el, er)
        com.set_leg(ll, lr)
        time.sleep(round(duration / step, 4))

# VC 02
vc_scl = 13       # B2 - SCL
vc_sda = 25       # B3 - SDA
vc_a27 = 26       # A27 
hearing_step    = 0.05     # s

def vc_a27_int(channel):
    hearing_start = time.perf_counter()
    while GPIO.input(vc_a27):
        continue
    hearing_stop = time.perf_counter()
    
    cmd = round((hearing_stop - hearing_start) / hearing_step, 2)
    
    if 0.6 <= cmd <= 1.4:
        # Wake up
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value
            if friendly_value < 20:
                what() 
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    what()
                else:
                    wake_up()
                    gain_friendly(-3)
            else:
                wake_up()
                gain_friendly(-3)
            
            acting.clear()

    elif 1.6 <= cmd <= 2.4:
        # Follow
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value
            if friendly_value < 30:
                no() 
                acting.clear()
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    acting.clear()
                    gain_friendly(5)
                else:
                    if check_internet():
                        if check_server():
                            gain_friendly(10)
                            follow()
                        else:
                            lost_server()
                            acting.clear()
                    else:
                        lost_connection()
                        acting.clear()
            else:
                if check_internet():
                    if check_server():
                        gain_friendly(10)
                        follow()
                    else:
                        lost_server()
                        acting.clear()
                else:
                    lost_connection()
                    acting.clear()

    elif 2.6 <= cmd <= 3.4:
        # What is this
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    if check_internet():
                        gain_friendly(-2)
                        what_is_this()
                    else:
                        lost_connection()
                        acting.clear()
                    
            else:
                if check_internet():
                    gain_friendly(-2)
                    what_is_this()
                else:
                    lost_connection()
                    acting.clear()

            acting.clear()

    elif 3.6 <= cmd <= 4.4:
        # Go around
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value
            if friendly_value < 30:
                no() 
                acting.clear()
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    acting.clear()
                    gain_friendly(5)
                else:
                    if check_internet():
                        if check_server():
                            gain_friendly(10)
                            go_around()
                        else:
                            lost_server()
                            acting.clear()
                    else:
                        lost_connection()
                        acting.clear()
                    
            else:
                if check_internet():
                    if check_server():
                        gain_friendly(10)
                        go_around()
                    else:
                        lost_server()
                        acting.clear()
                else:
                    lost_connection()
                    acting.clear()

    elif 4.6 <= cmd <= 5.4:
        # Stop moving
        stop()

    elif 5.6 <= cmd <= 6.4:
        # Shutdown
        if not acting.is_set():
            acting.set()
            shutdown()

    elif 6.6 <= cmd <= 7.4:
        # Restart
        if not acting.is_set():
            acting.set()
            reboot()

    elif 7.6 <= cmd <= 8.4:
        # Stop talking
        stop_chatting()

    elif 8.6 <= cmd <= 9.4:
        # Reset friendly
        reset_friendly()
        
    elif cmd > 1:
        # Miss
        if not acting.is_set():
            acting.set()
            miss_command()
            acting.clear()

def vc_scl_int(channel):
    hearing_start = time.perf_counter()
    while GPIO.input(vc_scl):
        continue
    hearing_stop = time.perf_counter()
    
    cmd = round((hearing_stop - hearing_start) / hearing_step, 2)
    
    if 0.6 <= cmd <= 1.4:
        # Go forward
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    go_forward()
            else:
                gain_friendly(-2)
                go_forward()

            acting.clear()

    elif 1.6 <= cmd <= 2.4:
        # Go backward
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    go_backward()
            else:
                gain_friendly(-2)
                go_backward()

            acting.clear()

    elif 2.6 <= cmd <= 3.4:
        # Go left
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    turn_left()
            else:
                gain_friendly(-2)
                turn_left()

            acting.clear()

    elif 3.6 <= cmd <= 4.4:
        # Go right
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    turn_right()
            else:
                gain_friendly(-2)
                turn_right()

            acting.clear()

    elif 4.6 <= cmd <= 5.4:
        # Turn around
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    turn_around()
            else:
                gain_friendly(-2)
                turn_around()

            acting.clear()

    elif 5.6 <= cmd <= 6.4:
        # Dance
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    dance()
            else:
                gain_friendly(-2)
                dance()

            acting.clear()

    elif 6.6 <= cmd <= 7.4:
        # Chat
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
                acting.clear()
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                    acting.clear()
                else:
                    if check_internet():
                        gain_friendly(-10)
                        chat()
                    else:
                        lost_connection()
                        acting.clear()
                    
            else:
                if check_internet():
                    gain_friendly(-10)
                    chat()
                else:
                    lost_connection()
                    acting.clear()

    elif 7.6 <= cmd <= 8.4:
        # Draw image
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
                acting.clear()
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                    acting.clear()
                else:
                    if check_internet():
                        gain_friendly(-10)
                        draw_image()
                    else:
                        lost_connection()
                        acting.clear()
                    
            else:
                if check_internet():
                    gain_friendly(-10)
                    draw_image()
                else:
                    lost_connection()
                    acting.clear()
    elif 8.6 <= cmd <= 10.4:
        # Optimus
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("optimus")
            else:
                gain_friendly(-2)
                mimic("optimus")

            acting.clear()
    elif cmd > 1:
        # Miss
        if not acting.is_set():
            acting.set()
            miss_command()
            acting.clear()

def vc_sda_int(channel):
    hearing_start = time.perf_counter()
    while GPIO.input(vc_sda):
        continue
    hearing_stop = time.perf_counter()
    
    cmd = round((hearing_stop - hearing_start) / hearing_step, 2)
    
    if 0.6 <= cmd <= 1.4:
        # I love you
        if not acting.is_set():
            acting.set()
            friendly_value = friendly.value
            if friendly_value < 30:
                hate()
            else:
                love()
            gain_friendly(10)
            acting.clear()

    elif 1.6 <= cmd <= 2.4:
        # Birthday
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    birthday()
            else:
                gain_friendly(-2)
                birthday()

            acting.clear()

    elif 2.6 <= cmd <= 3.4:
        # Cat
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("cat")
            else:
                gain_friendly(-2)
                mimic("cat")

            acting.clear()

    elif 3.6 <= cmd <= 4.4:
        # Cow
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("cow")
            else:
                gain_friendly(-2)
                mimic("cow")

            acting.clear()

    elif 4.6 <= cmd <= 5.4:
        # Dog
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("dog")
            else:
                gain_friendly(-2)
                mimic("dog")

            acting.clear()

    elif 5.6 <= cmd <= 6.4:
        # Duck
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("duck")
            else:
                gain_friendly(-2)
                mimic("duck")

            acting.clear()

    elif 6.6 <= cmd <= 7.4:
        # Elephant
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    gain_friendly(-2)
                    mimic("elephant")
            else:
                gain_friendly(-2)
                mimic("elephant")

            acting.clear()

    elif 7.6 <= cmd <= 8.4:
        # F*ck
        if not acting.is_set():
            acting.set()
            angry(code = 4)
            gain_friendly(-10)
            rgb.set_battery()
            acting.clear()

    elif 8.6 <= cmd <= 9.4:
        # Mimic process
        if not acting.is_set():
            acting.set()

            friendly_value = friendly.value

            if friendly_value < 30:
                no() 
                gain_friendly(5)
            elif friendly_value < 50:
                skip = random.choice([True, False])
                if skip:
                    no()
                    gain_friendly(5)
                else:
                    if check_internet():
                        if check_server():
                            gain_friendly(-2)
                            mimic_process()
                        else:
                            lost_server()
                            acting.clear()
                    else:
                        lost_connection()
                        acting.clear()
            else:
                if check_internet():
                    if check_server():
                        gain_friendly(-2)
                        mimic_process()
                    else:
                        lost_server()
                        acting.clear()
                else:
                    lost_connection()
                    acting.clear()

            acting.clear()

    elif cmd > 1:
        # Miss
        if not acting.is_set():
            acting.set()
            miss_command()
            acting.clear()

def vc_setup():
    GPIO.setup(vc_scl, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(vc_scl, GPIO.BOTH, callback = vc_scl_int)

    GPIO.setup(vc_sda, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(vc_sda, GPIO.BOTH, callback = vc_sda_int)

    GPIO.setup(vc_a27, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(vc_a27, GPIO.BOTH, callback = vc_a27_int)

def wake_up():
    response = random.choices(["huh", "uh_huh", "what_alt"], [0.4, 0.4, 0.2])[0]
    play_sound(f"{SOUND_DIR}/{response}.wav")
    with express.get_lock():
        express.value = random.choices([17, 20])[0]
    command = random.randint(1, 4)
    if command == 1:
        for _ in range(2):
            com.set_ear(20, 20)             ; time.sleep(0.05)
            com.set_ear(-20, -20)           ; time.sleep(0.05)
        range_ear(-20, 0, -20, 0, 10, 0.1)
    elif command == 2:
        for _ in range(2):
            com.set_ear(10, 0)              ; time.sleep(0.05)
            com.set_ear(-10, 0)             ; time.sleep(0.05)
        range_ear(-10, 0, 0, 0, 10, 0.1)
    elif command == 3:
        for _ in range(2):
            com.set_ear(0, 10)              ; time.sleep(0.05)
            com.set_ear(0, -10)             ; time.sleep(0.05)
        range_ear(0, 0, -10, 0, 10, 0.1)
    elif command == 4:
        for _ in range(2):
            com.set_ear(20, -20)            ; time.sleep(0.05)
            com.set_ear(-20, 20)            ; time.sleep(0.05)
        range_ear(-20, 0, 20, 0, 10, 0.1)

def what():
    rgb.set_val(115, 76, 165)
    com.set_ear(10, 10)
    play_sound(f"{SOUND_DIR}/what_prompt.wav", wait = True)
    com.set_ear(0, 0)
    rgb.set_battery()

def sigh():
    play_sound(f"{SOUND_DIR}/sigh.wav")
    time.sleep(0.5)
    with express.get_lock():
        express.value = Expression.SIGH
    
def hi():
    hi = lcd.current_express.split("_")[-1]
    if hi == "hi":
        hi = "hi"
    else:
        hi = "bello"
    play_sound(f"{SOUND_DIR}/{hi}.wav")
    
def no():
    with express.get_lock():
        express.value = Expression.ANGRY
    time.sleep(0.5)

    play_sound(f"{SOUND_DIR}/no.wav")

    rgb.set_val(255, 100, 4)

    com.send_motor_speed(-10, -10)
    leg = random.choice([10, 0])
    com.set_leg(leg , 10 - leg)

    time.sleep(0.2)
    com.send_motor_speed(0, 0)
    com.set_ear(0, 0)
    com.set_leg(0, 0)

    rgb.set_battery()

    with express.get_lock():
        express.value = Expression.IDLE

def miss_command():
    with express.get_lock():
        express.value = random.choices([17, 20])[0]
    play_sound(f"{SOUND_DIR}/huh.wav")

def what_is_this():
    with express.get_lock():
        express.value = Expression.LET_ME_SEE
    play_sound(f"{SOUND_DIR}/let_me_see.wav", wait = True)
    img = cam.get_image()
    
    # Process image
    w, h = 320, 240
    for i in range(1, 4):
        back = cv2.imread(f"{EXPRESSION_DIR}/show/idle_to_show/{i}.jpg")

        s_w, s_h = int(w * i / 4), int(h * i / 4)
        small_img = cv2.resize(img, (s_w, s_h))
        x = (w - s_w) // 2
        y = (h - s_h) // 2

        result = merge_image(back, small_img, x, y)

        cv2.imwrite(f"{EXPRESSION_DIR}/show/idle_to_show/{i}.jpg", result)
        cv2.imwrite(f"{EXPRESSION_DIR}/show/show_to_idle/{3 - i}.jpg", result)

    cv2.imwrite(f"{EXPRESSION_DIR}/show/show/0.jpg", cv2.resize(img, (320, 240)))
    cv2.imwrite(f"{LATEST_CAMERA_IMAGE}", cv2.resize(img, (320, 240)))

    with express.get_lock():
        express.value = Expression.SHOW

    img = encode_image(img, 100)

    result = opi.image_to_text(img)
    text = result["choices"][0]["message"]["content"]

    opi.text_to_speech(text)

    with express.get_lock():
        express.value = Expression.IDLE

    time.sleep(0.2)

    with express.get_lock():
        express.value = Expression.TALKING

    play_sound(f"{OPENAI_DIR}/out.wav", wait = True)
    
    with express.get_lock():
        express.value = Expression.IDLE

def chat():
    chatting.set()

    # Create a process for chatting process
    chat_instance = Thread(target = chat_process, args = (chatting, ))
    chat_instance.start()

def chat_process(chatting):
    phrase_timeout = 1
    phrase_time = None
    
    queue = Queue()
    last_sample = bytes()
    amplified_data = bytes()

    first_time = True

    stop_chat = False

    with express.get_lock():
        express.value = Expression.TALKING

    friendly_value = friendly.value
    if friendly_value < 40:
        play_sound(f"{SOUND_DIR}/what_you_want.wav")
        diaglog = opi.messages_system(opi.system_prompt_angry)
    elif friendly_value < 60:
        skip = random.choice([True, False])
        if skip:
            play_sound(f"{SOUND_DIR}/what_you_want.wav")
        else:
            play_sound(f"{SOUND_DIR}/help_you.wav")
        diaglog = opi.messages_system(opi.system_prompt_neutral)
    else:
        play_sound(f"{SOUND_DIR}/help_you.wav")
        diaglog = opi.messages_system(opi.system_prompt_nice)
    

    while chatting.is_set():
        with mic.microphone as source:
            audio = mic.recognizer.listen(source)

        now = datetime.utcnow()
        data = audio.get_raw_data()
    
        queue.put(data)
    
        if not queue.empty() and chatting.is_set():
            phrase_complete = False

            if phrase_time and now - phrase_time > timedelta(seconds = phrase_timeout):
                last_sample = bytes()
                phrase_complete = True

            phrase_time = now

            while not queue.empty() and chatting.is_set():
                data = queue.get()
                last_sample += data 

                if phrase_complete and chatting.is_set():
                    amplified_data = mic.amplify_audio(last_sample)

                if not first_time:
                    text = opi.whisper_model(amplified_data)
                
                    if text not in halucination and "lalaschool" not in text and chatting.is_set() :

                        friendly_value = friendly.value
                        if friendly_value < 40:
                            diaglog = opi.messages_system(opi.system_prompt_angry)
                        elif friendly_value < 60:
                            diaglog = opi.messages_system(opi.system_prompt_neutral)
                        else:
                            diaglog = opi.messages_system(opi.system_prompt_nice)

                        print(f"User: {text}")
                        reply, func = opi.chatgpt(text, diaglog)
                        
                        print(f"EVE: {reply}")

                        for i in range(0, - 31 , -5):
                            com.set_ear(i, i)
                            time.sleep(0.025)

                        with express.get_lock():
                            express.value = Expression.THINKING

                        # change text_to_speech
                        opi.text_to_speech(reply)

                        with express.get_lock():
                            express.value = Expression.IDLE

                        for i in range(-10, 1, -1):
                            com.set_ear(i, i)
                            time.sleep(0.05)

                        with express.get_lock():
                            express.value = Expression.TALKING

                        play_sound(f"{OPENAI_DIR}/out.wav", wait = True)
                        
                        with express.get_lock():
                            express.value = Expression.IDLE

                        if func is not None:
                            if func.name == "get_drawing_infomation":
                                dic_tti =  ast.literal_eval(func.arguments)
                                promt =  dic_tti["tti_prompt"]
                                draw(promt)
                                gain_friendly(- 2)

                            if func.name == "stop_talking":
                                stop_chat = True
                                stop_chatting()
                                break
                        
                        time.sleep(0.5)

                        with express.get_lock():
                            express.value = random.choice([42, 43])
                            if express.value == Expression.LISTENING_1:
                                com.set_ear(30, -20)
                            else:
                                com.set_ear(-20, 30)

                        gain_friendly(2)

                else:
                    first_time = False
                    with express.get_lock():
                        express.value = random.choice([42, 43])

                        if express.value == Expression.LISTENING_1:
                            com.set_ear(20, 0)
                        else:
                            com.set_ear(0, 20)
                        
                        
        else:
            time.sleep(0.1)

    if not stop_chat:
        with express.get_lock():
            express.value = Expression.TALKING

        play_sound(f"{SOUND_DIR}/goodbye.wav", wait = True)

    print("Stop chatting")

    chatting.clear()

    with express.get_lock():
        express.value = Expression.IDLE

    com.set_ear(0, 0)
    acting.clear()

def draw(promt):
    with express.get_lock():
        express.value = Expression.PAINTING

    image = opi.image_generations(promt)

    image = cv2.resize(image, (320, 240))

    for (i, y) in enumerate([12, 37, 71, 102, 137, 172]):
        back = cv2.imread(f"{EXPRESSION_DIR}/painting/painting_to_idle/{14+ i}.jpg")
        result =  merge_image(back, image, 0, y)

        cv2.imwrite(f"{EXPRESSION_DIR}/painting/painting_to_idle/{14+ i}.jpg", result)
    
    cv2.imwrite(f"{EXPRESSION_DIR}/painting/painting_to_idle/13.jpg", image)
    settings.paths.drawing_results.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", promt).strip("_")[:80] or "drawing"
    cv2.imwrite(str(settings.paths.drawing_results / f"{safe_name}.jpg"), image)

    with express.get_lock():
        express.value = Expression.IDLE

    time.sleep(11)

def draw_image():
    chatting.set()

    # Create a process for chatting process
    draw_instance = Thread(target = draw_process, args = (chatting, ))
    draw_instance.start()

def draw_process(chatting):
    phrase_timeout = 1
    phrase_time = None
    
    queue = Queue()
    last_sample = bytes()
    amplified_data = bytes()

    first_time = True

    stop_chat = False

    with express.get_lock():
        express.value = Expression.TALKING

    play_sound(f"{SOUND_DIR}/what_image.wav")
    diaglog = opi.messages_system(opi.system_prompt_neutral)
    

    while chatting.is_set():
        with mic.microphone as source:
            audio = mic.recognizer.listen(source)

        now = datetime.utcnow()
        data = audio.get_raw_data()
    
        queue.put(data)
    
        if not queue.empty() and chatting.is_set():
            phrase_complete = False

            if phrase_time and now - phrase_time > timedelta(seconds = phrase_timeout):
                last_sample = bytes()
                phrase_complete = True

            phrase_time = now

            while not queue.empty() and chatting.is_set():
                data = queue.get()
                last_sample += data 

                if phrase_complete and chatting.is_set():
                    amplified_data = mic.amplify_audio(last_sample)

                if not first_time:
                    text = opi.whisper_model(amplified_data)
                
                    if text not in halucination and "lalaschool" not in text and chatting.is_set() :
                        print(f"User: {text}")
                        reply, func = opi.chatgpt(text, diaglog)
                        
                        print(f"EVE: {reply}")

                        for i in range(0, - 31 , -5):
                            com.set_ear(i, i)
                            time.sleep(0.025)

                        with express.get_lock():
                            express.value = Expression.THINKING

                        # change text_to_speech
                        opi.text_to_speech(reply)

                        with express.get_lock():
                            express.value = Expression.IDLE

                        for i in range(-10, 1, -1):
                            com.set_ear(i, i)
                            time.sleep(0.05)

                        with express.get_lock():
                            express.value = Expression.TALKING

                        if func is not None:
                            if func.name == "get_drawing_infomation":
                                play_sound(f"{OPENAI_DIR}/out.wav", wait = True)
                        
                                with express.get_lock():
                                    express.value = Expression.IDLE

                                dic_tti =  ast.literal_eval(func.arguments)
                                promt =  dic_tti["tti_prompt"]
                                draw(promt)
                                gain_friendly(- 2)
                                stop_chatting()
                                break

                            elif func.name == "stop_talking":
                                play_sound(f"{OPENAI_DIR}/out.wav", wait = True)
        
                                with express.get_lock():
                                    express.value = Expression.IDLE

                                stop_chat = True
                                stop_chatting()
                                break
                        
                        else:
                            play_sound(f"{SOUND_DIR}/cannot_draw.wav", wait = True)

                            with express.get_lock():
                                express.value = Expression.IDLE

                        time.sleep(0.5)

                        with express.get_lock():
                            express.value = random.choice([42, 43])
                            if express.value == Expression.LISTENING_1:
                                com.set_ear(30, -20)
                            else:
                                com.set_ear(-20, 30)

                        gain_friendly(2)

                else:
                    first_time = False
                    with express.get_lock():
                        express.value = random.choice([42, 43])

                        if express.value == Expression.LISTENING_1:
                            com.set_ear(20, 0)
                        else:
                            com.set_ear(0, 20)
                        
                        
        else:
            time.sleep(0.1)
    
    if not stop_chat:
        time.sleep(1)
        with express.get_lock():
            express.value = Expression.TALKING

        play_sound(f"{SOUND_DIR}/draw_again.wav", wait = True)

    print("Stop chatting")

    chatting.clear()

    with express.get_lock():
        express.value = Expression.IDLE

    com.set_ear(0, 0)
    acting.clear()

def roger():
    response = random.choices(["okay", "okay_alt_1", "okay_alt_2", "roger", "yes_sir"], [0.3, 0.3, 0.3, 0.05, 0.05])[0]
    play_sound(f"{SOUND_DIR}/{response}.wav")

    ear = random.choice([-1, 1])
    com.set_ear(ear * 10, - ear * 10)
    time.sleep(0.5)
    com.set_ear(0, 0)

def go_forward():
    roger()

    with express.get_lock():
        express.value = Expression.HAPPY

    com.send_motor_speed(round(w_m_max * 0.7, 2), round(w_m_max * 0.7, 2))

    range_all(0, -20, 0, -20, 0, -10, 0, -10, 50, 0.5)

    time.sleep(0.5)

    com.send_motor_speed(0, 0)
    
    time.sleep(0.5)

    range_all(-10, 0, -10, 0, -10, 0, -10, 0, 50, 0.5)
    
    with express.get_lock():
        express.value = Expression.IDLE

def go_backward():
    roger()
    with express.get_lock():
        express.value = Expression.HAPPY

    com.send_motor_speed(- round(w_m_max * 0.7, 2), - round(w_m_max * 0.7, 2))

    range_all(0, 20, 0, 20, 0, 10, 0, 10, 50, 0.5)

    time.sleep(0.5)
    
    com.send_motor_speed(0, 0)

    time.sleep(0.5)

    range_all(10, 0, 10, 0, 10, 0, 10, 0, 50, 0.5)
    
    with express.get_lock():
        express.value = Expression.IDLE

def turn_left():
    roger()
    
    with express.get_lock():
        express.value = Expression.HAPPY

    range_all(0, -20, 0, 20, 0 , -5, 0, 5, 20, 0.5)

    com.send_motor_speed(- w_m_max, w_m_max)
    com.set_ear(- 20,  20)

    time.sleep(3)

    range_all(-20, 0, 20, 0, -5, 0, 5, 0, 20, 0.5) 

    com.send_motor_speed(0, 0)
    
    with express.get_lock():
        express.value = Expression.IDLE

def turn_right():
    roger()

    with express.get_lock():
        express.value = Expression.HAPPY

    range_all(0, 20, 0, -20, 0, 5, 0, -5, 20, 0.5)

    com.send_motor_speed(w_m_max, - w_m_max)
    com.set_ear(20,  -20)

    time.sleep(3)

    range_all(20, 0, -20, 0, 5, 0, -5, 0, 20, 0.5) 
    
    com.send_motor_speed(0, 0)

    with express.get_lock():
        express.value = Expression.IDLE

def turn_around():
    roger()
    with express.get_lock():
        express.value = Expression.HAPPY
    which_leg = random.choice([-1, 1])
    
    range_all(0, -20, 0, -20, 0 , which_leg * 5, 0, - which_leg * 5, 20, 0.5)
              
    com.send_motor_speed(w_m_max * which_leg, - w_m_max * which_leg)
        
    turn_arround_time = random.randint(8, 12)
    time.sleep(turn_arround_time)
    
    with express.get_lock():
        express.value = Expression.DIZZY

    play_sound(f"{SOUND_DIR}/dizzy.wav", wait = True)

    com.send_motor_speed(0, 0)

    range_all(-20, 0, -20, 0 , which_leg * 5, 0, - which_leg * 5, 0, 20, 0.5)

def hate():
    with express.get_lock():
        express.value = Expression.HATE
    play_sound(f"{SOUND_DIR}/i_hate_you.wav")

    rgb.set_val(255, 42, 3)

    com.send_motor_speed(-10, -10)
    com.set_leg(10, 0)

    for i in range(50):
        l = random.randint(30, 70)
        r = random.randint(30, 70)
        com.set_ear(l, r)
        time.sleep(0.03)

        if i >= 5:
            com.send_motor_speed(0, 0)
            com.set_leg(0, 0)

    com.set_ear(0,0)

    rgb.set_battery()

def love():
    with express.get_lock():
        express.value = Expression.LOVE_IDLE
    play_sound(f"{SOUND_DIR}/love.wav")
    rgb.set_val(169, 64, 100)

    range_all(0, -40, 0, -40, 0, -10, 0, -10, 100, 1.0)
    range_all(-40, 0, -40, 0, -10, 0, -10, 0, 100, 0.5)
    
    rgb.set_battery()

def dance():
    with express.get_lock():
        express.value = Expression.HAPPY

    play_sound(f"{SOUND_DIR}/never_gonna.wav")

    for i in range(8):
        if i % 2 == 0:
            range_all(0, 20, 0, -20, 0, 5, 0, 5, 20, 0.25)
            range_all(20, 0, -20, 0, 5, 0, 5, 0, 20, 0.25)
        else:
            range_all(0, -20, 0, 20, 0, -5, 0, -5, 20, 0.25)
            range_all(-20, 0, 20, 0, -5, 0, -5, 0, 20, 0.25)
    
    with express.get_lock():
        express.value = Expression.IDLE

def birthday():
    range_ear(0, 45, 0, 45, 20, 0.5)
    
    play_sound(f"{SOUND_DIR}/birthday.wav")
    time.sleep(0.5)

    with express.get_lock():
        express.value = Expression.BIRTHDAY

    current_bat = rgb.light

    for light in range(current_bat, 100):
        rgb.light = light
        rgb.set_val(255, 178, 102)
        time.sleep(0.01)
    for light in range(100, -1, -1):
        rgb.light = light
        rgb.set_val(255, 178, 102)
        time.sleep(0.01)

    for _ in range(3):
        for light in range(0, 100):
            rgb.light = light
            rgb.set_val(255, 178, 102)
            time.sleep(0.01)
        for light in range(100, -1, -1):
            rgb.light = light
            rgb.set_val(255, 178, 102)
            time.sleep(0.01)
    
    range_ear(45, 0, 45, 0, 20, 0.5)

    rgb.light = current_bat
    rgb.set_battery()
    
def go_around():
    roger()
    with state.get_lock():
        state.value = RobotMode.GO_AROUND

    range_leg(0, 6, 0, 6, 50, 1.0)

    with express.get_lock():
        express.value = Expression.LOOK_CENTER

def follow():
    roger()
    
    with state.get_lock():
        state.value = RobotMode.FOLLOW

    range_leg(0, -20, 0, -20, 50, 1.0)

    with express.get_lock():
        express.value = Expression.LOOK_CENTER

def stop():
    roger()

    com.send_motor_speed(0, 0)

    if state.value == RobotMode.GO_AROUND:
        range_leg(6, 0, 6, 0, 50, 1.0)
    elif state.value == RobotMode.FOLLOW:
        range_leg(-20, 0, -20, 0, 50, 1.0)
    
    with state.get_lock():
        state.value = RobotMode.STAND_STILL

    with express.get_lock():
        express.value = Expression.IDLE
    
    acting.clear()

def stop_chatting():
    chatting.clear()

def angry(code = 2):
    if code == 2:
        # angry 20%

        with express.get_lock():
            express.value = Expression.ANGRY_ALT_1

        touch = random.choice([True, False])
        if touch:
            play_sound(f"{SOUND_DIR}/do_not_touch_me.wav")
        else:
            play_sound(f"{SOUND_DIR}/angry_alt_{code - 1}.wav")

        rgb.set_val(255, 100, 4)
    
        for i in range(25):
            l = random.randint(50, 70)
            r = random.randint(50, 70)
            com.set_ear(l, r)
            time.sleep(0.03)

        com.set_ear(0, 0)
        rgb.set_battery()

    elif code == 3:
        # angry 50%

        with express.get_lock():
            express.value = Expression.ANGRY_ALT_2

        touch = random.choice([True, False])
        if touch:
            play_sound(f"{SOUND_DIR}/do_not_touch_me.wav")
        else:
            play_sound(f"{SOUND_DIR}/angry_alt_{code - 1}.wav")

        rgb.set_val(255, 42, 3)

        com.send_motor_speed(-10, -10)

        for i in range(50):
            l = random.randint(30, 70)
            r = random.randint(30, 70)
            com.set_ear(l, r)
            time.sleep(0.03)

            if i == 5:
                com.send_motor_speed(0, 0)

        com.set_ear(0, 0)
        rgb.set_battery()

    elif code == 4:
        # angry 100 %
        
        with express.get_lock():
            express.value = Expression.ANGRY_ALT_3
        play_sound(f"{SOUND_DIR}/angry_alt_{code - 1}.wav")

        rgb.set_val(255, 0, 0)

        com.send_motor_speed(-10, -10)

        for i in range(50):
            l = random.randint(30, 70)
            r = random.randint(30, 70)
            com.set_ear(l, r)
            time.sleep(0.03)

            if i == 5:
                com.send_motor_speed(0, 0)

        com.set_ear(0, 0)
        rgb.set_battery()

    else:
        pass

def lost_connection():
    with express.get_lock():
        express.value = Expression.CONNECTION_LOST
    play_sound(f"{SOUND_DIR}/lost_connection.wav", wait = True)

def lost_server():
    with express.get_lock():
        express.value = Expression.CONNECTION_LOST
    play_sound(f"{SOUND_DIR}/server_connection_failed.wav", wait = True)

def shutdown():
    save_friendly()
    with express.get_lock():
        express.value = Expression.BYE
    play_sound(f"{SOUND_DIR}/bye.wav")
    time.sleep(2.5)
    com.send_motor_speed(0, 0)
    lcd.switch(on = False)
    rgb.stop()
    time.sleep(0.5)
    subprocess.run(["sudo", "shutdown", "-h", "now"])
    
def reboot():
    save_friendly()
    with express.get_lock():
        express.value = Expression.BYE
    play_sound(f"{SOUND_DIR}/bye.wav")
    time.sleep(2.5)
    com.send_motor_speed(0, 0)
    lcd.switch(on = False)
    rgb.stop()
    subprocess.run(["sudo", "reboot"])
    time.sleep(0.5)
    
def low_battery():
    with express.get_lock():
        express.value = Expression.LOW_BATTERY
    play_sound(f"{SOUND_DIR}/low_battery.wav", wait = True)

def mumble():
    mumble = random.randint(1, 4)
    
    with express.get_lock():
        express.value = Expression.HAPPY

    play_sound(f"{SOUND_DIR}/mumble_{mumble}.wav", wait = True)

    with express.get_lock():
        express.value = Expression.IDLE

def got_error():
    with express.get_lock():
        express.value = Expression.ERROR
    play_sound(f"{SOUND_DIR}/error.wav", wait = True)
    time.sleep(2)
    play_sound(f"{SOUND_DIR}/reboot_in_5_seconds.wav")
    time.sleep(5)
    reboot()

def mimic(animal):  
    if animal == "cat":
        with express.get_lock():
            express.value = animal_dictionary[animal]
    
        play_sound(f"{SOUND_DIR}/{animal}.wav")

        range_ear(0, 20, 0, -20, 20, 1.0)
        range_ear(20, -20, -20, 20, 20, 1.0)
        range_ear(-20, 0, 20, 0, 20, 0.5)

    elif animal == "cow":
        range_all(0, 70, 0, 70, 0, 10, 0, 10, 20, 0.5)

        with express.get_lock():
            express.value = animal_dictionary[animal]
    
        play_sound(f"{SOUND_DIR}/{animal}.wav")

        range_leg(10, -10, 10, -10, 100, 0.9)
        time.sleep(0.5)
        range_all(70, 0, 70, 0, -10, 0, -10, 0, 100, 0.5)

    elif animal == "dog":
        with express.get_lock():
            express.value = animal_dictionary[animal]
    
        play_sound(f"{SOUND_DIR}/{animal}.wav")

        range_ear(0, 45, 0, 45, 2, 0.5)
        if random.choice([True, False]):    
            com.send_motor_speed(w_m_max, w_m_max)
        time.sleep(0.3)
        com.send_motor_speed(0, 0)
        time.sleep(0.25)
        if random.choice([True, False]):    
            com.send_motor_speed(w_m_max, w_m_max)
        time.sleep(0.25)
        com.send_motor_speed(0, 0)
        time.sleep(0.5)
        range_ear(45, 0, 45, 0, 10, 0.2)

    elif animal == "duck":
        range_leg(0, -10, 0, -10, 20, 0.5)

        with express.get_lock():
            express.value = animal_dictionary[animal]
    
        play_sound(f"{SOUND_DIR}/{animal}.wav")

        for _ in range(8):
            com.set_ear(20, - 20)
            time.sleep(0.05)
            com.set_ear(- 20, 20)
            time.sleep(0.05)

        time.sleep(0.5)

        range_all(-20, 0, 20, 0, -10, 0, -10, 0, 20, 0.5)

    elif animal == "elephant":
        range_leg(0, 10, 0, 10, 20, 0.5)

        with express.get_lock():
            express.value = animal_dictionary[animal]
    
        play_sound(f"{SOUND_DIR}/{animal}.wav")

        range_all(0, 40, 0, 40, 10, -10, 10, -10, 50, 1.0)

        time.sleep(0.5)

        range_all(40, 0, 40, 0, -10, 0, -10, 0, 50, 0.5)
    
    elif animal == "optimus":
        with express.get_lock():
            express.value = random.choices([21, 18], [0.9, 0.1])[0]
        
        time.sleep(0.25)

        play_sound(f"{SOUND_DIR}/{animal}.wav")

        for i in range(6):
            if i % 2 == 0:
                range_all(0, 20, 0, -20, 0, 5, 0, 5, 20, 0.5)
                range_all(20, 0, -20, 0, 5, 0, 5, 0, 20, 0.5)
            else:
                range_all(0, -20, 0, 20, 0, -5, 0, -5, 20, 0.5)
                range_all(-20, 0, 20, 0, -5, 0, -5, 0, 20, 0.5)
        
def mimic_process():
    with express.get_lock():
        express.value = Expression.LET_ME_SEE
    play_sound(f"{SOUND_DIR}/let_me_see.wav", wait = True)

    for _ in range(10):
        mqtt.upload_state("detect")

        frame = cam.get_image()
        encoded_image = cam.encode_image(frame, quality = 60)
        mqtt.upload_image(encoded_image)

        time.sleep(0.1)

    animal = ""

    if mqtt.detect != {}:
        for k in mqtt.detect.keys():
            if k in ["cat", "dog", "cow", "elephant"]:
                animal = k
            elif k in ["car", "airplane", "bus", "train", "truck"]:
                animal = "optimus"

    if animal == "":
        with express.get_lock():
            express.value = 19
        play_sound(f"{SOUND_DIR}/i_dont_know.wav", wait = True)
    else:
        mimic(animal)

    mqtt.detect = {}
    mqtt.upload_state("")

def compute_motor_speed(v, w):
    return differential_wheel_speeds(
        v,
        w,
        wheel_radius=radius,
        axle_length=length,
        max_wheel_speed=w_m_max,
    )
    
def follow_process(ee, ww):
    v, w = fuz.follow(ee, ww)
    wl, wr = compute_motor_speed(max(min(v, 100), -100), max(min(w, 100), -100))
    # print(f"{ee=:.2f}, {ww=:.2f}, {v=:.2f}, {w=:.2f}, {wl=:.2f}, {wr=:.2f}")
    com.send_motor_speed(round(wl, 2), round(wr, 2))

    if ee > 75:
        if express.value != Expression.LOOK_RIGHT:
            with express.get_lock():
                express.value = Expression.LOOK_RIGHT
    elif ee < -75: 
        if express.value != Expression.LOOK_LEFT:
            with express.get_lock():
                express.value = Expression.LOOK_LEFT
    else:
        if express.value != Expression.SHOW:
            with express.get_lock():
                express.value = Expression.LOOK_CENTER

def go_around_process(ll, ff, rr):
    v, w = fuz.go_around(ll, ff, rr)
    wl, wr = compute_motor_speed(max(min(v, 100), -100), max(min(w, 100), -100))
    # print(f"{ll=:.2f}, {ff=:.2f}, {rr=:.2f}, {v=:.2f}, {w=:.2f}, {wl=:.2f}, {wr=:.2f}")
    com.send_motor_speed(round(wl, 2), round(wr, 2))

    if w > 10:
        if express.value != Expression.LOOK_LEFT:
            with express.get_lock():
                express.value = Expression.LOOK_LEFT
    elif w < -10: 
        if express.value != Expression.LOOK_RIGHT:
            with express.get_lock():
                express.value = Expression.LOOK_RIGHT
    else:
        if express.value != Expression.SHOW:
            with express.get_lock():
                express.value = Expression.LOOK_CENTER


"""
                                                            ################
                                                            ###  Touchy  ###
                                                            ################
"""

# Touch sensor
head_sensor = 6
chin_sensor = 5

def head_rubbing(channel):
    if GPIO.input(head_sensor):
        if not acting.is_set():

            start_holding = time.perf_counter()

            while time.perf_counter() - start_holding < 0.5:
                if not GPIO.input(head_sensor):
                    stop_holding = time.perf_counter()
                    break
                else:
                    stop_holding = time.perf_counter()

            acting.set()

            if stop_holding - start_holding >= 0.45:
                friendly_value = friendly.value
                if friendly_value < 20:
                    angry(code = 4)
                    gain_friendly(5)
                elif friendly_value < 40:
                    angry(code = 3)
                    gain_friendly(4)
                else:
                    rgb.set_val(255, 128, 213)

                    with express.get_lock():
                        express.value = Expression.WRINKLE

                    gain_friendly_time = time.perf_counter()
                    gain_time = 1

                    range_leg(0, 5, 0, 5, 50, 0.5)

                    play_sound(f"{SOUND_DIR}/ehheh.wav")

                    while GPIO.input(head_sensor):
                        l = random.randint(-10, 10)
                        r = random.randint(-10, 10)
                        com.set_ear(l, r)
                        time.sleep(0.02)

                        if time.perf_counter() - gain_friendly_time >= gain_time:
                            if gain_time <= 5:
                                gain_friendly(5)
                            elif gain_time >= 15:
                                gain_friendly(-2)
                            gain_time += 1

                    rgb.set_battery()

                    with express.get_lock():
                        express.value = Expression.IDLE

                    range_all(10, 0, 10, 0, 5, 0, 5, 0, 20, 0.2)

            elif 0.02 <= stop_holding - start_holding < 0.45:
                friendly_value = friendly.value
                if friendly_value < 20:
                    angry(code = 4)
                    gain_friendly(-7)
                elif friendly_value < 40:
                    angry(code = 3)
                    gain_friendly(-6)
                else:
                    angry(code = 2)
                    gain_friendly(-5)

            acting.clear()
    else:
        if not acting.is_set():
            rgb.set_battery()
            com.set_all()

            with express.get_lock():
                express.value = Expression.IDLE

def chin_rubbing(channel):
    if GPIO.input(chin_sensor):
        if not acting.is_set():

            start_holding = time.perf_counter()

            while time.perf_counter() - start_holding < 0.5:
                if not GPIO.input(chin_sensor):
                    stop_holding = time.perf_counter()
                    break
                else:
                    stop_holding = time.perf_counter()

            acting.set()

            if stop_holding - start_holding >= 0.45:
                friendly_value = friendly.value
                if friendly_value < 20:
                    angry(code = 4)
                    gain_friendly(5)
                elif friendly_value < 40:
                    angry(code = 3)
                    gain_friendly(4)
                else:
                    rgb.set_val(255, 128, 213)

                    with express.get_lock():
                        express.value = 44

                    range_leg(0, -5, 0, -5, 50, 0.5)

                    play_sound(f"{SOUND_DIR}/ehheh.wav")

                    gain_friendly_time = time.perf_counter()
                    gain_time = 1
                    while GPIO.input(chin_sensor):
                        l = random.randint(-10, 10)
                        r = random.randint(-10, 10)
                        com.set_ear(l, r)
                        time.sleep(0.02)

                        if time.perf_counter() - gain_friendly_time >= gain_time:
                            if gain_time <= 5:
                                gain_friendly(5)
                            elif gain_time >= 15:
                                gain_friendly(-2)
                            gain_time += 1

                    rgb.set_battery()

                    with express.get_lock():
                        express.value = Expression.IDLE

                    range_all(10, 0, 10, 0, -5, 0, -5, 0, 20, 0.5)

            elif 0.02 <= stop_holding - start_holding < 0.45:
                friendly_value = friendly.value
                if friendly_value < 20:
                    angry(code = 4)
                    gain_friendly(-7)
                elif friendly_value < 40:
                    angry(code = 3)
                    gain_friendly(-6)
                else:
                    angry(code = 2)
                    gain_friendly(-5)

            acting.clear()
    else:
        if not acting.is_set():
            rgb.set_battery()
            com.set_all()

            with express.get_lock():
                express.value = Expression.IDLE

def touch_setup():
    GPIO.setup(head_sensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(head_sensor, GPIO.BOTH, callback = head_rubbing)

    GPIO.setup(chin_sensor, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(chin_sensor, GPIO.BOTH, callback = chin_rubbing)
