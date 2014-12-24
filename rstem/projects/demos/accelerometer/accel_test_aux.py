#!/usr/bin/env python

import curses, time
from rstem import accel

accel.init(1)
THRESHOLD = 3

def main(stdscr):
	# Clear screen
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)

	stdscr.addstr("Accelerometer Tester", curses.A_REVERSE)
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

		angles = accel.angles()
		x_diff = angles[0]
		y_diff = angles[1]

		stdscr.addstr(curses.LINES-1, 0, "Press 'Q' to quit   |   Roll: {0: < 8.4f} Pitch: {1: < 8.4f}".format(x_diff, y_diff))

		if x_diff > THRESHOLD and ball_x < box_COLS-2:
			ball_x += 1
		elif x_diff < -THRESHOLD and ball_x > 1:
			ball_x -= 1
		if y_diff > THRESHOLD and ball_y > 1:
			ball_y -= 1
		elif y_diff < -THRESHOLD and ball_y < box_LINES-2:
			ball_y += 1

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
