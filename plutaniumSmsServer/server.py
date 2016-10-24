#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
#import httplib2

import argparse

import base64
import email
import time

import pprint # prettyprint for debug
pp = pprint.PrettyPrinter(indent=4)


import logging
import signal
import traceback

from tempfile import gettempdir

from pep3143daemon import DaemonContext
from pep3143daemon import PidFile

from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import * # GsmModemException, TimeoutException, CommandError, PinRequiredError, IncorrectPinError etc.
from serial import SerialException

from plumbum import FG, BG, NOHUP
from plumbum.cmd import socat, ls, kill

# from lockfile.pidlockfile import PIDLockFile
# from lockfile import AlreadyLocked


PYTHON_VERSION = sys.version_info[0]

# import our helper functions
from utils import *
from utils.configUtils import * ## global variable config[]

from smshandlers import babcaPersonal
#from smshandlers import replyDemo

from gmailhandlers.processFirstUnreadGmailMessage import processFirstUnreadGmailMessage

#from utils.smsStringUtils import *


class plutaniumSmsServerDaemonizable:
	""" Trida reprezentuje plutaniumSmsServer demona, s implementovanymi metodami minimalne start a stop """
	def __init__(self, incomingGmailHandler=None, incomingSmsHandler=None, incomingSmsStatusReportHandler=None, cwd=os.getcwd()):
		# Set the initial variables
		self.running = False
		self.cwd = cwd
		self.incomingGmailHandler           = incomingGmailHandler           or self._placeholderCallback
		self.incomingSmsHandler             = incomingSmsHandler             or self._placeholderCallback
		self.incomingSmsStatusReportHandler = incomingSmsStatusReportHandler or self._placeholderCallback
		
		if (not hasattr(self.incomingGmailHandler, '__call__')):
			raise ValueError('Provided incomingGmailHandler callback is not a callable function, please fix it.')
		if (not hasattr(self.incomingSmsHandler, '__call__')):
			raise ValueError('Provided incomingSmsHandler callback is not a callable function, please fix it.')
		if (not hasattr(self.incomingSmsStatusReportHandler, '__call__')):
			raise ValueError('Provided incomingSmsStatusReportHandler callback is not a callable function, please fix it.')

	def start(self):
		"""	Samotne jadro daemona: setupneme GmailAPI, setupneme GSM modem a zacneme provadet nekonecnou smycku """
		self.running = True

		# (0) SETUP VIRTUAL SERIAL PORT FOR MODEM
		if "virtualPortInitCommand" in myconfig['modem']:
			try:
				virtualSerialPortInstance = virtualSerialPort(myconfig['modem']['virtualPortInitCommand'])
				virtualSerialPortInstance.start()
			except:
				pass
		else:
			virtualSerialPortInstance = None

		# (1) SETUP GMAIL ACCESS
		logging.info('Initializing GMAIL access...')
		try:
			gmailService = gmailUtils.get_service(self.cwd)
		except RuntimeError as e:
			print(str(e))
			logging.critical(str(e))
			if (virtualSerialPortInstance is not None):
				virtualSerialPortInstance.stop()
			#sys.exit(1)
			self.stop()
		
		######################################################################################################################################################
		# (2) SETUP GSM MODEM + bind a "smsReceived" callback + poll gmail inbox
		logging.info('Initializing GSM modem on {0} port @ {1} speed...'.format(myconfig['modem']['port'], myconfig['modem']['baudrate']))
		modem = GsmModem(myconfig['modem']['port'], myconfig['modem']['baudrate'], smsReceivedCallbackFunc=self.incomingSmsHandler)
		modem.smsTextMode = False

		while self.running:
			# start of gsm init loop
			try:
				modem.connect(myconfig['modem']['pin'])
			except serial.SerialException:
				logging.error('Error: Cannot connect to modem on serial port %s @ %s. Trying again in %d sec...' % (myconfig['modem']['port'], myconfig['modem']['baudrate'], myconfig['modem']['errorRetryWaitTime']))
				time.sleep(myconfig['modem']['errorRetryWaitTime'])
			except TimeoutException:
				logging.error('Error: Serial device %s @ %s timeout. Trying again in %d sec...' % (myconfig['modem']['port'], myconfig['modem']['baudrate'], myconfig['modem']['errorRetryWaitTime']))
				time.sleep(myconfig['modem']['errorRetryWaitTime'])
			except PinRequiredError:
				# Fatal error
				logging.critical('Error: SIM card PIN required. Please provide PIN in the config file.')
				self.stop()
				return 1
			except IncorrectPinError:
				# Fatal error
				logging.critical('Error: Incorrect SIM card PIN entered!')
				self.stop()
				return 1
			else:
				logging.info('Modem connected.')
				try:
					logging.info('Checking for network coverage...')
					modem.waitForNetworkCoverage(8) # of seconds
				except TimeoutException:
					logging.warning('We can now start gmail inbox polling infinite loop.')
					print('Network signal strength is not sufficient, please adjust modem position/antenna and try again.')
					modem.close()
				else:
					logging.info('GSM modem is ready.')  
					logging.info('We are now handling all incoming SMS messages.') 

					try:
						if (myconfig['incomingSmsHandlerSetup']['processStoredSms'] == "all"):
							modem.processStoredSms(unreadOnly=False)
						elif (myconfig['incomingSmsHandlerSetup']['processStoredSms'] == "unread"):
							modem.processStoredSms(unreadOnly=True)
					except Exception as e:
						logging.critical("Nastal problem pri zpracovani drivejsich neprectenych SMS:")
						raise
						sys.exit(0)
					else:
						logging.info('We can now start gmail inbox polling infinite loop.')

						try:
							while self.running:
								# start of main gmail loop
								logging.debug('Checking incoming emails...') 
								newMessagesCount = self.incomingGmailHandler(gmailService, modem)
								time.sleep(myconfig['general']['gmailQueueWaitingPeriod'] if newMessagesCount > 0 else myconfig['general']['gmailPollingInterval'])
								# end of main gmail loop
						except KeyboardInterrupt:
							#sys.exit(0)
							self.stop()
							return 0
						except Exception as e:
							print("Nastala vyjimka v hlavni smycce daemona, viz log.")
							logging.exception("Nastal problem v hlavni smycce:")
							raise
						finally:
							print("Bye gmail loop.")
					finally:
						print("Bye stored sms handling try-cache.")
				finally:
					print("Bye.")
					modem.close()
					if (virtualSerialPortInstance is not None):
						virtualSerialPortInstance.stop()
						
			finally:
				print("end of gsm init loop")

			# end of gsm init loop
			# normally we won't reach this place, but when a non-fatal error happens
			# (like 'No modem found', 'No GSM signal', etc.), we can continue the loop to
			# try it again in the new iteration of the main loop
			
		# TODO - move kill socat here. Move socat init to try finally

		######################################################################################################################################################
		return 0 # just for make sure, the program should never end up on this line
	
	def stop(self):
		self.running = False

	def _placeholderCallback(self, *args):
		""" Does nothing """
		logging.debug('_placeHolderCallback called with args: {0}'.format(args))


