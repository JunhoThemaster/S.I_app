// src/App.tsx

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/SideBar';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/DashBoard';
import { useNavigate } from "react-router-dom"; 
const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 컴포넌트가 마운트될 때 localStorage 값 읽어옴
  useEffect(() => {
    const loggedIn = localStorage.getItem("isLoggedIn") === "true";
    setIsLoggedIn(loggedIn);
  }, []);

  return (
    <Router>
      {isLoggedIn && <Header />}
      <div style={{ display: 'flex', height: '100vh' }}>
        {isLoggedIn && <Sidebar />}
        <main style={{ flex: 1, padding: '2rem' }}>
          <Routes>
            <Route path="/login" element={<LoginPage onLoginSuccess={() => setIsLoggedIn(true)} />} />
            <Route
              path="/dashboard"
              element={isLoggedIn ? <Dashboard /> : <Navigate to="/login" replace />}
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


