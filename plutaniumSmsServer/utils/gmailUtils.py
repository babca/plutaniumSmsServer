#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib2
import os
import sys

from apiclient import discovery
from apiclient import errors
import oauth2client
from oauth2client import client
from oauth2client import tools

from utils.configUtils import * ## global variable config[]

#######################################################################################################
# GMAIL API POMOCNE FUNKCE

def get_service(cwd=os.getcwd()):
    try:
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        return service
    except:
        raise

def get_credentials(cwd=os.getcwd()):
    """
    Gets valid user credentials from storage.
    Critical error when no credentials available.

    Returns:
        Credentials, the obtained credential.
    """

    credential_path = os.path.join(cwd, myconfig['gmailApiSetup']['credentialsJsonFilename'])
    logging.info('get_credentials(): %s %s %s ' % (credential_path, cwd, myconfig['gmailApiSetup']['credentialsJsonFilename']))
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    
    if not credentials or credentials.invalid:
        raise RuntimeError("No Gmail credentials file found, or credentials file is invalid. The CREDENTIALS_FILE setting is now set to '%s'. Check the path, or create a new credentials file with an utility for that purpose." % credential_path)
    
    return credentials

def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        query: String used to filter messages returned.
        Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

    Returns:
        List of Messages that match the criteria of the query. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate ID to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        label_ids: Only return Messages with these labelIds applied.

    Returns:
        List of Messages that have all required Labels applied. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate id to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, labelIds=label_ids, pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)


def GetMessage(service, user_id, msg_id):
    """Get a Message with given ID.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The ID of the Message required.

    Returns:
        A Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        #print ('Message snippet: %s' % message['snippet'])

        return message
    except errors.HttpError as error:
        print( 'An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id):
    """Get a Message and use it to create a MIME Message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The ID of the Message required.

    Returns:
        A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()

        #print ('Message snippet: %s' % message['snippet'])
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        mime_msg = email.message_from_string(msg_str)

        return mime_msg
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)


def ModifyMessage(service, user_id, msg_id, msg_labels):
    """Modify the Labels on the given Message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The id of the message required.
        msg_labels: The change in labels.

    Returns:
        Modified message, containing updated labelIds, id and threadId.
    """
    try:
        message = service.users().messages().modify(userId=user_id, id=msg_id, body=msg_labels).execute()

        label_ids = message['labelIds']

        #print 'Message ID: %s - With Label IDs %s' % (msg_id, label_ids)
        return message
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)

