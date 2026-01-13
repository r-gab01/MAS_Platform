import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useTeams } from '../services/teams';
import Header from '../components/Layout/Header';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Textarea from '../components/common/Textarea';
import Select from '../components/common/Select';

export default function NewChat() {
  const navigate = useNavigate();
  const { data: teams, isLoading } = useTeams();
  const [teamId, setTeamId] = useState<number>(0);
  const [message, setMessage] = useState('');

  const handleStartChat = () => {
    if (!teamId || !message.trim()) {
      alert('Please select a team and enter a message');
      return;
    }

    const threadId = uuidv4();
    navigate(`/chat/${threadId}`, {
      state: { teamId, initialMessage: message },
    });
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <Header title="New Chat" />
        <div className="mt-6 text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <Header title="New Chat" subtitle="Start a new conversation with an AI team" />
      <div className="p-6">
        <div className="mx-auto max-w-2xl">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="space-y-4">
              <Select
                label="Select Team *"
                value={teamId}
                onChange={(e) => setTeamId(parseInt(e.target.value))}
                options={teams?.map((t) => ({ value: t.id, label: t.name })) || []}
                placeholder="Choose a team to chat with"
                required
              />
              <Textarea
                label="Initial Message *"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={6}
                placeholder="Type your message here..."
                required
              />
              <div className="flex justify-end">
                <Button onClick={handleStartChat} disabled={!teamId || !message.trim()}>
                  Start Chat
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

