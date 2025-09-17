import google.generativeai as genai
import os
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API with your API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Keywords to use for filtering relevant announcements
RELEVANT_KEYWORDS = [
    "assignment", "quiz", "exam", "test", "homework", "report", "submission", "project", 
    "deadline", "due", "due by", "submit", "due date", "turn in", "presentation",
    "tomorrow", "next week", "friday", "monday", "tuesday", "wednesday", "thursday",
    "saturday", "sunday", "lab report", "midterm", "final"
]

def setup_gemini_model():
    """Setup and return the Gemini model"""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    return model

def filter_relevant_announcements(announcements):
    """Filter announcements to only include those potentially containing deadline information"""
    relevant = []
    for announcement in announcements:
        text = announcement.get("text", "").lower()
        # Skip announcements with no text
        if not text:
            continue
            
        # Check if any relevant keyword is in the text
        if any(keyword in text for keyword in RELEVANT_KEYWORDS):
            relevant.append(announcement)
    
    print(f"Filtered {len(relevant)}/{len(announcements)} announcements as potentially relevant")
    return relevant

def extract_deadlines(model, announcements):
    """Extract deadline information from a batch of announcements in a single API call"""
    
    # Create the prompt with your specified format
    batch_prompt = """You are an expert AI assistant specializing in academic scheduling. Your task is to analyze classroom announcements and extract only actionable deadlines that can be scheduled.

TASK: For each announcement, determine if it contains a schedulable event like an assignment, quiz, exam, test, homework, report, submission or project submission.
"""
    
    # Add each announcement to the prompt
    for i, announcement in enumerate(announcements, 1):
        batch_prompt += f"\nANNOUNCEMENT {i}:\n"
        batch_prompt += f"Course: \"{announcement['courseName']}\"\n"
        batch_prompt += f"Created at: {announcement.get('creationTime', 'unknown time')}\n"
        batch_prompt += f"Text: \"{announcement['text']}\"\n"
    
    batch_prompt += """
Carefully extract any deadline information(if any) and return a JSON array where each item corresponds to an announcement:
[
  {
    "announcementNumber": 1,
    "title": "Brief title for this event based on the content",
    "dueDate": "YYYY-MM-DD format if ANY specific date is mentioned, null if no date found",
    "dueTime": "HH:MM in 24-hour format if a specific time is mentioned, null otherwise",
    "description": "Brief description of the deadline or event",
    "eventType": "Assignment, Quiz, Exam, Project, or Other",
    "confidence": "A number between 0 and 1 indicating confidence in the extraction"
  },
  ... and so on for each announcement
]

IMPORTANT INSTRUCTIONS:
1. Pay special attention to phrases like "due by", "submit by", "deadline", "due date", etc.
2. Look for relative dates like "next Friday", "tomorrow", "this weekend" and convert them to actual dates (If it is relevant to quiz or test, class, submission, etc.)
3. If dates are mentioned without a year, assume the current year
4. MOST MOST IMPORTANTLY If there is similar information for multiple announcements, select only the latest announcement.
5. There May be an announcement which contains irrelevant to this.
6. Please Don't give this type of announcement "Please bring pencil, ruler and other stationary to class tomorrow"
7. There can be announcements which explains the same thing but in different ways like of same course "first quiz is on 18th August (Monday) and will be based on games" and topic= quiz 1"The quiz based on CSPs will be held on 7PM this Friday". Consider these as same and make only one entry.

Only return valid JSON array without explanations.
"""
    
    try:
        print(f"Generating content with Gemini for batch of {len(announcements)} announcements...")
        response = model.generate_content(batch_prompt)
        print(f"Received response from Gemini")
        response_text = response.text
        
        # Print the first 100 chars of the response for debugging
        print(f"Response starts with: {response_text[:100]}...")
        
        # Clean the response - extract JSON from possible markdown formatting
        json_text = extract_json_from_response(response_text)
        
        try:
            # Parse JSON array
            deadline_infos = json.loads(json_text)
            
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing failed: {json_err}")
            print("Attempting fallback parsing approach...")
            
            # Fallback: try to construct a JSON array manually
            deadline_infos = fallback_json_parse(response_text)
        
        # Process the results and add course info
        processed_deadlines = []
        
        print(f"Raw AI response contains information about {len(deadline_infos)} announcements")
        
        for deadline_info in deadline_infos:
            # Get announcement number (adjusting for 0-based indexing)
            announcement_num = deadline_info.get("announcementNumber", 0)
            
            # Ensure the index is valid
            if 1 <= announcement_num <= len(announcements):
                # Get the corresponding announcement
                announcement_index = announcement_num - 1
                announcement = announcements[announcement_index]
                
                # Only add entries that have a due date and reasonable confidence
                due_date = deadline_info.get("dueDate")
                confidence = float(deadline_info.get("confidence", 0))
                
                if due_date and due_date != "null" and confidence >= 0.5:
                    # Add course name and source to the response
                    deadline_info["courseName"] = announcement["courseName"]
                    deadline_info["source"] = "announcement"
                    processed_deadlines.append(deadline_info)
                    print(f"Found deadline: {deadline_info.get('title')} due on {due_date}")
                else:
                    reason = "low confidence" if confidence < 0.5 else "no due date"
                    print(f"Skipped announcement {announcement_num} - {reason}")
        
        print(f"Processed {len(deadline_infos)} items, found {len(processed_deadlines)} valid deadlines")
        return processed_deadlines
        
    except Exception as e:
        print(f"Error processing batch with Gemini: {e}")
        return []

