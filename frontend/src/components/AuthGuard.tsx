"use client";

import { useState, useEffect } from "react";
import { UserIcon, LogIn } from "lucide-react";

export interface AuthState {
  token: string;
  userId: string;
  username: string;
}

interface AuthGuardProps {
  onAuth: (auth: AuthState) => void;
}

export function AuthGuard({ onAuth }: AuthGuardProps) {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim() }),
      });
      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();
      localStorage.setItem("pavo_token", data.token);
      localStorage.setItem("pavo_user_id", data.user_id);
      localStorage.setItem("pavo_username", username.trim());
      onAuth({ token: data.token, userId: data.user_id, username: username.trim() });
    } catch (err: any) {
      setError(err.message || "Failed to login");
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-sm w-full mx-4">
        <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mx-auto mb-4">
          <UserIcon className="w-6 h-6 text-blue-600" />
        </div>
        <h1 className="text-xl font-semibold text-center text-gray-900">Pavo AI Agent</h1>
        <p className="text-sm text-center text-gray-500 mt-1">Enter your username to start</p>
        <div className="mt-6">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            placeholder="Your username..."
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
          <button
            onClick={handleLogin}
            disabled={loading || !username.trim()}
            className="w-full mt-3 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? "Connecting..." : (
              <><LogIn className="w-4 h-4" /> Start</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
