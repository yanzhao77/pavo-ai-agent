'use client';

import { useState, useEffect } from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { Hero } from '@/components/landing/Hero';
import { FeatureSection } from '@/components/landing/FeatureSection';
import { AuthModal } from '@/common/AuthModal';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { useRouter } from 'next/navigation';

export default function Home() {
  const { isAuthenticated, checkAuth } = useAuthStore();
  const { createProject } = useProjectStore();
  const router = useRouter();
  const [showAuth, setShowAuth] = useState(false);

  // Init auth from localStorage
  useEffect(() => { checkAuth(); }, []);

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />
      <Hero />
      <FeatureSection />

      {/* Workflow Preview */}
      <section className="py-24 px-4 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-8">AI Creation Pipeline</h2>
          <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
            {[
              { icon: '🧠', name: '故事导演' },
              { icon: '🎭', name: '角色设计师' },
              { icon: '🌆', name: '场景构建师' },
              { icon: '🎨', name: '道具师' },
              { icon: '🎬', name: '分镜导演' },
              { icon: '🔍', name: '审查' },
              { icon: '🔧', name: '修复' },
            ].map((a, i) => (
              <div key={i} className="flex items-center gap-1">
                <div className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-xs">
                  <span className="mr-1">{a.icon}</span>{a.name}
                </div>
                {i < 6 && <span className="text-gray-600">→</span>}
              </div>
            ))}
          </div>
          <p className="text-gray-600 text-xs mt-6">7 AI agents work together to transform your story into a complete animation</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>Pavo AI Agent</span>
          <span>AI-powered storyboard generation</span>
        </div>
      </footer>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
}