def extract_json_from_response(response_text):
    """Extract JSON from the model response, handling various formats"""
    # Check for markdown code blocks
    if "```json" in response_text:
        json_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_text = response_text.split("```")[1].strip()
    else:
        # Try to find JSON array in the text
        start_idx = response_text.find("[")
        end_idx = response_text.rfind("]") + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
        else:
            json_text = response_text
    
    return json_text

def fallback_json_parse(response_text):
    """Fallback method for extracting JSON objects when standard parsing fails"""
    # Try to find all JSON objects
    json_objects = re.findall(r'\{[^{}]*\}', response_text)
    
    deadline_infos = []
    if json_objects:
        # Attempt to parse each object individually
        for obj_str in json_objects:
            try:
                obj = json.loads(obj_str)
                deadline_infos.append(obj)
            except:
                pass
        
        print(f"Fallback parsing found {len(deadline_infos)} JSON objects")
    else:
        print("Fallback parsing failed. No valid JSON objects found.")
    
    return deadline_infos

def extract_deadlines_from_announcements(announcements):
    """Process all announcements and extract deadlines using Gemini API in a single call"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    
    print(f"Starting deadline extraction for {len(announcements)} announcements")
    
    if len(announcements) == 0:
        print("No announcements to process")
        return []
    
    # Step 1: Filter announcements to find relevant ones
    relevant_announcements = filter_relevant_announcements(announcements)
    
    if not relevant_announcements:
        print("No relevant announcements found after filtering")
        return []
    
    # Step 2: Process all filtered announcements in a single API call
    model = setup_gemini_model()
    
    print(f"Processing all {len(relevant_announcements)} filtered announcements in a single API call")
    
    # Process entire filtered set in a single API call
    all_deadlines = extract_deadlines(model, relevant_announcements)
    
    print(f"Extraction complete. Found a total of {len(all_deadlines)} deadlines from {len(announcements)} announcements")
    return all_deadlines

# For testing
if __name__ == "__main__":
    # Sample announcements for testing
    test_announcements = [
        {
            "text": "Hi everyone, The quiz on Unit 3 will be held next Friday at 2:30 PM. Please make sure to review all materials.",
            "courseName": "Introduction to Computer Science",
            "creationTime": "2023-09-10T14:30:00Z"
        },
        {
            "text": "Please submit your final project reports by November 15th, 2023. The submission link is now available on the course page.",
            "courseName": "Software Engineering",
            "creationTime": "2023-11-01T09:15:00Z"
        },
        {
            "text": "Reminder: Homework 3 is due tomorrow at 11:59 PM. Late submissions will not be accepted.",
            "courseName": "Data Structures",
            "creationTime": "2023-10-15T08:00:00Z"
        },
        {
            "text": "Just a reminder that I'll be available for office hours every Tuesday from 3-5 PM.",
            "courseName": "Database Systems",
            "creationTime": "2023-09-20T10:00:00Z"
        }
    ]

    extracted_deadlines = extract_deadlines_from_announcements(test_announcements)
    print(json.dumps(extracted_deadlines, indent=2))