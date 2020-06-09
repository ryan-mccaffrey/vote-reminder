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
# REAL sheet
FORM_RESPONSE_SHEET_ID = '1ve9JZdtaxLmJD797reJG02G65loeeHsUuX7thMBZmXA'
# TEST sheet
# FORM_RESPONSE_SHEET_ID = '1dFA2K3lOk0ZxGSUNpzfka0jZJECAcN4x_0hx4xmQUZU'

FORM_RESPONSE_RANGE = 'Form_Responses!A2:E'

class FormSubmission:
    def __init__(self, timestamp, name, phone_str, state):
        self.submit_time = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        self.name = name
        self.phone_num = phonenumbers.parse(phone_str, 'US')
        self.state_code = state
        self.num_submissions = 1
        self.is_new = True

    def __str__(self):
        return '{} (State: {}, Phone: {} -- new = {})'.format(self.name, self.state_code, 
            phonenumbers.format_number(self.phone_num, phonenumbers.PhoneNumberFormat.E164), self.is_new)

    def __eq__(self, other):
        if not isinstance(other, FormSubmission):
            return False
        return self.phone_num == other.phone_num and self.state_code == other.state_code

    # kind of a hash
    def get_set_key(self):
        return '{}_{}'.format(phonenumbers.format_number(self.phone_num, phonenumbers.PhoneNumberFormat.E164), self.state_code)

    def set_phone_num(self, num):
        self.phone_num = phonenumbers.parse(num, 'US')

def get_test_user():
    return FormSubmission('6/6/2020 21:29:28', 'Ryan', '631-707-5422', 'CA')


def get_google_creds():
    creds = None
    # Check first if access and refresh tokens already exist
    if os.path.exists('cache/google_token.pickle'):
        with open('cache/google_token.pickle', 'rb') as token:
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
        with open('cache/google_token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_new_users():
    form_users = _get_form_responses()

    if not os.path.exists('cache/users.pickle'):
        return form_users.values()

    with open('cache/users.pickle', 'rb') as f:
        existing_users = pickle.load(f)

    new_users = {}
    for user_key, user in form_users.items():
        if user_key not in existing_users:
            new_users[user_key] = user

    for user_key, user in existing_users.items():
        if user.is_new:
            new_users[user_key] = user

    return new_users.values()

def get_all_users():
    form_users = _get_form_responses()    

    if not os.path.exists('cache/users.pickle'):
        return form_users.values()

    with open('cache/users.pickle', 'rb') as f:
        existing_users = pickle.load(f)

    for user_key, user in form_users.items():
        if user_key not in existing_users:
            existing_users[user_key] = user

    return existing_users.values()

def save_users(users):
    user_map = {}
    for user in users:
        user_map[user.get_set_key()] = user

    with open('cache/users.pickle', 'wb') as f:
        pickle.dump(user_map, f)

def _get_form_responses():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = get_google_creds()
    logger.info('Got google credentials...')
    assert creds and creds.valid
    logger.info('... and they are valid')
    # TODO: make cache discovery True if this ever evolves past a cron
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=FORM_RESPONSE_SHEET_ID,
                                range=FORM_RESPONSE_RANGE).execute()

    users = {}
    res = result.get('values', [])
    for submission in res: 
        if len(submission) == 0:
            continue

        time, name, phone, state = submission[FORM_TIME_IDX], submission[FORM_NAME_IDX], submission[FORM_PHONE_IDX], submission[FORM_STATE_IDX]
        user = FormSubmission(time, name, phone, state)

        if not phonenumbers.is_valid_number(user.phone_num):
            logger.warning('user {} has invalid phone number {}'.format(user.name, user.phone_num))
            continue

        # de-duplicate the form responses.
        if user.get_set_key() in users:
            logger.info('Found duplicate user {} while parsing form'.format(user))
        else:
            users[user.get_set_key()] = user

    logger.info('Collected {} unique users from google form'.format(len(users)))
    return users


# if __name__ == '__main__':
#     get_form_responses()
    # get_google_creds()
