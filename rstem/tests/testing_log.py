from os.path import expanduser
import time
import os

log = None

def log_name():
    global log
    log_dir = expanduser("~/rstem_logs/")
    symlink_name = log_dir + 'testlog.txt'
    log_file_name = 'testlog.' + str(int(time.time())) + '.txt'
    return (log_dir, symlink_name, log_file_name)
    
def new():
    global log
    log_dir, symlink_name, log_file_name = log_name()
    print('Creating new log:', log_file_name)
    os.makedirs(log_dir, exist_ok=True)
    try: 
        os.remove(symlink_name)
    except: pass
    os.symlink(log_file_name, symlink_name)
    log = open(log_dir + log_file_name, 'w')

def write(func, result):
    global log
    log.write(str(func) + str(result) + '\n')

def close():
    global log
    log.close()

def dump():
    global log
    log_dir, symlink_name, log_file_name = log_name()
    with open(symlink_name) as log:
        for line in log:
            print(line)
