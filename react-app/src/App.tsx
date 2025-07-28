import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/SideBar';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/DashBoard';

const App: React.FC = () => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  
  return (
    <Router>
      {isLoggedIn && <Header />}
      <div style={{ display: 'flex', height: '100vh' }}>
        {isLoggedIn && <Sidebar />}
        <main style={{ flex: 1, padding: '2rem' }}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
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
