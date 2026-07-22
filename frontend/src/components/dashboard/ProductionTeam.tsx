'use client';

import { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import type { Project } from '@/types/project';

const TEAM_MEMBERS = [
  { id: 'StoryDirector', icon: '🧠', displayName: '故事导演' },
  { id: 'CharacterDesigner', icon: '🎭', displayName: '角色设计师' },
  { id: 'SceneBuilder', icon: '🌆', displayName: '场景构建师' },
  { id: 'PropMaster', icon: '🎨', displayName: '道具师' },
  { id: 'StoryboardDirector', icon: '🎬', displayName: '分镜导演' },
  { id: 'QualityReviewer', icon: '🔍', displayName: '质量审查官' },
  { id: 'FixExpert', icon: '🔧', displayName: '修复专家' },
];

const AGENT_KEYWORDS: Record<string, string[]> = {
  StoryDirector: ['故事导演', 'StoryDirector', 'Director'],
  CharacterDesigner: ['角色设计师', 'CharacterDesigner'],
  SceneBuilder: ['场景构建师', 'SceneBuilder'],
  PropMaster: ['道具师', '道具师', 'PropMaster'],
  StoryboardDirector: ['分镜导演', 'StoryboardDirector'],
  QualityReviewer: ['质量审查官', '审查', 'QualityReviewer'],
  FixExpert: ['修复专家', '修复', 'FixExpert'],
};

interface ProductionTeamProps {
  projects: Project[];
}

function getAgentProjectCount(agentId: string, projects: Project[]): number {
  const keywords = AGENT_KEYWORDS[agentId] || [];
  return projects.filter((p) => {
    if (!p.traceLog || p.traceLog.length === 0) return false;
    return p.traceLog.some((entry) =>
      keywords.some((kw) => entry.agent?.includes(kw)),
    );
  }).length;
}

function getAgentProjects(agentId: string, projects: Project[]): Project[] {
  const keywords = AGENT_KEYWORDS[agentId] || [];
  return projects.filter((p) => {
    if (!p.traceLog || p.traceLog.length === 0) return false;
    return p.traceLog.some((entry) =>
      keywords.some((kw) => entry.agent?.includes(kw)),
    );
  });
}

function getAgentStatus(projects: Project[]): 'idle' | 'working' {
  const hasRunning = projects.some((p) => p.status === 'generating');
  return hasRunning ? 'working' : 'idle';
}

export function ProductionTeam({ projects }: ProductionTeamProps) {
  const [expandedMember, setExpandedMember] = useState<string | null>(null);

  const membersWithCounts = useMemo(
    () =>
      TEAM_MEMBERS.map((m) => ({
        ...m,
        projectCount: getAgentProjectCount(m.id, projects),
        agentProjects: getAgentProjects(m.id, projects),
      })),
    [projects],
  );

  return (
    <section>
      <h2 className="text-lg font-semibold text-white mb-4">
        AI Production Team
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {membersWithCounts.map((member) => {
          const isExpanded = expandedMember === member.id;
          const status = getAgentStatus(member.agentProjects);

          return (
            <div
              key={member.id}
              className="rounded-xl border border-white/10 bg-white/[0.03] overflow-hidden transition-all duration-200 hover:bg-white/[0.06]"
            >
              <button
                onClick={() =>
                  setExpandedMember(isExpanded ? null : member.id)
                }
                className="w-full flex items-center gap-3 p-4 text-left"
              >
                <span className="text-2xl">{member.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">
                      {member.displayName}
                    </span>
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        status === 'working'
                          ? 'bg-emerald-400 animate-pulse'
                          : 'bg-gray-600'
                      }`}
                    />
                  </div>
                  <span className="text-[11px] text-gray-500">
                    {member.projectCount > 0
                      ? `${member.projectCount} 个项目`
                      : '暂无参与项目'}
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-500 shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500 shrink-0" />
                )}
              </button>

              {isExpanded && (
                <div className="border-t border-white/5 px-4 py-3 space-y-2">
                  {member.agentProjects.length > 0 ? (
                    member.agentProjects.map((p) => (
                      <a
                        key={p.id}
                        href={`/studio?id=${p.id}`}
                        className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                      >
                        <ExternalLink className="w-3 h-3 shrink-0" />
                        <span className="truncate">
                          {p.title || p.input?.slice(0, 40) || p.id.slice(0, 8)}
                        </span>
                        <span
                          className={`ml-auto shrink-0 text-[10px] px-1.5 py-0.5 rounded ${
                            p.status === 'completed'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : p.status === 'generating'
                                ? 'bg-indigo-500/10 text-indigo-400'
                                : 'bg-gray-500/10 text-gray-500'
                          }`}
                        >
                          {p.status === 'completed'
                            ? '完成'
                            : p.status === 'generating'
                              ? '进行中'
                              : '草稿'}
                        </span>
                      </a>
                    ))
                  ) : (
                    <p className="text-xs text-gray-600">
                      该成员尚未参与任何项目
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
