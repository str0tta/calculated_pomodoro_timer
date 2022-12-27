from sympy import symbols, solve_linear
from datetime import datetime, timedelta
from flask import Flask
from time import sleep
from os import environ
from threading import Thread
from dotenv import load_dotenv

# general equation to calculate a pomodoro set of sessions: 5x + x + d1 + 5x + x + d2 + 5x + x + d3 + 5x + 4x = t_tot
# where
# x = short pause
# d{1..3} = delay in starting the timer again
# t_tot = total number of minutes in a sessions set

load_dotenv() # loads the environment variables from the (MANDATORY!!!) .env file.

x = symbols('x')
s1 = None # total duration of the first pomodoro session of the set (focus time + short pause)
d1 = None # delay in seconds between the end of the first session and the start of the second one. This also includes all the time that passes during the first session while the timer is paused
s2 = None # total duration of the second pomodoro session of the set (focus time + short pause)
d2 = None # delay in seconds between the end of the second session and the start of the third one. This also includes all the time that passes during the second session while the timer is paused
s3 = None # total duration of the third pomodoro session of the set (focus time + short pause)
d3 = None # delay in seconds between the end of the third session and the start of the fourth one. This also includes all the time that passes during the third session while the timer is paused
s4 = None # total duration of the fourth pomodoro session of the set (focus time + long pause)
t_tot = None # total time of four pomodoro sessions
eq = None # this object represents the equation used by SymPy to calculate the session durations
passed_timer = None # a timedelta - basically a timespan - object representing how much time has already passed
target_timer = None # a timedelta object which represents our goal
short_pause = None # the length of the short pause, which represents the "x" of the equations which keeps everything glued
session_id = None # the session number (1-2-3-4)
timer_ticking = None # True if the time is ongoing, False if it's paused
pause_phase = None # True if we're during the pause of a session, False otherwise

app = Flask(__name__)

def calculate_h_max(hh):
    new_day = False
    if 9 <= hh < 11:
        h_max = 11
    elif 11 <= hh < 13:
        h_max = 13
    elif 14 <= hh < 16:
        h_max = 16
    elif 16 <= hh < 18:
        h_max = 18
    elif 22 <= hh < 0:
        h_max = 0
        new_day = True
    elif 0 <= hh < 2:
        h_max = 2
    else:
        return 'Out of Work!'
    return (h_max, new_day)

# Initializes all the variables of the system.
def init_kernel():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, session_id
    """
    In order to determine t_tot, let's split the whole day in some fixed time spans:
    
    - 9am-11
    - 11-13
    - 14-16
    - 16-18
    - 22-24
    - 24-2am
    
    We are choosing spans of two hours because the algorithm works fine with such a disposition, but this might be changed, if desired.
    The span between 2:01am and 8:59am is considered to be sleeping time.
    The span between 13:01 and 13:59 is considered to be a lunch break.
    The span between 18:01 and 21:59 is considered to be dinner & free time (e.g. gym) time.
    During these three classes of timespans, the application cannot be used.
    """
    yyyy, mm, dd, hh = (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour)
    # h_max: the hour we need to reach to end the session set
    # new_day: if this is True, the end of the session set lies in a new day
    h_max, new_day = calculate_h_max(hh)

    dt_goal = datetime(yyyy, mm, dd, h_max, 0, 0) # the target date in which the session set will end
    if new_day:
        dt_goal += timedelta(days=1)

    t_tot = dt_goal - datetime.now().replace(second=0)
    s1 = 5*x+x
    d1 = 0
    s2 = 5*x+x
    d2 = 0
    s3 = 5*x+x
    d3 = 0
    s4 = 5*x+4*x

    session_id = None # this is set as None in order to start a session set from the session 1

# Solves the equation of the session set giving the current value of x.
def xval():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq
    eq = solve_linear(s1 + d1 + s2 + d2 + s3 + d3 + s4, t_tot.seconds)
    return float(eq[1])

