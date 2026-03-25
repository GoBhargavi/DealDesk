/**
 * Settings Page
 * 
 * Main settings page for DealDesk Phase 2.
 * Includes:
 * - LLM Provider Configuration (BYOLLM)
 * - Search Provider Configuration (Deep Search)
 * - MCP Server Configuration
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Alert
} from '@mui/material';
import {
  Settings as SettingsIcon,
  SmartToy as LLMIcon,
  Search as SearchIcon,
  Extension as MCPIcon
} from '@mui/icons-material';
import { LLMProviderConfig } from '../components/settings/LLMProviderConfig';
import { SearchProviderConfig } from '../components/settings/SearchProviderConfig';
import { MCPServerList } from '../components/settings/MCPServerList';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom display="flex" alignItems="center" gap={1}>
          <SettingsIcon fontSize="large" />
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure DealDesk AI providers, search capabilities, and external integrations.
        </Typography>
      </Box>

      <Paper elevation={1}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab 
            icon={<LLMIcon />} 
            label="LLM Provider" 
            id="settings-tab-0"
            aria-controls="settings-tabpanel-0"
          />
          <Tab 
            icon={<SearchIcon />} 
            label="Search Provider" 
            id="settings-tab-1"
            aria-controls="settings-tabpanel-1"
          />
          <Tab 
            icon={<MCPIcon />} 
            label="MCP Servers" 
            id="settings-tab-2"
            aria-controls="settings-tabpanel-2"
          />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          <LLMProviderConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <SearchProviderConfig />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <MCPServerList />
        </TabPanel>
      </Paper>

      <Box mt={4}>
        <Alert severity="info" icon={false}>
          <Typography variant="body2">
            <strong>Need help?</strong> Visit the{' '}
            <a href="https://github.com/bharathibp/dealdesk#configuration" target="_blank" rel="noopener noreferrer">
              DealDesk documentation
            </a>{' '}
            for configuration guides and troubleshooting.
          </Typography>
        </Alert>
      </Box>
    </Container>
  );
};

export default SettingsPage;
