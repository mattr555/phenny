# -*- coding: utf-8 -*-
"""
mailing_list.py - mailing list reporter
author: mattr555 <mattramina@gmail.com>
"""

#TODO: multiple channels to broadcast
#fail gracefully on no defined lists
#function for last message in list
#obfuscate emails

import threading
import imaplib
import email
from email.utils import parsedate_tz
import datetime
import re

def configured(phenny):
    return all(hasattr(phenny.config, i) for i in ['imap_server', 'imap_user', 'imap_pass', 'mailing_lists'])

def setup(phenny):
    if not configured(phenny):
        print("Mailing list configuration not fully defined, aborting.")
        return
    phenny.mailing_list_timer = threading.Timer(60*5, check_mail, (phenny,))
    phenny.mailing_list_timer.start()

def recipients(e):
    s = e.get('From', '') + e.get('To', '') + e.get('CC', '')
    return s

def get_text(e):
    for part in e.walk():
        if part.get_content_maintype() == "text":
            return part.get_payload()

def strip_reply_lines(e):
    message = get_text(e).split('\n')
    stripped = []
    for i in message:
        if i.startswith('>'):
            continue
        stripped.append(i)
    return " ␍ ".join(stripped)

def obfuscate_address(address):
    def first_three_chars(match):
        return match.group(1)[:3] + '...' + match.group(2)
    return re.sub(r'([^\s@]+)(@[^@]+\.[^@]+)', first_three_chars, address)

def login(phenny):
    if not configured(phenny):
        return
    try:
        mail = imaplib.IMAP4_SSL(phenny.config.imap_server)
        mail.login(phenny.config.imap_user, phenny.config.imap_pass)
        return mail
    except imaplib.IMAP4.error:
        phenny.msg(phenny.config.owner, 'IMAP connection/auth failed :(')

def format_email(e, list_name):
    message = '{} on "{}" in {}: {}'.format(obfuscate_address(e['From']), e['Subject'], list_name, strip_reply_lines(e))
    if len(message) > 400:
        return message[:395] + '[...]'
    else:
        return message

def check_mail(phenny):
    found = False
    mail = login(phenny)
    if not mail:
        return
    mail.select('inbox')
    rc, data = mail.uid('search', None, 'UNSEEN')
    unseen_mails = data[0].split()

    for uid in unseen_mails:
        rc, data = mail.uid('fetch', uid, '(RFC822)')
        e = email.message_from_string(data[0][1].decode('utf8'))
        for name, (address, channels) in phenny.config.mailing_lists.items():
            if address in recipients(e):
                found = True
                message = format_email(e, name)
                if type(channels) is str:
                    channels = [channels]
                for channel in channels:
                    phenny.msg(channel, message)
        rc, data = mail.uid('store', uid, '+FLAGS', '(\\Seen)')

    mail.logout()
    phenny.mailing_list_timer = threading.Timer(60*5, check_mail, (phenny,))
    phenny.mailing_list_timer.start()
    return found

def list_report(phenny, input):
    ".mailinglist - poll for new mailing list messages"
    phenny.reply('Ok, polling.')
    if not check_mail(phenny):
        phenny.reply('Sorry, no unread mailing list messages.')
list_report.name = "mailing list reporter"
list_report.rule = ('.mailinglist')
list_report.priority = 'medium'
list_report.thread = True

def last_message(phenny, input):
    ".lastmessage <list> - get the latest message from a mailing list"
    #this works on setting up filters in the gmail inbox with the same names as the friendly names
    if input.group(1) and input.group(1) in phenny.config.mailing_lists:
        phenny.reply('Ok, may take some time!')
        mail = login(phenny)
        mail.select(input.group(1))
        uids = mail.uid('search', None, 'ALL')[1][0].decode('utf8').split(' ')
        best = ('', 0)
        for uid in uids:
            d = mail.uid('fetch', uid, '(BODY[HEADER.FIELDS (DATE)])')[1][0][1]
            d = parsedate_tz(d.decode('utf8').strip('Date: ').strip())
            d = datetime.datetime(*d[:7])
            if d.timestamp() > best[1]:
                best = (uid, d.timestamp())
        m = mail.uid('fetch', best[0], '(RFC822)')
        e = email.message_from_string(m[1][0][1].decode('utf8'))
        message = format_email(e, input.group(1))
        phenny.reply(message)
    else:
        phenny.reply('Syntax: .lastmessage [{}]'.format(', '.join(phenny.config.mailing_lists.keys())))
last_message.rule = r'\.lastmessage ?([\w-]+)?'
last_message.thread = True
