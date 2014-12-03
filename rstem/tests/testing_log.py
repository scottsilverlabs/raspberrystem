from os.path import expanduser
import time
import os
import csv

class TestLogger:
    def __init__(self):
        log_dir, symlink_name, log_file_name = self._log_name()
        print('Creating new log:', log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        try: 
            os.remove(symlink_name)
        except: pass
        os.symlink(log_file_name, symlink_name)
        self.log_file = open(symlink_name, 'w')
        self.log = csv.writer(self.log_file, delimiter=',', quotechar='"')

    def _log_name(self):
        log_dir = expanduser("~/rstem_logs/")
        symlink_name = log_dir + 'testlog.txt'
        log_file_name = 'testlog.' + str(int(time.time())) + '.txt'
        return (log_dir, symlink_name, log_file_name)
        
    def write(self, func, result):
        self.log.writerow([str(func), str(result)])

    def close(self):
        self.log_file.close()

    def dump(self):
        log_dir, symlink_name, log_file_name = self._log_name()
        with open(symlink_name) as log:
            for row in csv.reader(log):
                print(row)

logger = None

def create():
    global logger
    logger = TestLogger()
    
def write(func, result):
    global logger
    logger.write(func, result)

def close():
    global log
    logger.close()

def dump():
    global log
    logger.dump()

