import React from 'react';

function SyncProgressBar({ step, currentAction }) {
  // Define the steps in the sync process
  const steps = [
    { id: 1, name: 'Fetching Assignments', description: 'Getting assignments from Google Classroom' },
    { id: 2, name: 'Fetching Announcements', description: 'Getting announcements from Google Classroom' },
    { id: 3, name: 'Syncing Assignments', description: 'Creating calendar events for assignments' },
    { id: 4, name: 'Syncing Announcements', description: 'Creating calendar events for announcements' },
    { id: 5, name: 'Complete', description: 'Sync process completed successfully' },
  ];

  return (
    <div className="py-4">
      <div className="mb-4">
        <div className="text-sm font-medium text-gray-700 mb-1">
          {currentAction || `Step ${step} of ${steps.length}`}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-in-out" 
            style={{ width: `${(step / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>
      
      <ol className="space-y-4 md:flex md:space-y-0 md:space-x-8">
        {steps.map((syncStep) => (
          <li key={syncStep.id} className="md:flex-1">
            <div className="flex flex-col py-2 pl-4 border-l-4 md:pl-0 md:pt-4 md:pb-0 md:border-l-0 md:border-t-4 border-gray-200">
              <span className={`text-xs font-semibold tracking-wide uppercase ${
                step >= syncStep.id ? 'text-blue-600' : 'text-gray-500'
              }`}>
                Step {syncStep.id}
              </span>
              <span className="text-sm font-medium">
                {syncStep.name}
              </span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default SyncProgressBar;