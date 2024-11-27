# For best results, please run in powershell! Thanks :)
import os, sys
from sys import stdout
import ctypes, ctypes.wintypes, struct
import subprocess, msvcrt, time, re
#
import network
from const import *


VERSIONS = [(3, 11), (3, 12), (3, 13)]

if sys.version_info[:2] not in VERSIONS:
	c = " | ".join([f"{v[0]}.{v[1]}" for v in VERSIONS])
	raise Exception(f"Incompatible python version\nCompatible versions: {c}")

client_name = None
client_color = None


def init():
	network.init_udp()
	init_screen()
	menu_screen()
	prompt_name()
	network.listen_udp()
	prompt_host()


def init_screen():
	subprocess.call("", shell=True)
	
	class COORD(ctypes.Structure):
		_fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
	
	class CONSOLE_FONT_INFOEX(ctypes.Structure):
		_fields_ = [("cbSize", ctypes.c_ulong),
					("nFont", ctypes.c_ulong),
					("dwFontSize", COORD),
					("FontFamily", ctypes.c_uint),
					("FontWeight", ctypes.c_uint),
					("FaceName", ctypes.c_wchar * 32)]
	
	font = CONSOLE_FONT_INFOEX()
	font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
	font.dwFontSize.X = 8 * FONTSIZE
	font.dwFontSize.Y = 8 * FONTSIZE
	font.FaceName = "Terminal"
	
	rect = ctypes.wintypes.SMALL_RECT(0, 0, WIDTH-1, HEIGHT-1)
	
	handle = ctypes.windll.kernel32.GetStdHandle(-11)
	ctypes.windll.kernel32.SetCurrentConsoleFontEx(handle, False, ctypes.pointer(font))
	ctypes.windll.kernel32.SetConsoleWindowInfo(handle, True, ctypes.pointer(rect))
	ctypes.windll.kernel32.SetConsoleTitleW("WALACHAT")


