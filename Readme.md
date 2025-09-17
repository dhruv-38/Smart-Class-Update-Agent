# Smart Class Update Agent

## Developer Information
- **Name:** Dhruv Choudhary
- **Roll No.:**23110097
- **University:** Indian Institute of Technology Gandhinagar (IIT GN)
- **Department:** Chemical Engineering with Minor in Computer Science and Engineering
- **Internship:** "I'm beside you" Internship Application

## Project Overview
The Smart Class Update Agent is an AI-powered application designed to automate the process of tracking academic deadlines from Google Classroom and synchronizing them to Google Calendar. The system extracts deadlines from classroom assignments and announcements, then creates corresponding calendar events, helping students manage their academic responsibilities more efficiently.

## Features
- Google Classroom and Google Calendar integration
- Automatic synchronization of assignments to calendar events
- AI-powered extraction of deadlines from announcements
- Custom event creation for additional deadlines
- Deduplication to avoid redundant calendar events
- Clean and intuitive user interface

## Technologies Used
- **Frontend:** React, Tailwind CSS, Axios
- **Backend:** FastAPI, Google API Client Libraries
- **AI Integration:** Google Gemini API
- **Authentication:** Google OAuth 2.0

## Installation and Setup

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. Create OAuth credentials:
   - Place your `client_secret.json` file in the root of the backend directory
   - Get this file from the Google Cloud Console

5. Run the backend server:
   ```
   python src/main.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

## Usage
1. Log in with your Google account
2. Click "Sync Now" to retrieve your Google Classroom data
3. View synchronized events in the Calendar Events section
4. Add custom events as needed
5. Delete events you no longer need

## System Architecture
The system follows a client-server architecture with:
- **Frontend Client:** React-based web application
- **Backend Server:** FastAPI-based REST API
- **AI Services:** Google Gemini API for natural language understanding
- **External Services:** Google Classroom API and Google Calendar API

## Future Enhancements
- Mobile application support
- Smart notifications for upcoming deadlines
- Priority-based event sorting
- Analytics on workload distribution

## License
This project was developed as part of an internship application and is not licensed for commercial use.