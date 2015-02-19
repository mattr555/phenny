import web
import json
import time
import datetime
import threading
import lxml.html

def setup(phenny):
    phenny.tpplasttime = time.time() - 10  # manual flood protection
    phenny.tpplastdex = None
    phenny.tpplastmoney = None
    phenny.tppteam = []
    phenny.tpporgtime = 0
    phenny.tpplast = []
    phenny.tpp_timer = threading.Timer(60, check_new, (phenny,))
    phenny.tpp_timer.start()

def check_new(phenny):
    try:
        r = web.get(phenny.config.tpp_update_url)
        r = json.loads(r)
        phenny.tpplast = r['data']['children']
        phenny.tpp_timer = threading.Timer(60, check_new, (phenny,))
        phenny.tpp_timer.start()
    except:
        pass

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

def update_from_tpporg(phenny):
    if not phenny.tpplastdex or phenny.tpporgtime + 60 > time.time():
        r = web.get('http://twitchplayspokemon.org/')
        d = lxml.html.document_fromstring(r)
        dex = d.get_element_by_id('pokemon').getchildren()
        owned = dex[2].text_content().split(' ')[1]
        seen = dex[3].text_content().split(' ')[1]
        phenny.tpplastdex = '{}/{}/151'.format(owned, seen)
        phenny.tpplastmoney = '$' + d.xpath('body/div[1]/div[2]/div[2]/p[5]')[0].text_content().split(': ')[1]

        phenny.tppteam = []
        pokemon = d.cssselect('#pokemon + div table')[0]
        for i in range(len(pokemon.cssselect('th'))):
            mon = pokemon.cssselect('th')[i].text_content().split()[1]
            level = pokemon.cssselect('tr')[2].cssselect('td')[i].text_content().split()[1]
            phenny.tppteam.append('L{} {}'.format(level, mon))

def pokedex(phenny, input):
    if phenny.tpplasttime + 10 > time.time():
        return  # bail, spammers
    update_from_tpporg(phenny)
    phenny.say(phenny.tpplastdex)
    phenny.tpplasttime = time.time()
pokedex.rule = r'!(pok[eé])?dex'

def money(phenny, input):
    if phenny.tpplasttime + 10 > time.time():
        return  # bail, spammers
    update_from_tpporg(phenny)
    phenny.say(phenny.tpplastmoney)
    phenny.tpplasttime = time.time()
money.rule = r'!(money|(pok[eé])?yen)'

def team(phenny, input):
    if phenny.tpplasttime + 10 > time.time():
        return  # bail, spammers
    update_from_tpporg(phenny)
    phenny.say(', '.join(phenny.tppteam))
    phenny.tpplasttime = time.time()
team.rule = r'!team'
