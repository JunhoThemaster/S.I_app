// src/App.tsx (수정된 완전한 버전)

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/SideBar';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/DashBoard';
import InterviewSimulator from './pages/InterviewSimulator';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(true);

  return (
    <Router>
      {isLoggedIn && <Header />}
      <div style={{ display: 'flex', height: '100vh' }}>
        {isLoggedIn && <Sidebar />}
        <main style={{ flex: 1, padding: isLoggedIn ? '2rem' : '0' }}>
          <Routes>
            <Route 
              path="/login" 
              element={<LoginPage onLoginSuccess={() => setIsLoggedIn(true)} />} 
            />
            <Route
              path="/dashboard"
              element={isLoggedIn ? <Dashboard /> : <Navigate to="/login" replace />}
            />
            <Route
              path="/interview"
              element={isLoggedIn ? <InterviewSimulator /> : <Navigate to="/login" replace />}
            />
            <Route
              path="/"
              element={<Navigate to={isLoggedIn ? '/dashboard' : '/login'} replace />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;