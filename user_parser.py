from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime
import phonenumbers
import logging
import os
import pickle

logger = logging.getLogger(__name__)

# Form response columns
FORM_TIME_IDX = 0
FORM_NAME_IDX = 1
FORM_PHONE_IDX = 2
FORM_STATE_IDX = 3

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
FORM_RESPONSE_SHEET_ID = '1ve9JZdtaxLmJD797reJG02G65loeeHsUuX7thMBZmXA'
FORM_RESPONSE_RANGE = 'Form_Responses!A2:E'

class FormSubmission:
    def __init__(self, timestamp, name, phone_str, state):
        self.submit_time = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        self.name = name
        self.phone_num = phonenumbers.parse(phone_str, 'US')
        self.state_code = state
        self.num_submissions = 1

def get_test_user():
    return FormSubmission('6/6/2020 21:29:28', 'Ryan', '631-707-5422', 'CA')


def get_google_creds():
    creds = None
    # Check first if access and refresh tokens already exist
    if os.path.exists('google_token.pickle'):
        with open('google_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # TODO: need a login message
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('google_token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_form_responses():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = get_google_creds()
    logger.info('Got google credentials...')
    assert creds and creds.valid
    logger.info('... and they are valid')
    # TODO: make cache discovery True if this ever evolves past a cron
    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=FORM_RESPONSE_SHEET_ID,
                                range=FORM_RESPONSE_RANGE).execute()

    unique_users = {}
    res = result.get('values', [])
    for submission in res: 
        if len(submission) == 0:
            continue

        time, name, phone, state = submission[FORM_TIME_IDX], submission[FORM_NAME_IDX], submission[FORM_PHONE_IDX], submission[FORM_STATE_IDX]
        user = FormSubmission(time, name, phone, state)

        if not phonenumbers.is_valid_number(user.phone_num):
            logger.warning('user {} has invalid phone number {}'.format(user.name, user.phone_num))
            continue

        # res is stored in time submitted order, so we just keep the first submission.
        # dedup by phone number
        phone_str = phonenumbers.format_number(user.phone_num, phonenumbers.PhoneNumberFormat.E164)
        if phone_str in unique_users:
            unique_users[phone_str].num_submissions += 1
        else:
            unique_users[phone_str] = user

    logger.info('Collected {} unique users'.format(len(unique_users)))
    return unique_users.values()


# if __name__ == '__main__':
#     get_form_responses()
    # get_google_creds()
