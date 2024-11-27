
COL = lambda c: f"\033[{c}m"
RGB_FG = lambda r, g, b: f"\033[38;2;{r};{g};{b}m"
RGB_BG = lambda r, g, b: f"\033[48;2;{r};{g};{b}m"
RGB = lambda r1, g1, b1, r2, g2, b2: f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m"
CLR_SCR = lambda: f"\033[2J"
CLR_BUF = lambda: f"\033[3J"
ALT_BUF = lambda b=True: f"\033[?1049h" if b else f"\033[?1049l"
CURSOR = lambda b=False: f"\033[?25h" if b else f"\033[?25l"
UNDER = lambda b=True: f"\033[4m" if b else f"\033[24m"
POS = lambda x, y: f"\033[{y};{x}H"
POS_U = lambda y: f"\033[{y}A"
POS_D = lambda y: f"\033[{y}B"
POS_R = lambda x: f"\033[{x}C"
POS_L = lambda x: f"\033[{x}D"

PORT = 42069

FONTSIZE = 2
WIDTH = 42
HEIGHT = 42

NAMESIZE = 15

MAX_CHATTERS = 99
MAX_HOSTS = 15

TICK_SPEED = 0.01
BLINK_SPEED = 10

MSG_MAX_LEN = 1000

SCROLL_SPEED = 4

from string import ascii_letters, digits, punctuation
CHARS = ascii_letters + digits + punctuation + " "
