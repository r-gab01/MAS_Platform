import { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useTeams } from '../services/teams';
import { useThreadMessages } from '../services/threads';
import { useStreamingChat } from '../hooks/useStreamingChat';
import Header from '../components/Layout/Header';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import type { ChatMessageRead } from '../types/api';

export default function ChatArea() {
  const { threadId } = useParams<{ threadId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: teams } = useTeams();
  
  const [teamId, setTeamId] = useState<number>(
    location.state?.teamId || 0
  );
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: existingMessages } = useThreadMessages(threadId || '');
  const { messages, sendMessage, isStreaming, setMessages } = useStreamingChat(
    threadId || '',
    teamId
  );

  // Load existing messages on mount
  useEffect(() => {
    if (existingMessages && existingMessages.length > 0) {
      setMessages(existingMessages);
    }
  }, [existingMessages, setMessages]);

  // Send initial message if provided
  useEffect(() => {
    if (location.state?.initialMessage && teamId && threadId) {
      sendMessage(location.state.initialMessage);
      // Clear the state to avoid resending
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, teamId, threadId, sendMessage, navigate]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !teamId || !threadId) return;

    const message = inputMessage.trim();
    setInputMessage('');
    await sendMessage(message);
  };

  const allMessages = messages.length > 0 ? messages : existingMessages || [];

  if (!threadId) {
    return (
      <div>
        <Header title="Chat" />
        <div className="p-6 text-center text-gray-500">
          Invalid thread ID. Please start a new chat.
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <Header title="Chat" />
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Team selector */}
        <div className="border-b border-gray-200 bg-white px-6 py-3">
          <Select
            label="Team"
            value={teamId}
            onChange={(e) => setTeamId(parseInt(e.target.value))}
            options={teams?.map((t) => ({ value: t.id, label: t.name })) || []}
            placeholder="Select a team"
            className="max-w-xs"
          />
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <div className="mx-auto max-w-4xl space-y-4">
            {allMessages.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No messages yet. Start the conversation!
              </div>
            ) : (
              allMessages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            {isStreaming && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary-600"></div>
                <span>AI is typing...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 bg-white p-6">
          <form onSubmit={handleSend} className="mx-auto max-w-4xl">
            <div className="flex gap-3">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={isStreaming || !teamId}
                className="flex-1"
              />
              <Button
                type="submit"
                disabled={!inputMessage.trim() || isStreaming || !teamId}
              >
                Send
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessageRead }) {
  const isHuman = message.type === 'human';

  return (
    <div className={`flex ${isHuman ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isHuman
            ? 'bg-primary-600 text-white'
            : 'bg-white text-gray-900 border border-gray-200'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        <div
          className={`mt-1 text-xs ${
            isHuman ? 'text-primary-100' : 'text-gray-500'
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

