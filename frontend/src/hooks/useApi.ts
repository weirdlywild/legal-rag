import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, getErrorMessage } from '@/lib/api/client';
import type {
  DocumentListResponse,
  DocumentUploadResponse,
  DocumentDetailResponse,
  DeleteResponse,
  QueryRequest,
  QueryResponse,
  SystemInfoResponse,
  UsageResponse,
  ReadinessResponse,
} from '@/lib/api/types';

// Query keys
export const queryKeys = {
  documents: ['documents'] as const,
  document: (id: string) => ['documents', id] as const,
  systemInfo: ['system', 'info'] as const,
  usage: ['system', 'usage'] as const,
  readiness: ['health', 'ready'] as const,
};

// Health hooks
export function useReadiness() {
  return useQuery({
    queryKey: queryKeys.readiness,
    queryFn: async (): Promise<ReadinessResponse> => {
      const { data } = await apiClient.get('/health/ready');
      return data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Document hooks
export function useDocuments() {
  return useQuery({
    queryKey: queryKeys.documents,
    queryFn: async (): Promise<DocumentListResponse> => {
      const { data } = await apiClient.get('/documents');
      return data;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: queryKeys.document(id),
    queryFn: async (): Promise<DocumentDetailResponse> => {
      const { data } = await apiClient.get(`/documents/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      title,
    }: {
      file: File;
      title?: string;
    }): Promise<DocumentUploadResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      if (title) {
        formData.append('title', title);
      }

      const { data } = await apiClient.post('/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string): Promise<DeleteResponse> => {
      const { data } = await apiClient.delete(`/documents/${id}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents });
    },
  });
}

// Query hook
export function useQueryDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: QueryRequest): Promise<QueryResponse> => {
      const { data } = await apiClient.post('/query', request);
      return data;
    },
    onSuccess: () => {
      // Refresh usage stats after query
      queryClient.invalidateQueries({ queryKey: queryKeys.usage });
    },
  });
}

// System hooks
export function useSystemInfo() {
  return useQuery({
    queryKey: queryKeys.systemInfo,
    queryFn: async (): Promise<SystemInfoResponse> => {
      const { data } = await apiClient.get('/system/info');
      return data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

export function useUsage() {
  return useQuery({
    queryKey: queryKeys.usage,
    queryFn: async (): Promise<UsageResponse> => {
      const { data } = await apiClient.get('/system/usage');
      return data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// Re-export error helper
export { getErrorMessage };
