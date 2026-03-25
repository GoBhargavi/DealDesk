/**
 * Search Provider Configuration Component
 * 
 * Allows users to configure their search provider for Deep Search:
 * - Select provider (Tavily, Perplexity, Exa AI)
 * - Enter API key
 * - Configure max results and query limits
 * - Test connection before saving
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
  Slider,
  Switch,
  FormControlLabel as FormControlLabelSwitch,
  Alert,
  CircularProgress,
  Tooltip
} from '@mui/material';
import { 
  Search as SearchIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { SearchConfig, SearchConfigCreate, SearchProvider } from '../../types/settings';
import { getSearchConfig, setSearchConfig, testSearchProvider } from '../../api/settings';

const PROVIDER_INFO: Record<SearchProvider, { label: string; description: string }> = {
  tavily: {
    label: 'Tavily',
    description: 'AI-powered search engine optimized for LLM applications'
  },
  perplexity: {
    label: 'Perplexity',
    description: 'AI search with real-time information and citations'
  },
  exa: {
    label: 'Exa AI',
    description: 'Neural search for finding specific web content'
  }
};

export const SearchProviderConfig: React.FC = () => {
  const [config, setConfig] = useState<SearchConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [provider, setProvider] = useState<SearchProvider>('tavily');
  const [apiKey, setApiKey] = useState('');
  const [maxResults, setMaxResults] = useState(5);
  const [maxQueries, setMaxQueries] = useState(5);
  const [enableFullFetch, setEnableFullFetch] = useState(true);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const data = await getSearchConfig();
      setConfig(data);
      
      if (data) {
        setProvider(data.provider);
        setMaxResults(data.max_results_per_query);
        setMaxQueries(data.max_queries_per_task);
        setEnableFullFetch(data.enable_full_page_fetch);
      }
    } catch (err) {
      setError('Failed to load search configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await testSearchProvider();
      if (result.success) {
        setSuccess(`Test successful! Found ${result.result_count} results.`);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('Test failed. Please check your API key.');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const newConfig: SearchConfigCreate = {
        provider,
        api_key: apiKey || undefined,
        max_results_per_query: maxResults,
        max_queries_per_task: maxQueries,
        enable_full_page_fetch: enableFullFetch,
        is_active: true
      };

      await setSearchConfig(newConfig);
      setSuccess('Search configuration saved successfully!');
      await loadConfig();
      setApiKey('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
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
        Search Provider Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure web search for Deep Research. Deep Search finds relevant sources 
        across the web to ground AI responses in real data.
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
            Select Search Provider
          </Typography>
          <RadioGroup
            value={provider}
            onChange={(e) => setProvider(e.target.value as SearchProvider)}
          >
            <Box display="flex" flexDirection="column" gap={2}>
              {(Object.keys(PROVIDER_INFO) as SearchProvider[]).map((key) => (
                <FormControlLabel
                  key={key}
                  value={key}
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle2">{PROVIDER_INFO[key].label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {PROVIDER_INFO[key].description}
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
            Configuration
          </Typography>

          <Box display="flex" flexDirection="column" gap={3}>
            {/* API Key */}
            <TextField
              label="API Key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={config?.api_key_masked || `Enter your ${PROVIDER_INFO[provider].label} API key`}
              helperText={config?.api_key_masked && `Current: ${config.api_key_masked}`}
              fullWidth
            />

            {/* Max Results Slider */}
            <Box>
              <Typography gutterBottom>
                Max Results Per Query: {maxResults}
                <Tooltip title="Number of search results to fetch per query (1-10)">
                  <InfoIcon fontSize="small" sx={{ ml: 1, verticalAlign: 'middle', color: 'text.secondary' }} />
                </Tooltip>
              </Typography>
              <Slider
                value={maxResults}
                onChange={(_, value) => setMaxResults(value as number)}
                min={1}
                max={10}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            {/* Max Queries Slider */}
            <Box>
              <Typography gutterBottom>
                Max Queries Per Task: {maxQueries}
                <Tooltip title="Number of parallel search queries to run per research task (1-10)">
                  <InfoIcon fontSize="small" sx={{ ml: 1, verticalAlign: 'middle', color: 'text.secondary' }} />
                </Tooltip>
              </Typography>
              <Slider
                value={maxQueries}
                onChange={(_, value) => setMaxQueries(value as number)}
                min={1}
                max={10}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            {/* Enable Full Page Fetch */}
            <FormControlLabelSwitch
              control={
                <Switch
                  checked={enableFullFetch}
                  onChange={(e) => setEnableFullFetch(e.target.checked)}
                />
              }
              label={
                <Box>
                  <Typography variant="body2">Enable Full Page Content Fetching</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Fetches full page content for better synthesis (slower but more accurate)
                  </Typography>
                </Box>
              }
            />

            {/* Action Buttons */}
            <Box display="flex" gap={2} mt={2}>
              <Button
                variant="outlined"
                onClick={handleTest}
                disabled={testing || saving}
                startIcon={testing ? <CircularProgress size={20} /> : <SearchIcon />}
              >
                Test Search
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={testing || saving}
                startIcon={saving ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              >
                Save Configuration
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SearchProviderConfig;
