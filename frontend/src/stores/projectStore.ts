import { create } from 'zustand';
import { projectService } from '@/services/project';

interface ProjectState {
  currentProjectId: string | null;
  setCurrentProjectId: (id: string | null) => void;
  createProject: (input: string, userId?: string) => Promise<string>;
}

export const useProjectStore = create<ProjectState>((set) => ({
  currentProjectId: null,

  setCurrentProjectId: (id) => set({ currentProjectId: id }),

  createProject: async (input, userId) => {
    const data = await projectService.create(input, userId);
    const projectId = data.projectId;
    set({ currentProjectId: projectId });
    return projectId;
  },
}));
