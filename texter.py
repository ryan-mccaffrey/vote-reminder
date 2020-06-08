from election_parser import MessageEvent, TimeWarning, get_test_election_info, get_election_info_state_map
from message_builder import get_event_msg, get_receipt_msg
from user_parser import get_test_user

from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
import phonenumbers
import pickle
import logging
import os

class TextManager:
    def __init__(self, now, is_test=False):
        load_dotenv()

        if is_test:
            account_sid = os.getenv('TWILIO_TEST_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_TEST_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_TEST_FROM_NUMBER')
        else:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.from_number = os.getenv('TWILIO_FROM_NUMBER')

        self.client = Client(username=account_sid, password=auth_token)
        self.is_test = is_test

        # send initializing text to myself
        admin_num = phonenumbers.parse(os.getenv('RYAN_PHONE_NUMBER'), 'US')
        self.admin_numbers = [admin_num]
        msg = 'Vote reminder cron: starting run at {}'.format(now)
        self.send_text(admin_num, msg)
        logging.info('Initialized text manager, admin_numbers: {}'.format(self.admin_numbers))

    def send_all_event_texts(self, now, users, events):
        logging.info('Sending text messages for all events...')
        num_new_user_texts = self.send_new_user_texts(now, users)
        event_map = self.send_event_texts(users, events)

        # generate receipt to send to myself
        logging.info('Sending text receipt to admins...')
        msg = get_receipt_msg(now, num_new_user_texts, event_map)
        for admin in self.admin_numbers:
            self.send_text(admin, msg)

    def send_new_user_texts(self, now, users):
        election_info_state_map = get_election_info_state_map()
        assert election_info_state_map is not None

        last_runtime = None
        if os.path.exists('last_runtime.pickle'):
            with open('last_runtime.pickle', 'rb') as lrt:
                last_runtime = pickle.load(lrt)

        # Send all new user texts. All of the times operate in the local PT timezone.
        texts_sent = 0
        for user in users:
            if last_runtime is None or user.submit_time > last_runtime:
                msg = get_event_msg(MessageEvent.NEW_USER, user, election_info_state_map[user.state_code], TimeWarning.NONE)
                self.send_text(user.phone_num, msg)
                texts_sent += 1

        # Record the current time for next run, but only if not testing
        if not self.is_test:
            with open('last_runtime.pickle', 'wb') as lrt:
                pickle.dump(now, lrt)

        return texts_sent

    def send_event_texts(self, users, events):
        # store users in dict by state
        user_map = {}
        for user in users:
            if user.state_code not in user_map:
                user_map[user.state_code] = [user]
            else:
                user_map[user.state_code].append(user)

        # stores readable event description in key and frequency as val
        receipt_map = defaultdict(int)
        for event_tuple in events:
            event, warning, info = event_tuple
            event_desc = '{} {} ({} notification)'.format(info.state, event.value, warning.value)

            # send to all users affected by this event
            for user in user_map[info.state_code]:
                msg = get_event_msg(event, user, info, warning)
                self.send_text(user.phone_num, msg)
                receipt_map[event_desc] += 1

        return receipt_map

    def send_text(self, to_num, msg_body):
        to_str = phonenumbers.format_number(to_num, phonenumbers.PhoneNumberFormat.E164)
        try:
            message = self.client.messages.create(to=to_str, 
                from_=self.from_number, body=msg_body)
            logging.info('sent text to {}: {}'.format(to_str, message.sid))
        except Exception as e:
            print('Could not send text to {}: {}'.format(to_str, e))
            logging.warning('Could not send text to {}: {}'.format(to_str, e))

def main():
    run_time = datetime.now()
    manager = TextManager(run_time, is_test=True)
    info = get_test_election_info()
    user = get_test_user()
    text = get_event_msg(MessageEvent.NEW_USER, user, info)

    manager.send_text('631-707-5422', text)

if __name__ == '__main__':
    main()
