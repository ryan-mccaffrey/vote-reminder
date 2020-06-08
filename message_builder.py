from election_parser import get_test_election_info, TimeWarning, MessageEvent
from user_parser import get_test_user
from datetime import datetime
from jinja2 import Template
from enum import Enum
import os

def get_event_msg(msg_event, user, election_info, warning_time):
    filename = 'message/{}.txt'.format(msg_event.value)
    assert os.path.exists(filename)

    with open(filename, 'r') as f:
        msg = f.read()

    t = Template(msg)
    data = election_info.to_dict()
    data['name'] = user.name
    data['warning_time'] = warning_time.value
    text = t.render(data)
    return text

def get_receipt_msg(start, user_texts, event_text_dict):
    with open('message/cron_receipt.txt', 'r') as f:
        msg = f.read()

    t = Template(msg)
    data = {
        "runtime": datetime.now() - start,
        "new_user_texts": user_texts,
        "event_text_dict": event_text_dict,
    }
    text = t.render(data)
    return text

if __name__ == '__main__':
    # event text
    # info = get_test_election_info()
    # user = get_test_user()
    # text = get_event_msg(MessageEvent.GENERAL_DEADLINE, user, info, TimeWarning.WEEK)

    # cron receipt
    start = datetime.now()
    text = get_receipt_msg(start, 12, {"sample thing": 2, "sample three": 3})
    print(text)