#!/usr/bin/env python

import argparse
import httplib2
import json

from apiclient.discovery import build
from apiclient.http import BatchHttpRequest
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser


crontable = []
outputs = []


# Storage for current message objects
messages = []


#crontable.append([15*60, 'print_builds'])


def check_builds(data):
    # Parse the command-line arguments (e.g. --noauth_local_webserver)
    parser = argparse.ArgumentParser(parents=[argparser])
    flags = parser.parse_args(['--noauth_local_webserver'])

    # Path to the client_secret.json file downloaded from the Developer Console
    CLIENT_SECRET_FILE = 'client_secret.json'

    # Check https://developers.google.com/gmail/api/auth/scopes
    # for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

    # Location of the credentials storage file
    STORAGE = Storage('gmail.storage')

    # Start the OAuth flow to retrieve credentials
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
    http = httplib2.Http()

    # Try to retrieve credentials from storage or run the flow to generate them
    credentials = STORAGE.get()
    if credentials is None or credentials.invalid:
      raise ValueError('Storage location did not have valid stored credentials! Please run scraper.py as a standalone process to recreate a valid credential store')

    # Authorize the httplib2.Http object with our credentials
    http = credentials.authorize(http)

    # Build the Gmail service from discovery
    gmail_service = build('gmail', 'v1', http=http)

    # Retrieve a page of threads
    threads = gmail_service.users().messages().list(userId='me', labelIds='Label_8').execute()

    batch = BatchHttpRequest(callback=handle_data)
    if 'messages' in threads:
        count = len(threads['messages']) - 1
        for thread in threads['messages']:
            count -= 1
            if count == 0:
                batch.add(gmail_service.users().messages().get(userId='me', id=thread['id'], format='metadata', metadataHeaders='Subject'), request_id='channel:'+data['channel'])
            else:
                batch.add(gmail_service.users().messages().get(userId='me', id=thread['id'], format='metadata', metadataHeaders='Subject'))
    batch.execute(http=http)


builds = []
def handle_data(request_id, response, exception):
    if exception is not None:
        pass
    else:
        for headers in response['payload']['headers']:
            try:
                if headers['name'].lower() == 'subject':
                    builds.append(headers['value'])
            except Exception:
                pass
    if request_id.startswith('channel:'):
        buildslist = {}
        for build in reversed(builds):
            build = build.split('Build Notification: ', 1)[1]
            build, ver = build.split(', ')
            if '\\' in ver:
                ver = ver.split('\\', 1)[0]
            buildslist[build] = ver
        versions = [ '*{}*, {}'.format(build, buildslist[build]) for build in sorted(buildslist) ]
        outputs.append([request_id.split('channel:', 1)[1], ' \n '.join(versions)])
        

def process_message(data):
    if data['text'].lower().startswith('?builds'):
        check_builds(data)


def run_setup():
    # Parse the command-line arguments (e.g. --noauth_local_webserver)
    parser = argparse.ArgumentParser(parents=[argparser])
    flags = parser.parse_args(['--noauth_local_webserver'])

    # Path to the client_secret.json file downloaded from the Developer Console
    CLIENT_SECRET_FILE = 'client_secret.json'

    # Check https://developers.google.com/gmail/api/auth/scopes
    # for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

    # Location of the credentials storage file
    STORAGE = Storage('gmail.storage')

    # Start the OAuth flow to retrieve credentials
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
    http = httplib2.Http()

    # Try to retrieve credentials from storage or run the flow to generate them
    credentials = STORAGE.get()
    if credentials is None or credentials.invalid:
      credentials = run_flow(flow, STORAGE, flags, http=http)
    http = credentials.authorize(http)


if __name__ == '__main__':
    run_setup()
