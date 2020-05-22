# -*- coding: utf-8 -*-
import datetime as dt
import json
import logging

import boto3
import msal
import requests
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup

TAGS = [
    "cost",
    "detaildesc",
    "eventid",
    "eventname",
    "eventtype",
    "evenddt",
    "registrationlink",
    "registrationtitle",
    "evstartdt",
]
CONTACT_TAGS = ["email", "firstname", "lastname", "title", "phone", "post"]
VENUE_TAGS = ["city", "country", "state", "location"]
ENDPOINT = "http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1}"
BUCKET = "trade-events"

s3 = boto3.client("s3")


def handler(event, context):
    entries = get_concat_events()
    try:
        s3.put_object(
            Bucket=BUCKET,
            Body=json.dumps(entries),
            Key="ita.json",
            ContentType="application/json",
        )
        print(f" ✅ Uploaded ita.json file with {len(entries):d} trade events")
    except ClientError as e:
        logging.error(e)
        return False
    return True


def get_event(item):
    event = {tag: get_text(item, tag) for tag in TAGS}
    event["url"] = get_url(item)
    event["evenddt"] = normalize_date(event["evenddt"])
    event["evstartdt"] = normalize_date(event["evstartdt"])
    event["contacts"] = get_contacts(item)
    event["venues"] = get_venues(item)
    event["industries"] = get_industries(item)
    event["cost"] = float(event["cost"])
    return event


def get_venues(item):
    return [get_venue(item.stop)]


def get_venue(venue_entry):
    venue = {tag: get_text(venue_entry, tag) for tag in VENUE_TAGS}
    return venue


def get_industries(item):
    return [get_industry(industry) for industry in item.findAll("industry")]


def get_industry(industry_entry):
    return industry_entry.text


def get_contacts(item):
    return [get_contact(contact) for contact in item.findAll("contact")]


def get_contact(contact_entry):
    contact = {tag: get_text(contact_entry, tag) for tag in CONTACT_TAGS}
    return contact


def get_url(item):
    try:
        url = item.websites.website["url"]
    except Exception:
        url = None
    return url


def normalize_date(entry_date):
    return dt.datetime.strptime(entry_date, "%m/%d/%Y").strftime("%Y-%m-%d")


def get_text(item, tag):
    inner_text = get_inner_text(item, tag)
    result_text = "{}".format(inner_text)
    return result_text


def get_inner_text(item, tag):
    element = item.find(tag)
    try:
        element_text = element.text
    except AttributeError:
        element_text = ""
    return element_text


def get_event_list():
    print("Fetching XML feed of items...")
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    far_off = dt.date.today() + dt.timedelta(days=365 * 4)
    endpoint = ENDPOINT.format(
        tomorrow.strftime("%m/%d/%Y"), far_off.strftime("%m/%d/%Y")
    )
    soup = get_soup(endpoint)
    items = soup.eventlist.findAll("eventinfo")
    event_list = [get_event(item) for item in items]
    print(f"Found {len(event_list):d} ITA trade items on eMenu")
    return event_list


def get_soup(link):
    response = requests.get(link)
    poorly_formed_xml = response.text
    soup = BeautifulSoup(poorly_formed_xml, "html.parser")
    return soup


SCOPE = ["https://graph.microsoft.com/.default"]
AUTHORITY = "https://login.microsoftonline.com/a1d183f2-6c7b-4d9a-b994-5f2f31b3f780"
SHAREPOINT_ENDPOINT = (
    "https://graph.microsoft.com/beta/sites/itaisinternationaltrade.sharepoint.com"
    ",04a0935b-f459-4fe4-9e92-934a7fc75845,bfa89772-5e48-4ee8-8d09-09bd96bf04c3/"
    "lists/2d9a7dde-0495-41c6-b09c-0bbf11a92662/items?expand=fields"
)

PERMITTED_STATUS = [
    "MOA Received",
    "Waiting on End of Show Report",
    "Event Completed"
]


def get_sharepoint_secret():
    """Get the Azure client secret from AWS"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )
    get_secret_value_response = client.get_secret_value(
        SecretId="sharepoint_api"
    )
    return json.loads(get_secret_value_response['SecretString'])


def get_sharepoint_graph_data():
    """Get new access_token from Azure, use it to make request to endpoint"""
    response = get_sharepoint_secret()
    app = msal.ConfidentialClientApplication(
        response["client_id"],
        authority=AUTHORITY,
        client_credential=response["client_secret"]
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    graph_data = requests.get(
        SHAREPOINT_ENDPOINT,
        headers={"Authorization": "Bearer " + result["access_token"]}
    ).json()
    return graph_data


def get_allowed_events():
    for row in get_sharepoint_graph_data()["value"]:
        if (row["fields"]["AStatus"] in PERMITTED_STATUS):
            yield row


def convert_date(event_item, date_col):
    try:
        return dt.datetime.strptime(
            str(event_item["fields"][date_col]), "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%Y-%m-%d")
    except TypeError:
        return None


def get_a_name(event_item, n):
    try:
        return event_item["fields"]["oogt"].partition(" ")[
            n
        ]
    except AttributeError:
        return None


def get_tepp_contact_info(event_item):
    contact = {}
    contact["firstname"] = get_a_name(event_item, 0)
    contact["title"] = None
    contact["lastname"] = get_a_name(event_item, -1)
    contact["phone"] = event_item["fields"]["ContactPhoneNumber"]
    contact["post"] = event_item["fields"]["qcfm"]
    contact["email"] = event_item["fields"]["Contact_x0020_Email"]
    return contact


def get_tepp_description(event_item):
    some_description = event_item["fields"]["Show_x0020_Description"]
    soup = BeautifulSoup(some_description, "html.parser")
    return soup.text


def get_tepp_attribute(event_item, attribute):
    try:
        return event_item["fields"][attribute]
    except KeyError:
        return None


def get_tepp_venue(event_item):
    venue = {}
    venue["city"] = get_tepp_attribute(event_item, "Event_x0020_Location_x0020__x0020")
    venue["state"] = get_tepp_attribute(event_item, "Event_x0020_Location_x0020__x002")
    venue["country"] = event_item["fields"]["Country"]
    location_array = [venue["city"], venue["state"], venue["country"]]
    venue["location"] = ", ".join([str(item) for item in location_array if item])
    return venue


def generate_eventid(event_item):
    return event_item["fields"]["@odata.etag"].partition(",")[
        0
    ].replace('"', "")


def make_tepp_event(event_item):
    event = {}
    event["eventid"] = generate_eventid(event_item)
    event["eventname"] = event_item["fields"]["Title"]
    event["detaildesc"] = get_tepp_description(event_item)
    event["url"] = event_item["fields"]["Organizer_x0020_Website"]
    event["evstartdt"] = convert_date(event_item, "pu1v")
    event["evenddt"] = convert_date(event_item, "u6gh")
    event["venues"] = [get_tepp_venue(event_item)]
    event["contacts"] = [get_tepp_contact_info(event_item)]
    event["industries"] = get_tepp_attribute(event_item, "Primary_x0020_Industry")
    event["eventtype"] = "Trade Events Partnership Program"
    event["registrationlink"] = None
    event["cost"] = None
    event["registrationtitle"] = None
    return event


def get_tepp_events():
    events = []
    for i in get_allowed_events():
        events.append(make_tepp_event(i))
    print(f"Found {len(events):d} TEPP items in SharePoint")
    return events


def get_concat_events():
    concat_events = get_event_list()
    concat_events.extend(get_tepp_events())
    return concat_events
