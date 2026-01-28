import { useState, useCallback, useRef, useEffect } from 'react';
import { sendChatMessage } from '../services/threads';
import type { ChatMessageRead, ChatRequest } from '../types/api';

export function useStreamingChat(threadId: string, teamId: number) {
  const [messages, setMessages] = useState<ChatMessageRead[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isStreaming) return;

    // Add user message immediately
    const userMessage: ChatMessageRead = {
      id: crypto.randomUUID(),
      type: 'human',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add placeholder for AI response
    const aiMessageId = crypto.randomUUID();
    const aiMessage: ChatMessageRead = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, aiMessage]);

    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      const request: ChatRequest = {
        message,
        team_id: teamId,
      };

      const response = await sendChatMessage(threadId, request);

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          // Try to parse as JSON (SSE format: data: {...})
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, content: msg.content + data.content }
                      : msg
                  )
                );
              }
            } catch (e) {
              // If not JSON, treat as plain text chunk
              const text = line.slice(6);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === aiMessageId
                    ? { ...msg, content: msg.content + text }
                    : msg
                )
              );
            }
          } else {
            // Plain text streaming
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMessageId
                  ? { ...msg, content: msg.content + line }
                  : msg
              )
            );
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted');
      } else {
        console.error('Error streaming chat:', error);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, content: msg.content + '\n\n[Error: Failed to get response]' }
              : msg
          )
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [threadId, teamId, isStreaming]);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    sendMessage,
    isStreaming,
    stopStreaming,
    clearMessages,
    setMessages,
  };
}



