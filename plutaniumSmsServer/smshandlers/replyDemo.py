#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
from requests_jwt import JWTAuth
jwt = JWTAuth('secretT0Ken') # HTTP JSON Web Token, heslo pro komunikaci s webapp

from utils import smsStringUtils
from utils.configUtils import * ## global variable config[]

from gsmmodem.exceptions import * # GsmModemException, TimeoutException, CommandError, PinRequiredError, IncorrectPinError etc.
from serial import SerialException

import re
from datetime import datetime
import dateutil.parser


# simple SMS reply demo

def incomingSmsHandler(sms):
    loggerSentSMS = logging.getLogger('sent_sms') # a nize v kodu je i prosty logging, ten miri na defaultni logger ktery nemame nazvany.

    print(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
    receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(sms.text)
    logging.info      (u"SMS received: [%s] %s [[%s,%s,%s]]" % (sms.number, sms.text, receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining))
    loggerSentSMS.info(u"SMS received: [%s] %s [[%s,%s,%s]]" % (sms.number, sms.text, receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining))

    smsDestination = ""
    smsContent     = ""

    try:
        # HANDLE SMS REPLY DEMO
        smsDestination = sms.number
        smsContent     = u'Huurray! Your text: "{0}{1}"'.format(sms.text[:20], '...' if len(sms.text) > 20 else '')
        
        # convert to GSM 7-bit encoded string from original text, if required by settings, else leave as is
        smsContent     = smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent)) if (myconfig['SMS_HANDLER_CONVERT_TO_7BIT'] is True) else smsContent

        logging.info("Reply mode = replying to the received SMS now!")
    
        # check destination number
        if (smsStringUtils.isDestinationNumberPermitted(smsDestination) is False):
            raise ValueError("Destination number '%s' not permitted." % smsDestination)
        
        # finally send the sms message!
        sms.sendSms(smsDestination, smsContent)

    except SerialException as e:
        logging.error('SerialException while sending sms from incomingSmsHandler(): %s' % repr(e))
        raise
    except TimeoutException:
        logging.error('Failed to send a message: the send operation timed out')
        loggerSentSMS.warning(u'Failed to send a message: the send operation timed out. Original message: '+sms.text)
    except ValueError as e:
        logging.error('SMS not sent. %s' % repr(e))
        raise
    else:
        logging.info('SMS sent!')
        sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(smsContent)
        loggerSentSMS.info(u"SMS sent:     [%s] %s [[%s,%s,%s]]" % (smsDestination, smsContent, sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining)) # mezery zarovnane podle "SMS received"


