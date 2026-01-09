import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import client from '@/lib/api/client';

// KEY: The return type is inferred automatically from the schema!
// No manual 'interface Repository { ... }' needed.

export function useRepositories() {
  return useQuery({
    queryKey: ['repos'],
    queryFn: async () => {
      const { data, error } = await client.GET('/repos/');
      if (error) throw error;
      return data; // Typed as RepositoryResponse[]
    },
  });
}

export function useIngestRepo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ url, isPrivate }: { url: string; isPrivate: boolean }) => {
      const { data, error } = await client.POST('/ingest/', {
        body: {
          repo_url: url,
          is_private: isPrivate,
        },
      });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repos'] });
    },
  });
}