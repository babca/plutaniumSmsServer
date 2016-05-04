# plutaniumSmsServer
Plutanium SMS Server is a daemon which connects to your USB 3G modem and Gmail and lets you redirect your Gmail to SMS, and SMS to SMS, making your own smart SMS gateway. Your GSM modem can be hooked up on local or remote machine, or on Mikrotik router. Implemented as a linux daemon, written in Python.

Only documentation is open sourced at the moment. If you are interested in the library let me know!

#Getting started

1. make you modem working over serial port
2. test the port with screen

* OS X same commands, but sudo needed everywhere

**debian**
curently tested on Debian.
easy_install pip

**OS X**
sudo easy_install pip


## Local serial port setup

Check serial connection:

```bash
screen /dev/ttyUSB0 9600
screen /dev/ttyUSB1 9600
screen /dev/ttyUSB2 9600
```

For Huawei E372, /dev/ttyUSB2 is your choice. /dev/ttyUSB0 port works too, but it lacks some features like sms notifications, call notifications and signal strength notifications.


## Remote serial port setup
Going to have GSM modem hooked up to a different machine?
Share the serial port of the GSM modem over the network and connect to it with socat command.
Future versions will have this included.

#### remote side (modem)
Share modem over LAN.

**share from mikrotik routeros**
http://babcuvpisecek.com/nezarazene/access-a-gsm-modem-connected-to-mikrotik-device-over-lan/

**share from debian**
* install ser2net
* edit setting file /etc/ser2net.conf
* ```
  3002:telnet:600:/dev/ttyUSB2:115200 8DATABITS NONE 1STOPBIT banner
  ```
* then run
  ```bash
  ser2net -c /etc/ser2net.conf -n
  ```

#### local side (smsserver)
Setup virtual serial port (pseudo terminal).

Try creating virtual port manually first.

**debian**
```bash
socat -d -d -d -d pty,link=/dev/vmodem0,raw tcp:<IP>:<PORT>
socat pty,link=/dev/vmodem0,raw tcp:<IP>:<PORT> &
screen /dev/vmodem0 9600
```

**OS X**
```bash
brew install socat
sudo socat -d -d -d -d pty,link=/dev/vmodem0,raw tcp:<IP>:<PORT>
sudo socat pty,link=/dev/vmodem0,raw tcp:<IP>:<PORT> &
sudo screen /dev/vmodem0 9600
```

I had a small issue with `screen` on os x, I had to leave `screen` with `Ctrl+A K` instead of `Ctrl+A D`, and it kills socat too, so you must start socat again every time.

If it's working, then place the command to INI setting file. SMS server will now setup the virtual port automatically every time it starts.


## Requirements

install python 2.7.10+

upgrade pip
```bash
$ pip install --upgrade pip
```

### install dependencies

```bash
$ pip install httplib2
$ pip install pyserial        ////// see below
$ pip install python-gsmmodem ////// see below
$ pip install pep3143daemon
$ pip install google-api-python-client
$ pip install requests
$ pip install requests_jwt
$ pip install python-dateutil
```

on os x, there can be an issue with old preinstalled six module, use:
```bash
$ sudo pip install google-api-python-client --ignore-installed six (on OS X El Capitan)
$ sudo pip uninstall six
$ sudo pip install six  // to upgrade six to current version
```

pyserial must be 3.1a0 and newer, older versions fail to connect to some port.
```
git clone https://github.com/pyserial/pyserial
cd pyserial
$ python setup.py install
```

python-gsmmodem must be a github fork from jeromez80

```
git clone https://github.com/jeromez80/python-gsmmodem
cd pyserial
$ python setup.py install
```

### try sms handler demo

```bash
$ python sms_handler_demo.py
```

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

need edit, todo: new location ~/.credentials/plutaniumSmsServerGmailApiCredentials.json

### Test if PySerial library is working
after setting then try to connect from Python. PySerial module must be installed first, see below.
```bash
python -m serial.tools.miniterm /dev/ttyUSB0
python -m serial.tools.miniterm /dev/ttyUSB1
python -m serial.tools.miniterm /dev/ttyUSB2
```

> `IOError: [Errno 25] Inappropriate ioctl for device`

If it fails to connect to /dev/ttyUSB2, then there is a problem with PySerial module. Try to install different versions. PySerial 2.7 - 3.0.1 are having a trouble connecting to some ports.

**Debian** PySerial 3.1a0 is working good. Version 3.0.1 doesn't.
**OS X** PySerial 2.7 works good. Version 3.1a0 doesn't.


### check setting file

all settings here.


### first run

run on foreground:
```bash
$ python server.py fg
```

run as linux daemon:
```bash
$ python server.py start
$ python server.py status
$ python server.py reload
$ python server.py stop
```

see log file:
```bash
$ tail -f /var/log/gmail2sms.log 
```

### troubleshooting

> I'm on OS X and ... prints permissions error.

Use sudo with every command.

### misc

list python processes:
```bash
$ ps aux | grep python
```

check versions of installed python modules:
```bash
pip freeze
```