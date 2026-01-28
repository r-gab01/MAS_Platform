import { Link, useLocation } from 'react-router-dom';

const navigation = [
    { name: 'Knowledge Bases', href: '/kb', icon: '📚' },
    { name: 'Prompts', href: '/prompts', icon: '📝' },
    { name: 'Agents', href: '/agents', icon: '🤖' },
    { name: 'Teams', href: '/teams', icon: '👥' },
  { name: 'New Chat', href: '/chat/new', icon: '💬' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900 text-white">
      <div className="flex h-16 items-center justify-center border-b border-gray-800">
        <h1 className="text-xl font-bold">AI RAG Platform</h1>
      </div>
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
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
    </div>
  );
}