class virtualSerialPort:
	""" Creates a local virtual serial with an external shell command and links it to remotely attached serial device. """
	def __init__(self, command):
		self.command = command
		self.commandSplit = command.split(' ')
		self.virtualPortService = None

	def start(self):
		logging.info('Initializing VIRTUAL SERIAL PORT...')
		
		if (self.virtualPortService):
			logging.warning('virtualSerialPort.start() called again. Virtual port service is already running.')
			return 0

		elif (self.commandSplit[0].lower() == "sudo"):
			logging.critial('virtualSerialPort: Please remove sudo from VIRTUAL_PORT_SETUP_COMMAND setting. Socat is run with the same privileges as python. Just sudo python.')
			raise ValueError('Please remove sudo from VIRTUAL_PORT_SETUP_COMMAND setting.')

		elif (self.commandSplit[0] != "socat"):
			logging.critial('virtualSerialPort: For security reasons, currently only socat command is supported. Feel free to edit the source code.')
			raise ValueError('Currently only socat command is supported. Feel free to edit the source code.')
		
		else:
			# run socat with plumbum
			self.virtualPortService = socat[self.commandSplit[1:]] & BG

	def stop(self):
		logging.info('Stopping VIRTUAL SERIAL PORT...')
		
		if (self.virtualPortService):
			# run kill with plumbum
			kill[self.virtualPortService.proc.pid] & FG

