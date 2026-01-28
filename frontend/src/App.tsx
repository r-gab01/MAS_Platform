import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import TeamsLibrary from './pages/TeamsLibrary';
import AgentsLibrary from './pages/AgentsLibrary';
import PromptsLibrary from './pages/PromptsLibrary';
import KBLibrary from './pages/KBLibrary';
import Chat from './pages/Chat';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/teams" replace />} />
          <Route path="teams" element={<TeamsLibrary />} />
          <Route path="agents" element={<AgentsLibrary />} />
          <Route path="prompts" element={<PromptsLibrary />} />
          <Route path="kb" element={<KBLibrary />} />
          <Route path="chat/:threadId?" element={<Chat />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;



