# plutaniumSmsServer
Plutanium SMS Server is a daemon which connects to your USB 3G modem and Gmail and lets you forward your Gmail to SMS, and SMS to SMS, making your own smart SMS gateway. Your GSM modem can be hooked up on local or remote machine, or on Mikrotik router. Implemented as a linux daemon, written in Python, tested on Debian and OS X.

Only documentation is open sourced at the moment. If you are interested in the library let me know!

##Use cases
* forward Gmail to SMS
* forward SMS to SMS
* make a smart SMS gateway.
* make a simple SMS chat

###Gmail2SMS
* forward Gmail to SMS
* connect to Gmail with Gmail API (you must generate access token)
* send emails do Gmail from your app, email title=targer number, body=sms content
* edit the Inbox query – filter senders, labels, etc.
* Gmail is then used as a realiable FIFO queue
* daemon will fetch one unread email every N seconds, send it as SMS and set as read

###SMS redirect
* forward SMS to SMS
  Very useful feature since GSM carriers don't offer redirecting SMS, unline call redirect which is a standard GSM feature.
* detect keywords to update active destination number

###Gmail2SMS + SMS redirect = Smart SMS gateway
* Just set up both the features.
* Send info-sms from the gateway and make sure you won't miss any calls and sms sent back to the gateway number. Redirect everything to your work mobile number.
* process SMS keywords/regex and respond to it / send SMS elsewhere / call AJAX / call AJAX, process it and respond with useful information, and resend unrecognised messages to your work number

##Features
* send and receive SMS
* process SMS keywords
* unicode SMS, or strip any string to 7-bit GSM alphabet
* multipart SMS
* well behaved linux daemon
* local or remote modem
* modem autoreconnect and reinit 
* log inbound, outbound sms
* I can implement new functionality

###Access GSM modem from a remote machine / RPi / Mikrotik router
Going to have GSM modem hooked up to a different device?
Plutanium SMS server supports connecting to modems over the network, see docs.

## Getting started
1. setup your modem
2. setup sms server
3. ???
4. profit

See documentation on https://github.com/babca/plutaniumSmsServer/blob/master/docs/docs.md

##TODO
* split to multiple files
* make it more modular
* add webadmin
* add more connectors
* REST api
* replace outcoming an incoming sms log files with a SQL database
* everyday self test

