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

def processFirstUnreadGmailMessage(gmailService, modem): # gmailService = instance gmail api, modem = instance gsm modemu
	""" Projde nove neprectene zpravy, tu prvni odesle jako SMS a oznaci jako prectenou = vyjme ji z fronty pri pristim volani """
	""" Mohl by tu byt i cyklus na process vsech neprectenych zprav, ale pocitam s tim ze tuto funkci stejne volame co ~10 sekund """
	""" a smsek je vyrazne mene nez jedna za 10 sekund, takze to zatim staci bohate """
	""" Moje classa sms_sender navic aktualne nepodporuje neco jako frontu, popr. jak rychle lze tridu volat aby to nezahltilo USB 3G modem """
	loggerSentSMS = logging.getLogger('sent_sms')
	
	messages = gmailUtils.ListMessagesMatchingQuery(gmailService, "me", myconfig['incomingGmailHandlerSetup']['gmailQuery'])

	if not messages:
		#print('No new messages.')
		print('.')
	else:
		print('--- A new email found! Total: %s email(s) found, we will process the first one in this cycle. ---' % len(messages))
		logging.info('A new email found! Total: %s email(s) found, we will process the first one in this cycle.' % len(messages))

		for message in messages:
			smsDestination = ""
			smsContent     = ""

			print (" MESSAGE ID %s" % message['id'])
			messageContent = gmailUtils.GetMessage(gmailService, "me", message['id'])
			#pp.pprint(messageContent['payload']) # cely multipart email s hlavickami zformatovany do jsonu

			# get From and Subject fields
			for headerItem in messageContent['payload']['headers']:
				if headerItem["name"] == "From":
					print (' %s: %s' % (headerItem["name"].encode('UTF-8'), headerItem["value"].encode('UTF-8')))

				if headerItem["name"] == "Subject":
					smsDestination = ''.join(headerItem["value"].split()) # = strips all whitespace
					print (' %s: %s' % (headerItem["name"].encode('UTF-8'), headerItem["value"].encode('UTF-8')))

			# get 100 character snippet
			# smsContent = messageContent['snippet']
			# print (' Snippet: %s' % messageContent['snippet'])

			# get email body
			# We prefer plaintext-only and multipart (with plaintext part included) emails. HTML-only emails are generally not invited, there's no reason to send such emails to our mailbox. At the moment, HTML tags are not stripped.
			if (messageContent['payload']['mimeType'] in ('text/plain', 'text/html')):
				messageBodyBase64 = messageContent['payload']['body']['data'] # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL
			else: # 'multipart'
				for part in messageContent['payload']['parts']:
					if part["mimeType"] == "text/plain":
						messageBodyBase64 = part['body']['data'].encode('ASCII') # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL

			plainTextBody = base64.urlsafe_b64decode(messageBodyBase64.encode('ASCII')) # pozor gmail pouziva urlsafe_decode64() aneb dva znaky base64 jsou jine kvuli kompatibilite s URL
			plainTextBody = plainTextBody.decode("utf-8") # Dekodujeme email dle pouziteho kodovani do Unicode stringu. Nechce se me to slozite cist z hlavicek = predpokladame UTF-8 a hotovo.
			plainTextBody = plainTextBody.strip() # strip oreze whitespace na okrajich, dulezite, protoze i poslana zdanlive prazdna zprava z jineho gmailu ma jinak 2 znaky, nejinak to bude i u jinych html klientu
			
			print (' Mime/type: %s' % messageContent['payload']['mimeType'])
			print (' Body: %s' % plainTextBody.encode('UTF-8'))
			
			# generate SMS content from email body
			smsContent = plainTextBody[:myconfig['incomingGmailHandlerSetup']['smsMaxLength']] # Pozor toto orezani na pocet znaku neni uplne presne, nektere gsm-7 znaky jsou escapovane a zaberou dva znaky v SMS a zas tak dopodrobna to udelany neni.
			smsContentIsEncodableToGsm7Alphabet = smsStringUtils.isEncodableToGsm7Alphabet(smsContent)

			logging.info(u"SMS prepared: smsDestination=%s smsContentIsEncodableToGsm7Alphabet=%s convertTextTo7bit=%s \n smsContent=%s \n strip_accents(smsContent)=%s \n stripNonGsm7Characters(strip_accents(smsContent))=%s" % (smsDestination, smsContentIsEncodableToGsm7Alphabet, myconfig['incomingGmailHandlerSetup']['convertTextTo7bit'], smsContent, smsStringUtils.strip_accents(smsContent), smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent))))

			if (myconfig['incomingGmailHandlerSetup']['convertTextTo7bit'] is True and smsContentIsEncodableToGsm7Alphabet is False):
				smsContent = smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent))

			# check text length
			try:
				if (len(smsContent) < myconfig['incomingGmailHandlerSetup']['smsMinLength']):
					print("mala delak SMS")
				elif (len(smsContent) > myconfig['incomingGmailHandlerSetup']['smsMaxLength']):
					print("mala dlouha SMS")
			except:
				logging.warning("SMS not sent - empty smsContent or TOO LONG body. len(smsContent) = '%d'." % len(smsContent))

				# Oznacime mail jako precteny a tim ho vyjmeme ze zpracovani pri pristim spusteni
				logging.info("Setting the e-mail as read, removing it from next round.")
				gmailUtils.ModifyMessage(gmailService, "me", message['id'], {'removeLabelIds': ['UNREAD'], 'addLabelIds': []})


			# try to send SMS
			if (smsStringUtils.isDestinationNumberPermitted(smsDestination)):
				logging.info("ODESLEME SMSku!")
				
				try:
					sms = modem.sendSms(smsDestination, smsContent)
				except SerialException as e:
					logging.error('SerialException while sending sms from Gmail: %s' % repr(e))
					raise
				except TimeoutException:
					logging.error('Failed to send message: the send operation timed out')
				else:
					logging.info('SMS message sent!')
					sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(smsContent)
					loggerSentSMS.info(u"SMS sent:     [%s] %s [[%s,%s,%s]]" % (smsDestination, smsContent, sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining)) # mezery zarovnane podle "SMS received"

					# Oznacime mail jako precteny a tim ho vyjmeme ze zpracovani pri pristim spusteni
					logging.info("Setting the e-mail as read, removing it from next round.")
					gmailUtils.ModifyMessage(gmailService, "me", message['id'], {'removeLabelIds': ['UNREAD'], 'addLabelIds': []})
			else:
				logging.warning("SMS not sent. Destination number '%s' not permitted." % smsDestination)
			

			# ted BREAKNEME to po prvni iteraci. Teoreticky by tady slo zpracovat vsechny sms, ale pri soucasne ocekavane zatezi to takto zatim neni koncipovany.
			break

