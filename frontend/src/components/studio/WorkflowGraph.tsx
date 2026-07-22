'use client';

import { useCallback, useRef, useEffect } from 'react';
import type { AgentState } from '@/stores/workflowStore';

interface Props {
  agents: AgentState[];
}

const STATUS_COLORS: Record<string, string> = {
  idle: '#2a2a2a', running: '#6366f1', completed: '#10b981',
  failed: '#ef4444', retry: '#f59e0b',
};

export function WorkflowGraph({ agents }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const tRef = useRef(0);

  const draw = useCallback((time: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const nodeW = 52;
    const gap = (W - agents.length * nodeW) / (agents.length + 1);
    const y = rect.height / 2;

    tRef.current += 0.02;

    agents.forEach((agent, i) => {
      const x = gap + i * (nodeW + gap);
      const color = STATUS_COLORS[agent.status] || '#2a2a2a';
      const isActive = agent.status === 'running';
      const pulse = isActive ? Math.sin(tRef.current * 3 + i) * 0.08 + 1 : 1;
      const r = (nodeW / 2) * pulse;

      // Draw arrow from previous node
      if (i > 0) {
        const prevX = gap + (i - 1) * (nodeW + gap);
        ctx.strokeStyle = agent.status === 'completed' ? '#10b981' :
                          agent.status === 'running' ? '#6366f1' : '#2a2a2a';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(prevX + nodeW / 2 + 2, y);
        ctx.lineTo(x - nodeW / 2 - 2, y);
        ctx.stroke();
      }

      // Draw node circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = isActive ? `${color}40` : `${color}30`;
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Emoji
      ctx.font = `${Math.round(nodeW * 0.5)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.icon, x, y - 1);

      // Label below
      ctx.font = '9px sans-serif';
      ctx.fillStyle = agent.status === 'idle' ? '#555' : '#999';
      ctx.textBaseline = 'top';
      ctx.fillText(agent.displayName, x, y + r + 6);

      // Progress on completed
      if (agent.status === 'completed') {
        ctx.font = '8px sans-serif';
        ctx.fillStyle = '#10b981';
        ctx.textBaseline = 'bottom';
        ctx.fillText('✓', x + r - 6, y - r + 10);
      }
    });

    animRef.current = requestAnimationFrame(draw);
  }, [agents]);

  useEffect(() => {
    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-[160px]"
    />
  );
}
