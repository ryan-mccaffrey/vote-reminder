from user_parser import get_form_responses, get_test_user
from election_parser import parse_elections_csv, get_all_election_events
from texter import TextManager
from datetime import datetime
import logging

# TODO:
# - error handling around not being able to send texts

def main():
    run_time = datetime.now()
    logging.basicConfig(filename='logs/cronscript_{}.log'.format(run_time.strftime('%Y%m%d_%H%M%S'),level=logging.DEBUG))

    texter = TextManager(run_time)
    users = get_form_responses()

    election_infos = parse_elections_csv()
    events = get_all_election_events(election_infos, runtime)
    texter.send_all_event_texts(run_time, users, events)

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
    # main()
    end_to_end_test()