class plutaniumSmsServer:
	""" Trida reprezentuje plutaniumSmsServer - parsuje argumenty a spousti samotne demonovane vlakno """
	def __init__(self, args):
		# Set the initial variables
		self.daemonAction = False
		self.nodaemon = False
		self.args = args

		# Set daemonAction from commandline sys.argv
		self.parse_args(args)

	def parse_args(self, args):
		""" Metoda nastavi vnitrni promenne z commandline argumentu """

		argparser = argparse.ArgumentParser(description='Custom CLI programek na posilani SMS primo z lokalne pripojeneho 3G USB modemu.')
		argparser.add_argument('daemonAction', action='store', help='Akce. fg = foreground, no daemon',  choices=['start', 'stop', 'reload', 'status', 'fg'])
		args = argparser.parse_args()

		self.daemonAction = args.daemonAction
		self.check_args()

	def check_args(self):
		""" Kontrola parametru """
		return True

	def main(self):
		plutaniumSmsServerDaemonizableInstance = plutaniumSmsServerDaemonizable(incomingGmailHandler = processFirstUnreadGmailMessage, incomingSmsHandler=babcaPersonal.incomingSmsHandler, cwd=os.getcwd()) # incomingSmsStatusReportHandler = None # getcwd must be here because when run as daemon, the original current working directory is "lost". Deamons start at root /

		if self.daemonAction == 'fg':
			print ('plutaniumSmsServer running in no-daemon mode.')
			print ('  you can monitor logs in another terminal with the commands:')
			print ('  general log:   tail -f '+myconfig['loggingSetup']['mainLogFilename'])
			print ('  sent sms log:  tail -f '+myconfig['loggingSetup']['sentSmsLogFilename'])
			print ('  stdout is pretty minimal, it prints new incoming emails and sms messages,')
			print ('  a dot means that Gmail inbox has been checked and no new messages has been found.')
			
			daemon = daemonUtils.NoDaemon(daemonizable=plutaniumSmsServerDaemonizableInstance)
			daemon.start(log_file=myconfig['loggingSetup']['mainLogFilename'], dump_stack_trace=True)
		else:
			daemon = daemonUtils.Daemon(daemonizable=plutaniumSmsServerDaemonizableInstance)

		if self.daemonAction == 'start':
			daemon.start(log_file=myconfig['loggingSetup']['mainLogFilename'], dump_stack_trace=True)
		elif self.daemonAction == 'stop':
			daemon.stop()
		elif self.daemonAction == 'reload':
			daemon.reload(log_file=myconfig['loggingSetup']['mainLogFilename'], dump_stack_trace=True)
		elif self.daemonAction == 'status':
			daemon.status()

		return 0

if __name__ == '__main__':
	plutaniumSmsServerInstance = plutaniumSmsServer(sys.argv)
	sys.exit(plutaniumSmsServerInstance.main())




##
## TODO: jwt secret token ---> config file
## TODO: translate remaining commnents in czech language to english
## TODO: use custom exceptions in the code and clean it
## TODO: kill already running duplicate instances of socat (previous running socat with same command)
## TODO: sql server
## TODO: sms status report
