/**
 * LLM Provider Configuration Component
 * 
 * Allows users to configure their LLM provider (BYOLLM):
 * - Select provider (Anthropic, OpenAI, Google, Azure OpenAI, Ollama)
 * - Enter API key and model ID
 * - Configure optional base URL and API version
 * - Test connection before saving
 * - View and manage per-agent model overrides
 */

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  RadioGroup, 
  FormControlLabel, 
  Radio,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip
} from '@mui/material';
import { 
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { 
  LLMConfig, 
  LLMConfigCreate, 
  LLMProviderInfo, 
  AgentLLMOverride,
  AgentName,
  ValidationResult 
} from '../../types/settings';
import { 
  getLLMConfig, 
  setLLMConfig, 
  getLLMProviders, 
  validateLLMConfig,
  getAgentOverrides,
  setAgentOverride
} from '../../api/settings';

const AGENT_LABELS: Record<AgentName, string> = {
  comps: 'Comps Agent',
  dcf: 'DCF Agent',
  news: 'News Agent',
  document: 'Document Agent',
  pitchbook: 'Pitchbook Agent',
  research: 'Research Agent'
};

export const LLMProviderConfig: React.FC = () => {
  // State
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);
  const [overrides, setOverrides] = useState<AgentLLMOverride[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [selectedProvider, setSelectedProvider] = useState<string>('anthropic');
  const [apiKey, setApiKey] = useState('');
  const [modelId, setModelId] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiVersion, setApiVersion] = useState('');
  
  // Override dialog state
  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentName | null>(null);
  const [overrideModelId, setOverrideModelId] = useState('');

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [configData, providersData, overridesData] = await Promise.all([
        getLLMConfig(),
        getLLMProviders(),
        getAgentOverrides()
      ]);
      
      setConfig(configData);
      setProviders(providersData);
      setOverrides(overridesData);
      
      // Populate form if config exists
      if (configData) {
        setSelectedProvider(configData.provider);
        setModelId(configData.model_id);
        setBaseUrl(configData.base_url || '');
        setApiVersion(configData.api_version || '');
      } else if (providersData.length > 0) {
        // Set defaults from first provider
        setSelectedProvider(providersData[0].id);
        if (providersData[0].models.length > 0) {
          setModelId(providersData[0].models[0]);
        }
      }
    } catch (err) {
      setError('Failed to load LLM configuration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Get current provider info
  const currentProvider = providers.find(p => p.id === selectedProvider);

  // Handle provider change
  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const provider = providers.find(p => p.id === providerId);
    if (provider && provider.models.length > 0) {
      setModelId(provider.models[0]);
    }
    setBaseUrl('');
    setApiVersion('');
  };

  // Test configuration
  const handleTest = async () => {
    if (!apiKey && !config?.api_key_masked) {
      setError('API key is required');
      return;
    }

    setTesting(true);
    setError(null);
    setSuccess(null);

    try {
      const testConfig: LLMConfigCreate = {
        provider: selectedProvider as any,
        model_id: modelId,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
        api_version: apiVersion || undefined
      };

      const result: ValidationResult = await validateLLMConfig(testConfig);
      
      if (result.valid) {
        setSuccess('Configuration is valid! You can now save it.');
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('Validation failed. Please check your configuration.');
    } finally {
      setTesting(false);
    }
  };

  // Save configuration
  const handleSave = async () => {
    if (!apiKey && !config?.api_key_masked) {
      setError('API key is required');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const newConfig: LLMConfigCreate = {
        provider: selectedProvider as any,
        model_id: modelId,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
        api_version: apiVersion || undefined,
        is_active: true
      };

      await setLLMConfig(newConfig);
      setSuccess('LLM configuration saved successfully!');
      await loadData();
      setApiKey(''); // Clear API key from form after save
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  // Open override dialog
  const openOverrideDialog = (agentName: AgentName) => {
    setSelectedAgent(agentName);
    const existing = overrides.find(o => o.agent_name === agentName);
    setOverrideModelId(existing?.llm_config?.model_id || modelId);
    setOverrideDialogOpen(true);
  };

  // Save agent override
  const handleSaveOverride = async () => {
    if (!selectedAgent) return;

    try {
      // Find or create config for this override
      const overrideConfig: LLMConfigCreate = {
        provider: selectedProvider as any,
        model_id: overrideModelId,
        api_key: apiKey || config?.api_key_masked || undefined,
        base_url: baseUrl || undefined,
        api_version: apiVersion || undefined,
        is_active: true
      };

      // First save the config, then set override
      const savedConfig = await setLLMConfig(overrideConfig);
      await setAgentOverride(selectedAgent, {
        llm_config_id: savedConfig.id,
        is_active: true
      });

      setSuccess(`Override set for ${AGENT_LABELS[selectedAgent]}`);
      await loadData();
      setOverrideDialogOpen(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to set override');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        LLM Provider Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure your AI provider and model settings. You can use Anthropic Claude, OpenAI, 
        Google Gemini, Azure OpenAI, or local models via Ollama.
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

      {/* Provider Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Provider
          </Typography>
          <RadioGroup
            value={selectedProvider}
            onChange={(e) => handleProviderChange(e.target.value)}
          >
            <Box display="flex" flexWrap="wrap" gap={2}>
              {providers.map((provider) => (
                <FormControlLabel
                  key={provider.id}
                  value={provider.id}
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle2">{provider.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {provider.models.slice(0, 3).join(', ')}
                        {provider.models.length > 3 && '...'}
                      </Typography>
                    </Box>
                  }
                />
              ))}
            </Box>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Configuration Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Configuration Details
          </Typography>

          <Box display="flex" flexDirection="column" gap={2}>
            {/* Model Selection */}
            <FormControl fullWidth>
              <InputLabel>Model</InputLabel>
              <Select
                value={modelId}
                label="Model"
                onChange={(e) => setModelId(e.target.value)}
              >
                {currentProvider?.models.map((model) => (
                  <MenuItem key={model} value={model}>
                    {model}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* API Key */}
            <TextField
              label="API Key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={config?.api_key_masked || 'Enter your API key'}
              helperText={config?.api_key_masked && `Current: ${config.api_key_masked}`}
              fullWidth
            />

            {/* Base URL (for Azure/Ollama) */}
            {(selectedProvider === 'azure_openai' || selectedProvider === 'ollama') && (
              <TextField
                label="Base URL"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder={selectedProvider === 'ollama' ? 'http://localhost:11434' : 'https://your-resource.openai.azure.com'}
                helperText={selectedProvider === 'ollama' ? 'Ollama server URL' : 'Azure OpenAI endpoint'}
                fullWidth
              />
            )}

            {/* API Version (for Azure) */}
            {selectedProvider === 'azure_openai' && (
              <TextField
                label="API Version"
                value={apiVersion}
                onChange={(e) => setApiVersion(e.target.value)}
                placeholder="2024-02-01"
                helperText="Azure API version"
                fullWidth
              />
            )}

            {/* Action Buttons */}
            <Box display="flex" gap={2} mt={2}>
              <Button
                variant="outlined"
                onClick={handleTest}
                disabled={testing || saving}
                startIcon={testing ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              >
                Test Connection
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={testing || saving}
                startIcon={saving ? <CircularProgress size={20} /> : null}
              >
                Save Configuration
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Per-Agent Overrides */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Per-Agent Model Overrides
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Use different models for specific agents. For example, use a faster model for News Agent 
            and a more capable model for Pitchbook generation.
          </Typography>

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Agent</TableCell>
                <TableCell>Current Model</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(Object.keys(AGENT_LABELS) as AgentName[]).map((agentName) => {
                const override = overrides.find(o => o.agent_name === agentName);
                return (
                  <TableRow key={agentName}>
                    <TableCell>{AGENT_LABELS[agentName]}</TableCell>
                    <TableCell>
                      {override?.llm_config?.model_id || config?.model_id || 'Default'}
                    </TableCell>
                    <TableCell>
                      {override?.is_active ? (
                        <Chip size="small" color="success" label="Override Active" />
                      ) : (
                        <Chip size="small" variant="outlined" label="Using Default" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<SettingsIcon />}
                        onClick={() => openOverrideDialog(agentName)}
                      >
                        {override?.is_active ? 'Change' : 'Set Override'}
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Override Dialog */}
      <Dialog open={overrideDialogOpen} onClose={() => setOverrideDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Set Model Override for {selectedAgent && AGENT_LABELS[selectedAgent]}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Model</InputLabel>
              <Select
                value={overrideModelId}
                label="Model"
                onChange={(e) => setOverrideModelId(e.target.value)}
              >
                {currentProvider?.models.map((model) => (
                  <MenuItem key={model} value={model}>
                    {model}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              This agent will use {currentProvider?.label} with {overrideModelId}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOverrideDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveOverride}>
            Save Override
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LLMProviderConfig;
