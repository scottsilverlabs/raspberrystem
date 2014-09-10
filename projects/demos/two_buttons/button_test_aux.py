#!/usr/bin/env python

import curses, time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main(stdscr):
	# Clear screen
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)

	stdscr.addstr("Button Tester", curses.A_REVERSE)
	stdscr.chgat(-1, curses.A_REVERSE)

	#stdscr.addstr(curses.LINES-1, 0, "Press 'Q' to quit")

	stdscr.nodelay(1)  # make getch() non-blocking

	# set up window to bounce ball
	ball_win = curses.newwin(curses.LINES-2, curses.COLS, 1, 0)
	ball_win.box()

	#ball_win.addch(curses.LINES-1,curses.COLS-1, ord('F'))

	# Update the internal window data structures
	stdscr.noutrefresh()
	ball_win.noutrefresh()

	# Redraw the screen
	curses.doupdate()

	box_LINES, box_COLS = ball_win.getmaxyx()

	ball_x, ball_y = (int(box_COLS/2), int(box_LINES/2))

	while True:
		# Quit if 'Q' was pressed
		c = stdscr.getch()
		if c == ord('Q') or c == ord('q'):
			break

		# remove previous location of ball
		ball_win.addch(ball_y, ball_x, ord(' '))

		stdscr.addstr(curses.LINES-1, 0, "Press 'Q' to quit   |   Left: {0} Right: {1}".format(not GPIO.input(23), not GPIO.input(18)))

		if not GPIO.input(23) and ball_x > 1:
			ball_x -= 1
		if not GPIO.input(18) and ball_x < box_COLS-2:
			ball_x += 1

		# update ball location
		ball_win.addch(ball_y, ball_x, ord('0'))

		# Refresh the windows from the bottom up
		stdscr.noutrefresh()
		ball_win.noutrefresh()
		curses.doupdate()

	# Restore the terminal
	curses.nocbreak()
	curses.echo()
	curses.curs_set(1)
	curses.endwin()

	#stdscr.refresh()
	#stdscr.getkey()

curses.wrapper(main)
