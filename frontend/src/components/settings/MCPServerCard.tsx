/**
 * MCP Server Card Component
 * 
 * Displays a single MCP server configuration with:
 * - Connection status
 * - Tool count
 * - Toggle active/inactive
 * - Delete option
 */

import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Switch,
  Avatar
} from '@mui/material';
import {
  CheckCircle as ConnectedIcon,
  Cancel as DisconnectedIcon,
  Delete as DeleteIcon,
  Functions as ToolIcon
} from '@mui/icons-material';
import { MCPServerConfig, MCPServerType } from '../../types/settings';

const SERVER_TYPE_ICONS: Record<MCPServerType, string> = {
  sec_edgar: '📄',
  financial_data: '📈',
  news: '📰',
  slack: '💬',
  custom: '🔌'
};

const SERVER_TYPE_LABELS: Record<MCPServerType, string> = {
  sec_edgar: 'SEC EDGAR',
  financial_data: 'Financial Data',
  news: 'News',
  slack: 'Slack',
  custom: 'Custom'
};

interface MCPServerCardProps {
  server: MCPServerConfig;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export const MCPServerCard: React.FC<MCPServerCardProps> = ({ server, onToggle, onDelete }) => {
  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          {/* Left: Icon and Info */}
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: server.is_connected ? 'success.main' : 'grey.400' }}>
              {SERVER_TYPE_ICONS[server.server_type]}
            </Avatar>
            <Box>
              <Typography variant="h6" component="div">
                {server.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {SERVER_TYPE_LABELS[server.server_type]} • {server.endpoint_url}
              </Typography>
            </Box>
          </Box>

          {/* Right: Status and Actions */}
          <Box display="flex" alignItems="center" gap={1}>
            {/* Connection Status */}
            <Tooltip title={server.is_connected ? 'Connected' : 'Disconnected'}>
              <Chip
                icon={server.is_connected ? <ConnectedIcon /> : <DisconnectedIcon />}
                label={server.is_connected ? 'Connected' : 'Disconnected'}
                color={server.is_connected ? 'success' : 'default'}
                size="small"
                variant={server.is_connected ? 'filled' : 'outlined'}
              />
            </Tooltip>

            {/* Tool Count */}
            <Tooltip title={`${server.tool_count} tools available`}>
              <Chip
                icon={<ToolIcon />}
                label={server.tool_count}
                size="small"
                variant="outlined"
              />
            </Tooltip>

            {/* Active Toggle */}
            <Switch
              checked={server.is_active}
              onChange={() => onToggle(server.id)}
              inputProps={{ 'aria-label': 'Toggle server active' }}
            />

            {/* Delete Button */}
            <Tooltip title="Delete server">
              <IconButton
                size="small"
                color="error"
                onClick={() => onDelete(server.id)}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MCPServerCard;
