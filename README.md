# plutaniumSmsServer
Plutanium SMS Server is a daemon which connects to your USB 3G modem and Gmail and lets you forward your Gmail to SMS, and SMS to SMS, making your own smart SMS gateway. Your GSM modem can be hooked up on local or remote machine, or on Mikrotik router. Implemented as a linux daemon, written in Python.

Only documentation is open sourced at the moment. If you are interested in the library let me know!

##Use cases
* forward Gmail to SMS
* forward SMS to SMS
* make a smart SMS gateway. Send info sms from the gateway and make sure you won't miss any calls and sms sent back to the gateway number. Redirect everything to your work mobile number.
* process SMS keywords/regex and respond to it / send SMS elsewhere / call AJAX / call AJAX, process it and respond with useful information, and resend unrecognised messages to your work number
* make a simple SMS chat

##Features
* send and receive SMS
* unicode SMS
* multipart SMS
* strip any string to 7-bit GSM alphabet
* process SMS keywords
* fetch gmail
* well behaved linux daemon
* local or remote modem
* modem autoreconnect and reinit 
* log inbound, outbound sms

###Gmail2SMS
* connect to Gmail with Gmail API (you must generate access token)
* send emails do Gmail from your app, email title=targer number, body=sms content
* edit the Inbox query – filter senders, labels, etc.
* Gmail is then used as a realiable FIFO queue
* daemon will fetch one unread email every N seconds, send it as SMS and set as read

###SMS redirect
Very useful feature since GSM carriers don't offer redirecting SMS, unline call redirect which is a standard GSM feature.

* detect keywords to update active destination number

###Gmail2SMS + SMS redirect
Just set up both. :-)

##Access GSM modem on a remote machine
Going to have GSM modem hooked up to a different machine than the location you'll going to run the daemon on?
Share serial port of the GSM modem over the network and create a virtual serial port at the daemons side.

###Access GSM modem on a Mikrotik
http://babcuvpisecek.com/nezarazene/access-a-gsm-modem-connected-to-mikrotik-device-over-lan/

##TODO
* split to multiple files
* make it more modular
* add webadmin
* add more connectors
* REST api
* replace outcoming an incoming sms log files wit SQL database

