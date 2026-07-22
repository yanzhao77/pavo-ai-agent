'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | null;
  trendLabel?: string;
}

export function StatsCard({ label, value, icon, trend, trendLabel }: StatsCardProps) {
  const formattedValue =
    value >= 1000
      ? `${(value / 1000).toFixed(1).replace(/\.0$/, '')}k`
      : String(value);

  return (
    <div className="group p-5 rounded-xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/20 transition-all duration-200 hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div className="flex flex-col">
          <span className="text-3xl font-bold text-white tracking-tight">
            {formattedValue}
          </span>
          <span className="text-xs text-gray-500 mt-1">{label}</span>
        </div>
        <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/20 transition-colors">
          {icon}
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-3">
          {trend === 'up' ? (
            <TrendingUp className="w-3 h-3 text-emerald-400" />
          ) : (
            <TrendingDown className="w-3 h-3 text-red-400" />
          )}
          <span className="text-[11px] text-gray-500">{trendLabel}</span>
        </div>
      )}
    </div>
  );
}
