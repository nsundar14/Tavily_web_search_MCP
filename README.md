# Web Search MCP Server - SSE Version

A production-ready web search MCP server demonstrating proper environment variable handling.

## Features

- ✅ **Native SSE Transport** - No supergateway needed
- ✅ **Multiple Search Providers**:
  - Tavily (premium, requires API key)
  - Serper (Google results, requires API key)
  - DuckDuckGo (free fallback, no key needed)
- ✅ **Environment Variable Demo** - Shows proper config injection
- ✅ **3 Tools**: search_web, search_news, get_search_config

## Environment Variables

### Required (Choose One):
- `TAVILY_API_KEY` - Tavily API key (get from https://tavily.com)
- `SERPER_API_KEY` - Serper API key (get from https://serper.dev)
- **Or neither** - Uses DuckDuckGo (free, no key)

### Optional:
- `MAX_RESULTS` - Maximum search results (default: 5)
- `TIMEOUT` - Request timeout in seconds (default: 10)
- `PORT` - Server port (default: 8000)

## Configuration Flow Test

This server is perfect for testing the configure → deploy flow:

### 1. Create Tool
```powershell
POST /api/v1/tools/create
{
  "repo_url": "https://github.com/[your-account]/web_search_mcp_sse",
  "tool_name": "web-search-test",
  "domain": "utilities"
}
```

### 2. Configure (Provide API Keys)
```powershell
GET /api/v1/tools/{tool_id}/configure
# Returns: discovered_variables (TAVILY_API_KEY, MAX_RESULTS, etc.)

POST /api/v1/tools/{tool_id}/configure
{
  "environment_variables": [
    {
      "name": "TAVILY_API_KEY",
      "value": "tvly-your-api-key-here",
      "required": false
    },
    {
      "name": "MAX_RESULTS",
      "value": "10",
      "required": false
    }
  ]
}
```

### 3. Deploy (Uses Saved Config)
```powershell
POST /api/v1/tools/deploy
{
  "tool_id": "{tool_id}",
  "container_port": "8000",
  "kubernetes_port": "30200"
}
```

## Docker Build vs Runtime

### ❌ Build Time (Image Creation)
```dockerfile
# NO secrets here!
FROM python:3.11-slim
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "server.py"]
```

### ✅ Runtime (Kubernetes Pod)
```yaml
env:
  - name: TAVILY_API_KEY
    valueFrom:
      secretKeyRef:
        name: web-search-secrets
        key: TAVILY_API_KEY
  - name: MAX_RESULTS
    value: "10"
```

## Testing Search Providers

### DuckDuckGo (No Config)
Works immediately without any API keys.

### Tavily (With Config)
1. Get API key from https://tavily.com
2. Configure tool with `TAVILY_API_KEY`
3. Deploy
4. Server automatically uses Tavily

### Check Active Provider
Call `get_search_config()` tool to see which provider is active.

## Available Tools

1. **search_web(query, max_results)** - Web search
2. **search_news(query, max_results)** - News search
3. **get_search_config()** - Show active provider and config

## Local Testing

```bash
# Without API key (uses DuckDuckGo)
python server.py

# With Tavily API key
export TAVILY_API_KEY=tvly-your-key
export MAX_RESULTS=10
python server.py
```

Server starts on `http://localhost:8000/sse`

## Production Deployment

Environment variables are:
1. ✅ Encrypted and stored in MongoDB (configure step)
2. ✅ Passed to GitHub Actions (deployment trigger)
3. ✅ Created as Kubernetes Secret (deployment step)
4. ✅ Injected into pod at runtime (pod startup)
5. ❌ **NEVER** baked into Docker image

This ensures secure, flexible configuration management! 🔐
