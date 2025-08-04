// src/pages/LoginPage.tsx

import React, { useState } from "react";
import { loginUser } from "../api/user";
import { useNavigate } from "react-router-dom";
interface Props {
  onLoginSuccess: () => void;
}

const LoginPage: React.FC<Props> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const handleLogin = async () => {
    try {
      const data = await loginUser(username, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("isLoggedIn", "true");
      onLoginSuccess(); // ✅ App.tsx에게 "로그인 성공!" 알림
      navigate("/dashboard");
      
    } catch (error) {
      alert("로그인 실패");
    }
  };

  return (
    <div>
      <h2>로그인</h2>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="아이디"
      />
      <br />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="비밀번호"
      />
      <br />
      <button onClick={handleLogin}>로그인</button>
    </div>
  );
};

export default LoginPage;
