# -*- coding: utf-8 -*-
import json
import boto3
import requests
import datetime as dt
from bs4 import BeautifulSoup

TAGS = ['cost', 'detaildesc', 'eventid', 'eventname', 'eventtype', 'evenddt', 'registrationlink', 'registrationtitle',
        'evstartdt']
CONTACT_TAGS = ['email', 'firstname', 'lastname', 'title', 'phone', 'post']
VENUE_TAGS = ['city', 'country', 'state', 'location']
ENDPOINT = "http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1}"

s3 = boto3.resource('s3')


def handler(event, context):
    entries = get_event_list()
    if len(entries) > 0:
        s3.Object('trade-events', 'ita.json').put(Body=json.dumps(entries), ContentType='application/json')
        return "Uploaded ita.json file with %i trade events" % len(entries)
    else:
        return "No entries loaded from %s so there is no JSON file to upload" % ENDPOINT


def get_event(item):
    event = {tag: get_text(item, tag) for tag in TAGS}
    event['url'] = get_url(item)
    event['evenddt'] = normalize_date(event['evenddt'])
    event['evstartdt'] = normalize_date(event['evstartdt'])
    event['contacts'] = get_contacts(item)
    event['venues'] = get_venues(item)
    event['industries'] = get_industries(item)
    event['cost'] = float(event['cost'])
    return event


def get_venues(item):
    return [get_venue(item.stop)]


def get_venue(venue_entry):
    venue = {tag: get_text(venue_entry, tag) for tag in VENUE_TAGS}
    return venue


def get_industries(item):
    return [get_industry(industry) for industry in item.findAll('industry')]


def get_industry(industry_entry):
    return industry_entry.text.encode('utf8')


def get_contacts(item):
    return [get_contact(contact) for contact in item.findAll('contact')]


def get_contact(contact_entry):
    contact = {tag: get_text(contact_entry, tag) for tag in CONTACT_TAGS}
    return contact


def get_url(item):
    try:
        url = item.websites.website['url'].encode('utf8')
    except:
        url = None
    return url


def normalize_date(entry_date):
    return dt.datetime.strptime(entry_date, '%m/%d/%Y').strftime("%Y-%m-%d")


def get_text(item, tag):
    inner_text = get_inner_text(item, tag)
    result_text = '{}'.format(inner_text)
    return result_text


def get_inner_text(item, tag):
    element = item.find(tag)
    try:
        element_text = element.text.encode('utf8')
    except AttributeError:
        element_text = ""
    return element_text


def get_event_list():
    print "Fetching XML feed of items..."
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    far_off = dt.date.today() + dt.timedelta(days=365 * 4)
    endpoint = ENDPOINT.format(tomorrow.strftime('%m/%d/%Y'), far_off.strftime('%m/%d/%Y'))
    soup = get_soup(endpoint)
    items = soup.eventlist.findAll('eventinfo')
    event_list = [get_event(item) for item in items]
    print "Found %i items" % len(event_list)
    return event_list


def get_soup(link):
    response = requests.get(link)
    poorly_formed_xml = response.text
    soup = BeautifulSoup(poorly_formed_xml, "html.parser")
    return soup
