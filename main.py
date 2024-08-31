# Script that generates the CETL weekly email that is sent out every monday morning at 6am
# Original Author: Henry Acevedo
# Last Edited by Jeff Henline - May 2024 (refactored for hosting on AWS
# and Sendgrid for email delivery, config.ini integration, and external txt file for emails)

import configparser
import re
import json
import requests
import datetime
from collections import defaultdict
from eventbrite import Eventbrite
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail, To, Cc

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('/home/bitnami/scripts/config.ini')
SENDGRID_API_KEY = config.get('auth', 'sendgrid_api_key')
MYTOKEN = config.get('auth', 'eventbrite')

# Initialize Eventbrite API
eventbrite = Eventbrite(MYTOKEN)
MYURL = 'https://www.eventbriteapi.com/v3'
MYTOKEN = 'Bearer {}'.format(MYTOKEN)


def sendEmail(data):
    # Load email recipients from recipients.txt
    to_emails = []
    cc_emails = []
    with open('recipients.txt', 'r') as file:
        lines = file.readlines()
        current_list = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                if 'TO' in line:
                    current_list = to_emails
                elif 'CC' in line:
                    current_list = cc_emails
            elif line:
                if current_list is not None:
                    current_list.append(line)

    mon = datetime.datetime.now()
    fri = datetime.datetime.now() + datetime.timedelta(days=4)
    sg = SendGridAPIClient(SENDGRID_API_KEY)

    # Create a SendGrid Mail object with dynamic email recipients
    message = Mail(
        from_email='cetltech@calstatela.edu',
        to_emails=[To(email) for email in to_emails],
        subject=f"This week at CETL {mon.strftime('%m/%d/%Y')} - {fri.strftime('%m/%d/%Y')} (from FDMS)",
        html_content=data
    )

    # Add CC recipients dynamically
    for email in cc_emails:
        message.add_cc(Cc(email))

    # Send the email
    try:
        response = sg.send(message)
        print("Email Response Status Code:", response.status_code)
        print("Email Response Body:", response.body)
        print("Email Response Headers:", response.headers)
    except Exception as e:
        print("Error sending email:", str(e))

    # Check if data is empty
    if not data.strip():
        print("Warning: Email content is empty.")



# function that uses the Eventbrite API to get the events for the current week
def main():
    print("Main function started")
    header = {'Authorization': MYTOKEN}

    # Get the current date and reset the time to 0:00:00
    current_time = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # create variable dt and set it to the current date plus 7 days
    dt = current_time + datetime.timedelta(days=7)
    early = current_time + datetime.timedelta(days=0)

    # print the current date and the date of the friday of the week to the console
    print(current_time, early, dt)

    # Snippet of code that is used to remove the text in parentheses from the event name
    paren = re.compile(r"\(.+\)")
    staOnly = re.compile(
        "Workshops for all instructors of record, including Lecturers and graduate Teaching Assistants.")

    payload = {"order_by": "start_asc", "expand": "venue", "status": "live"}
    events = eventbrite.get(f'/organizations/58546560081/events/', data=payload)
    # print(events)

    # Define the email template string
    email_template = """
    <tr>
        <td colspan="4">
            <div>
            <strong><br><font face="Arial" size="3">{day}<br>{start} - {end}<br>Location: {venue}<br>
            <a href="{URL}">Click here to RSVP</a>
            </font></strong>
            </p>
            </div>
        </td>
    </tr>
    """

    body = """
            <tr height="40">
            <td colspan="4">
            <img width="600" src="https://fdms.online/images/cetl_banner.png" alt="CETL Banner" title="CETL Banner">
            <font face="Arial"><h1>This week at CETL</h1></font>
            </td>
            </tr>
            """

    # The code processes a collection of events, modifies and extracts specific information from each event,
    # and organizes the data into dictionaries (dEvents, logos, and descs) for further usage or analysis.
    dEvents = defaultdict(list)
    logos = dict()
    descs = dict()
    for event in events["events"]:
        event_date = datetime.datetime.strptime(event["start"]["local"], "%Y-%m-%dT%H:%M:%S")

        if event['organizer_id'] != '3741604165' or event_date <= early:
            continue

        if event_date >= dt:
            break

        # Digging through information to get wanted info.
        eventName = event["name"].get("text", "No Name")
        eventName = re.sub(paren, "", eventName).strip()
        dEvents[eventName].append(event)
        if event["logo"] is not None:
            logos[eventName] = event["logo"].get("url", "No Logo")
        else:
            logos[eventName] = "No Logo"

        resp = requests.get(f"{MYURL}/events/{event['id']}/description/", headers=header)
        myJSON = json.loads(resp.text)

        # using the description of the event, replace the staOnly text with an empty string
        # staOnly was used in the past but maybe not anymore
        desc = myJSON['description']
        desc = re.sub(staOnly, "", desc).strip()
        descs[eventName] = desc
    # print(dEvents)

    for workshop in dEvents:
        body += f"""
                <tr>
                    <td colspan="4">
                        <p><img src="{logos[workshop]}" alt="{workshop}" title="{workshop}" height="150" width="300"><br>
                        <font face="Arial" style="font-size: 11pt">{descs[workshop]}</font></p>
                    </td>
                </tr>
                """
        # print(workshop)

        for event in dEvents[workshop]:
            if event['online_event']:
                eventAddr = "Online Event"
            else:
                eventAddr = event['venue']['address']['address_1']
            eventReg = event.get("url", "No Registration URL")
            startTimeUTC = event["start"].get("local", "No start")
            endTimeUTC = event["end"].get("local", "No end")

            startTime = datetime.datetime.strptime(startTimeUTC, "%Y-%m-%dT%H:%M:%S")
            startD = startTime.strftime("%A, %B %d, %Y")
            startT = startTime.strftime("%I:%M %p")

            endTime = datetime.datetime.strptime(endTimeUTC, "%Y-%m-%dT%H:%M:%S")
            endT = endTime.strftime("%I:%M %p")

            body += email_template.format(
                day=startD, start=startT, end=endT, venue=eventAddr, URL=eventReg
            )
        body += '<tr height="30"><td colspan="4"></td></tr>'
    # Send the email after the loop has completed constructing the body
    sendEmail(body)
    print("sendEmail function called")



if __name__ == "__main__":
    print("Script started")
    main()
    print("Script finished")
