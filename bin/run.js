#!/usr/bin/env node
/**
 * ExposureGuard MCP Server launcher (npm wrapper)
 * Runs the Python MCP server via the installed package.
 */
const { spawn } = require('child_process');
const path = require('path');

const serverPath = path.join(__dirname, '..', 'server.py');

const proc = spawn('python3', [serverPath], {
  stdio: 'inherit',
  env: { ...process.env },
});

proc.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error('Error: python3 not found. Install Python 3.10+ and pip install mcp httpx');
    process.exit(1);
  }
  console.error('Error starting ExposureGuard MCP server:', err.message);
  process.exit(1);
});

proc.on('exit', (code) => {
  process.exit(code || 0);
});
