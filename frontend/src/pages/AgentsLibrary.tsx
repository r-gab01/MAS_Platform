import { useState } from 'react';
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent, useAgent } from '../services/agents';
import { usePrompts } from '../services/prompts';
import { useLLMModels } from '../services/llm';
import { useTools } from '../services/tools';
import { useKnowledgeBases } from '../services/kb';
import Header from '../components/Layout/Header';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import Textarea from '../components/common/Textarea';
import Select from '../components/common/Select';
import MultiSelect from '../components/common/MultiSelect';
import type { AgentCreate, AgentType } from '../types/api';

export default function AgentsLibrary() {
  const { data: agents, isLoading } = useAgents();
  const { data: prompts } = usePrompts();
  const { data: llmModels } = useLLMModels();
  const { data: tools } = useTools();
  const { data: knowledgeBases } = useKnowledgeBases();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();
  const deleteAgent = useDeleteAgent();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewingAgent, setViewingAgent] = useState<number | null>(null);
  const [editingAgent, setEditingAgent] = useState<number | null>(null);
  const [formData, setFormData] = useState<AgentCreate>({
    name: '',
    description: '',
    prompt_id: null,
    llm_model_id: 0,
    temperature: 0,
    agent_type: 'worker',
    tool_ids: [],
    kb_ids: [],
  });

  const handleOpenModal = (agentId?: number) => {
    if (agentId) {
      const agent = agents?.find((a) => a.id === agentId);
      if (agent) {
        setEditingAgent(agentId);
        setFormData({
          name: agent.name,
          description: agent.description,
          prompt_id: agent.prompt_id,
          llm_model_id: agent.llm_model_id,
          temperature: agent.temperature,
          agent_type: agent.agent_type,
          tool_ids: [],
          kb_ids: [],
        });
      }
    } else {
      setEditingAgent(null);
      setFormData({
        name: '',
        description: '',
        prompt_id: null,
        llm_model_id: 0,
        temperature: 0,
        agent_type: 'worker',
        tool_ids: [],
        kb_ids: [],
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingAgent(null);
    setViewingAgent(null);
  };

  const handleViewAgent = (id: number) => {
    setViewingAgent(id);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.description || !formData.llm_model_id) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      if (editingAgent) {
        await updateAgent.mutateAsync({ id: editingAgent, agent: formData });
      } else {
        await createAgent.mutateAsync(formData);
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error saving agent:', error);
      alert('Error saving agent. Please try again.');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await deleteAgent.mutateAsync(id);
      } catch (error) {
        console.error('Error deleting agent:', error);
        alert('Error deleting agent. Please try again.');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <Header title="Agents Library" />
        <div className="mt-6 text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <Header title="Agents Library" subtitle="Manage your AI agents" />
      <div className="p-6">
        <div className="mb-4 flex justify-end">
          <Button onClick={() => handleOpenModal()}>Create Agent</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents?.map((agent) => (
            <div key={agent.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                  <p className="mt-1 text-sm text-gray-600">{agent.description}</p>
                  <div className="mt-2 flex gap-2">
                    <span className="inline-flex items-center rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-medium text-primary-800">
                      {agent.agent_type}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => handleViewAgent(agent.id)}>
                  View
                </Button>
                <Button size="sm" variant="secondary" onClick={() => handleOpenModal(agent.id)}>
                  Edit
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(agent.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>

        {agents?.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No agents found. Create your first agent to get started.
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={
          viewingAgent
            ? 'Agent Details'
            : editingAgent
            ? 'Edit Agent'
            : 'Create Agent'
        }
        footer={
          viewingAgent ? (
            <Button onClick={handleCloseModal}>Close</Button>
          ) : (
            <>
              <Button variant="ghost" onClick={handleCloseModal}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={createAgent.isPending || updateAgent.isPending}
              >
                {editingAgent ? 'Update' : 'Create'}
              </Button>
            </>
          )
        }
      >
        {viewingAgent ? (
          <AgentDetails agentId={viewingAgent} />
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Name *"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <Textarea
              label="Description *"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Agent Type *"
                value={formData.agent_type}
                onChange={(e) => setFormData({ ...formData, agent_type: e.target.value as AgentType })}
                options={[
                  { value: 'worker', label: 'Worker' },
                  { value: 'supervisor', label: 'Supervisor' },
                ]}
                required
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature: {formData.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
            <Select
              label="LLM Model *"
              value={formData.llm_model_id}
              onChange={(e) => setFormData({ ...formData, llm_model_id: parseInt(e.target.value) })}
              options={llmModels?.map((m) => ({ value: m.id, label: `${m.name} (${m.provider})` })) || []}
              placeholder="Select an LLM model"
              required
            />
            <Select
              label="Prompt (Optional)"
              value={formData.prompt_id || ''}
              onChange={(e) => setFormData({ ...formData, prompt_id: e.target.value ? parseInt(e.target.value) : null })}
              options={[
                { value: '', label: 'None' },
                ...(prompts?.map((p) => ({ value: p.id, label: p.name })) || []),
              ]}
            />
            <MultiSelect
              label="Tools"
              selected={formData.tool_ids || []}
              onChange={(selected) => setFormData({ ...formData, tool_ids: selected as number[] })}
              options={tools?.map((t) => ({ value: t.id, label: t.display_name })) || []}
              placeholder="Select tools"
            />
            <MultiSelect
              label="Knowledge Bases"
              selected={formData.kb_ids || []}
              onChange={(selected) => setFormData({ ...formData, kb_ids: selected as (string | null)[] })}
              options={knowledgeBases?.map((kb) => ({ value: kb.id, label: kb.name })) || []}
              placeholder="Select knowledge bases"
            />
          </form>
        )}
      </Modal>
    </div>
  );
}

function AgentDetails({ agentId }: { agentId: number }) {
  const { data: agent, isLoading } = useAgent(agentId);

  if (isLoading) {
    return <div>Loading agent details...</div>;
  }

  if (!agent) {
    return <div>Agent not found</div>;
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">{agent.name}</h3>
        <p className="text-sm text-gray-600">{agent.description}</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <span className="text-sm font-medium text-gray-700">Type:</span>
          <span className="ml-2 text-sm text-gray-900">{agent.agent_type}</span>
        </div>
        <div>
          <span className="text-sm font-medium text-gray-700">Temperature:</span>
          <span className="ml-2 text-sm text-gray-900">{agent.temperature}</span>
        </div>
      </div>
      <div>
        <span className="text-sm font-medium text-gray-700">LLM Model:</span>
        <span className="ml-2 text-sm text-gray-900">
          {agent.llm_model.name} ({agent.llm_model.provider})
        </span>
      </div>
      {agent.prompt && (
        <div>
          <span className="text-sm font-medium text-gray-700">Prompt:</span>
          <span className="ml-2 text-sm text-gray-900">{agent.prompt.name}</span>
        </div>
      )}
      {agent.tools.length > 0 && (
        <div>
          <span className="text-sm font-medium text-gray-700">Tools:</span>
          <div className="mt-1 flex flex-wrap gap-2">
            {agent.tools.map((tool) => (
              <span
                key={tool.id}
                className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
              >
                {tool.display_name}
              </span>
            ))}
          </div>
        </div>
      )}
      {agent.knowledge_bases.length > 0 && (
        <div>
          <span className="text-sm font-medium text-gray-700">Knowledge Bases:</span>
          <div className="mt-1 flex flex-wrap gap-2">
            {agent.knowledge_bases.map((kb) => (
              <span
                key={kb.id}
                className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
              >
                {kb.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

