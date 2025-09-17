import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import LoadingSpinner from './LoadingSpinner';
import StatsCard from './StatsCard';
import SyncProgressBar from './SyncProgressBar';
import CalendarEventsList from './CalendarEventsList';

// Define backend URL (adjust if your backend runs on a different port)
const BACKEND_URL = 'http://localhost:8000';

function DashboardView() {
  // State for sync data
  const [syncData, setSyncData] = useState({
    isLoading: false,
    progress: 0,
    step: 0,
    currentAction: '',
    error: null,
  });

  // State for calendar events
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  
  // Stats for display
  const [stats, setStats] = useState({
    assignments: 0,
    announcements: 0,
    totalEvents: 0
  });

  // Fetch calendar events when component mounts
  useEffect(() => {
    fetchCalendarEvents();
  }, []);

  // Fetch calendar events from backend
  const fetchCalendarEvents = async () => {
    try {
      setEventsLoading(true);
      const response = await axios.get(`${BACKEND_URL}/list-calendar-events`);
      
      if (response.data && response.data.calendar_events) {
        setCalendarEvents(response.data.calendar_events);
        
        // Update stats
        if (response.data.stats) {
          setStats({
            assignments: response.data.stats.assignments || 0,
            announcements: response.data.stats.announcements || 0,
            totalEvents: response.data.stats.total_calendar_events || 0
          });
        }
      }
    } catch (error) {
      console.error('Error fetching calendar events:', error);
      toast.error('Failed to fetch calendar events');
    } finally {
      setEventsLoading(false);
    }
  };

  // Handle Sync Now button click
  const handleSync = async () => {
    try {
      setSyncData({
        isLoading: true,
        progress: 0,
        step: 1,
        currentAction: 'Starting sync process...',
        error: null
      });

      // First request to start the sync
      const response = await axios.get(`${BACKEND_URL}/sync-all`);
      
      setSyncData(prev => ({
        ...prev,
        progress: 100,
        step: 5,
        currentAction: 'Sync complete!',
      }));

      // Update calendar events with the new data
      if (response.data && response.data.calendar_events) {
        setCalendarEvents(response.data.calendar_events);
        setLastSyncTime(new Date());
        
        // Update stats
        if (response.data.sync_stats) {
          setStats({
            assignments: response.data.sync_stats.assignments_count || 0,
            announcements: response.data.sync_stats.announcements_count || 0,
            totalEvents: response.data.sync_stats.total_calendar_events || 0
          });
        }
        
        toast.success('Successfully synchronized with Google Calendar');
      }
    } catch (error) {
      console.error('Error during sync:', error);
      setSyncData(prev => ({
        ...prev,
        error: error.response?.data?.detail || 'Failed to sync with Google Classroom and Calendar'
      }));
      toast.error('Sync failed. Please try again.');
    } finally {
      setSyncData(prev => ({ ...prev, isLoading: false }));
    }
  };

  // Handle calendar event deletion
  const handleDeleteEvent = async (eventId) => {
    try {
      // Show loading indicator
      toast.info('Deleting event...', { autoClose: 2000 });
      
      // Make the API call
      await axios.delete(`${BACKEND_URL}/calendar-event/${eventId}`);
      
      // Remove the deleted event from state
      setCalendarEvents(prev => prev.filter(event => event.id !== eventId));
      
      // Update stats
      setStats(prev => ({
        ...prev,
        totalEvents: prev.totalEvents - 1
      }));
      
      // Show success message
      toast.success('Event deleted successfully');
    } catch (error) {
      console.error('Error deleting event:', error);
      
      // Show a more detailed error message
      const errorMessage = error.response?.data?.detail || 'Failed to delete event';
      toast.error(`Error: ${errorMessage}`);
    }
  };

  // Handle adding a custom event
  const handleAddEvent = async (eventData) => {
    try {
      // Show loading indicator
      toast.info('Adding event...', { autoClose: 2000 });
      
      console.log('Sending event data:', eventData); // Debug log
      
      const response = await axios.post(`${BACKEND_URL}/calendar-event`, eventData);
      
      if (response.data && response.data.id) {
        // Add the new event to state
        setCalendarEvents(prev => [...prev, response.data]);
        
        // Update stats
        setStats(prev => ({
          ...prev,
          totalEvents: prev.totalEvents + 1
        }));
        
        toast.success('Event added successfully');
      }
    } catch (error) {
      console.error('Error adding event:', error);
      
      // Show a more detailed error message
      const errorMessage = error.response?.data?.detail || 'Failed to add event';
      toast.error(`Error: ${errorMessage}`);
    }
  };

  // Format the last sync time for display
  const getLastSyncTimeDisplay = () => {
    if (!lastSyncTime) return 'Never';
    return lastSyncTime.toLocaleString();
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatsCard 
          title="Assignments" 
          value={stats.assignments} 
          icon={
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"></path>
            </svg>
          } 
          color="bg-blue-500" 
        />
        <StatsCard 
          title="Announcements" 
          value={stats.announcements} 
          icon={
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 9h-2V5h2v6zm0 4h-2v-2h2v2z"></path>
            </svg>
          } 
          color="bg-purple-500" 
        />
        <StatsCard 
          title="Calendar Events" 
          value={stats.totalEvents} 
          icon={
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2zm-7 5h5v5h-5v-5z"></path>
            </svg>
          } 
          color="bg-green-500" 
        />
      </div>

      {/* Sync Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Sync Classroom & Calendar</h2>
        
        <div className="mb-4 text-sm text-gray-500">
          <p>Last synchronized: {getLastSyncTimeDisplay()}</p>
        </div>
        
        {syncData.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <p>{syncData.error}</p>
          </div>
        )}
        
        {syncData.isLoading ? (
          <div className="mb-6">
            <SyncProgressBar 
              step={syncData.step} 
              currentAction={syncData.currentAction} 
            />
          </div>
        ) : (
          <button
            onClick={handleSync}
            className="w-full md:w-auto px-6 py-3 bg-blue-600 text-white font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            disabled={syncData.isLoading}
          >
            Sync Now
          </button>
        )}
        
        <div className="mt-4 text-sm text-gray-500">
          <p>This will fetch your assignments and announcements from Google Classroom and sync them to your Calendar.</p>
        </div>
      </div>

      {/* Calendar Events Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Calendar Events</h2>
        
        {eventsLoading ? (
          <div className="flex justify-center items-center p-12">
            <LoadingSpinner message="Loading calendar events..." />
          </div>
        ) : (
          <CalendarEventsList
            events={calendarEvents}
            onDeleteEvent={handleDeleteEvent}
            onAddEvent={handleAddEvent}
          />
        )}
      </div>
    </div>
  );
}

export default DashboardView;