# Google Classroom and Google Calendar Integration

This project integrates Google Classroom with Google Calendar to automatically fetch assignments and announcements from Google Classroom and sync them as events in Google Calendar.

## Project Structure

```
google-classroom-calendar-integration
├── src
│   ├── main.py               # Entry point of the application
│   ├── classroom
│   │   └── fetch_assignments.py  # Fetch assignments and announcements from Google Classroom
│   ├── calendar
│   │   └── sync_events.py    # Sync fetched assignments as events in Google Calendar
│   ├── utils
│   │   └── google_auth.py    # Handle Google API authentication
│   └── types
│       └── index.py          # Define data types and interfaces
├── requirements.txt           # List of dependencies
├── README.md                  # Project documentation
└── .env                       # Environment variables for sensitive information
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd google-classroom-calendar-integration
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up Google API credentials:**
   - Create a project in the Google Cloud Console.
   - Enable the Google Classroom API and Google Calendar API.
   - Create OAuth 2.0 credentials and download the JSON file.
   - Store the credentials in the `.env` file.

5. **Run the application:**
   ```
   uvicorn src.main:app --reload
   ```

## Usage Guidelines

- Access the FastAPI application at `http://127.0.0.1:8000`.
- Use the defined endpoints to fetch assignments and sync them to your Google Calendar.

## Overview of Functionality

- **Fetch Assignments:** The application retrieves assignments and announcements from Google Classroom using the Google Classroom API.
- **Sync Events:** The fetched assignments are converted into events and added to Google Calendar using the Google Calendar API.
- **Authentication:** The application securely manages OAuth2 credentials to access the Google APIs.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.