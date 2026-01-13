import { useState } from 'react';
import { useTeams, useCreateTeam, useUpdateTeam, useDeleteTeam } from '../services/teams';
import { useAgents } from '../services/agents';
import Header from '../components/Layout/Header';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Input from '../components/common/Input';
import Textarea from '../components/common/Textarea';
import Select from '../components/common/Select';
import MultiSelect from '../components/common/MultiSelect';
import type { TeamCreate } from '../types/api';

export default function TeamsLibrary() {
  const { data: teams, isLoading } = useTeams();
  const { data: agents } = useAgents();
  const createTeam = useCreateTeam();
  const updateTeam = useUpdateTeam();
  const deleteTeam = useDeleteTeam();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<number | null>(null);
  const [formData, setFormData] = useState<TeamCreate>({
    name: '',
    description: '',
    supervisor_id: 0,
    worker_ids: [],
  });

  const supervisorAgents = agents?.filter((a) => a.agent_type === 'supervisor') || [];
  const workerAgents = agents?.filter((a) => a.agent_type === 'worker') || [];

  const handleOpenModal = (teamId?: number) => {
    if (teamId) {
      const team = teams?.find((t) => t.id === teamId);
      if (team) {
        setEditingTeam(teamId);
        setFormData({
          name: team.name,
          description: team.description || '',
          supervisor_id: 0, // Will be loaded from full team data
          worker_ids: [],
        });
      }
    } else {
      setEditingTeam(null);
      setFormData({
        name: '',
        description: '',
        supervisor_id: 0,
        worker_ids: [],
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingTeam(null);
    setFormData({
      name: '',
      description: '',
      supervisor_id: 0,
      worker_ids: [],
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.supervisor_id) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      if (editingTeam) {
        await updateTeam.mutateAsync({ id: editingTeam, team: formData });
      } else {
        await createTeam.mutateAsync(formData);
      }
      handleCloseModal();
    } catch (error) {
      console.error('Error saving team:', error);
      alert('Error saving team. Please try again.');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this team?')) {
      try {
        await deleteTeam.mutateAsync(id);
      } catch (error) {
        console.error('Error deleting team:', error);
        alert('Error deleting team. Please try again.');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <Header title="Teams Library" />
        <div className="mt-6 text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <Header title="Teams Library" subtitle="Manage your agent teams" />
      <div className="p-6">
        <div className="mb-4 flex justify-end">
          <Button onClick={() => handleOpenModal()}>Create Team</Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {teams?.map((team) => (
            <div key={team.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
              {team.description && (
                <p className="mt-2 text-sm text-gray-600">{team.description}</p>
              )}
              <div className="mt-4 flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => handleOpenModal(team.id)}>
                  Edit
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(team.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>

        {teams?.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No teams found. Create your first team to get started.
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingTeam ? 'Edit Team' : 'Create Team'}
        footer={
          <>
            <Button variant="ghost" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createTeam.isPending || updateTeam.isPending}
            >
              {editingTeam ? 'Update' : 'Create'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name *"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Textarea
            label="Description"
            value={formData.description || ''}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={3}
          />
          <Select
            label="Supervisor *"
            value={formData.supervisor_id}
            onChange={(e) => setFormData({ ...formData, supervisor_id: parseInt(e.target.value) })}
            options={supervisorAgents.map((a) => ({ value: a.id, label: a.name }))}
            placeholder="Select a supervisor agent"
            required
          />
          <MultiSelect
            label="Workers"
            selected={formData.worker_ids || []}
            onChange={(selected) => setFormData({ ...formData, worker_ids: selected as number[] })}
            options={workerAgents.map((a) => ({ value: a.id, label: a.name }))}
            placeholder="Select worker agents"
          />
        </form>
      </Modal>
    </div>
  );
}

