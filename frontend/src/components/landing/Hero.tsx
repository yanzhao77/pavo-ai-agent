'use client';

import { useState } from 'react';
import { Sparkles, ArrowRight, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { useRouter } from 'next/navigation';

const EXAMPLES = [
  'A father comes home from work, his 5-year-old son brings him a foot basin',
  'A cyberpunk detective walks through neon-lit streets in the rain',
  'Time-lapse of a cherry blossom tree blooming over four seasons',
];

export function Hero() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const { createProject } = useProjectStore();
  const router = useRouter();

  const handleSubmit = async () => {
    if (!input.trim() || loading) return;
    if (!isAuthenticated) {
      // will be handled by parent
      return;
    }
    setLoading(true);
    try {
      const userId = localStorage.getItem('pavo_user_id') || '';
      await createProject(input.trim(), userId);
      router.push('/studio');
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center pt-14 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/30 via-black to-black" />
      <div className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(99,102,241,0.15) 0%, transparent 50%)',
        }}
      />

      {/* Content */}
      <div className="relative z-10 max-w-3xl mx-auto px-4 text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-lg shadow-indigo-500/25">
          <Sparkles className="w-8 h-8 text-white" />
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight">
          Create Stories with{' '}
          <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">AI</span>
        </h1>
        <p className="text-gray-400 mt-4 text-lg max-w-xl mx-auto">
          Imagine your story, AI turns it into animation. Characters, scenes, and storyboards in seconds.
        </p>

        {/* Input */}
        <div className="mt-10 max-w-xl mx-auto">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="Write your story idea..."
              className="w-full px-5 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 text-sm backdrop-blur-sm transition-all"
              disabled={loading}
            />
            <button
              onClick={handleSubmit}
              disabled={loading || !input.trim()}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 w-10 h-10 bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg flex items-center justify-center transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 text-white animate-spin" /> : <ArrowRight className="w-4 h-4 text-white" />}
            </button>
          </div>
          <p className="text-gray-600 text-xs mt-2">Press Enter to start creating</p>
        </div>

        {/* Examples */}
        <div className="mt-8 space-y-2 max-w-lg mx-auto">
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => setInput(ex)}
              className="block w-full text-left text-xs text-gray-500 hover:text-gray-300 bg-white/[0.02] hover:bg-white/[0.05] rounded-lg px-4 py-2 transition-colors border border-white/5"
            >
              &ldquo;{ex}&rdquo;
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
