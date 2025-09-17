import google_auth_oauthlib.flow
import os

# Set this environment variable to enable insecure transport for local development only
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]

def get_flow(redirect_uri, state=None):
    if state:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    else:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    return flow

def get_authorization_url(redirect_uri):
    flow = get_flow(redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return authorization_url, state

def fetch_token(redirect_uri, state, authorization_response):
    flow = get_flow(redirect_uri, state)
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'granted_scopes': credentials.granted_scopes
    }