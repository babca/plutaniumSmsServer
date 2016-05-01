# plutaniumSmsServer
Plutanium SMS Server is a daemon which connects to your USB 3G modem and Gmail and lets you redirect your Gmail to SMS, and SMS to SMS, making your own smart SMS gateway. Your GSM modem can be hooked up on local or remote machine, or on Mikrotik router. Implemented as a linux daemon, written in Python.

Only documentation is open sourced at the moment. If you are interested in the library let me know!

##Getting started

### Local serial port setup

### Remote serial port setup

#### remote side (modem)
Share modem over LAN.

**mikrotik**
http://babcuvpisecek.com/nezarazene/access-a-gsm-modem-connected-to-mikrotik-device-over-lan/

**debian**
install ser2net
edit setting file /etc/ser2net.conf
3002:telnet:600:/dev/ttyUSB2:115200 8DATABITS NONE 1STOPBIT banner
then run
ser2net -c /etc/ser2net.conf -n

#### local side (smsserver)
Setup virtual port.

**OS X**
brew install socat
use socat 

**linux**
use socat 

#### check serial connection

screen /dev/ttyUSB0 9600
screen /dev/ttyUSB1 9600
screen /dev/ttyUSB2 9600

For Huawei E372, /dev/ttyUSB2 is for choice. /dev/ttyUSB0 port works too, but it lacks some features like sms notifications, call notifications and signal strength notifications.

then try to connect from Python. PySerial module must be installed first, see below.
python -m serial.tools.miniterm /dev/ttyUSB0
python -m serial.tools.miniterm /dev/ttyUSB1
python -m serial.tools.miniterm /dev/ttyUSB2 ... muze nefungovat kvuli bugu v pyserial 3.0.1, nutno mit 3.1a1 nebo starsi 2.7

If it fails to connect, then there is a problem with PySerial module.
PySerial 2.7 until 3.0.1 have a bug, use newer version, see below.


## Requirements

install python 2.7.10+

upgrade pip
$ pip install --upgrade pip

### install dependencies

$ pip install pyserial        ////// see below
$ pip install python-gsmmodem ////// see below
$ pip install pep3143daemon
$ pip install google-api-python-client
$ pip install requests
$ pip install requests_jwt
$ pip install python-dateutil

pyserial must be 3.1a0 and newer, older versions fail to connect to some port.
git clone https://github.com/pyserial/pyserial
cd pyserial
$ python setup.py install

python-gsmmodem must be a github fork from jeromez80
git clone https://github.com/jeromez80/python-gsmmodem
cd pyserial
$ python setup.py install

### try sms handler demo

$ python sms_handler_demo.py


### create Gmail account and activate Gmail API

1. create Gmail account

2. enable Gmail API

3. create a new file quickstart.py with contents available here:
https://developers.google.com/gmail/api/quickstart/python

4. and run it
$ python quickstart.py --noauth_local_webserver

5. it prints URL, open the URL in your browser, login to your gmail account and paste the code there

6. a token file client_secret.json will be generated

7. place the token file to the directory with sms server python files

### check setting file


### first run

run on foreground:
$ python gmail2smsDaemon.py fg

run as linux daemon:
$ python gmail2smsDaemon.py start
$ python gmail2smsDaemon.py status
$ python gmail2smsDaemon.py reload
$ python gmail2smsDaemon.py stop

see log file:
$ tail -f /var/log/gmail2sms.log 

### misc

list python processes:
$ ps aux | grep python

check versions of installed python modules:
pip freeze
