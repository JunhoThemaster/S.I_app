// src/api/user.ts
export const loginUser = async (username: string, password: string) => {
  const response = await fetch("http://localhost:8000/api/user/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("로그인 실패");
  }

  return response.json(); // { success: true }
};