def menu_screen():
	stdout.write(CLR_SCR())
	stdout.write(CLR_BUF())
	stdout.write(ALT_BUF(True))
	stdout.write(CURSOR(False))
	
	stdout.write(RGB_BG(0, 0, 0) + POS(1, 1) + (" " * WIDTH * HEIGHT))
	stdout.write(RGB_BG(100, 100, 100) + POS(1, 1) + (" " * WIDTH * 2))
	stdout.write(RGB_FG(50, 220, 255) + POS(WIDTH // 2 - 4, 2) + "WALACHAT")
	stdout.write(RGB_FG(255, 255, 255) + POS(1, 3) + ("═" * WIDTH))
	
	stdout.flush()


def prompt_name():
	stdout.write(CURSOR(False))
	stdout.write(POS(3, 7) + RGB(255, 255, 255, 0, 0, 0) + "Enter your name:")
	stdout.flush()
	
	name = ""
	tick = 0
	color = 31
	
	while True:
		stdout.write(POS(20, 7) + COL(color) + name + RGB_FG(255, 255, 255) + ("_" if tick // BLINK_SPEED % 2 == 0 else " ") + (" " * NAMESIZE))
		stdout.flush()
		
		tick += 1
		
		if msvcrt.kbhit():
			u = msvcrt.getch()
			if u in bytes(CHARS, "ascii"):
				name = (name + str(u, "ascii"))[:NAMESIZE]
			elif u == b"\x08":
				name = name[:-1]
			elif u == b"\t":
				color = color+1 if color < 36 else 31
			elif u == b"\r" and len(name) > 0:
				break
		time.sleep(TICK_SPEED)
	
	global client_name, client_color
	client_name, client_color = name, color
	
	stdout.write(POS(20, 7) + COL(color) + name + " " * NAMESIZE)
	stdout.flush()


def prompt_host(errormsg=""):
	stdout.write(CURSOR(False))
	stdout.write(POS(3, 7) + RGB(255, 255, 255, 0, 0, 0) + "Enter your name:")
	stdout.write(POS(20, 7) + COL(client_color) + client_name + " " * NAMESIZE)
	
	if errormsg != "":
		stdout.write(POS(3, 38) + RGB(200, 10, 10, 0, 0, 0) + "Disconnected")
		stdout.write(POS(3, 39) + errormsg)
	
	stdout.write(POS(3, 10) + RGB(255, 255, 255, 0, 0, 0) + "Choose a room to join/host:")
	for i in range(MAX_HOSTS+5):
		stdout.write(RGB_BG(100, 100, 100) + POS(5, 13+i) + (" " * 32))
	stdout.write(RGB_FG(200, 200, 200) + POS(8, 14) + "HOST" + POS(26, 14) + "CHATTERS")
	stdout.write(RGB_FG(255, 100, 100) + POS(8, 16) + "Host your own room")
	stdout.flush()
	
	cursor = 0
	tick = 0
	oldlen = 0
	
	while True:
		if tick % 50 == 0 or oldlen != len(network.host_list):
			cursor = max(0, min((len(network.host_list)), cursor))
			
			for i in range(MAX_HOSTS-1):
				stdout.write(POS(6, 17 + i) + (" " * 30))
			for i, h in enumerate(network.host_list):
				stdout.write(POS(8, 17 + i) + RGB_FG(100, 150, 255) + h[0])
				stdout.write(POS(28, 17 + i) + (RGB_FG(100, 255, 100) if h[2] < MAX_CHATTERS else RGB_FG(50, 50, 50)) + f"{h[2]: >2}/{MAX_CHATTERS}")
		
		stdout.write(POS(6, 16 + cursor) + RGB_FG(255, 200, 0) + (">" if tick // BLINK_SPEED % 2 != 0 else " "))
		stdout.flush()
		
		tick += 1
		
		if msvcrt.kbhit():
			u = msvcrt.getch()
			if u == b"\xE0" or u == b"000":
				u = msvcrt.getch()
				if u == b"H":
					cursor = max(0, cursor - 1)
				elif u == b"P":
					cursor = min((len(network.host_list)), cursor + 1)
				for i in range(MAX_HOSTS):
					stdout.write(POS(6, 16 + i) + " ")
			elif u == b"\r":
				break
		
		oldlen = len(network.host_list)
		time.sleep(TICK_SPEED)
	
	stdout.write(POS(6, 16 + cursor) + RGB_FG(255, 200, 0) + ">")
	stdout.write(POS(3, 37) + RGB(50, 220, 255, 0, 0, 0) + "Connecting...")
	stdout.flush()
	
	join_room(cursor)


def join_room(room_id):
	network.terminate_udp_listen()
	
	if room_id == 0:
		try:
			network.init_tcp()
		except OSError:
			ret = "Already hosting on this machine"
		else:
			network.listen_tcp()
			network.broadcast_udp(client_name, client_color)
			network.connect_tcp(client_name, "localhost", PORT)
			ret = chat_room(client_name, client_color)
	else:
		network.connect_tcp(client_name, *network.host_list[room_id-1][3:5])
		ret = chat_room(*network.host_list[room_id-1][0:2])
	
	network.terminate_broadcast(client_name)
	network.terminate_tcp_all()
	network.listen_udp()
	menu_screen()
	prompt_host(ret)


def chat_room(room_name, room_color):
	
	stdout.write(CLR_SCR())
	stdout.write(CURSOR(False))
	
	stdout.write(RGB_BG(0, 0, 0) + POS(1, 1) + (" " * WIDTH * HEIGHT))
	stdout.write(RGB_BG(100, 100, 100) + POS(1, 1) + (" " * WIDTH * 2))
	stdout.write(COL(room_color) + POS(2, 2) + room_name + RGB_FG(255, 255, 255) + "'s room")
	stdout.write(POS(1, 3) + ("═" * WIDTH))
	
	stdout.write(POS(1, HEIGHT - 4) + ("═" * WIDTH))
	stdout.write(POS(1, HEIGHT - 3) + (" " * WIDTH * 4))
	stdout.write(RGB_FG(150, 150, 150) + POS(2, HEIGHT - 3) + "SEND MESSAGE")
	
	stdout.flush()
	
	buf_dirty = True
	out_dirty = True
	msg_buffer = []
	out_string = ""
	out_cursor = 0
	scroll = 0
	tick = 0
	room_size = 0
	
	while True:
		if len(network.data_queue) >= 1 and network.data_queue[-1][0] == b"\xE0":
			err = network.data_queue[-1][1]
			network.data_queue.clear()
			return err
		
		while len(network.data_queue) >= 1:
			d = network.data_queue.pop(0)
			if d[0] == b"\x00":
				color, name, msg = d[1].split("\n")[:3]
				
				un = re.findall("__.*?__", msg)
				for u in un:
					msg = msg.replace(u, UNDER(True) + u[2:-2] + UNDER(False), 1)
				
				lines = process_words(msg, f"{COL(int(color))}{name}{RGB_FG(255, 255, 255)}: {RGB_FG(220, 220, 220)}", WIDTH - len(name) - 4, WIDTH - 2)
				
				msg_buffer.extend(lines)
				msg_buffer.append("")
				if scroll > 0:
					scroll = max(0, min(len(msg_buffer) - HEIGHT+10, scroll + len(lines) + 1))
				buf_dirty = True
				
			elif d[0] == b"\x10":
				msg_buffer.append("")
				msg_buffer.append(f"{RGB_FG(255, 200, 0)}{d[1] + ' joined the room': >{WIDTH - 3}}")
				msg_buffer.append("")
				msg_buffer.append("")
				if scroll > 0:
					scroll = max(0, min(len(msg_buffer) - HEIGHT+10, scroll + 4))
				room_size += 1
				buf_dirty = True
				
			elif d[0] == b"\x11":
				msg_buffer.append("")
				msg_buffer.append(f"{RGB_FG(255, 200, 0)}{d[1] + ' left the room': >{WIDTH - 3}}")
				msg_buffer.append("")
				msg_buffer.append("")
				if scroll > 0:
					scroll = max(0, min(len(msg_buffer) - HEIGHT+10, scroll + 4))
				room_size -= 1
				buf_dirty = True
		
		if buf_dirty:
			buf_dirty = False
			stdout.write(POS(WIDTH - 5, 2) + RGB(255, 255, 255, 100, 100, 100) + f"{room_size: >2}/{MAX_CHATTERS}")
			stdout.write(RGB_BG(0, 0, 0) + POS(1, 4) + (" " * WIDTH * (HEIGHT-8)))
			stdout.write(RGB(255, 255, 255, 0, 0, 0))
			
			for i, b in enumerate(msg_buffer[-HEIGHT+10 - scroll:None if scroll == 0 else -scroll]):
				stdout.write(POS(2, 5 + i) + b)
		
		if msvcrt.kbhit():
			out_dirty = True
			u = msvcrt.getch()
			
			if u in bytes(CHARS, "ascii") and len(out_string) < MSG_MAX_LEN:
				if out_cursor == 0:
					out_string = out_string + str(u, "ascii")
				else:
					out_string = out_string[:-out_cursor] + str(u, "ascii") + out_string[-out_cursor:]
				
			elif u == b"\x08":
				if out_cursor == 0:
					out_string = out_string[:-1]
				else:
					out_string = out_string[:-out_cursor-1] + out_string[-out_cursor:]
				
			elif u == b"\xE0" or u == b"000":
				u = msvcrt.getch()
				if u == b"K": #left
					out_cursor = min(len(out_string), out_cursor + 1)
					
				elif u == b"M": #right
					out_cursor = max(0, out_cursor - 1)
					
				elif u == b"I" or u == b"H": #page up / up
					scroll = max(0, min(len(msg_buffer) - HEIGHT+10, scroll + SCROLL_SPEED))
					buf_dirty = True
					
				elif u == b"Q" or u == b"P": #page down / down
					scroll = max(0, scroll - SCROLL_SPEED)
					buf_dirty = True
					
				elif u == b"O": #end
					scroll = 0
					buf_dirty = True
					
				elif u == b"S": #DEL
					if out_cursor == 1:
						out_string = out_string[:-1]
						out_cursor -= 1
					elif out_cursor > 1:
						out_string = out_string[:-out_cursor] + out_string[-out_cursor+1:]
						out_cursor -= 1
					
			elif u == b"\r" and out_string.replace(" ", "") != "":
				network.send_tcp(client_name, client_color, out_string)
				out_string = ""
				out_cursor = 0
					
			elif u == b"\x1B":
				return ""
		
		out_lines = process_words(out_string, "", WIDTH - 2, WIDTH - 2)
		c = out_cursor
		cursor_line = 0
		for i, l in enumerate(out_lines[::-1]):
			c -= len(l)
			if c < 0:
				cursor_line = len(out_lines) - i - 1
				break
		
		if out_dirty:
			out_dirty = False
			stdout.write(RGB_BG(100, 100, 100) + POS(1, HEIGHT - 2) + (" " * WIDTH * 3))
			
			if len(out_lines) == 1:
				stdout.write(RGB(255, 255, 255, 100, 100, 100) + POS(2, HEIGHT - 2) + out_lines[-1])
			else:
				stdout.write(RGB(255, 255, 255, 100, 100, 100) + POS(2, HEIGHT - 2) + out_lines[-2 if cursor_line == len(out_lines)-1 else cursor_line])
				stdout.write(RGB(255, 255, 255, 100, 100, 100) + POS(2, HEIGHT - 1) + out_lines[-1 if cursor_line == len(out_lines)-1 else cursor_line + 1])
		
		stdout.write(POS(2 + len(out_lines[cursor_line]) - out_cursor + sum(len(l) for l in out_lines[-1:cursor_line:-1]), HEIGHT - (2 if len(out_lines) == 1 or cursor_line != len(out_lines)-1 else 1)) + CURSOR(tick // BLINK_SPEED % 2 == 0))
		stdout.flush()
		
		tick += 1
		
		time.sleep(TICK_SPEED)


def process_words(msg, start, remain, width):
	lines = []
	s = start
	
	words = re.findall("[^ .?!:,;-]*[ .?!:,;-]*", msg)
	
	for w in words:
		if len(w) <= remain:
			s += w
			remain -= len(w)
		else:
			if len(w) > width:
				s += w[:remain]
				lines.append(s)
				s, w = "", w[remain:]
				
				while len(w) > width:
					temp, w = w[:width], w[width:]
					lines.append(temp)
				
			else:
				lines.append(s)
			
			s = w
			remain = width - len(w)
	
	lines.append(s)
	return lines



if __name__ == "__main__":
	try:
		init()
		input()
	except (KeyboardInterrupt, SystemExit):
		network.terminate_broadcast(client_name)
		network.terminate_udp_listen()
		network.terminate_tcp_all()
		raise
