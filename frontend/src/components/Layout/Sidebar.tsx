import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useThreads, useDeleteThread } from '../../services/threads';

const navigation = [
  { name: 'Knowledge Bases', href: '/kb', icon: '📚' },
  { name: 'Prompts', href: '/prompts', icon: '📝' },
  { name: 'Agents', href: '/agents', icon: '🤖' },
  { name: 'Teams', href: '/teams', icon: '👥' },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: threads, isLoading } = useThreads();
  const deleteThread = useDeleteThread();

  const handleDeleteThread = async (e: React.MouseEvent, threadId: string) => {
    e.preventDefault(); // Prevent navigation
    if (window.confirm('Are you sure you want to delete this chat?')) {
      await deleteThread.mutateAsync(threadId);
      if (location.pathname === `/chat/${threadId}`) {
        navigate('/chat');
      }
    }
  };

  // Sort threads by updated_at descending (newest first)
  const sortedThreads = [...(threads || [])].sort((a, b) => {
    const dateA = new Date(a.updated_at || a.created_at).getTime();
    const dateB = new Date(b.updated_at || b.created_at).getTime();
    return dateB - dateA;
  });

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900 text-white">
      <div className="flex h-16 items-center justify-center border-b border-gray-800">
        <Link to="/" className="text-xl font-bold hover:text-gray-300 transition-colors">
          MAS Platform
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-4">
        {/* Main Navigation */}
        <nav className="space-y-1 mb-6">
          {navigation.map((item) => {
            const isActive = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Recent Chats Section */}
        <div className="pt-4 border-t border-gray-800">
          <Link
            to="/chat"
            className={`flex items-center gap-3 rounded-lg px-3 py-2 mb-4 text-sm font-medium transition-colors ${location.pathname === '/chat'
              ? 'bg-primary-600 text-white'
              : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
          >
            <span className="text-lg">💬</span>
            <span>New Chat</span>
          </Link>

          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Recent Chats
          </h3>
          <div className="space-y-1">
            {isLoading ? (
              <div className="px-3 text-gray-500 text-sm">Loading...</div>
            ) : sortedThreads.length === 0 ? (
              <div className="px-3 text-gray-500 text-sm">No recent chats</div>
            ) : (
              sortedThreads.map((thread) => {
                const isActive = location.pathname === `/chat/${thread.thread_id}`;
                return (
                  <Link
                    key={thread.thread_id}
                    to={`/chat/${thread.thread_id}`}
                    className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                      }`}
                  >
                    <div className="truncate flex-1" title={thread.title || 'Untitled Chat'}>
                      {thread.title || 'Untitled Chat'}
                    </div>
                    <button
                      onClick={(e) => handleDeleteThread(e, thread.thread_id)}
                      className={`ml-2 opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity ${deleteThread.isPending ? 'cursor-wait' : ''
                        }`}
                      title="Delete Chat"
                    >
                      ×
                    </button>
                  </Link>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

