const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3737;
const API_KEY = process.env.ANTHROPIC_API_KEY || '';

if (!API_KEY) {
  console.error('\n❌  ANTHROPIC_API_KEY não definida.');
  console.error('   Rode: export ANTHROPIC_API_KEY=sk-ant-...\n');
  process.exit(1);
}

const MIME = {
  '.html': 'text/html',
  '.css':  'text/css',
  '.js':   'application/javascript',
  '.json': 'application/json',
  '.ico':  'image/x-icon',
};

function proxyAnthropic(req, res) {
  let body = '';
  req.on('data', c => body += c);
  req.on('end', () => {
    let parsedBody = {};
    try { parsedBody = JSON.parse(body); } catch(e) {}
    const hasMcp = Array.isArray(parsedBody.mcp_servers) && parsedBody.mcp_servers.length > 0;

    const headers = {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01',
    };
    if (hasMcp) headers['anthropic-beta'] = 'mcp-client-2025-04-04';

    const options = {
      hostname: 'api.anthropic.com',
      path: '/v1/messages',
      method: 'POST',
      headers,
    };

    const apiReq = https.request(options, apiRes => {
      res.writeHead(apiRes.statusCode, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      });
      apiRes.pipe(res);
    });

    apiReq.on('error', e => {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: e.message }));
    });

    apiReq.write(body);
    apiReq.end();
  });
}

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url);

  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    });
    return res.end();
  }

  // API proxy
  if (req.method === 'POST' && parsed.pathname === '/api/messages') {
    return proxyAnthropic(req, res);
  }

  // Static files
  let filePath = parsed.pathname === '/' ? '/index.html' : parsed.pathname;
  filePath = path.join(__dirname, filePath);

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      return res.end('Not found');
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`\n✅  Dashboard rodando em http://localhost:${PORT}\n`);
});
