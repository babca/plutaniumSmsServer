# plutaniumSmsServer
Plutanium SMS Server is a daemon which connects to your USB 3G modem and Gmail and lets you redirect your Gmail to SMS, and SMS to SMS, making your own smart SMS gateway. Your GSM modem can be hooked up on local or remote machine, or on Mikrotik router. Implemented as a linux daemon, written in Python.

Only documentation is open sourced at the moment. If you are interested in the library let me know!

# Getting started

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

### test if PySerial library is working
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

<table>
	<thead>
		<tr>
			<th> </th>
			<th>values</th>
			<th>default</th>
			<tH>desc.</tH>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>GMAIL_POLLING_INTERVAL</td>
			<td> </td>
			<td>30</td>
			<td> </td>
		</tr>
		<tr>
			<td>GMAIL_QUERY</td>
			<td> </td>
			<td> label:inbox is:unread</td>
			<td> label:inbox is:unread from:(mypersonal@email.com OR sms@mycompany.com)</td>
		</tr>
		<tr>
			<td>LOG_FILE</td>
			<td> </td>
			<td> </td>
			<td>main log</td>
		</tr>
		<tr>
			<td>LOG_FILE_SMS</td>
			<td> </td>
			<td> </td>
			<td>received/sent sms log</td>
		</tr>
		<tr>
			<td>LOG_LEVEL_FOREGROUND</td>
			<td> </td>
			<td> </td>
			<td>log level for the server run in foreground</td>
		</tr>
		<tr>
			<td>LOG_LEVEL_DAEMON</td>
			<td> </td>
			<td> </td>
			<td>log level for the server run as a service</td>
		</tr>
		<tr>
			<td>SMS_MIN_LENGTH</td>
			<td> </td>
			<td>1</td>
			<td>
				<p>type any number, e.g. 40 to process only 40+ long messages.<br />
					sms server doesn't process empty messages for default.<br />
					to enable processing empty messages, set the setting to 0.</p>
			</td>
		</tr>
		<tr>
			<td>SMS_MAX_LENGTH</td>
			<td> </td>
			<td>160</td>
			<td>feel free to set it to 250 and higher to turn long messages support on.</td>
		</tr>
		<tr>
			<td>CONVERT_TO_7BIT</td>
			<td> </td>
			<td>false</td>
			<td>if true, every email is converted to GSM7 for maximum chars per message</td>
		</tr>
		<tr>
			<td>SCOPES</td>
			<td> </td>
			<td> </td>
			<td>gmail api spe</td>
		</tr>
		<tr>
			<td>CLIENT_SECRET_FILE</td>
			<td> </td>
			<td> </td>
			<td>gmail api specific, you chose this value when enabling gmail api</td>
		</tr>
		<tr>
			<td>APPLICATION_NAME</td>
			<td> </td>
			<td> </td>
			<td>gmail api specific, you chose this value when enabling gmail api</td>
		</tr>
		<tr>
			<td>VIRTUAL_PORT_SETUP_COMMAND</td>
			<td> </td>
			<td> </td>
			<td>leave empty for locally attached device<br />
				or place here a proper socat command which works on your system. Test the command in the terminal first.
			</td>
		</tr>
		<tr>
			<td>PORT</td>
			<td> </td>
			<td>/dev/ttyUSB0</td>
			<td>
				<p>make sure you use the correct device dev path. For example, Huawei modems make more device paths. You may want use the last one.</p>
				<p>ls /dev/ttyUSB*</p>
			</td>
		</tr>
		<tr>
			<td>BAUDRATE</td>
			<td> </td>
			<td>115200</td>
			<td>
				<p>Current devices work on wide range of speeds, 115200 is a safe bet, there's no point in setting higher speeds.<br />
					Mikrotik users: If you are going to attach the modem to your Mikrotik and access it remotely, use 9600. My mikrotik doesn't support any other serial baud rate anyway. There's no apparent difference in real-life speed.</p>
			</td>
		</tr>
		<tr>
			<td>PIN</td>
			<td> </td>
			<td> </td>
			<td>leave empty if you don't use PIN<br />
				PIN setting is suppported, but not properly tested.
			</td>
		</tr>
		<tr>
			<td>SMS_HANDLER_MODE</td>
			<td> </td>
			<td> </td>
			<td>process this command as you wish in your SMS handler</td>
		</tr>
		<tr>
			<td>SMS_HANDLER_REDIRECT_TO</td>
			<td> </td>
			<td> </td>
			<td> </td>
		</tr>
		<tr>
			<td>SMS_HANDLER_CONVERT_TO_7BIT</td>
			<td> </td>
			<td> </td>
			<td> </td>
		</tr>
		<tr>
			<td>SMS_HANDLER_PROCESS_SMS_PREVIOUSLY_STORED_ON_SIM</td>
			<td>all | unread | (empty)</td>
			<td> </td>
			<td>Process also all sms stored on modem/sim, that might be received while sms server was not running.</td>
		</tr>
	</tbody>
</table>

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

### how does it work

Send an email to your API connected gmail mailbox and wait for the SMS server to process it.

1. Make sure the sender is on a whitelist (see `GMAIL_QUERY` setting).
2. Put SMS destination number into email *subject*.
3. Put SMS content into email *body* and send it.

SMS server polls the inbox every `GMAIL_POLLING_INTERVAL` and resends valid incoming message to a mobile number. The email is then set as read.

Default email handler can also read MIME messages, it reads the plaintext part out of the multipart email.

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