# Handles the timer tick - a tick occurs once per second.
def timer_tick():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause,pause_phase
    if not timer_ticking and session_id is None:
        return
    if session_id is None:
        calc_new_session()
    else:
        if session_id == 1:
            if not timer_ticking: d1 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 2:
            if not timer_ticking: d2 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 3:
            if not timer_ticking: d3 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 4:
            if timer_ticking: passed_timer += timedelta(seconds=1)
    if passed_timer.seconds == target_timer.seconds:
        handle_session_end()
    remaining_time = target_timer - passed_timer
    if ((remaining_time.seconds <= short_pause) or (remaining_time.seconds <= 4 * short_pause and session_id == 4)) and remaining_time.seconds > 0:
        pause_phase = True
        pass # TODO: Report that the focus time has ended and the user can now have a pause (be it short or long)
    else:
        pause_phase = False

# Handles the end of a session, giving feedbacks to the user.
def handle_session_end():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    timer_ticking = False
    pass # TODO: Report that the session ended

# Lets user know how much time is still remaining for the current session to end, in a human readable way.
@app.route('/remaining')
def to_string():
    if calculate_h_max(datetime.now().hour) == 'Out of Work!':
        return '【 Out of Work! 】'
    global target_timer, passed_timer, timer_ticking, session_id, pause_phase
    if target_timer is None:
        return '【 --:--:-- (no active sessions) 】'
    if target_timer.seconds == passed_timer.seconds == 0:
        return '【 --:--:-- (no active sessions) 】'
    remaining_time = target_timer - passed_timer
    minute, second = divmod(remaining_time.seconds, 60)
    phase_str = f'session {session_id} '
    if pause_phase:
        phase_str += f'| {"short" if session_id != 4 else "long"} pause'
    phase_str = phase_str.strip()
    duration = f'00:{str(minute).zfill(2)}:{str(second).zfill(2)}'

    return '【 ' + duration + ' ' + f'({phase_str})' + ' 】'

# Calculates the duration of the first pomodoro session (focus time + short pause).
def calc_s1():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s1 = s1.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=float(s1))
    session_id = 1

# Calculates the duration of the second pomodoro session (focus time + short pause).
def calc_s2():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s2 = s2.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=float(s2))
    session_id = 2

# Calculates the duration of the third pomodoro session (focus time + short pause).
def calc_s3():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s3 = s3.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=float(s3))
    session_id = 3

# Calculates the duration of the fourth pomodoro session (focus time + long pause).
def calc_s4():
    global x, s1, d1, s2, d2, s3, d3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s4 = s4.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=float(s4))
    session_id = 4

# Calculates the duration of the next pomodoro session, basing on the current session.
def calc_new_session():
    if session_id is None:
        init_kernel()
        calc_s1()
    elif session_id == 1:
        calc_s2()
    elif session_id == 2:
        calc_s3()
    elif session_id == 3:
        calc_s4()
    elif session_id == 4:
        init_kernel()
        calc_new_session()

# Starts/pauses the timer.
@app.route('/toggle')
def toggle_timer():
    global timer_ticking, passed_timer, target_timer
    if calculate_h_max(datetime.now().hour) == "Out of Work!":
        raise Exception("Out of Work!")
    timer_ticking = not timer_ticking
    pass # TODO: handle timer start and stop sound effects
    if target_timer is None or passed_timer is None: # at this stage, the application is not ready yet to handle differences between timespans
        return ''
    remaining_time = target_timer - passed_timer
    if remaining_time.seconds == 0:
        calc_new_session()
        pass # TODO: handle new session sound effects
    return ''

# Ticks the timer once per second.
def poll_ticking():
    while True:
        timer_tick()
        sleep(1)

######## MAIN PROGRAM FLOW ########

Thread(target=poll_ticking).start()
app.run(host=environ.get('IP_ADDRESS'), port=int(environ.get('PORT')), debug=False)