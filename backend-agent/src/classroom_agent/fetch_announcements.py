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

# Use the same cutoff date
cutoff = datetime(2025, 3, 23, tzinfo=timezone.utc)

def fetch_announcements(credentials):
    service = get_classroom_service(credentials)
    
    # Get the user's courses
    courses_result = service.courses().list().execute()
    courses = courses_result.get("courses", [])
    sem_courses = []
    
    # Filter courses created after cutoff date
    for course in courses:
        iso = course.get("creationTime")
        if not iso:
            continue
        created = datetime.fromisoformat(iso.replace("Z", "+00:00"))

        if created > cutoff:
            sem_courses.append(course)
    
    if not sem_courses:
        return {"message": "No courses found."}
    
    # For each course, get announcements
    all_announcements = []
    for course in sem_courses:
        course_id = course['id']
        course_name = course['name']
        
        # Try to get announcements
        try:
            announcements_result = service.courses().announcements().list(
                courseId=course_id
            ).execute()
            
            announcements = announcements_result.get('announcements', [])
            
            # Process each announcement - only keep text and course name
            for announcement in announcements:
                announcement_info = {
                    "text": announcement.get("text", ""),
                    "courseName": course_name,
                    "creationTime": announcement.get("creationTime", "")
                }
                
                # Add to the list of all announcements
                all_announcements.append(announcement_info)
                
        except Exception as e:
            # Some courses might not have announcements or you might not have permission
            print(f"Error getting announcements for course {course_name}: {str(e)}")
    
    return all_announcements