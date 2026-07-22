import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '@/services/project';

export const useProject = (id: string | null) =>
  useQuery({
    queryKey: ['project', id],
    queryFn: () => projectService.get(id!),
    enabled: !!id,
    refetchInterval: (query: any) => {
      if (query.state.data?.status === 'generating') return 2000;
      return false;
    },
  });

export const useProjects = (userId?: string) =>
  useQuery({
    queryKey: ['projects', userId],
    queryFn: () => projectService.list(userId),
  });

export const useGalleryProjects = (limit = 20) =>
  useQuery({
    queryKey: ['gallery'],
    queryFn: async () => {
      const all = await projectService.list();
      const completed = (all || []).filter((p: any) => p.status === 'completed');
      return completed.slice(0, limit);
    },
  });

export const useCreateProject = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ input, userId }: { input: string; userId?: string }) =>
      projectService.create(input, userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });
};
