import React from 'react';

function LoadingSpinner({ size = "medium", color = "blue", message = "Loading...", fullscreen = false }) {
  // Determine the size class
  const sizeClass = {
    small: "h-4 w-4",
    medium: "h-8 w-8",
    large: "h-12 w-12",
    xlarge: "h-16 w-16",
  }[size] || "h-8 w-8";

  // Determine the color class
  const colorClass = {
    blue: "text-blue-600",
    white: "text-white",
    gray: "text-gray-600",
    green: "text-green-600",
    purple: "text-purple-600",
  }[color] || "text-blue-600";

  // If fullscreen, render a full-screen overlay
  if (fullscreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center">
          <div className={`animate-spin ${sizeClass} ${colorClass}`}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          {message && <p className="mt-3 text-gray-700 font-medium">{message}</p>}
        </div>
      </div>
    );
  }

  // Otherwise, render an inline spinner
  return (
    <div className="flex items-center justify-center">
      <div className={`animate-spin ${sizeClass} ${colorClass}`}>
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      {message && <p className="ml-3 text-gray-700">{message}</p>}
    </div>
  );
}

export default LoadingSpinner;