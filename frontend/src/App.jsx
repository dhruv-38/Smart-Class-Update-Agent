import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import axios from 'axios';
import LoginScreen from './components/LoginScreen';
import DashboardView from './components/DashboardView';
import Header from './components/Header';
import LoadingSpinner from './components/LoadingSpinner';

// Backend URL - adjust if your backend is on a different port
const BACKEND_URL = 'http://localhost:8000';

// Set up axios defaults
axios.defaults.baseURL = BACKEND_URL;
axios.defaults.withCredentials = true;  // Important for cookies/session

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status when component mounts
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Check if user is authenticated
  const checkAuthStatus = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/check-auth-status');
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error('Authentication check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle login button click
  const handleLogin = () => {
    // Redirect to backend login endpoint
    window.location.href = `${BACKEND_URL}/login`;
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await axios.get('/logout');
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    } catch (error) {
      console.error('Logout failed:', error);
      toast.error('Logout failed');
    }
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Loading application..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast container for notifications */}
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* Header */}
      <Header isAuthenticated={isAuthenticated} onLogout={handleLogout} />
      
      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {isAuthenticated ? (
          <DashboardView />
        ) : (
          <LoginScreen onLogin={handleLogin} />
        )}
      </main>
    </div>
  );
}

export default App;
