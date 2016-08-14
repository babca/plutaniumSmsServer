#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import xmltodict
import xml.parsers.expat
import json

def stringToLoggingLevel(levelName):
	""" converts string to logging.LEVEL constant """
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

def intTryParse(value):
    try:
        return int(value)
    except ValueError:
        return value

def getConfigWithSelectedSetupsOnly(unprocessedJsonConfig):
	# reads single or multiple module setups given from setup.xml and returns the selected one.
	# it is meant for a possibility to comfortably experiment with multiple modems/gmail apis/sms handlers
	# and quickly switch between them
	configWithSelectedSetupsOnly = {}
	configWithSelectedSetupsOnly["general"] = unprocessedJsonConfig["general"]

	moduleSetupsAvailable = {
		# key-value: module name - setting name containing ID of the selected setup
		"modems": "selectModem",
		"gmailApiSetups": "selectGmailApiSetup",
		"loggingSetups": "selectLoggingSetup",
		"incomingGmailHandlerSetups": "selectIncomingGmailHandlerSetup",
		"incomingSmsHandlerSetups": "selectIncomingSmsHandlerSetup"
		}

	for moduleName, selectedSetupSettingName in moduleSetupsAvailable.iteritems():
		#("selectModem", "selectGmailApiSetup", "selectLoggingSetup", "selectIncomingGmailHandlerSetup", "selectIncomingSmsHandlerSetup"):

		# (1) if it is a list of multiple OrderedDicts, we need a selectedSetupID for choosing a right setup
		if (isinstance(unprocessedJsonConfig[moduleName], list)):
			for singleSetup in unprocessedJsonConfig[moduleName]:
				if (unprocessedJsonConfig["general"][selectedSetupSettingName] == singleSetup["id"]):
					configWithSelectedSetupsOnly[moduleName[:-1]] = singleSetup # hacky here! we drop the "s" at the end of the name
					break
				else:
					continue
			
			# print('There is an error in the configuration file. Check the general settings, there are selectXxxxSetup options.')
			# print('One or more IDs do not correspond to any of the setups in config.xml.')
			# print('Make a proper connection between a ID number in the general settings with the id property in corresponding section.')
			# print('Make sure the IDs are the same type, typically int (dont use brackets).')
			# exit(1)

		# (2) if it is a single OrderedDict, we simply use it directly
		else:
			configWithSelectedSetupsOnly[moduleName[:-1]] = unprocessedJsonConfig[moduleName]

	return configWithSelectedSetupsOnly


def validateModuleSetup(moduleName, moduleSetup):
	# check the setup file and convert some settings to int and string
	setup = {}
	if (moduleName == "general"):
		setup = [int(i) for i in results]
		return setup 


		int(moduleSetup["selectModem"])

	else:
		return setup

def getValidatedConfig(jsonFilename):
	# READ JSON CONFIG FILE NOW
	try:
		with open('config.json') as fd:
			unprocessedJsonConfig = json.load(fd)

	except xml.parsers.expat.ExpatError as e:
		print('There is an error in the configuration file, please open config.xml and fix it:')
		print(str(e))
		exit(1)

	# PROCESS CONFIG VALUES
	sectionNames = {
		# key-value: module name - setting name containing ID of the selected setup
		"general": "",
		"modem": "",
		"gmailApiSetup": "",
		"loggingSetup": "",
		"incomingGmailHandlerSetup": "",
		"incomingSmsHandlerSetup": ""
		}
	
	config = getConfigWithSelectedSetupsOnly(unprocessedJsonConfig)
	#print(json.dumps(config, indent=4));
	
	for sectionName, selectedSetupSettingName in sectionNames.iteritems():
		if (sectionName == "general"):
			config[sectionName]["gmailPollingInterval"] = int(config[sectionName]["gmailPollingInterval"])
		elif (sectionName == "modem"):
			#config[sectionName]["virtualPortRestartInterval"] = intTryParse(config[sectionName]["virtualPortRestartInterval"])
			config[sectionName]["baudrate"] = int(config[sectionName]["baudrate"])
			config[sectionName]["port"] = str(config[sectionName]["port"])
			config[sectionName]["pin"] = config[sectionName]["pin"] if (config[sectionName]["pin"] is not None and 1 <= int(config[sectionName]["pin"]) <= 9999) else None			
			## SET HARD-CODED SETTINGS
			config[sectionName]['errorRetryWaitTime'] = 15
		elif (sectionName == "loggingSetup"):
			config[sectionName]['foregroundLogLevel'] = stringToLoggingLevel(config[sectionName]['foregroundLogLevel'])
			config[sectionName]['daemonLogLevel']     = stringToLoggingLevel(config[sectionName]['daemonLogLevel'])
		elif (sectionName == "incomingGmailHandlerSetup"):
			config[sectionName]['smsMinLength']     = int(config[sectionName]['smsMinLength'])
			config[sectionName]['smsMaxLength']     = int(config[sectionName]['smsMaxLength'])
		elif (sectionName == "incomingSmsHandlerSetup"):
			doNothing123 = 123
	
	# return setup in variable
	#print(json.dumps(config, indent=4));
	#print(config)
	return config


# READ JSON CONFIG NOW
myconfig = getValidatedConfig('config.json')


