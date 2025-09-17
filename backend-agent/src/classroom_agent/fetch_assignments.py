from datetime import datetime, timezone
import google.oauth2.credentials
from googleapiclient.discovery import build

def get_classroom_service(credentials):
    # Convert the dictionary back to a Credentials object
    credentials = google.oauth2.credentials.Credentials(
        token=credentials['token'],
        refresh_token=credentials.get('refresh_token'),
        scopes=credentials.get('granted_scopes')
    )
    
    # Build the service with these credentials
    service = build('classroom', 'v1', credentials=credentials)
    return service

cutoff = datetime(2025, 3, 23, tzinfo=timezone.utc)
def fetch_classwork(credentials):
    service = get_classroom_service(credentials)
    
    # Get the user's courses
    courses_result = service.courses().list().execute()
    courses = courses_result.get("courses", [])
    sem_courses = []
    for course in courses:
        iso = course.get("creationTime")
        if not iso:
            continue
        created = datetime.fromisoformat(iso.replace("Z", "+00:00"))

        if created > cutoff:
            sem_courses.append(course)
    if not sem_courses:
        return {"message": "No courses found."}
    
    # Get current date and time with timezone awareness
    now = datetime.now().astimezone()
    
    # For each course, get assignments
    all_assignments = []
    for course in sem_courses:
        course_id = course['id']
        course_name = course['name']
        
        # Try to get course work
        try:
            coursework_result = service.courses().courseWork().list(courseId=course_id).execute()
            assignments = coursework_result.get('courseWork', [])
            
            # Add course name to each assignment for better context
            for assignment in assignments:
                # Extract relevant fields with safe defaults
                simplified = {
                    "title": assignment.get("title"),
                    "description": assignment.get("description"),
                    "courseName": course_name,
                    "workType": assignment.get("workType"),
                }

                # Extract due date & time if present
                due_date = assignment.get("dueDate")
                due_time = assignment.get("dueTime")
                
                # Skip if no due date
                if not due_date:
                    continue
                    
                # Format due date string
                due_date_str = f"{due_date['year']}-{due_date['month']:02d}-{due_date['day']:02d}"
                simplified["dueDate"] = due_date_str
                
                # Store original UTC time values for correct calendar sync
                if due_time:
                    utc_hours = due_time.get('hours', 0)
                    utc_minutes = due_time.get('minutes', 0)
                    # Format due time string in UTC
                    due_time_str = f"{utc_hours:02d}:{utc_minutes:02d}"
                    simplified["dueTime"] = due_time_str
                    simplified["dueTimeUTC"] = True  # Flag to indicate this is UTC time
                
                # Check if assignment is in the future or due today
                is_future_or_today = False
                
                # Create datetime objects for comparison
                if due_time:
                    # Create full datetime in UTC
                    utc_assignment_datetime = datetime(
                        due_date['year'], 
                        due_date['month'], 
                        due_date['day'],
                        due_time.get('hours', 0),
                        due_time.get('minutes', 0),
                        tzinfo=timezone.utc
                    )
                    
                    # Convert to local time for comparison
                    local_assignment_datetime = utc_assignment_datetime.astimezone()
                    
                    # Include assignments due today or in the future
                    is_future_or_today = local_assignment_datetime >= now
                    
                    # Add local time representation for display in frontend
                    local_time = local_assignment_datetime.strftime("%H:%M")
                    simplified["localDueTime"] = local_time
                    simplified["localTimezone"] = str(local_assignment_datetime.tzinfo)
                    
                else:
                    # If no time specified, compare dates and include today
                    assignment_date = datetime(
                        due_date['year'], 
                        due_date['month'], 
                        due_date['day']
                    ).date()
                    
                    is_future_or_today = assignment_date >= now.date()
                
                # Include assignments due today or in the future
                if is_future_or_today:
                    all_assignments.append(simplified)
                    
        except Exception as e:
            # Some courses might not have assignments or you might not have permission
            print(f"Error getting assignments for course {course_name}: {str(e)}")
    
    return all_assignments