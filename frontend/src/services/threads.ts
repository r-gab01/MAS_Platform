import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api';
import type { ChatThreadRead, ChatMessageRead, ChatRequest } from '../types/api';

// Query keys
export const threadKeys = {
  all: ['threads'] as const,
  lists: () => [...threadKeys.all, 'list'] as const,
  details: () => [...threadKeys.all, 'detail'] as const,
  detail: (id: string) => [...threadKeys.details(), id] as const,
  messages: (id: string) => [...threadKeys.detail(id), 'messages'] as const,
};

// Get all threads
export const useThreads = () => {
  return useQuery({
    queryKey: threadKeys.lists(),
    queryFn: async () => {
      const { data } = await apiClient.get<ChatThreadRead[]>('/api/v1/execution/threads');
      return data;
    },
  });
};

// Get messages for a thread
export const useThreadMessages = (threadId: string) => {
  return useQuery({
    queryKey: threadKeys.messages(threadId),
    queryFn: async () => {
      const { data } = await apiClient.get<ChatMessageRead[]>(
        `/api/v1/execution/threads/${threadId}/messages`
      );
      return data;
    },
    enabled: !!threadId,
  });
};

// Delete thread
export const useDeleteThread = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (threadId: string) => {
      await apiClient.delete(`/api/v1/execution/threads/${threadId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: threadKeys.lists() });
    },
  });
};

// Send chat message (streaming handled separately)
export const sendChatMessage = async (threadId: string, request: ChatRequest): Promise<Response> => {
  return fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/execution/threads/${threadId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
};

