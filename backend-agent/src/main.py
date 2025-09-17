from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
import secrets
from typing import Optional
import uvicorn

from calendar_agent.sync_events import sync_assignments_to_calendar, sync_announcements_to_calendar
from utils.google_auth import get_authorization_url, fetch_token

app = FastAPI(
    title="Smart-Class-Update-Agent",
    description="A tool to sync Google Classroom assignments and announcements with Google Calendar",
    version="1.0.0"
)

# Generate a more secure secret key if not provided in environment
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", secrets.token_hex(32))

# Create a secure store for OAuth state
oauth_states = {}

app.add_middleware(
    SessionMiddleware, 
    secret_key=SESSION_SECRET_KEY,
    max_age=3600  # Session expiry in seconds (1 hour)
)

app.add_middleware(
    CORSMiddleware,
    # Add all possible frontend URLs - add or remove as needed for your development setup
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React default
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie", "Content-Type"]
)

# Store for now, change and use a database
credentials_store = {}
assignments_store = {}
announcements_store = {}

@app.get("/")
def root():
    return {"message": "Google Classroom and Calendar Integration"}

@app.get("/login")
async def login(request: Request):
    # Use localhost instead of 127.0.0.1 for consistency with Google OAuth settings
    base_url = str(request.base_url).replace("127.0.0.1", "localhost")
    redirect_uri = base_url.rstrip("/") + "/oauth2callback"
    
    try:
        auth_url, state = get_authorization_url(redirect_uri)
        # Store state in our secure dictionary
        oauth_states[state] = True
        print(f"Login: Generated state={state}")
        return RedirectResponse(auth_url)
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create authorization URL: {str(e)}")

@app.get("/oauth2callback")
async def callback(request: Request, code: str, state: Optional[str] = None):
    print(f"Callback received with state={state}")
    print(f"OAuth states contains: {list(oauth_states.keys())}")
    
    # Verify state using our secure dictionary instead of session
    if not state or state not in oauth_states:
        print(f"Invalid state parameter: {state}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Invalid state parameter",
                "debug_info": {
                    "received_state": state,
                    "valid_states": list(oauth_states.keys())
                }
            }
        )
    
    try:
        # Use localhost instead of 127.0.0.1 for consistency with Google OAuth settings
        base_url = str(request.base_url).replace("127.0.0.1", "localhost")
        redirect_uri = base_url.rstrip("/") + "/oauth2callback"
        
        authorization_response = str(request.url).replace("127.0.0.1", "localhost")
        credentials = fetch_token(redirect_uri, state, authorization_response)
        
        # Generate a session ID
        session_id = secrets.token_hex(16)
        request.session["session_id"] = session_id
        credentials_store[session_id] = credentials
        
        # Clean up used state
        if state in oauth_states:
            del oauth_states[state]
        
        print(f"Auth successful, generated session_id={session_id}")
        
        # Redirect to frontend - use whatever port your frontend is running on
        frontend_url = "http://localhost:5173/?auth=success"
        return RedirectResponse(frontend_url)
        # return RedirectResponse("/check-auth-success")
    except Exception as e:
        print(f"Callback error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"detail": f"Failed to fetch token: {str(e)}"}
        )

@app.get("/check-auth-success")
def auth_success():
    return {"message": "Authorization successful! You can now use the API."}

@app.get("/check-auth-status")
async def check_auth_status(request: Request):
    """Check if the user is authenticated"""
    session_id = request.session.get("session_id")
    if session_id and session_id in credentials_store:
        return {"authenticated": True}
    else:
        return {"authenticated": False}

async def get_current_credentials(request: Request):
    session_id = request.session.get("session_id")
    if not session_id or session_id not in credentials_store:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in first."
        )
    return credentials_store[session_id]

@app.get("/fetch-classwork")
async def get_courses(request: Request, credentials: dict = Depends(get_current_credentials)):
    # Pass the credentials to your courses function
    from classroom_agent.fetch_assignments import fetch_classwork
    classwork = fetch_classwork(credentials)
    session_id = request.session.get("session_id")
    assignments_store[session_id] = classwork
    return classwork

from utils.ai_deduplication import deduplicate_with_ai

