from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import pytz

def sync_assignments_to_calendar(assignments, credentials):
    """Sync assignments to Google Calendar"""
    
    # Create credentials object
    creds = Credentials(
        token=credentials['token'],
        refresh_token=credentials.get('refresh_token'),
        scopes=credentials.get('granted_scopes')
    )
    
    # Build calendar service
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'primary'  # Default to primary calendar
    
    # Track the results
    results = {
        "total": len(assignments),
        "success": 0,
        "failed": 0,
        "events": []
    }
    
    # Process each assignment
    for assignment in assignments:
        if not assignment.get("dueDate"):
            # Skip assignments with no due date
            results["failed"] += 1
            continue
            
        try:
            # Format due time string if available
            due_time_str = ""
            if assignment.get('dueTime'):
                # Convert 24-hour time format to more readable format
                try:
                    time_parts = assignment['dueTime'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    # Convert from UTC to IST (UTC+5:30)
                    ist_hour = hour + 5
                    ist_minute = minute + 30
                    
                    # Handle minute overflow
                    if ist_minute >= 60:
                        ist_hour += 1
                        ist_minute -= 60
                    
                    # Handle hour overflow
                    if ist_hour >= 24:
                        ist_hour -= 24

                    am_pm = "AM" if ist_hour < 12 else "PM"
                    ist_hour = ist_hour if ist_hour <= 12 else ist_hour - 12
                    ist_hour = 12 if ist_hour == 0 else ist_hour  # Convert 0 to 12 for 12 AM

                    due_time_str = f" (Due: {ist_hour}:{ist_minute:02d} {am_pm} IST)"
                except:
                    due_time_str = f" (Due: {assignment['dueTime']} UTC)"

            # Create event details with title and due time
            event = {
                'summary': f"{assignment.get('title')}{due_time_str} - {assignment.get('courseName')}",
                'description': assignment.get('description', '') or '',
                'start': {},
                'end': {}
            }
            
            # Set start and end times if we have them
            if assignment.get('dueTime'):
                # If we have a specific time
                start_datetime = f"{assignment['dueDate']}T{assignment['dueTime']}:00"
                event['start'] = {
                    'dateTime': start_datetime,
                    'timeZone': 'UTC',
                }
                
                # Calculate end time (1 hour after start) and format as string
                end_datetime = datetime.fromisoformat(start_datetime).replace(tzinfo=None) + timedelta(hours=1)
                end_datetime_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                
                event['end'] = {
                    'dateTime': end_datetime_str,
                    'timeZone': 'UTC',
                }
            else:
                # All-day event
                event['start'] = {
                    'date': assignment['dueDate'],
                }
                event['end'] = {
                    'date': assignment['dueDate'],
                }
            
            # Create the event
            created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            
            results["success"] += 1
            results["events"].append({
                "title": assignment.get('title'),
                "calendar_id": created_event['id']
            })
            
            # Store complete event data for frontend
            results.setdefault("created_events", []).append({
                "id": created_event['id'],
                "summary": created_event['summary'],
                "description": created_event.get('description', ''),
                "start": created_event['start'],
                "end": created_event['end'],
                "htmlLink": created_event.get('htmlLink', ''),
                "type": "assignment",
                "courseName": assignment.get('courseName', ''),
                "courseId": assignment.get('courseId', '')
            })
            
        except Exception as e:
            results["failed"] += 1
            print(f"Error creating event for {assignment.get('title')}: {str(e)}")
    
    return results


def sync_announcements_to_calendar(announcements, credentials):
    """Sync deadlines extracted from announcements to Google Calendar"""
    
    # Create credentials object
    creds = Credentials(
        token=credentials['token'],
        refresh_token=credentials.get('refresh_token'),
        scopes=credentials.get('granted_scopes')
    )
    
    # Build calendar service
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = 'primary'  # Default to primary calendar
    
    # Get the current date and time
    now = datetime.now()
    
    # Track the results
    results = {
        "total": len(announcements),
        "success": 0,
        "failed": 0,
        "skipped_past_events": 0,
        "events": []
    }
    
    # Process each extracted deadline from announcements
    for deadline in announcements:
        if not deadline.get("dueDate"):
            # Skip deadlines with no due date
            results["failed"] += 1
            continue
        
        try:
            # Check if the deadline is in the future
            due_date = datetime.fromisoformat(deadline["dueDate"]).date()
            
            # If we have a due time, use it for comparison
            if deadline.get('dueTime'):
                try:
                    time_parts = deadline['dueTime'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Create time object correctly
                    from datetime import time
                    time_obj = time(hour=hour, minute=minute)
                    due_datetime = datetime.combine(due_date, time_obj)
                    
                    # Skip if the deadline has already passed
                    if due_datetime < now:
                        results["skipped_past_events"] += 1
                        continue
                except (ValueError, IndexError) as e:
                    print(f"Error parsing time {deadline.get('dueTime')}: {e}")
                    # Continue with just the date if time parsing fails
            else:
                # For all-day events, skip if the date has passed
                if due_date < now.date():
                    results["skipped_past_events"] += 1
                    continue
                
            # Format due time string if available
            due_time_str = ""
            if deadline.get('dueTime'):
                # Convert 24-hour time format to more readable format
                try:
                    time_parts = deadline['dueTime'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    # Convert from UTC to IST (UTC+5:30)
                    ist_hour = hour + 5
                    ist_minute = minute + 30
                    
                    # Handle minute overflow
                    if ist_minute >= 60:
                        ist_hour += 1
                        ist_minute -= 60
                    
                    # Handle hour overflow
                    if ist_hour >= 24:
                        ist_hour -= 24

                    am_pm = "AM" if ist_hour < 12 else "PM"
                    ist_hour = ist_hour if ist_hour <= 12 else ist_hour - 12
                    ist_hour = 12 if ist_hour == 0 else ist_hour  # Convert 0 to 12 for 12 AM

                    due_time_str = f" (Due: {ist_hour}:{ist_minute:02d} {am_pm} IST)"
                except:
                    due_time_str = f" (Due: {deadline['dueTime']} UTC)"
            
            # Get the event type to include in the title
            event_type = deadline.get('eventType', 'Deadline')
            
            # Create event details with title and due time
            event = {
                'summary': f"{event_type}: {deadline.get('title')}{due_time_str} - {deadline.get('courseName')}",
                'description': deadline.get('description', '') or '',
                'start': {},
                'end': {},
                'colorId': '4'  # Use different color for announcement-derived events (4 = purple)
            }
            
            # Set start and end times if we have them
            if deadline.get('dueTime'):
                # If we have a specific time
                start_datetime = f"{deadline['dueDate']}T{deadline['dueTime']}:00"
                event['start'] = {
                    'dateTime': start_datetime,
                    'timeZone': 'UTC',
                }
                
                # Calculate end time (1 hour after start) and format as string
                end_datetime = datetime.fromisoformat(start_datetime).replace(tzinfo=None) + timedelta(hours=1)
                end_datetime_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                
                event['end'] = {
                    'dateTime': end_datetime_str,
                    'timeZone': 'UTC',
                }
            else:
                # All-day event
                event['start'] = {
                    'date': deadline['dueDate'],
                }
                event['end'] = {
                    'date': deadline['dueDate'],
                }
            
            # Create the event
            created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            
            results["success"] += 1
            results["events"].append({
                "title": deadline.get('title'),
                "calendar_id": created_event['id'],
                "source": "announcement"
            })
            
            # Store complete event data for frontend
            results.setdefault("created_events", []).append({
                "id": created_event['id'],
                "summary": created_event['summary'],
                "description": created_event.get('description', ''),
                "start": created_event['start'],
                "end": created_event['end'],
                "htmlLink": created_event.get('htmlLink', ''),
                "type": "announcement",
                "courseName": deadline.get('courseName', ''),
                "courseId": deadline.get('courseId', '')
            })
            
        except Exception as e:
            results["failed"] += 1
            print(f"Error creating event for announcement deadline '{deadline.get('title')}': {str(e)}")
    
    return results




def main():
    credentials = Credentials.from_authorized_user_file('path/to/credentials.json')
    classroom_service = build('classroom', 'v1', credentials=credentials)
    calendar_id = 'primary'  # or your specific calendar ID



