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

import json
import urllib

# babca's personal sms handler (czech language used)

def incomingSmsHandler(sms):
    loggerSentSMS = logging.getLogger('sent_sms') # a nize v kodu je i prosty logging, ten miri na defaultni logger ktery nemame nazvany.

    print(u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
    receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(sms.text)
    logging.info      (u"SMS received: [%s] %s [[%s,%s,%s]]" % (sms.number, sms.text, receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining))
    loggerSentSMS.info(u"SMS received: [%s] %s [[%s,%s,%s]]" % (sms.number, sms.text, receivedSMS_numberOfSMS, receivedSMS_charactersUsed, receivedSMS_charactersRemaining))

    smsDestination = None
    smsContent     = None

    if (myconfig['incomingSmsHandlerSetup']['smsProcessingMode'] == 'keywords,redirect'):
        smsDestination = sms.number # default "reply", is overwritten with redirect number if keyword is not recognized
        pattern = re.compile("^(ZRUS|ZRUSIT)(?:[\s]*(\d))*$", re.IGNORECASE)

        if (sms.text == "Ahoj! Je tam nekdo?"):
            # HANDLE SMS KEYWORD
            logging.info("We're replying to known keyword: '%s'" % sms.text)
            smsContent = u"Tobe taky ahoj. Jo, je, ne clovek, ale bot. Uz se tesim az me nekdo napoji ne nejake chatovaci AI aby se se mnou dalo chatovat jako s clovekem. Kdo to udela?"

        elif (sms.text[:27] == "Mobilni klic pro Bazos.cz: " or sms.text[:27] == "Mobilny kluc pre Bazos.sk: "):
            # HANDLE SMS KEYWORD
            logging.info("We're replying to known sms format: 'BAZOS'")
            
            r1 = requests.get('http://radobacik.eu/audep/scripts/bazos_sms_checker.php?bazos_sms=%s' % urllib.quote(sms.text, safe=''), auth=jwt)
            r2 = requests.get('http://radobacik.eu/babcasmstester/smsHandler.php?bazos_sms=%s'       % urllib.quote(sms.text, safe=''), auth=jwt)
        
        elif (sms.text.upper() in ("STAV", "STATUS", "NA KDY JSEM OBJEDNANY?", "NA KDY JSEM OBJEDNANA?")):
            # HANDLE SMS KEYWORD "STAV", "STATUS"
            logging.info("We're replying to known keyword: '%s'" % sms.text)
            r = requests.get('http://lepsizubar.xyz/wp-admin/admin-ajax.php?action=sms_cancel_termin&phone=%s' % sms.number[4:], auth=jwt) # pozor zde predpokldamae pouze ceska cisla, v budoucnu nemusi stacit
            
            try:
                jsonArray = r.json() # vyhodi ValueError v pripade nevalidniho JSONu
                
                try:
                    pocet_terminu = len(jsonArray) # vyhodi TypeError pokud je obsahem JSONu obycejna cislovka
                except TypeError:
                    pocet_terminu = -1
                    pass
                
                if (pocet_terminu == -1):
                    # http server vratil cislovku, tzn nejaka interni chyba jako napr. vypadek MySQL
                    smsContent = u"Evidujeme problem s SMS serverem, pro zmenu terminu prosim volejte 777563364."
                    logging.error("Nastala chyba pri dekodovani JSON. Pocet_terminu==-1. Obsah JSONu: %s" % r.json())
                elif (pocet_terminu == 1):
                    # bud chybovy status, nebo prave jeden termin
                    try:
                        # neevidujeme zadny termin
                        if (jsonArray['status'] == "termin nenalezen"):
                            smsContent = u"Vazeny paciente, aktualne u Vas neevidujeme zadny objednany termin. Prosim objednejte se pres www.lepsizubar.cz"
                        # jiny problem
                        else:
                            smsContent = u"Omlouvame se, ale nastala chyba: %s" % (jsonArray['status'])
                            logging.info("Nastala chyba pro SMS odpoved: '%s' [%s]" % (sms.text, smsDestination))
                    except KeyError:
                        # evidujeme jediny neschvaleny budouci termin = zadani je jednoznacne, muzeme ho hned zrusit.
                        smsContent = u"Evidujeme u Vas termin %s, pocitame s Vami! Pro pripadne zruseni terminu odepiste klicovym slovem ZRUS, pro zmenu terminu volejte 777563364." % (ajaxReformatDatetime(jsonArray[0]['termin_date']['date']))
                elif (1 < pocet_terminu < 7):
                    smsContent = u"Prave u vas evidujeme celkem %s. Vybrany termin lze zrusit SMSkou ve tvaru ZRUS mezera cislo." % (sklonuj("zadny termin", "%s objednany termin", "%s objednane terminy", "%s objednanych terminu", pocet_terminu))
                    logging.error("PROSLI JSME %s" % smsContent)

                    i = 0
                    for termin in jsonArray:
                        logging.error("JUHU %s" % termin)
                        logging.error("JAJAJA %s" % termin['termin_date'])
                        logging.error("JAJAJA %s" % termin['termin_date']['date'])
                        logging.error("JEOU")
                        
                        smsContent += u"\nZRUS %s: %s" % (i+1, ajaxReformatDatetime(termin['termin_date']['date']))
                        i += 1

                    logging.error("FINAAAL %s" % smsContent)
                else:
                    smsContent = u"Prave u vas evidujeme %s, nejblizsi je %s. Pro vice informaci prosim kontaktujte 777563364." % (sklonuj("zadny termin", "%s objednany termin", "%s objednane terminy", "%s objednanych terminu", pocet_terminu), ajaxReformatDatetime(jsonArray[-1]['termin_date']['date']))
            except ValueError as e:
                smsContent = u"SMS server je docasne nedostupny, pro zmenu terminu prosim volejte 777563364."
                logging.error("Nastala chyba pri dekodovani JSON. (POZICE4) Status code: %s, snippet z obsahu: %s" % (r.status_code, r.text[:1000]))
                pass


        elif (sms.text.upper() in ("ZRUS", "ZRUSIT")):
            # HANDLE SMS KEYWORD "ZRUS", "ZRUSIT"
            smsDestination = sms.number # default "reply", is overwritten with redirect number if keyword is not recognized
            logging.info("We're replying to known keyword: '%s'" % sms.text)

            r = requests.get('http://lepsizubar.xyz/wp-admin/admin-ajax.php?action=sms_cancel_termin&phone=%s' % sms.number[4:], auth=jwt) # pozor zde predpokldamae pouze ceska cisla, v budoucnu nemusi stacit

            try:
                jsonArray = r.json()
                try:
                    pocet_terminu = len(jsonArray) # vyhodi TypeError pokud je obsahem JSONu obycejna cislovka
                except TypeError:
                    pocet_terminu = -1
                    pass
                
                if (pocet_terminu == -1):
                    # http server vratil cislovku, tzn nejaka interni chyba jako napr. vypadek MySQL
                    smsContent = u"Evidujeme problem s SMS serverem, pro zmenu terminu prosim volejte 777563364."
                    logging.error("Nastala chyba pri dekodovani JSON. Obsah JSONu: %s" % r.json())
                elif (pocet_terminu == 1):
                    # bud chybovy status, nebo prave jeden termin
                    try:
                        # zadny termin
                        if (jsonArray['status'] == "termin nenalezen"):
                            smsContent = u"Vazeny paciente, aktualne u Vas neevidujeme zadny objednany termin. Prosim objednejte se pres www.lepsizubar.cz"
                        else:
                            smsContent = u"Omlouvame se, ale nastala chyba: %s" % (jsonArray['status'])
                            logging.info("Nastala chyba pro SMS odpoved: '%s' [%s]" % (sms.text, smsDestination))
                    except KeyError:
                        # evidujeme jediny neschvaleny budouci termin = zadani je jednoznacne, muzeme ho hned zrusit.
                        r = requests.get('http://lepsizubar.xyz/wp-admin/admin-ajax.php?action=sms_cancel_termin&phone=%s&id=%s' % (sms.number[4:], jsonArray[0]['termin_id']), auth=jwt)
                        smsContent = u"Vas termin %s jsme uspesne zrusili, tesime se na Vas jindy! Novy termin si muzete vybrat na www.lepsizubar.cz." % (ajaxReformatDatetime(jsonArray[0]['termin_date']['date']))
                elif (1 < pocet_terminu < 7):
                    smsContent = u"Prave u vas evidujeme celkem %s. Vybrany termin lze zrusit SMSkou ve tvaru ZRUS mezera cislo:" % (sklonuj("zadny termin", "%s objednany termin", "%s objednane terminy", "%s objednanych terminu", pocet_terminu))

                    i = 0
                    for termin in jsonArray:
                        print(termin)
                        smsContent += u"\nZRUS %s: %s" % (i+1, ajaxReformatDatetime(termin['termin_date']['date'])) # vyhodi TypeError pokud ma datum jiny nez ocekavany ISO format
                        i += 1
                else:
                    smsContent = u"Prave u vas evidujeme %s, nejblizsi je %s. Nelze zrusit pres sms. Prosim kontaktujte 777563364." % (sklonuj("zadny termin", "%s objednany termin", "%s objednane terminy", "%s objednanych terminu", pocet_terminu), ajaxReformatDatetime(jsonArray[-1]['termin_date']['date']))
                
            except ValueError as e:
                smsContent = u"Evidujeme problem s SMS serverem, pro zmenu terminu prosim volejte 777563364."
                logging.error("Nastala chyba pri dekodovani JSON. Muze byt nevalidni, nebo datetime ma spatny format, nebo je chyba v programu. Obsah JSONu: %s" % r.json())
                pass
            
        elif (pattern.match(sms.text)):
            # HANDLE SMS KEYWORD "ZRUS 3", "ZRUSIT 3", "ZRUS2", "Zrusit     5", etc...
            logging.info("We're replying to known keyword: '%s'" % sms.text)

            # vycteme cislo vybraneho terminu. Nutno odecit jedna protoze indexy v poli jsou 0-based
            vybranyTerminIndex = int(pattern.search(sms.text).group(2)) - 1

            # vycteme si aktualni terminy
            r = requests.get('http://lepsizubar.xyz/wp-admin/admin-ajax.php?action=sms_cancel_termin&phone=%s' % sms.number[4:], auth=jwt) # pozor zde predpokladame pouze ceska cisla, v budoucnu nemusi stacit
            jsonArray = r.json()
            pocet_terminu = len(jsonArray)
            
            if (0 <= vybranyTerminIndex < pocet_terminu):
                # zrusime termin - ID terminu jsme nasli podle pozice
                r = requests.get('http://lepsizubar.xyz/wp-admin/admin-ajax.php?action=sms_cancel_termin&phone=%s&id=%s' % (sms.number[4:], jsonArray[vybranyTerminIndex]['termin_id']), auth=jwt)
                smsContent     = u"Vas termin %s jsme uspesne zrusili. Tesime se na Vas jindy!" % (ajaxReformatDatetime(jsonArray[vybranyTerminIndex]['termin_date']['date']))
            else:
                smsContent     = u"Zadali jste nespravne cislo terminu. Vyzadejte si seznam terminu ke zruseni odeslanim sms s textem ZRUS."

        else:
            smsDestination = myconfig['incomingSmsHandlerSetup']['redirectSmsTo']
            smsContent     = u"%s [Preposlano od: %s]" % (sms.text, sms.number)
            #smsContent     = u"%s (Preposlano od: 1234567890098)" % (sms.text)
            #smsContent     = u"%s" % (sms.text)
            logging.info("Not SMS keyword found -> redirecting SMS to %s!" % myconfig['incomingSmsHandlerSetup']['redirectSmsTo'])
    
    elif (myconfig['incomingSmsHandlerSetup']['smsProcessingMode'] == 'redirect'):
        # HANDLE SMS REDIRECT MODE
        smsDestination = myconfig['incomingSmsHandlerSetup']['redirectSmsTo']
        smsContent     = u"%s [Preposlano od: %s]" % (sms.text, sms.number)
        logging.info("Redirection mode = redirecting the received SMS now!")

    elif (myconfig['incomingSmsHandlerSetup']['smsProcessingMode'] == 'reply_demo'):
        # HANDLE SMS REPLY DEMO MODE
        smsDestination = sms.number
        smsContent     = u'Juhuu! Odpovidam zpet na prijatou SMS: "{0}{1}"'.format(sms.text[:20], '...' if len(sms.text) > 20 else '')
        logging.info("Reply mode = replying to the received SMS now!")

    elif (myconfig['incomingSmsHandlerSetup']['smsProcessingMode'] == ''):
        logging.info("Do nothing. Program is se to not process incoming SMS messages.")

    else:
        logging.error("Invalid smsProcessingMode setting.")
        raise ValueError("Invalid smsProcessingMode setting.")


    if (smsDestination is not None and smsContent is not None and myconfig['incomingSmsHandlerSetup']['smsProcessingMode'] != ''):
        try:
            # zkontrolujeme odesilatele
            if (smsStringUtils.isDestinationNumberPermitted(smsDestination)):
                # stripneme diakritiku / convert to GSM 7-bit encoded string from original text, if required by settings, else leave as is
                smsContent = smsStringUtils.stripNonGsm7Characters(smsStringUtils.strip_accents(smsContent)) if (myconfig['incomingSmsHandlerSetup']['convertTextTo7bit'] is True) else smsContent
                
                # nachystanou odpoved nyni odesleme
                sms.sendSms(smsDestination, smsContent)
            else:
                logging.info("SMS not sent. Destination number '%s' not permitted." % smsDestination)
        except SerialException as e:
            logging.error('SerialException while sending sms from incomingSmsHandler(): %s' % repr(e))
            raise
        except TimeoutException:
            logging.error('Failed to send message: the send operation timed out')
            loggerSentSMS.warning(u'Failed to send message: the send operation timed out. Original message: '+sms.text)
        else:
            logging.info('SMS sent!')
            sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining = smsStringUtils.smsCharacterCounter(smsContent)
            loggerSentSMS.info(u"SMS sent:     [%s] %s [[%s,%s,%s]]" % (smsDestination, smsContent, sentSMS_numberOfSMS, sentSMS_charactersUsed, sentSMS_charactersRemaining)) # mezery zarovnane podle "SMS received"



def ajaxReformatDatetime(dateString):
    """
    Prevede format data z ISO8601, typicky 2016-03-10 12:45:59 ale muze byt i s mikrosekundama nebo timezonou, na 10.3.2016 12:45
    Vyuzijeme ve funkci handleSms pri zpracovani datumu prijateho ajaxem, pri jinem pouziti serveru nemusi byt potrebna.
    """

    try:
        datetime = dateutil.parser.parse(dateString)
        return datetime.strftime("%-d.%-m. %-H:%M")
    except ValueError as e:
        print '"%s" is an invalid date' % dateString

def sklonuj(noItemText, oneItemText, twoItemsText, fiveItemsText, numberOfItems):
    """
    Vysklonuje dane slovo
    """

    if (numberOfItems == 0):
        return noItemText
    elif (numberOfItems == 1):
        return oneItemText
    elif (1 < numberOfItems < 5):
        return twoItemsText
    else:
        return fiveItemsText

def sklonuj(noItemText, oneItemText, twoItemsText, fiveItemsText, numberOfItems):
    """
    Vysklonuje dane slovo, dokonce doplni i cislovku, je-li v textu %s
    """

    if (numberOfItems == 0):
        return noItemText % (numberOfItems)
    elif (numberOfItems == 1):
        return oneItemText % (numberOfItems)
    elif (1 < numberOfItems < 5):
        return twoItemsText % (numberOfItems)
    else:
        return fiveItemsText % (numberOfItems)

