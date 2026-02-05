import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTeams } from '../services/teams';
import { useThreadMessages, useSendMessage } from '../services/threads';
import Select from '../components/common/Select';
import Textarea from '../components/common/Textarea';
import Button from '../components/common/Button';
import Header from '../components/Layout/Header';
import type { ChatMessageRead } from '../types/api';

export default function Chat() {
  const { threadId } = useParams<{ threadId?: string }>();
  const navigate = useNavigate();
  const { data: teams } = useTeams();
  const { data: existingMessages, isLoading: isLoadingMessages } = useThreadMessages(threadId);
  const sendMessage = useSendMessage();

  const [selectedTeamId, setSelectedTeamId] = useState<number | ''>('');
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessageRead[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatAreaRef = useRef<HTMLDivElement>(null);
  const streamingContentRef = useRef<string>('');

  // Load existing messages when threadId changes
  useEffect(() => {
    if (existingMessages) {
      setMessages(existingMessages);
      // Clear streaming content when messages are refreshed (after streaming completes)
      if (!isStreaming) {
        setStreamingContent('');
        streamingContentRef.current = '';
      }
    } else {
      setMessages([]);
    }
  }, [existingMessages, isStreaming]);

  // If threadId exists but no team selected, try to get team from localStorage
  useEffect(() => {
    if (threadId && !selectedTeamId) {
      const savedTeamId = localStorage.getItem(`thread_${threadId}_teamId`);
      if (savedTeamId) {
        setSelectedTeamId(Number(savedTeamId));
      }
    }
  }, [threadId, selectedTeamId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const generateThreadId = (): string => {
    return crypto.randomUUID();
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedTeamId || isStreaming) return;

    const messageText = inputMessage.trim();
    setInputMessage('');

    let currentThreadId = threadId;

    // If no threadId, generate one and update URL
    if (!currentThreadId) {
      currentThreadId = generateThreadId();
      navigate(`/chat/${currentThreadId}`, { replace: true });
    }

    // Save team_id to localStorage for this thread
    localStorage.setItem(`thread_${currentThreadId}_teamId`, String(selectedTeamId));

    // Add user message immediately
    const userMessage: ChatMessageRead = {
      id: crypto.randomUUID(),
      type: 'human',
      content: messageText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Start streaming
    setIsStreaming(true);
    setStreamingContent('');
    streamingContentRef.current = '';

    try {
      await sendMessage.mutateAsync({
        threadId: currentThreadId,
        request: {
          message: messageText,
          team_id: selectedTeamId as number,
        },
        onChunk: (chunk: Partial<ChatMessageRead>) => {
          // Update streaming content in real-time

          // 1. Handle Tool Calls (The AI wants to call a tool)
          if (chunk.type === 'ai' && chunk.tool_calls && chunk.tool_calls.length > 0) {
            setMessages((prev) => [
              ...prev,
              {
                id: crypto.randomUUID(),
                type: 'ai',
                content: chunk.content || '',
                tool_calls: chunk.tool_calls,
                created_at: new Date().toISOString()
              } as ChatMessageRead
            ]);
            setStreamingContent('');
            streamingContentRef.current = '';
          }

          // 2. Handle Tool Outputs (The result of the tool)
          else if (chunk.type === 'tool') {
            setMessages((prev) => [
              ...prev,
              {
                id: chunk.tool_call_id || crypto.randomUUID(),
                type: 'tool',
                content: chunk.content || '',
                name: chunk.name,
                tool_call_id: chunk.tool_call_id,
                created_at: new Date().toISOString()
              } as ChatMessageRead
            ]);
            setStreamingContent('');
            streamingContentRef.current = '';
          }

          // 3. Handle specific AI Text Content
          // Note: Standard content updates go to streamingContent to show typing effect
          else if (chunk.type === 'ai' && chunk.content) {
            // handle string content for streaming display
            if (typeof chunk.content === 'string') {
              streamingContentRef.current = chunk.content;
              setStreamingContent(chunk.content);
            } else {
              // If content is complex structure during streaming (unlikely for chunks but possible final payload)
              // We might want to just let the full refresh handle it or stringify it
              // For now assuming streaming chunks are text parts
            }
          }
        },
      });

      // Messages will be refreshed automatically by React Query via invalidateQueries
      // Set isStreaming to false, but keep streamingContent visible until messages refresh
      setIsStreaming(false);
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Error sending message. Please try again.');
      setIsStreaming(false);
      setStreamingContent('');
      streamingContentRef.current = '';
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const canSend = selectedTeamId && inputMessage.trim() && !isStreaming;

  return (
    <div className="flex h-full flex-col">
      <Header title="Chat" subtitle="Chat with your AI teams" />
      <div className="flex flex-1 flex-col overflow-hidden p-6">
        {/* Team Selector */}
        <div className="mb-4">
          <Select
            label="Select Team"
            value={selectedTeamId}
            onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : '')}
            options={
              teams?.map((team) => ({
                value: team.id,
                label: team.name,
              })) || []
            }
            placeholder="Choose a team..."
          />
          {threadId && messages.length > 0 && !selectedTeamId && (
            <p className="mt-1 text-sm text-gray-500">
              Select a team to continue the conversation
            </p>
          )}
        </div>

        {/* Chat Area */}
        <div
          ref={chatAreaRef}
          className="flex-1 overflow-y-auto rounded-lg border border-gray-200 bg-white p-4 mb-4"
        >
          {isLoadingMessages ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading messages...</div>
            </div>
          ) : messages.length === 0 && !isStreaming ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                {!selectedTeamId
                  ? 'Select a team and start a conversation'
                  : 'Start a conversation by sending a message'}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'human' ? 'justify-end' : 'justify-start'
                    }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${message.type === 'human'
                      ? 'bg-primary-600 text-white'
                      : message.type === 'tool'
                        ? 'bg-gray-50 border border-gray-200 text-gray-800'
                        : 'bg-gray-100 text-gray-900'
                      }`}
                  >
                    {/* Render Content */}
                    {message.type === 'tool' ? (
                      <div className="text-sm font-mono">
                        <div className="font-bold text-xs text-gray-500 mb-1">Tool Output ({message.name})</div>
                        <div className="whitespace-pre-wrap break-words">{typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}</div>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap break-words">
                        {Array.isArray(message.content) ? (
                          <div className="space-y-3">
                            {message.content.map((block, index) => {
                              if (block.type === 'text') {
                                return <div key={index}>{block.text}</div>;
                              }
                              if (block.type === 'tool_use') {
                                return (
                                  <div key={index} className="text-xs bg-white/50 p-2 rounded border border-gray-200">
                                    <div className="font-semibold text-gray-600">🛠️ Calling: <span className="text-gray-900 font-bold">{block.name}</span></div>
                                    <div className="font-mono text-gray-500 mt-1 whitespace-pre-wrap">
                                      {JSON.stringify(block.input, null, 2)}
                                    </div>
                                  </div>
                                );
                              }
                              return null;
                            })}
                          </div>
                        ) : (
                          message.content
                        )}
                      </div>
                    )}

                    {/* Render Tool Calls for AI messages */}
                    {message.type === 'ai' && message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.tool_calls.map((toolCall) => (
                          <div key={toolCall.id} className="text-xs bg-white/50 p-2 rounded border border-gray-200">
                            <div className="font-semibold text-gray-600">🛠️ Calling: {toolCall.name}</div>
                            <div className="font-mono text-gray-500 mt-1 whitespace-pre-wrap">
                              {JSON.stringify(toolCall.args, null, 2)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <div
                      className={`text-xs mt-1 ${message.type === 'human' ? 'text-primary-100' : 'text-gray-500'
                        }`}
                    >
                      {new Date(message.created_at || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              {/* Streaming message - show during streaming or until messages are refreshed */}
              {streamingContent && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
                    <div className="whitespace-pre-wrap break-words">{streamingContent}</div>
                    {isStreaming && (
                      <div className="text-xs mt-1 text-gray-500">
                        <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse"></span>
                        {' Typing...'}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <div className="flex-1">
            <Textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                !selectedTeamId && !threadId
                  ? 'Select a team first...'
                  : 'Type your message... (Press Enter to send, Shift+Enter for new line)'
              }
              rows={3}
              disabled={(!selectedTeamId && !threadId) || isStreaming}
            />
          </div>
          <div className="flex items-end">
            <Button
              onClick={handleSendMessage}
              disabled={!canSend}
              className="h-full"
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

