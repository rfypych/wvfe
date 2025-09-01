import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ScanDetailPage from './pages/ScanDetailPage';
import apiClient from './api';
import './App.css';


function HomePage({ isAuthenticated, onLogout }) {
  return (
    <div className="App-header">
      <h1>Welcome to WVFE</h1>
      <nav>
        {isAuthenticated ? (
          <button onClick={onLogout}>Logout</button>
        ) : (
          <>
            <Link to="/login" style={{color: 'white', marginRight: '10px'}}>Login</Link>
            <Link to="/register" style={{color: 'white'}}>Register</Link>
          </>
        )}
      </nav>
    </div>
  );
}

// A wrapper for LoginPage to handle navigation
function LoginWrapper({ onLoginSuccess }) {
    const navigate = useNavigate();
    const handleLogin = () => {
        onLoginSuccess();
        navigate('/dashboard');
    };
    return <LoginPage onLoginSuccess={handleLogin} />;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is already logged in on component mount
  useEffect(() => {
    const checkAuth = async () => {
        try {
            // A simple way to check auth is to hit a protected endpoint
            await apiClient.get('/api/dashboard');
            setIsAuthenticated(true);
        } catch (error) {
            setIsAuthenticated(false);
        } finally {
            setIsLoading(false);
        }
    };
    checkAuth();
  }, []);

  const handleLogout = async () => {
    await apiClient.get('/api/auth/logout');
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage isAuthenticated={isAuthenticated} onLogout={handleLogout} />} />
          <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginWrapper onLoginSuccess={() => setIsAuthenticated(true)} />} />
          <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <RegisterPage />} />
          <Route path="/dashboard" element={isAuthenticated ? <DashboardPage onLogout={handleLogout} /> : <Navigate to="/login" />} />
          <Route path="/scans/:id" element={isAuthenticated ? <ScanDetailPage /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
