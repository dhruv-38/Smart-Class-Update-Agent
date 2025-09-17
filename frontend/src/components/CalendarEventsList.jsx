import React, { useState } from 'react';

function CalendarEventsList({ events, onDeleteEvent, onAddEvent }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    date: '',
    time: '',
    type: 'custom',
  });
  const [filter, setFilter] = useState('all');

  // Filter events based on the selected filter
  const filteredEvents = events.filter(event => {
    if (filter === 'all') return true;
    return event.type === filter;
  });

  // Format event date for display
  const formatEventDate = (event) => {
    if (!event.start) return 'No date';
    
    if (event.start.date) {
      // All-day event
      return new Date(event.start.date).toLocaleDateString();
    } else if (event.start.dateTime) {
      // Time-specific event - this is stored in UTC by the backend
      const date = new Date(event.start.dateTime);
      
      // This will automatically convert the UTC time to local time
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }
    
    return 'Invalid date';
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewEvent(prev => ({ ...prev, [name]: value }));
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate the date format (should be YYYY-MM-DD)
    if (!newEvent.date.match(/^\d{4}-\d{2}-\d{2}$/)) {
      alert("Please enter a valid date in YYYY-MM-DD format");
      return;
    }
    
    // Validate the time format if provided (should be HH:MM)
    if (newEvent.time && !newEvent.time.match(/^\d{2}:\d{2}$/)) {
      alert("Please enter a valid time in HH:MM format");
      return;
    }
    
    // Create the event object in the format expected by the backend
    const eventData = {
      title: newEvent.title,
      description: newEvent.description || "",
      date: newEvent.date,
      // Fix: Convert time to UTC time string (add time zone offset adjustment)
      time: newEvent.time ? adjustTimeForBackend(newEvent.time) : null,
      type: 'custom'
    };
    
    // Debug message to show what's being sent
    console.log("Sending event data to backend:", eventData);
    
    onAddEvent(eventData);
    
    // Reset form
    setNewEvent({
      title: '',
      description: '',
      date: '',
      time: '',
      type: 'custom',
    });
    setShowAddForm(false);
  };

  // Function to adjust time for backend (compensate for timezone offset)
  const adjustTimeForBackend = (timeString) => {
    // Parse the input time
    const [hours, minutes] = timeString.split(':').map(Number);
    
    // Get timezone offset in minutes
    const timezoneOffsetInMinutes = new Date().getTimezoneOffset();
    
    console.log(`Current timezone offset: ${timezoneOffsetInMinutes} minutes`);
    
    // For IST (UTC+5:30), getTimezoneOffset() returns -330 minutes
    
    // Extract the hour part and minute part of the offset separately
    const offsetHours = Math.floor(Math.abs(timezoneOffsetInMinutes) / 60);
    const offsetMinutes = Math.abs(timezoneOffsetInMinutes) % 60;
    
    // Determine whether to add or subtract based on the sign of the offset
    // For negative offset (like IST), we need to subtract hours to get UTC
    let utcHours, utcMinutes;
    
    if (timezoneOffsetInMinutes <= 0) {
      // Timezone is ahead of UTC (like IST)
      // Subtract hours and minutes to get UTC time
      utcHours = hours - offsetHours;
      utcMinutes = minutes - offsetMinutes;
    } else {
      // Timezone is behind UTC
      // Add hours and minutes to get UTC time
      utcHours = hours + offsetHours;
      utcMinutes = minutes + offsetMinutes;
    }
    
    // Handle minute underflow
    if (utcMinutes < 0) {
      utcHours--;
      utcMinutes += 60;
    }
    
    // Handle minute overflow
    if (utcMinutes >= 60) {
      utcHours++;
      utcMinutes -= 60;
    }
    
    // Handle hour underflow/overflow
    utcHours = ((utcHours % 24) + 24) % 24;
    
    // Format as HH:MM
    const formattedUtcTime = `${String(utcHours).padStart(2, '0')}:${String(utcMinutes).padStart(2, '0')}`;
    
    console.log(`Original time (local): ${timeString}, Adjusted time (UTC for backend): ${formattedUtcTime}`);
    
    return formattedUtcTime;
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
        <div className="flex items-center mb-4 sm:mb-0">
          <label htmlFor="filter" className="mr-2 text-sm text-gray-600">
            Filter:
          </label>
          <select
            id="filter"
            className="form-select rounded border-gray-300"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Events</option>
            <option value="assignment">Assignments</option>
            <option value="announcement">Announcements</option>
            <option value="custom">Custom Events</option>
          </select>
        </div>
        
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {showAddForm ? 'Cancel' : '+ Add Event'}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Event</h3>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="col-span-2">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Event Title *
                </label>
                <input
                  type="text"
                  name="title"
                  id="title"
                  required
                  className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  value={newEvent.title}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="col-span-2">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  name="description"
                  id="description"
                  rows="3"
                  className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  value={newEvent.description}
                  onChange={handleInputChange}
                />
              </div>
              
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-700">
                  Date *
                </label>
                <input
                  type="date"
                  name="date"
                  id="date"
                  required
                  className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  value={newEvent.date}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-xs text-gray-500">Format: YYYY-MM-DD</p>
              </div>
              
              <div>
                <label htmlFor="time" className="block text-sm font-medium text-gray-700">
                  Time (optional)
                </label>
                <input
                  type="time"
                  name="time"
                  id="time"
                  className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  value={newEvent.time}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-xs text-gray-500">Format: HH:MM (24-hour)</p>
                {/* Add a notice about time zones */}
                <p className="mt-1 text-xs text-orange-500">
                  The time you enter will be used directly. No time zone conversion needed.
                </p>
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={() => setShowAddForm(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Add Event
              </button>
            </div>
          </form>
        </div>
      )}

      {filteredEvents.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date & Time
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEvents.map((event) => (
                <tr key={event.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {event.title}
                    </div>
                    {event.courseName && (
                      <div className="text-sm text-gray-500">
                        {event.courseName}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatEventDate(event)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      event.type === 'assignment' ? 'bg-blue-100 text-blue-800' : 
                      event.type === 'announcement' ? 'bg-purple-100 text-purple-800' : 
                      'bg-green-100 text-green-800'
                    }`}>
                      {event.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <a 
                        href={event.htmlLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </a>
                      <button 
                        onClick={() => onDeleteEvent(event.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-10 text-center">
          <p className="text-gray-500">
            {events.length > 0 
              ? 'No events match your current filter.'
              : 'No calendar events found. Sync with Google Classroom to create events.'}
          </p>
        </div>
      )}
    </div>
  );
}

export default CalendarEventsList;