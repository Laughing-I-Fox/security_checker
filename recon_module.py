from getmac import get_mac_address as gma
from requests import get
import ipaddress
import requests
from scapy.all import *
from scapy.layers.l2 import Ether, ARP
import getpass as gp

USER_NAME = gp.getuser()


def ip_finder():
    ip = get('https://api.ipify.org').content.decode('utf8')
    try:
        return '{}'.format(ip)
    except:
        return 'Can not find ip'


# variable for hostname
hostname = socket.gethostname()
# variable for local IP
local_ip = socket.gethostbyname(hostname)
# variable for subnet mask in local network
net_mask = ipaddress.IPv4Network(local_ip).netmask
# variable for mac address host machine
mac_hostname = gma()
# variable for public IP
public_ip = ip_finder()


# find country of public IP
def country_finder(ip):
    endpoint = f'https://ipinfo.io/{ip}/json'
    response = requests.get(endpoint, verify=True)
    if response.status_code != 200:
        return 'cannot find country'
    data = response.json()
    return data['country']


# variable for general host info
host_info = f'name: {hostname} local IP: {local_ip} subnet mask: {net_mask} mac: {mac_hostname} public IP: {public_ip}' \
            f' country: {country_finder(public_ip)} '

print(host_info)


def arp_monitor_callback(pkt, ARP=None):
    list_devices = []
    if ARP in pkt and pkt[ARP].op in (1, 2):  # who-has or is-at
        list_devices.append(pkt.sprintf("%ARP.hwsrc% %ARP.psrc%"))
        return list_devices


print(sniff(prn=arp_monitor_callback, filter="arp", store=0))


#
def arp_scan(ip):
    local_dev = open(f'C:/Users/{USER_NAME}/Downloads/local_devices.txt', 'a')
    request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans, un_ans = srp(request, timeout=2, retry=1)
    result = []

    for sent, received in ans:
        if received.hwsrc not in 'MAC':
            result.append({'IP': received.psrc, 'MAC': received.hwsrc})
        else:
            continue
    print(result, file=local_dev)
    for i in result:
        print(i['MAC'])
    # print(result[0]['MAC'])


arp_scan('192.168.0.18/24')
