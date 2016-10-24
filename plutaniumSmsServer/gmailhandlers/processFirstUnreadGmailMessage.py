#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import argparse

import base64
import email
import time

import logging

from tempfile import gettempdir
from time import sleep

# import our helper functions
from utils import *
from utils.configUtils import * ## global variable config[]

import pprint # prettyprint for debug
pp = pprint.PrettyPrinter(indent=4)

from gsmmodem.exceptions import * # GsmModemException, TimeoutException, CmsError, CmeError, EncodingError, CommandError, PinRequiredError, IncorrectPinError etc.
from serial import SerialException


def processFirstUnreadGmailMessage(gmailService, modem): # gmailService = instance gmail api, modem = instance gsm modemu
	""" Projde nove neprectene zpravy, tu prvni odesle jako SMS a oznaci jako prectenou = vyjme ji z fronty pri pristim volani """
	""" Mohl by tu byt i cyklus na process vsech neprectenych zprav, ale pocitam s tim ze tuto funkci stejne volame co ~10 sekund """
	""" a smsek je vyrazne mene nez jedna za 10 sekund, takze to zatim staci bohate """
	""" Moje classa sms_sender navic aktualne nepodporuje neco jako frontu, popr. jak rychle lze tridu volat aby to nezahltilo USB 3G modem 

	This class checks for unread emails (which is actually our SMS queue) and send the first email as SMS.
	No loop is implemented inside this class, the loop is situated in server.py.

	@return Returns a current length of queue (number of remaining unread emails).
	        This value can be used to set a proper waiting time for next iteration, e.g. set shorter waiting time if there are messages in the queue.
	"""
	
	loggerSentSMS = logging.getLogger('sent_sms')
	
	messageIDs = gmailUtils.ListMessagesMatchingQuery(gmailService, "me", myconfig['incomingGmailHandlerSetup']['gmailQuery'])

	if not messageIDs:
		print('.') #print('No new messages.')
		return 0

	else:
		print('--- A new email found! Total: %s email(s) found, we will process the first one in this cycle. ---' % len(messageIDs))
		logging.info('A new email found! Total: %s email(s) found, we will process the first one in this cycle.' % len(messageIDs))
		
		for messageID in reversed(messageIDs): # traverse email in reverse order ("ORDER BY datetime DESC")
			messageFrom    = ""
			messageSubject = ""
			messageBody    = ""
			messageBodyBase64    = ""
			messageBodyPlainText = ""
			smsDestination = ""
			smsContent     = ""

			message = gmailUtils.GetMessage(gmailService, "me", messageID['id'])

			# get From and Subject fields
			for headerItem in message['payload']['headers']:
				if headerItem["name"] == "From":
					messageFrom = headerItem["value"].encode('UTF-8')

				if headerItem["name"] == "Subject":
					messageSubject = headerItem["value"].encode('UTF-8')
					smsDestination = ''.join(messageSubject.split()) # = strips all whitespace
			
			# get email body
			if (message['payload']['mimeType'] in ('text/plain', 'text/html')):
				# plaintext only, or html only. HTML-only emails in general are not invited, there's no reason to send such emails to our mailbox. At the moment, HTML tags are not stripped.
				messageBodyBase64 = message['payload']['body']['data'] # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL
			else:
				# multipart. We're going to extract plaintext part form multipart email
				for part in message['payload']['parts']:
					if part["mimeType"] == "text/plain":
						messageBodyBase64 = part['body']['data'] #.encode('ASCII') # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL

			messageBodyPlainText = base64.urlsafe_b64decode(messageBodyBase64.encode('ASCII')) # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL
			messageBodyPlainText = messageBodyPlainText.decode("utf-8") # Dekodujeme email dle pouziteho kodovani do Unicode stringu. Nechce se me to slozite cist z hlavicek = predpokladame UTF-8 a hotovo.
			messageBodyPlainText = messageBodyPlainText.strip() # strip oreze whitespace na okrajich, dulezite, protoze i poslana zdanlive prazdna zprava z jineho gmailu ma jinak 2 znaky, nejinak to bude i u jinych html klientu
			
			# debug print
			print (" MESSAGE ID %s" % messageID['id'])
			print (' From: %s' % messageFrom)
			print (' Subject: %s' % messageSubject)
			print (' Mime/type: %s' % message['payload']['mimeType'])
			print (' Body: %s' % messageBodyPlainText.encode('UTF-8'))
			
			# generate SMS content from email body
			smsContent = messageBodyPlainText[:(myconfig['incomingGmailHandlerSetup']['smsMaxLength'] * 10)] # premature string strip. If the body is like 1 MB long, we strip it to much shorter string with this to not slow down next text transformations. 
			smsContent = smsContent.replace('\r\n', '\n') # strip e-mail new lines to single character new lines, this can strip up smsMaxLength number of characters
			smsContentIsEncodableToGsm7Alphabet = smsStringUtils.isEncodableToGsm7Alphabet(smsContent)

			if (myconfig['incomingGmailHandlerSetup']['convertTextTo7bit'] is True and smsContentIsEncodableToGsm7Alphabet is False):
				smsContent = smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent))

			
			smsContent = smsStringUtils.smsCropString(smsContent, myconfig['incomingGmailHandlerSetup']['smsMaxLength'], "characters", myconfig['incomingGmailHandlerSetup']['convertTextTo7bit'])
			

			# final checks
			if (len(smsContent) < myconfig['incomingGmailHandlerSetup']['smsMinLength']):
				logging.warning("SMS not sent: smsContent is too short. len(smsContent)=%d < smsMinLength=%s." % (len(smsContent), myconfig['incomingGmailHandlerSetup']['smsMinLength']))
				logging.info("Setting the e-mail as read, removing it from next round.")
				gmailUtils.SetAsRead(gmailService, "me", messageID['id'])

			elif (not smsStringUtils.isDestinationNumberPermitted(smsDestination)):
				logging.warning("SMS not sent: destination number '%s' is not permitted." % smsDestination)
				logging.info("Setting the e-mail as read, removing it from next round.")
				gmailUtils.SetAsRead(gmailService, "me", messageID['id'])


			# sms is ready to be sent
			logging.info(u"SMS prepared: smsDestination=%s smsContentIsEncodableToGsm7Alphabet=%s convertTextTo7bit=%s \n smsContent=%s \n strip_accents(smsContent)=%s \n stripNonGsm7Characters(strip_accents(smsContent))=%s"
				% (smsDestination, smsContentIsEncodableToGsm7Alphabet, myconfig['incomingGmailHandlerSetup']['convertTextTo7bit'], smsContent, smsStringUtils.strip_accents(smsContent), smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent))))

			# try to send SMS
			try:
				logging.info("SENDING SMS!")
				sms = modem.sendSms(smsDestination, smsContent)
			except CmsError as e:
				logging.error('CmsError: %s' % repr(e))
				print(e)
			except SerialException as e:
				logging.error('SerialException while sending sms from Gmail: %s' % repr(e))
				raise
			except TimeoutException:
				logging.error('Failed to send message: the send operation timed out')
			else:
				logging.info('SMS message sent!')

				# log success
				sentSMS_numberOfParts, sentSMS_charactersUsed, sentSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(smsContent)
				loggerSentSMS.info(u"SMS sent:     [%s] %s [[%s parts,%s chars,%s rem]]" % (smsDestination, smsContent, sentSMS_numberOfParts, sentSMS_charactersUsed, sentSMS_charactersRemaining)) # mezery zarovnane podle "SMS received"

				# Oznacime mail jako precteny a tim ho vyjmeme ze zpracovani pri pristim spusteni
				logging.info("Setting the e-mail as read, removing it from next round.")
				gmailUtils.SetAsRead(gmailService, "me", messageID['id'])

			# ted BREAKNEME to po prvni iteraci. Teoreticky by tady slo zpracovat vsechny sms, ale pri soucasne ocekavane zatezi to takto zatim neni koncipovany.
			break

		return len(messageIDs)



# def debugPrintEmail(gmailService, modem):
# 	print (" MESSAGE ID %s" % messageIDs['id'])
# 	print (' Mime/type: %s' % message['payload']['mimeType'])
# 	print (' Body: %s' % messageBodyPlainText.encode('UTF-8'))

