#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unicodedata

# Oreze diakritiku. Pozor v GSM se pro 160 znakove sms pouziva GSM 7-bit encoding, toto je ascii (8-bit) kompatibilni string. Ne kazdy ASCII se vejde do 7-bitove GSM abecedy.
def strip_accents(text):
    """
    Strip accents from input String.
    Takes Unicode string as an input. Unicode as output.
    """

    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return text


# Tables can be found at: http://en.wikipedia.org/wiki/GSM_03.38#GSM_7_bit_default_alphabet_and_extension_table_of_3GPP_TS_23.038_.2F_GSM_03.38
GSM7_ALL_CHARS = ('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà^{}\\[~]|€' + chr(0xFF) )
GSM7_BASIC = ('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà')
GSM7_EXTENDED = {chr(0xFF): 0x0A,
                 #CR2: chr(0x0D),
                 '^':  chr(0x14),
                 #SS2: chr(0x1B),
                 '{':  chr(0x28),
                 '}':  chr(0x29),
                 '\\': chr(0x2F),
                 '[':  chr(0x3C),
                 '~':  chr(0x3D),
                 ']':  chr(0x3E),
                 '|':  chr(0x40),
                 '€':  chr(0x65)}

# Maximum message sizes for each data coding
MAX_MESSAGE_LENGTH = {0x00: 160, # GSM-7
                      0x04: 140, # 8-bit
                      0x08: 70}  # UCS2

# Maximum multipart message sizes. Less characters are available for user text, because UDH takes 6-bytes
MAX_MULTIPART_MESSAGE_LENGTH = {0x00: 153, # GSM-7
                                0x04: 134, # 8-bit
                                0x08: 67}  # UCS2

def isEncodableToGsm7Alphabet(plaintext):
    """
    Find out if the specified text string is encodable to GSM-7 characters.
    Takes Unicode string as an input.
    """

    # convert unicode string to utf8 bytestring
    plaintext = plaintext.encode("utf-8")

    # check char after char
    for char in plaintext:
        if GSM7_ALL_CHARS.find(char) == -1:
            return False
    return True

def stripNonGsm7Characters(plaintext):
    """
    Strips characters not in GSM-7 alphabet from given string 
    Takes Unicode string as an input.
    """

    # convert unicode string to utf8 bytestring
    plaintext = plaintext.encode("utf-8")
    gsm7_text = u''

    # check char after char and make a new string
    for char in plaintext:
        if GSM7_ALL_CHARS.find(char) != -1:
            gsm7_text += char
    
    return gsm7_text

def smsCharacterCounter(plaintext):
    """
    Count how many of 140-byte SMS messages will be needed for given text
    Takes Unicode string as an input.
    """

    gsm7bit = isEncodableToGsm7Alphabet(plaintext)
    length = len(plaintext) # sms length. The number will include all sms escape characters too, see below.
    plaintext = plaintext.encode("utf-8") # pro byte-by-byte operace

    if gsm7bit:
        # 7-bit encoding
        # some chars need to be escaped (+escape char)
        for char in plaintext:
            if char in GSM7_EXTENDED:
                length+=1

        # count # of SMS
        if (length <= 160):
            numberOfSMS = 1
            charactersRemaining = 160 - length
        else:
            numberOfSMS = 1 + int(length / 153)
            charactersRemaining = 153 * numberOfSMS - length

    else:
        # USC-2 16-bit encoding
        # count # of SMS
        if (length <= 70):
            numberOfSMS = 1
            charactersRemaining = 70 - length
        else:
            numberOfSMS = 1 + int(length / 67)
            charactersRemaining = 67 * numberOfSMS - length

    return numberOfSMS, length, charactersRemaining



def isDestinationNumberPermitted(smsNumber):
    """
    ==Need to be placed elsewhere==

    Pravidla pro povolena telefonni cisla, vraci False pro zakazane cisla
    """

    # make sure the phone number is string
    smsNumber = str(smsNumber)

    # replace + for 00
    if (smsNumber[:1] == "+"):
        smsNumber = "00" + smsNumber[1:]

    # povolime jen cisla vypadajici jako cesky operator
    if (len(smsNumber) == 14):
        if (smsNumber[:2] == "00" and smsNumber[:5] == "00420" and int(smsNumber[5:]) >= 601000000 and int(smsNumber[5:]) <= 799999999):
            return True
        else:
            return False
    elif (len(smsNumber) == 9):
        if (int(smsNumber) >= 601000000 and int(smsNumber) <= 799999999):
            return True
        else:
            return False
    else:
        return False

    return False



# sometimes can be useful
def whatisthis(s):
    if isinstance(s, str):
        print "ordinary string"
    elif isinstance(s, unicode):
        print "unicode string"
    else:
        print "not a string"


