import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def deduplicate_with_ai(assignments, extracted_deadlines):
    """
    Use AI to identify and remove duplicate deadlines between
    assignments from Classroom API and extracted deadlines from announcements
    
    Parameters:
    - assignments: List of assignments from Classroom API
    - extracted_deadlines: List of deadlines extracted from announcements
    
    Returns:
    - Dictionary with both assignments (unchanged) and unique extracted deadlines
    """
    if not extracted_deadlines:
        return {
            "assignments": assignments,
            "unique_deadlines": []
        }
        
    if not assignments:
        return {
            "assignments": assignments,
            "unique_deadlines": extracted_deadlines
        }
    
    # Setup Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Create a prompt for the AI
    prompt = """As an academic scheduling expert, your task is to identify duplicates between assignments and extracted deadlines.

I have two sets of data with DIFFERENT structures:
1. Assignments from Google Classroom API
2. Deadlines extracted from classroom announcements

I want to keep ALL assignments and ONLY remove extracted deadlines that duplicate assignments.
Assignments always take priority over extracted deadlines.

Consider the following when determining duplicates:
- If they refer to the same assignment/quiz/exam in the same course
- If they have similar titles and are for the same course
- If they have the same due date/time and are for the same course
- The type of activity (quiz, exam, assignment) - different types should not be considered duplicates even if on the same date

ASSIGNMENTS FROM CLASSROOM API:
"""
    
    # Add assignments data
    prompt += json.dumps(assignments, indent=2)
    
    prompt += "\n\nEXTRACTED DEADLINES FROM ANNOUNCEMENTS:\n"
    
    # Add extracted deadlines data
    prompt += json.dumps(extracted_deadlines, indent=2)
    
    prompt += """

Return ONLY a JSON array of indices (0-based) of extracted deadlines that should be KEPT because they are NOT duplicates of any assignments.
For example: [0, 2, 5] means keep the first, third, and sixth extracted deadlines.

Your response should ONLY contain the JSON array of indices to keep, nothing else.
"""
    
    try:
        # Call the AI
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract the JSON array from the response
        indices_to_keep = parse_ai_response(response_text)
        
        # Filter deadlines based on indices
        unique_deadlines = [
            extracted_deadlines[i] for i in indices_to_keep 
            if i < len(extracted_deadlines)
        ]
        
        print(f"AI deduplication: keeping {len(unique_deadlines)} out of {len(extracted_deadlines)} extracted deadlines")
        
        unique_deadlines= check_due(unique_deadlines)
        # Return both assignments (unchanged) and unique extracted deadlines
        return {
            "assignments": assignments,
            "unique_deadlines": unique_deadlines
        }
        
    except Exception as e:
        print(f"Error in AI deduplication: {e}")
        # Fall back to returning all items if AI fails
        print("Falling back to no deduplication due to AI error")
        return {
            "assignments": assignments,
            "unique_deadlines": extracted_deadlines
        }

def parse_ai_response(response_text):
    """Parse the AI response to extract the indices array"""
    try:
        # Clean up the response to extract just the JSON array
        # Remove any markdown code blocks
        if "```" in response_text:
            # Extract content between code blocks
            parts = response_text.split("```")
            if len(parts) >= 3:  # At least one complete code block
                response_text = parts[1]
            else:
                response_text = parts[-1]  # Take the last part if not properly formatted
                
            # If there's a language specifier like ```json, remove it
            if response_text.startswith("json"):
                response_text = response_text.replace("json", "", 1)
            response_text = response_text.strip()
        
        # Find array in text if it's not cleanly formatted
        if not (response_text.startswith("[") and response_text.endswith("]")):
            import re
            array_pattern = r'\[.*?\]'
            match = re.search(array_pattern, response_text)
            if match:
                response_text = match.group(0)
        
        # Parse the JSON array
        indices = json.loads(response_text)
        
        # Ensure it's a list of integers
        if not isinstance(indices, list):
            print(f"AI didn't return a list: {response_text}")
            return []
            
        # Convert all items to integers and filter out invalid indices
        return [int(i) for i in indices if isinstance(i, (int, float, str)) and str(i).isdigit()]

    except Exception as e:
        print(f"Error parsing AI response: {e}")
        print(f"Raw response: {response_text}")
        return []

def check_due(deadlines):
    """
    Filter deadlines to only keep those that are in the future or due today
    
    Parameters:
    - deadlines: List of deadline objects with 'dueDate' field
    
    Returns:
    - Filtered list of deadlines that are in the future or due today
    """
    from datetime import datetime, time
    
    # Get current date and time
    now = datetime.now()
    today = now.date()
    
    # Filter deadlines
    future_deadlines = []
    
    for deadline in deadlines:
        try:
            # Skip if no due date
            if not deadline.get('dueDate'):
                continue
                
            # Parse the due date
            due_date = datetime.fromisoformat(deadline['dueDate']).date()
            
            # If due date is in the future, keep it
            if due_date > today:
                future_deadlines.append(deadline)
                continue
                
            # If due date is today, check the time if available
            if due_date == today and deadline.get('dueTime'):
                try:
                    # Parse the due time
                    time_parts = deadline['dueTime'].split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Create a datetime for the deadline
                    deadline_datetime = datetime.combine(due_date, time(hour=hour, minute=minute))
                    
                    # If the deadline is today but still in the future (not passed), keep it
                    if deadline_datetime > now:
                        future_deadlines.append(deadline)
                except (ValueError, IndexError):
                    # If we can't parse the time, keep it anyway since it's due today
                    future_deadlines.append(deadline)
            elif due_date == today:
                # It's due today but no specific time, so keep it
                future_deadlines.append(deadline)
                
        except (ValueError, TypeError) as e:
            print(f"Error checking deadline date: {e}")
            # If we can't parse the date, don't include it
            continue
    
    print(f"Date filtering: keeping {len(future_deadlines)} out of {len(deadlines)} deadlines (future or due today)")
    return future_deadlines     