@app.get("/fetch-announcements")
async def get_announcements(request: Request, credentials: dict = Depends(get_current_credentials)):
    session_id = request.session.get("session_id")
    try:
        from classroom_agent.fetch_announcements import fetch_announcements
        
        # Fetch announcements
        announcements = fetch_announcements(credentials)
        
        # Extract deadlines
        from RAG.extract_deadlines import extract_deadlines_from_announcements
        extracted_deadlines = extract_deadlines_from_announcements(announcements)
        
        # Get previously fetched assignments if available
        assignments = assignments_store.get(session_id, [])
        
        # Deduplicate deadlines using AI - returns both assignments and unique deadlines
        deduplication_result = deduplicate_with_ai(assignments, extracted_deadlines)
        
        # Get unique deadlines
        unique_deadlines = deduplication_result["unique_deadlines"]
        
        # Store results
        announcements_store[session_id] = unique_deadlines
        
        return {
            "announcements": announcements,
            "extracted_deadlines": unique_deadlines,  # Return only unique ones
            "stats": {
                "total_announcements": len(announcements),
                "deadlines_found": len(extracted_deadlines),
                "unique_deadlines": len(unique_deadlines),
                "duplicates_removed": len(extracted_deadlines) - len(unique_deadlines)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch announcements: {str(e)}")

@app.get("/sync-events")
async def create_events(request: Request, credentials: dict = Depends(get_current_credentials)):
    session_id = request.session.get("session_id")
    
    # Check if we have assignments data
    if session_id not in assignments_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No assignments data available. Please fetch courses first."
        )
    
    # Get stored assignments
    assignments = assignments_store[session_id]
    
    # Pass the credentials and stored assignments to your sync function
    result = sync_assignments_to_calendar(assignments, credentials)
    
    return {"message": "Events synced successfully", "result": result}

@app.get("/sync-announcements")
async def sync_announcement_events(request: Request, credentials: dict = Depends(get_current_credentials)):
    session_id = request.session.get("session_id")
    
    # Check if we have announcement deadline data
    if session_id not in announcements_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No announcement deadlines available. Please fetch announcements first."
        )
    
    # Get stored announcement deadlines
    announcement_deadlines = announcements_store[session_id]
    
    # Use the specialized function for announcements
    result = sync_announcements_to_calendar(announcement_deadlines, credentials)
    
    return {"message": "Announcement events synced successfully", "result": result}

@app.get("/sync-all")
async def sync_all(request: Request, credentials: dict = Depends(get_current_credentials)):
    """
    All-in-one endpoint that runs the full sync process:
    1. Fetch assignments
    2. Fetch announcements and extract deadlines
    3. Sync assignments to calendar
    4. Sync announcement deadlines to calendar
    Each step updates the frontend via returned status
    """
    session_id = request.session.get("session_id")
    results = {
        "step": 0,
        "total_steps": 4,
        "current_action": "Starting sync process",
        "completed": False,
        "classwork": [],
        "announcements": [],
        "calendar_events": [],
        "errors": []
    }
    
    try:
        # Step 1: Fetch classwork
        results["step"] = 1
        results["current_action"] = "Fetching assignments from Google Classroom"
        
        from classroom_agent.fetch_assignments import fetch_classwork
        classwork = fetch_classwork(credentials)
        assignments_store[session_id] = classwork
        
        results["classwork"] = classwork
        
        # Step 2: Fetch announcements and extract deadlines
        results["step"] = 2
        results["current_action"] = "Fetching announcements and extracting deadlines"
        
        from classroom_agent.fetch_announcements import fetch_announcements
        from RAG.extract_deadlines import extract_deadlines_from_announcements
        
        # Fetch announcements
        announcements = fetch_announcements(credentials)
        
        # Extract deadlines
        extracted_deadlines = extract_deadlines_from_announcements(announcements)
        
        # Deduplicate deadlines using AI
        deduplication_result = deduplicate_with_ai(classwork, extracted_deadlines)
        
        # Get unique deadlines
        unique_deadlines = deduplication_result["unique_deadlines"]
        
        # Store results
        announcements_store[session_id] = unique_deadlines
        
        results["announcements"] = {
            "raw_announcements": announcements,
            "extracted_deadlines": unique_deadlines,
            "stats": {
                "total_announcements": len(announcements),
                "deadlines_found": len(extracted_deadlines),
                "unique_deadlines": len(unique_deadlines),
                "duplicates_removed": len(extracted_deadlines) - len(unique_deadlines)
            }
        }
        
        # Step 3: Sync assignments to calendar
        results["step"] = 3
        results["current_action"] = "Syncing assignments to Google Calendar"
        
        assignments_sync_result = sync_assignments_to_calendar(classwork, credentials)
        results["calendar_events"] = results.get("calendar_events", [])
        
        # Store the assignment events with complete information
        if assignments_sync_result.get("created_events"):
            for event in assignments_sync_result.get("created_events", []):
                results["calendar_events"].append({
                    "type": "assignment",
                    "id": event.get("id"),
                    "title": event.get("summary"),
                    "description": event.get("description", ""),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "htmlLink": event.get("htmlLink", ""),
                    "courseName": event.get("courseName", ""),
                    "courseId": event.get("courseId", ""),
                    "status": "created" 
                })
        
        # Step 4: Sync announcement deadlines to calendar
        results["step"] = 4
        results["current_action"] = "Syncing deadlines to Google Calendar"
        
        announcements_sync_result = sync_announcements_to_calendar(unique_deadlines, credentials)
        
        # Store the announcement events with complete information
        if announcements_sync_result.get("created_events"):
            for event in announcements_sync_result.get("created_events", []):
                results["calendar_events"].append({
                    "type": "announcement",
                    "id": event.get("id"),
                    "title": event.get("summary"),
                    "description": event.get("description", ""),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "htmlLink": event.get("htmlLink", ""),
                    "courseName": event.get("courseName", ""),
                    "courseId": event.get("courseId", ""),
                    "status": "created"
                })
        
        
        return results
        
    except Exception as e:
        error_message = str(e)
        results["errors"].append(error_message)
        results["current_action"] = f"Error during sync: {error_message}"
        return results

