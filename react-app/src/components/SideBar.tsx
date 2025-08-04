import React from 'react';
import { NavLink } from 'react-router-dom';
import '../Sidebar.css'; // CSS 분리 추천

const SideBar: React.FC = () => {
  return (
    <aside className="sidebar">
      <nav>
        <ul>
          <li>
            <NavLink
              to="/"
              end
              className={({ isActive }: { isActive: boolean }) => (isActive ? 'active' : '')}
            >
              🏠 홈
            </NavLink>
          </li>
           <li>
            <NavLink
              to="/records"
              className={({ isActive }: { isActive: boolean }) => (isActive ? 'active' : '')}
            >
              🗂 나의 기록
            </NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default SideBar;
