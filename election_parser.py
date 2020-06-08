from datetime import datetime, timedelta
from enum import Enum
import logging
import csv
import os

logger = logging.getLogger(__name__)

PRIMARY_DATE_IDX = 0
STATE_IDX = 1
ABSENTEE_SITE_IDX = 2
PRIMARY_DEADLINE_IDX = 3
STATE_CODE_IDX = 4
REGISTRATION_DATE_IDX = 5
ONLINE_REGISTRATION_FLAG_IDX = 6
VOTEORG_REGISTRATION_SITE_IDX = 7
REGISTRATION_SITE_IDX = 8
ELECTION_TYPE_IDX = 12

# Event types to send messages for
class MessageEvent(Enum):
    TEST = 'test'
    NEW_USER = 'new_user'
    PRIMARY_DEADLINE = 'primary_deadline'
    GENERAL_DEADLINE = 'general_deadline'
    PRIMARY_ELECTION = 'primary_election'
    GENERAL_ELECTION = 'general_election'


class TimeWarning(Enum):
    NONE = 'none'
    TODAY = 'today'
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'


global_election_info_state_map = None

def get_election_info_state_map():
    global global_election_info_state_map
    return global_election_info_state_map

class StateElectionInfo:
    def __init__(self, vals):
        assert len(vals) == 15
        self.primary_date = datetime.strptime(vals[PRIMARY_DATE_IDX], '%Y-%m-%d')
        self.state = vals[STATE_IDX]
        self.state_code = vals[STATE_CODE_IDX]

        self.absentee_site = vals[ABSENTEE_SITE_IDX]
        self.voteorg_registration_site = vals[VOTEORG_REGISTRATION_SITE_IDX]
        self.registration_site = vals[REGISTRATION_SITE_IDX]

        try:
            self.primary_deadline = datetime.strptime(vals[PRIMARY_DEADLINE_IDX], '%Y-%m-%d')
        except ValueError:
            self.primary_deadline = None

        try:
            self.general_deadline = datetime.strptime(vals[REGISTRATION_DATE_IDX], '%Y-%m-%d')
            self.register_day_of = False
        except ValueError:
            self.general_deadline = None
            self.register_day_of = True
        
        self.register_online_flag = vals[ONLINE_REGISTRATION_FLAG_IDX].lower() == 'yes'

    # Get all of the text message events to send for this state election info object.
    def get_events_to_send(self, today):
        events = []
    
        if not self.register_day_of:
            # let's just not even do this
            # primary_deadline_event = get_warning_event(today, self.primary_deadline, False)
            # if primary_deadline_event != TimeWarning.NONE:
            #     events.append((MessageEvent.PRIMARY_DEADLINE, primary_deadline_event, self))

            general_deadline_event = get_warning_event(today, self.general_deadline, False)
            if general_deadline_event != TimeWarning.NONE:
                events.append((MessageEvent.GENERAL_DEADLINE, general_deadline_event, self))

        primary_date_event = get_warning_event(today, self.primary_date, True)
        if primary_date_event != TimeWarning.NONE:
            events.append((MessageEvent.PRIMARY_ELECTION, primary_date_event, self))

        # get every warning event for general election
        election_day = datetime.strptime('2020-11-03', '%Y-%m-%d')
        event = get_warning_event(today, election_day, True)
        if event != TimeWarning.NONE:
            events.append((MessageEvent.GENERAL_ELECTION, event, self))

        return events

    def to_dict(self):
        return {
            "primary_date": self.primary_date.strftime("%B %d, %Y"),
            "state": self.state,
            "state_code": self.state_code,
            "absentee_site": self.absentee_site,
            "voteorg_registration_site": self.voteorg_registration_site,
            "registration_site": self.registration_site,
            "primary_deadline": self.primary_deadline.strftime("%B %d, %Y") if self.primary_deadline else None,
            "general_deadline": self.general_deadline.strftime("%B %d, %Y") if self.general_deadline else None,
            "register_day_of": self.register_day_of,
            "register_online_flag": self.register_online_flag,
        }


def get_warning_event(today, event_date, election_event):
    if event_date is None:
        return TimeWarning.NONE

    num_days = (event_date - today).days
    if (event_date - today) - timedelta(days=num_days) > timedelta():
        num_days += 1

    if election_event and num_days == 0:
        return TimeWarning.TODAY
    elif num_days == 1:
        return TimeWarning.DAY
    elif not election_event and num_days == 7:
        return TimeWarning.WEEK
    return TimeWarning.NONE

def get_all_election_events(election_infos, today):
    events = []
    for info in election_infos:
        events = events + info.get_events_to_send(today)
    logger.info('Computed election events: {}'.format(events))
    return events

def get_test_election_info(state_code='NJ'):
    nh_row = ['2020-09-08', 'New Hampshire', 'https://www.vote.org/absentee-ballot/new-hampshire/', '2020-09-01', 'NH', '2020-10-27', 'No', '', 'https://sos.nh.gov/HowRegVote.aspx', '', '', '', 'State Primary', '', 'No']
    ny_row = ['2020-06-23', 'New York', 'https://www.vote.org/absentee-ballot/new-york/', '', 'NY', '2020-10-09', 'Yes', 'https://www.vote.org/register-to-vote/new-york/', 'http://dmv.ny.gov/org/more-info/electronic-voter-registration-application', '0', '27', 'https://ballotpedia.org/New_York_elections,_2020', 'State Primary and Presidential Primary', '', 'Yes; the Presidential Primary was originally scheduled for April 28.']
    nd_row = ['2020-06-09', 'North Dakota', 'https://www.vote.org/absentee-ballot/north-dakota/', '', 'ND', 'N/A', 'No', '', 'https://vip.sos.nd.gov/PortalListDetails.aspx?ptlhPKID=79&ptlPKID=7', '0', '1', 'https://ballotpedia.org/North_Dakota_elections,_2020', 'State Primary', '', 'No']
    nj_row = ['2020-07-07', 'New Jersey', 'https://www.vote.org/absentee-ballot/new-jersey/', '2020-06-16', 'NJ', '2020-10-13', 'Yes', 'https://www.vote.org/register-to-vote/new-jersey/', 'https://www.state.nj.us/state/elections/voter-registration.shtml', '', '', '', 'State Primary* and Presidential Primary', '', 'Yes; originally scheduled for June 2.']

    if state_code == 'NH':
        return StateElectionInfo(nh_row)
    elif state_code == 'ND':
        return StateElectionInfo(nd_row)
    elif state_code == 'NY':
        return StateElectionInfo(ny_row)
    return StateElectionInfo(nj_row)

def get_info_by_state_code(infos, code):
    for info in infos:
        if info.state_code == code:
            return info
    return None

def parse_elections_csv():
    global global_election_info_state_map
    assert os.path.exists('election_data.csv')

    election_infos = []
    global_election_info_state_map = {}

    with open('election_data.csv', 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        next(csv_reader) # skip header
        for row in csv_reader:
            info = StateElectionInfo(row)
            global_election_info_state_map[info.state_code] = info
            election_infos.append(info)
    
    logger.info('Finished parsing election info')
    return election_infos

# if __name__ == '__main__':
#     parse_elections_csv()
    # print(global_election_info_state_map)
    # pass
    # infos = parse_elections_csv()
    # today = datetime.now()



