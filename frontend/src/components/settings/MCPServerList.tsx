/**
 * MCP Server List Component
 * 
 * Manages the list of MCP servers and provides functionality to:
 * - View all configured MCP servers
 * - Add new MCP servers
 * - Toggle server active status
 * - Delete servers
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  Chip
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { MCPServerConfig, MCPServerConfigCreate, MCPServerType } from '../../types/settings';
import { getMCPServers, addMCPServer, toggleMCPServer, deleteMCPServer } from '../../api/settings';
import { MCPServerCard } from './MCPServerCard';

const SERVER_TYPE_OPTIONS: { value: MCPServerType; label: string }[] = [
  { value: 'sec_edgar', label: 'SEC EDGAR' },
  { value: 'financial_data', label: 'Financial Data' },
  { value: 'news', label: 'News' },
  { value: 'slack', label: 'Slack' },
  { value: 'custom', label: 'Custom' }
];

export const MCPServerList: React.FC = () => {
  const [servers, setServers] = useState<MCPServerConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [serverType, setServerType] = useState<MCPServerType>('custom');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [authToken, setAuthToken] = useState('');

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    setLoading(true);
    try {
      const data = await getMCPServers();
      setServers(data);
    } catch (err) {
      setError('Failed to load MCP servers');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await toggleMCPServer(id);
      await loadServers();
    } catch (err) {
      setError('Failed to toggle server');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this server?')) return;

    try {
      await deleteMCPServer(id);
      setSuccess('Server deleted');
      await loadServers();
    } catch (err) {
      setError('Failed to delete server');
    }
  };

  const handleAdd = async () => {
    if (!name || !endpointUrl) {
      setError('Name and endpoint URL are required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const newServer: MCPServerConfigCreate = {
        name,
        server_type: serverType,
        endpoint_url: endpointUrl,
        auth_token: authToken || undefined,
        is_active: true,
        metadata: {}
      };

      await addMCPServer(newServer);
      setSuccess('MCP server added successfully');
      setDialogOpen(false);
      resetForm();
      await loadServers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add server. Check the endpoint URL.');
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setName('');
    setServerType('custom');
    setEndpointUrl('');
    setAuthToken('');
  };

  // Calculate stats
  const connectedCount = servers.filter(s => s.is_connected).length;
  const activeCount = servers.filter(s => s.is_active).length;
  const totalTools = servers.reduce((sum, s) => sum + s.tool_count, 0);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        MCP Server Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Connect to Model Context Protocol (MCP) servers to give agents access to external tools 
        like SEC EDGAR filings, financial data APIs, news services, and Slack integration.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Stats */}
      <Box display="flex" gap={2} sx={{ mb: 3 }}>
        <Chip 
          label={`${connectedCount} Connected`} 
          color="success" 
          variant="outlined" 
        />
        <Chip 
          label={`${activeCount} Active`} 
          color="primary" 
          variant="outlined" 
        />
        <Chip 
          label={`${totalTools} Tools Available`} 
          variant="outlined" 
        />
      </Box>

      {/* Server List */}
      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : servers.length === 0 ? (
        <Alert severity="info">
          No MCP servers configured. Add a server to enable external tools for agents.
        </Alert>
      ) : (
        servers.map((server) => (
          <MCPServerCard
            key={server.id}
            server={server}
            onToggle={handleToggle}
            onDelete={handleDelete}
          />
        ))
      )}

      {/* Add Button */}
      <Box mt={3}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          Add MCP Server
        </Button>
      </Box>

      {/* Add Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add MCP Server</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="Server Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My SEC EDGAR Server"
              fullWidth
              required
            />

            <FormControl fullWidth>
              <InputLabel>Server Type</InputLabel>
              <Select
                value={serverType}
                label="Server Type"
                onChange={(e) => setServerType(e.target.value as MCPServerType)}
              >
                {SERVER_TYPE_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Endpoint URL"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              placeholder="http://localhost:3001"
              helperText="The MCP server endpoint URL"
              fullWidth
              required
            />

            <TextField
              label="Auth Token (Optional)"
              type="password"
              value={authToken}
              onChange={(e) => setAuthToken(e.target.value)}
              placeholder="Bearer token or API key"
              helperText="Authentication token if required by the server"
              fullWidth
            />

            <Alert severity="info" icon={false}>
              <Typography variant="body2">
                <strong>Note:</strong> The endpoint must be reachable from the DealDesk backend.
                For local development, use host.docker.internal instead of localhost.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleAdd}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            Add Server
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MCPServerList;
