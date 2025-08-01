// src/api/user.ts

export const loginUser = async (username: string, password: string) => {
  const response = await fetch("/api/user/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("로그인 실패");
  }

  const data = await response.json(); // { access_token, token_type }
  
  // localStorage 또는 sessionStorage에 저장
  localStorage.setItem("token", data.access_token);

  return data;
};
