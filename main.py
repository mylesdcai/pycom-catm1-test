import pycom
import socket
import ssl
import sys
import time
from network import LTE

BLACK = 0x000000
WHITE = 0xFFFFFF
RED = 0xFF0000
GREEN = 0x00FF00
BLUE = 0x0000FF
YELLOW = 0xFFFF00

# send AT command to modem and return response as list
def at(cmd):
    print("modem command: {}".format(cmd))
    r = lte.send_at_cmd(cmd).split('\r\n')
    r = list(filter(None, r))
    print("response={}".format(r))
    return r

def blink(rgb, n):
    for i in range(n):
        pycom.rgbled(rgb)
        time.sleep(0.25)
        pycom.rgbled(BLACK)
        time.sleep(0.1)

#####################################################################
print("CAT M1 Test - V0.6 - 4/20/18")

# input("")
# r = input("Enter anything to abort...")  # allow opportunity to stop program
# if r != "":
#    sys.exit(0)

print("disable MicroPython control of LED")
pycom.heartbeat(False)
pycom.rgbled(WHITE)

print("instantiate LTE object")
lte = LTE(carrier="verizon")
print("delay 4 secs")
time.sleep(4.0)

print("reset modem")
try:
    lte.reset()
except:
    print("Exception during reset")

print("delay 5 secs")
time.sleep(5.0)

if lte.isattached():
    try:
        print("LTE was already attached, disconnecting...")
        if lte.isconnected():
            print("disconnect")
            lte.disconnect()
    except:
        print("Exception during disconnect")

    try:
        if lte.isattached():
            print("detach")
            lte.dettach()
    except:
        print("Exception during dettach")

    try:
        print("resetting modem...")
        lte.reset()
    except:
        print("Exception during reset")

    print("delay 5 secs")
    time.sleep(5.0)

# enable network registration and location information, unsolicited result code
at('AT+CEREG=2')

# print("full functionality level")
at('AT+CFUN=1')
time.sleep(1.0)

# using Hologram SIM
at('AT+CGDCONT=1,"IP","hologram"')

print("attempt to attach cell modem to base station...")
# lte.attach()  # do not use attach with custom init for Hologram SIM

at("ATI")
time.sleep(2.0)

i = 0
while lte.isattached() == False:
    # get EPS Network Registration Status:
    # +CEREG: <stat>[,[<tac>],[<ci>],[<AcT>]]
    # <tac> values:
    # 0 - not registered
    # 1 - registered, home network
    # 2 - not registered, but searching...
    # 3 - registration denied
    # 4 - unknown (out of E-UTRAN coverage)
    # 5 - registered, roaming
    r = at('AT+CEREG?')
    try:
        r0 = r[0]  # +CREG: 2,<tac>
        r0x = r0.split(',')     # ['+CREG: 2',<tac>]
        tac = int(r0x[1])       # 0..5
        print("tac={}".format(tac))
    except IndexError:
        tac = 0
        print("Index Error!!!")

    # get signal strength
    # +CSQ: <rssi>,<ber>
    # <rssi>: 0..31, 99-unknown
    r = at('AT+CSQ')

    # extended error report
    # r = at('AT+CEER')

    if lte.isattached():
       print("Modem attached (isattached() function worked)!!!")
       break

    if (tac==1) or (tac==5):
       print("Modem attached!!!")
       break

    i = i + 5
    print("not attached: {} secs".format(i))

    if (tac != 0):
        blink(BLUE, tac)
    else:
        blink(RED, 5)

    time.sleep(2)

at('AT+CEREG?')
print("connect: start a data session and obtain an IP address")
lte.connect(cid=3)
i = 0
while not lte.isconnected():
    i = i + 1
    print("not connected: {}".format(i))
    blink(YELLOW, 1)
    time.sleep(1.0)

print("connected!!!")
pycom.rgbled(BLUE)

s = socket.socket()
s = ssl.wrap_socket(s)
print("get www.google.com address")
addr = socket.getaddrinfo('www.google.com', 443)
print(addr)
print("connect to {}".format(addr[0][-1]))
s.connect(addr[0][-1])
print("GET 50 bytes from google")
s.send(b"GET / HTTP/1.0\r\n\r\n")
print(s.recv(50))   # receive 50 bytes
print("close socket")
s.close()

try:
    lte.disconnect()
except:
    print("Exception during disconnect")

try:
    lte.dettach()
except:
    print("Exception during dettach")

# end of test, Red LED
print("end of test")

while True:
    blink(GREEN,5)
    time.sleep(1.0)
