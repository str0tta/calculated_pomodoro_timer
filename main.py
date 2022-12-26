from sympy import symbols, solve_linear
from datetime import datetime, timedelta
from time import sleep

# general equation to calculate a pomodoro set of sessions: 5x+x+r1+5x+x+r2+5x+x+r3+5x+4x=t_tot
# where
# x = short pause
# r{1..3} = delay in starting the timer again
# t_tot = total number of minutes in a sessions set

x = symbols('x')
s1 = None
r1 = None
s2 = None
r2 = None
s3 = None
r3 = None
s4 = None
t_tot = None
eq = None
target_timer = None # quanto tempo deve passare fino alla fine dell'attuale timer?
passed_timer = None # quanto tempo è già passato?
short_pause = None # quant'è la pausa breve (che nel sistema costituisce unità di tempo)?
session_id = None # sessione 1-2-3-4?
timer_ticking = None # timer attivo/in pausa?

def init_kernel():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, session_id
    """
    In order to determine t_tot, let's split the whole day in some fixed time spans:
    
    - 9-11
    - 11-13
    - 14-16
    - 16-18
    - 22-24
    - 24-2am
    
    We are choosing spans of two hours because the algorithm works fine with such a disposition, but this might be changed as desired.
    The span between 2:01am and 8:59am is considered to be sleeping time.
    The span between 13:01 and 13:59 is considered to be a lunch break.
    The span between 18:01 and 21:59 is considered to be dinner & free time (e.g. gym) time.
    """
    yyyy, mm, dd, hh = (datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour)
    h_max = -1 # the hour we need to reach to end the session set
    new_day = False # if this is True, the end of the session set lies in a new day
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
        raise Exception("Out of work!")

    dt_goal = datetime(yyyy, mm, dd, h_max, 0, 0) # the target date in which the session set will end
    if new_day:
        dt_goal += timedelta(days=1)

    t_tot = dt_goal - datetime.now().replace(second=0)
    s1 = 5*x+x
    r1 = 0
    s2 = 5*x+x
    r2 = 0
    s3 = 5*x+x
    r3 = 0
    s4 = 5*x+4*x

    session_id = None # this is set as None in order to start a session set from the session 1

def xval():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq
    eq = solve_linear(s1 + r1 + s2 + r2 + s3 + r3 + s4, t_tot)
    return float(eq[1])

def timer_tick():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    if not timer_ticking and session_id is None:
        return
    if session_id is None:
        calc_new_session()
    else:
        if session_id == 1:
            if not timer_ticking: r1 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 2:
            if not timer_ticking: r2 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 3:
            if not timer_ticking: r3 += 1
            if timer_ticking: passed_timer += timedelta(seconds=1)
        elif session_id == 4:
            if timer_ticking: passed_timer += timedelta(seconds=1)
    if passed_timer.seconds == target_timer.seconds:
        handle_timer_end()
    elif (passed_timer.seconds == short_pause) or (passed_timer.seconds == 4 * short_pause and session_id == 4):
        pass # TODO: Report that the focus time has ended and the user can now have a pause (be it short or long)

def handle_timer_end():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    timer_ticking = False
    pass # TODO: Report that the session ended

def to_string():
    pass

def calc_s1():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s1 = s1.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=s1)
    session_id = 1
    timer_ticking = False

def calc_s2():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s2 = s2.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=s2)
    session_id = 2
    timer_ticking = False

def calc_s3():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s3 = s3.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=s3)
    session_id = 3
    timer_ticking = False

def calc_s4():
    global x, s1, r1, s2, r2, s3, r3, s4, t_tot, eq, passed_timer, target_timer, session_id, timer_ticking, short_pause
    short_pause = xval()
    s4 = s4.subs({x: short_pause})
    passed_timer = timedelta(seconds=0)
    target_timer = timedelta(seconds=s4)
    session_id = 4
    timer_ticking = False

def calc_new_session():
    if session_id is None:
        init_kernel()
        calc_s1()
    elif session_id == 1:
        calc_s2()
    elif session_id == 2:
        calc_s3()
    elif session_id == 3:
        init_kernel()
        calc_new_session()

def start_timer():
    timer_status = True
    pass

def pause_timer():
    timer_status = False
    pass

#########################

while True:
    timer_tick()
    sleep(1)

#########################
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
s1 = s1.subs({x:40/9})
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
r1 = 3 # supponiamo che per 3 minuti, da quando finisce s1, ci dimentichiamo di riavviare il timer
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
s2 = s2.subs({x:4.30})
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
r2 = 0 # a sto giro siamo fulminei, 0 ritardo, neanche un microsecondo xd
s3 = s3.subs({x:4.30})
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
r3 = 14 # stavolta vuoi per un motivo vuoi per l'altro avviamo il timer dopo 14 minuti
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
s4 = s4.subs({x:2.74})
eq = solve_linear(s1+r1+s2+r2+s3+r3+s4, t_tot) ; print(eq)
# cerchiamo conferma...