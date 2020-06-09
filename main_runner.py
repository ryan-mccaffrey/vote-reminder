from user_parser import get_new_users, get_test_user, save_users, get_all_users
from election_parser import parse_elections_csv, get_all_election_events
from texter import TextManager
from datetime import datetime

# TODO:
# - better error handling around not being able to send texts
# - split new user and events texts
# - testing response sheet, and making sure the test vs. real caches are separate
# - database
# - convert to use mypy

def main_new_users():
    import logging.config
    start = datetime.now()
    logging.basicConfig(filename='logs/newusers_{}.log'.format(
        start.strftime('%Y%m%d_%H%M%S')), level=logging.DEBUG)

    texter = TextManager(start)
    users = get_new_users()
    texter.send_new_user_texts(start, users)
    save_users(users)


def main_send_events():
    import logging.config
    start = datetime.now()
    logging.basicConfig(filename='logs/sendevents_{}.log'.format(
        start.strftime('%Y%m%d_%H%M%S')), level=logging.DEBUG)

    texter = TextManager(start)
    users = get_all_users()
    election_infos = parse_elections_csv()
    events = get_all_election_events(election_infos, start)
    texter.send_all_event_texts(start, users, events)
    save_users(users)


def end_to_end_test():
    runtime = datetime.strptime('6/6/2020 21:31:00', '%m/%d/%Y %H:%M:%S')
    users = [get_test_user()]

    texter = TextManager(runtime, is_test=True)
    election_infos = parse_elections_csv()

    # hardcode CA date
    assert election_infos[4].state_code == 'CA'
    election_infos[4].primary_date = datetime.strptime('2020-06-07', '%Y-%m-%d')

    events = get_all_election_events(election_infos, runtime)
    print(events)
    texter.send_all_event_texts(runtime, users, events)

if __name__ == '__main__':
    end_to_end_test()
