'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { Sparkles } from 'lucide-react';
import { useState } from 'react';
import { AuthModal } from '@/common/AuthModal';
import { useRouter } from 'next/navigation';

export function Navbar() {
  const { isAuthenticated, username, logout } = useAuthStore();
  const [showAuth, setShowAuth] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-white font-semibold">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Pavo
          </Link>

          <div className="hidden md:flex items-center gap-6 text-sm">
            <Link href="/gallery" className="text-gray-400 hover:text-white transition-colors">Gallery</Link>
            <Link href="/studio" className="text-gray-400 hover:text-white transition-colors">Studio</Link>
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors">Dashboard</Link>
                <Link href="/projects" className="text-gray-400 hover:text-white transition-colors">Projects</Link>
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 bg-indigo-500 rounded-full flex items-center justify-center text-xs font-medium text-white">
                    {(username || 'U').charAt(0).toUpperCase()}
                  </div>
                  <button onClick={() => { logout(); router.push('/'); }} className="text-xs text-gray-500 hover:text-gray-300">
                    Exit
                  </button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowAuth(true)} className="px-4 py-1.5 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
                Sign In
              </button>
            )}
          </div>

          <button className="md:hidden text-gray-400" onClick={() => setMobileOpen(!mobileOpen)}>
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-white/10 bg-black/90 px-4 py-3 space-y-2 text-sm">
            <Link href="/gallery" className="block text-gray-400 py-1" onClick={() => setMobileOpen(false)}>Gallery</Link>
            <Link href="/studio" className="block text-gray-400 py-1" onClick={() => setMobileOpen(false)}>Studio</Link>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="block text-gray-400 py-1" onClick={() => setMobileOpen(false)}>Dashboard</Link>
                <Link href="/projects" className="block text-gray-400 py-1" onClick={() => setMobileOpen(false)}>Projects</Link>
                <button onClick={() => { logout(); router.push('/'); }} className="block text-gray-500 py-1">Exit</button>
              </>
            ) : (
              <button onClick={() => { setShowAuth(true); setMobileOpen(false); }} className="block text-white py-1">Sign In</button>
            )}
          </div>
        )}
      </nav>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </>
  );
}
