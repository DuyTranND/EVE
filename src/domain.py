"""Domain values shared by the application and hardware adapters."""

from enum import IntEnum


class RobotMode(IntEnum):
    STAND_STILL = 0
    FOLLOW = 1
    GO_AROUND = 2


class Expression(IntEnum):
    IDLE = 0
    ANGRY = 1
    GLARE = 2
    HAPPY = 3
    LOVE = 4
    SAD = 5
    SLEEP = 6
    WRINKLE = 7
    BELLO = 8
    BIRTHDAY = 9
    CAT = 10
    COW = 11
    DIZZY = 12
    DOG = 13
    DUCK = 14
    ELEPHANT = 15
    HI = 16
    WHAT = 17
    OPTIMUS = 18
    UNKNOWN = 19
    WHAT_ALT = 20
    OPTIMUS_ALT = 21
    ANGRY_ALT_1 = 22
    ANGRY_ALT_2 = 23
    ANGRY_ALT_3 = 24
    BYE = 25
    LOVE_IDLE = 26
    MUMBLE = 27
    LET_ME_SEE = 28
    IDLE_1 = 29
    IDLE_2 = 30
    IDLE_3 = 31
    IDLE_4 = 32
    IDLE_5 = 33
    IDLE_6 = 34
    IDLE_7 = 35
    IDLE_8 = 36
    IDLE_9 = 37
    IDLE_10 = 38
    IDLE_11 = 39
    LOW_BATTERY = 40
    TALKING = 41
    LISTENING_1 = 42
    LISTENING_2 = 43
    WRINKLE_ALT = 44
    THINKING = 45
    PAINTING = 46
    HATE = 47
    SIGH = 48
    CONNECTION_LOST = 49
    SHOW = 50
    LOOK_LEFT = 51
    LOOK_RIGHT = 52
    LOOK_CENTER = 53
    ERROR = 54


EXPRESSION_NAMES = (
    "idle_01", "angry", "glare", "happy", "love", "sad", "sleep", "wrinkle",
    "idle_bello", "idle_birthday", "idle_cat", "idle_cow", "idle_dizzy",
    "idle_dog", "idle_duck", "idle_elephant", "idle_hi", "idle_what",
    "idle_optimus", "idle_unknown", "idle_what_alt", "idle_optimus_alt",
    "idle_angry_alt_1", "idle_angry_alt_2", "idle_angry_alt_3", "idle_bye", "idle_love",
    "idle_mumble", "idle_let_me_see", "idle_01", "idle_02", "idle_03", "idle_04",
    "idle_05", "idle_06", "idle_07", "idle_08", "idle_09", "idle_10", "idle_11",
    "idle_battery", "talking", "listening_01", "listening_02", "wrinkle_alt", "thinking",
    "painting", "idle_hate", "idle_sigh", "idle_connection", "show", "look_left",
    "look_right", "look_center", "error",
)

ROBOT_MODE_NAMES = ("stand still", "follow", "go around")

ANIMAL_EXPRESSIONS = {
    "cat": Expression.CAT,
    "dog": Expression.DOG,
    "cow": Expression.COW,
    "elephant": Expression.ELEPHANT,
    "duck": Expression.DUCK,
}