# Endpoint to delete a calendar event
@app.delete("/calendar-event/{event_id}")
async def delete_calendar_event(
    event_id: str, 
    request: Request, 
    credentials: dict = Depends(get_current_credentials)
):
    """Delete a specific calendar event by ID"""
    try:
        # Build the Google Calendar API client
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Create credentials object from the provided token
        creds = Credentials(
            token=credentials['token'],
            refresh_token=credentials.get('refresh_token'),
            scopes=credentials.get('granted_scopes')
        )
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Delete the event
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        
        # Return success response
        return {"status": "success", "message": f"Event {event_id} deleted successfully"}
        
    except Exception as e:
        # Log the error details for debugging
        print(f"Error deleting calendar event {event_id}: {str(e)}")
        # Return error response with details
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete event: {str(e)}"
        )

# Endpoint to create a custom calendar event
@app.post("/calendar-event")
async def create_calendar_event(
    request: Request,
    credentials: dict = Depends(get_current_credentials)
):
    """Create a custom calendar event"""
    try:
        # Parse request body
        event_data = await request.json()
        
        # Validate required fields
        if not event_data.get('title') or not event_data.get('date'):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: title and date are required"
            )
        
        # Build the Google Calendar API client
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime
        
        # Create credentials object from the provided token
        creds = Credentials(
            token=credentials['token'],
            refresh_token=credentials.get('refresh_token'),
            scopes=credentials.get('granted_scopes')
        )
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Prepare event data
        title = event_data.get('title')
        description = event_data.get('description', '')
        date = event_data.get('date')  # Expected format: YYYY-MM-DD
        time = event_data.get('time')  # Expected format: HH:MM
        
        event = {
            'summary': title,
            'description': description,
            'colorId': '7',  # Use a different color for custom events (7 = gray)
        }
        
        # Set start and end times/dates
        if time:
            # If time is provided, create a time-specific event
            start_datetime = f"{date}T{time}:00"
            event['start'] = {
                'dateTime': start_datetime,
                'timeZone': 'UTC',
            }
            
            # End time is one hour after start time by default
            try:
                dt = datetime.fromisoformat(start_datetime)
                end_datetime = dt.replace(hour=dt.hour+1).isoformat()
                event['end'] = {
                    'dateTime': end_datetime,
                    'timeZone': 'UTC',
                }
            except Exception as e:
                print(f"Error calculating end time: {e}")
                # Fallback to one hour later
                event['end'] = {
                    'dateTime': f"{date}T{time.split(':')[0]}:59:59",
                    'timeZone': 'UTC',
                }
        else:
            # All-day event
            event['start'] = {
                'date': date,
            }
            event['end'] = {
                'date': date,
            }
        
        # Create the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        # Return the created event
        return {
            "id": created_event['id'],
            "title": created_event['summary'],
            "description": created_event.get('description', ''),
            "start": created_event['start'],
            "end": created_event['end'],
            "htmlLink": created_event.get('htmlLink', ''),
            "type": "custom",
            "status": "created"
        }
            
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions
        raise http_ex
    except Exception as e:
        # Log the error details for debugging
        print(f"Error creating calendar event: {str(e)}")
        # Return error response with details
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create event: {str(e)}"
        )

# Add the main function to run the app
if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
