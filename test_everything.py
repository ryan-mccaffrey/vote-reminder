from election_parser import get_warning_event, get_test_election_info, MessageEvent, TimeWarning
from datetime import datetime
import pytest
import os
import time

def mock_today(today):
    return datetime.strptime(today, '%Y-%m-%d')

def test_messages_exist():
    for mt in MessageEvent:
        if mt == MessageEvent.PRIMARY_DEADLINE: continue
        assert os.path.exists('message/{}.txt'.format(mt.value))

def test_get_events():
    info = get_test_election_info(state_code='NJ')

    # Second num is number of events expected
    test_cases = [
        # primary deadline is 2020-06-16. No notifications for this anymore
        ('2020-06-09', 0, MessageEvent.PRIMARY_DEADLINE, TimeWarning.WEEK),
        ('2020-06-15', 0, MessageEvent.PRIMARY_DEADLINE, TimeWarning.DAY),
        ('2020-06-16', 0, MessageEvent.PRIMARY_DEADLINE, TimeWarning.NONE),
        # primary election is 2020-07-07
        ('2020-06-30', 0, MessageEvent.PRIMARY_ELECTION, TimeWarning.NONE),
        ('2020-07-06', 1, MessageEvent.PRIMARY_ELECTION, TimeWarning.DAY),
        ('2020-07-07', 1, MessageEvent.PRIMARY_ELECTION, TimeWarning.TODAY),
        # general deadline is 2020-10-13
        ('2020-10-06', 1, MessageEvent.GENERAL_DEADLINE, TimeWarning.WEEK),
        ('2020-10-12', 1, MessageEvent.GENERAL_DEADLINE, TimeWarning.DAY),
        ('2020-10-13', 0, MessageEvent.GENERAL_DEADLINE, TimeWarning.NONE),
        # general election is, of course, 2020-11-03
        ('2020-10-27', 0, MessageEvent.GENERAL_ELECTION, TimeWarning.NONE),
        ('2020-11-02', 1, MessageEvent.GENERAL_ELECTION, TimeWarning.DAY),
        ('2020-11-03', 1, MessageEvent.GENERAL_ELECTION, TimeWarning.TODAY),
    ]

    for i in range(len(test_cases)):
        print('test {}'.format(i))
        date, num_events, event, warning = test_cases[i]
        today = mock_today(date)
        events = info.get_events_to_send(today)

        assert len(events) == num_events
        if num_events == 0:
            continue

        actual_event, actual_warning, _ = events[0]
        assert actual_event == event
        assert actual_warning == warning

if __name__ == '__main__':
    test_get_events()