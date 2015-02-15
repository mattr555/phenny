import web
import json
import time
import datetime
import threading
import os

def filename(phenny):
    name = phenny.nick + '-' + phenny.config.host + '.tpp.db'
    return os.path.join(os.path.expanduser('~/.phenny'), name)

def dump(phenny):
    with open(filename(phenny), 'w') as f:
        json.dump(phenny.tpplast, f)

def load(phenny):
    if os.path.exists(filename(phenny)):
        with open(filename(phenny)) as f:
            try:
                phenny.tpplast = json.loads(f.read())
            except ValueError:
                phenny.tpplast = []
    else:
        phenny.tpplast = []
    dump(phenny)

def setup(phenny):
    phenny.tpplasttime = time.time() - 10  # manual flood protection
    load(phenny)
    phenny.tpp_timer = threading.Timer(60, check_new, (phenny,))
    phenny.tpp_timer.start()

def list_difference(new, old):
    if len(old) == 0:
        return new
    newest = old[0]
    for i in range(len(new)):
        if new[i] == newest:
            return new[:i] + old

def check_new(phenny):
    r = web.get(phenny.config.tpp_update_url)
    r = json.loads(r)
    phenny.tpplast = list_difference(r['data']['children'], phenny.tpplast)[:500]
    dump(phenny)
    phenny.tpp_timer = threading.Timer(60, check_new, (phenny,))
    phenny.tpp_timer.start()

def get_msg(phenny, input):
    if phenny.tpplasttime + 10 > time.time():
        return  # bail, spammers
    if not phenny.tpplast:
        check_new(phenny)
    if input.group(1) and input.group(1).isdigit():
        num = int(input.group(1)) - 1
    else:
        num = 0
    if num > len(phenny.tpplast) - 1:
        return phenny.say('Sorry, too far back.')
    phenny.tpplasttime = time.time()
    phenny.say('{} - /u/{}'.format(phenny.tpplast[num]['data']['body'], phenny.tpplast[num]['data']['author']))
get_msg.rule = r'!update(?:\s(\d+))?'

def get_time(phenny, input):
    delta = datetime.datetime.now() - datetime.datetime(2015, 2, 12, 16)
    d = delta.days
    h = delta.seconds // (60*60)
    m = delta.seconds // 60 % 60
    phenny.say('{}d{}h{}m'.format(d, h, m))
get_time.rule = r'!time'
