"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";

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
      const res = await fetch(`${API_BASE}/auth/login`, {
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
    <div className="min-h-screen bg-cream flex">
      {/* Left — branding */}
      <div className="hidden lg:flex flex-1 items-center justify-center bg-gradient-to-br from-pavo-50 to-pavo-100">
        <div className="max-w-md text-center px-8">
          <div className="w-16 h-16 bg-warm rounded-2xl flex items-center justify-center mx-auto mb-6">
            <span className="text-white text-2xl font-bold">P</span>
          </div>
          <h1 className="text-4xl font-bold text-warm leading-tight">
            Free Your Creativity,
            <br />
            <span className="text-pavo-500">Manifest Ideas Instantly</span>
          </h1>
          <p className="text-pavo-400 mt-4 text-sm leading-relaxed">
            AI-powered video storyboard generation. Describe your vision, and let
            our agents craft characters, scenes, and storyboards in seconds.
          </p>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8 text-center">
            <div className="w-12 h-12 bg-warm rounded-xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-lg font-bold">P</span>
            </div>
            <h1 className="text-2xl font-bold text-warm">Pavo</h1>
          </div>

          <h2 className="text-xl font-semibold text-warm">Welcome to Pavo</h2>
          <p className="text-sm text-pavo-400 mt-1">Enter your details to sign in</p>

          <div className="mt-8 space-y-4">
            <div>
              <label className="text-xs font-medium text-warm/60 uppercase tracking-wider mb-1.5 block">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                placeholder="Your username..."
                className="input-base"
                disabled={loading}
                autoFocus
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>
            )}

            <button
              onClick={handleLogin}
              disabled={loading || !username.trim()}
              className="btn-primary w-full"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Connecting...
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
