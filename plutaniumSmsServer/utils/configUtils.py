#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import logging

# SET DEFAULT SETTINGS
config = ConfigParser.RawConfigParser({\
    'GMAIL_POLLING_INTERVAL': 30, \
    'GMAIL_QUERY': 'label:inbox is:unread',\
    'LOG_FILE:': '/var/log/gmail2sms.log', \
    'LOG_FILE_SMS:': 'sent_sms.log', \
    'LOG_LEVEL_FOREGROUND:': 'debug', \
    'LOG_LEVEL_DAEMON:': 'info', \
    'SMS_MIN_LENGTH': 1, \
    'SMS_MAX_LENGTH': 160, \
    'CONVERT_TO_7BIT': True, \
    'VIRTUAL_PORT_SETUP_COMMAND': '', \
    'PORT': '/dev/ttyUSB2', \
    'PIN': '', \
    'BAUDRATE': 115200, \
    'SMS_HANDLER_MODE': 'doNothing', \
    'SMS_HANDLER_REDIRECT_TO': '', \
    'SMS_HANDLER_CONVERT_TO_7BIT': False, \
    'SMS_HANDLER_PROCESS_SMS_PREVIOUSLY_STORED_ON_SIM': '' })
config.read('config.txt')

myconfig = {}

# IMPORT GENERAL SETTINGS
myconfig['LOG_FILE']               = config.get       ('gmail2sms', 'LOG_FILE')
myconfig['LOG_FILE_SMS']           = config.get       ('gmail2sms', 'LOG_FILE_SMS')
myconfig['LOG_LEVEL_FOREGROUND']   = config.get       ('gmail2sms', 'LOG_LEVEL_FOREGROUND')
myconfig['LOG_LEVEL_DAEMON']       = config.get       ('gmail2sms', 'LOG_LEVEL_DAEMON')
myconfig['GMAIL_POLLING_INTERVAL'] = config.getint    ('gmail2sms', 'GMAIL_POLLING_INTERVAL')
myconfig['GMAIL_QUERY']            = config.get       ('gmail2sms', 'GMAIL_QUERY')
myconfig['CONVERT_TO_7BIT']        = config.getboolean('gmail2sms', 'CONVERT_TO_7BIT')
myconfig['SMS_MIN_LENGTH']         = config.get       ('gmail2sms', 'SMS_MIN_LENGTH')
myconfig['SMS_MAX_LENGTH']         = config.getint    ('gmail2sms', 'SMS_MAX_LENGTH')

# IMPORT SMS HANDLER SETTINGS
myconfig['SMS_HANDLER_MODE']            = config.get       ('incomingSmsHandler', 'SMS_HANDLER_MODE')
myconfig['SMS_HANDLER_REDIRECT_TO']     = config.get       ('incomingSmsHandler', 'SMS_HANDLER_REDIRECT_TO')
myconfig['SMS_HANDLER_CONVERT_TO_7BIT'] = config.getboolean('incomingSmsHandler', 'SMS_HANDLER_CONVERT_TO_7BIT')
myconfig['SMS_HANDLER_PROCESS_SMS_PREVIOUSLY_STORED_ON_SIM'] = config.get('incomingSmsHandler', 'SMS_HANDLER_PROCESS_SMS_PREVIOUSLY_STORED_ON_SIM')

# IMPORT GSM MODEM SETTINGS
myconfig['VIRTUAL_PORT_SETUP_COMMAND'] = config.get('modem', 'VIRTUAL_PORT_SETUP_COMMAND')
myconfig['PORT']           = config.get   ('modem', 'PORT')
myconfig['BAUDRATE']       = config.getint('modem', 'BAUDRATE')
myconfig['PIN']            = config.get   ('modem', 'PIN')
myconfig['PIN']            = myconfig['PIN'] if (len(myconfig['PIN']) and 1 <= int(myconfig['PIN']) <= 9999) else None

# IMPORT GMAIL API SETTINGS
# If modifying these scopes (now placed in the settings file), delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json AND run quickstart.py to generate new token 
myconfig['APPLICATION_NAME']   = config.get('gmail_api', 'APPLICATION_NAME')
myconfig['SCOPES']             = config.get('gmail_api', 'SCOPES')
myconfig['CLIENT_SECRET_FILE'] = config.get('gmail_api', 'CLIENT_SECRET_FILE')
myconfig['CREDENTIALS_FILE']   = config.get('gmail_api', 'CREDENTIALS_FILE')


def stringToLoggingLevel(levelName):
    """ converts string to logging.LEVEL """

    #if (levelName in ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')):

    levelName = levelName.lower()

    if (levelName == "debug"):
        return logging.DEBUG
    elif (levelName == "info"):
        return logging.INFO
    elif (levelName == "warning"):
        return logging.WARNING
    elif (levelName == "error"):
        return logging.ERROR
    elif (levelName == "critical"):
        return logging.CRITICAL
    else:
        return logging.NOTSET

myconfig['LOG_LEVEL_FOREGROUND'] = stringToLoggingLevel(myconfig['LOG_LEVEL_FOREGROUND'])
myconfig['LOG_LEVEL_DAEMON']     = stringToLoggingLevel(myconfig['LOG_LEVEL_DAEMON'])

## SET HARD-CODED SETTINGS
myconfig['GSM_MODEM_RETRY_WAIT_TIME'] = 3 
