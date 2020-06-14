from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import sys

# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
def create_meeting(dog_name, place, time, owner_email, client_email):
    credentials = pickle.load(open("token.pkl", "rb"))
    service = build("calendar", "v3", credentials=credentials)

    event = {
        'summary': 'Meeting with ' + dog_name,
        'location': place,
        'description': 'meeting with the dog and the owners',
        'start': {
            'dateTime': time +':00',
            'timeZone': 'Asia/Jerusalem',
        },
        'end': {
            'dateTime': time +':00',
            'timeZone': 'Asia/Jerusalem',
        },
        'attendees': [
            {'email': owner_email},
            {'email': client_email}
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute() # pylint: disable=no-member

    print ('Event created: %s' % (event.get('htmlLink')))


create_meeting(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])