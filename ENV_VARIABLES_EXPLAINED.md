# Environment Variables: Development vs Production

## The Confusion: .env Files vs Environment Variables

### ❌ Common Misconception
"I need a .env file for `os.getenv()` to work"

### ✅ Reality
`os.getenv()` reads **actual OS environment variables**, not .env files!

---

## 📚 Three Ways to Set Environment Variables

### **1. .env File (Development Only)**
```bash
# .env file
TAVILY_API_KEY=tvly-local-dev-key
MAX_RESULTS=10
```

```python
# Load .env into environment
from dotenv import load_dotenv
load_dotenv()  # Reads .env, sets os.environ["TAVILY_API_KEY"]

# Now os.getenv() works
import os
API_KEY = os.getenv("TAVILY_API_KEY")  # "tvly-local-dev-key"
```

**What load_dotenv() does:**
```python
# Simplified version
def load_dotenv():
    with open('.env') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key] = value  # Sets actual environment variable
```

### **2. Terminal/Shell (Development)**
```bash
# Windows
set TAVILY_API_KEY=tvly-key
python server.py

# Linux/Mac
export TAVILY_API_KEY=tvly-key
python server.py
```

```python
# No load_dotenv() needed!
import os
API_KEY = os.getenv("TAVILY_API_KEY")  # Works!
```

### **3. Kubernetes Secret (Production)**
```yaml
# Kubernetes Deployment
env:
  - name: TAVILY_API_KEY
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: TAVILY_API_KEY
```

```python
# No load_dotenv() needed!
# No .env file exists!
import os
API_KEY = os.getenv("TAVILY_API_KEY")  # Works!
```

---

## 🐳 Docker + Kubernetes: How It Works

### **Dockerfile (NO env vars set here)**
```dockerfile
FROM python:3.11-slim
COPY . .
RUN pip install -r requirements.txt

# ❌ WRONG: Don't hardcode secrets
# ENV TAVILY_API_KEY=tvly-key

CMD ["python", "server.py"]
```

### **Kubernetes Deployment YAML**
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: web-search
        image: myregistry/web-search:v1.0
        env:  # ← Kubernetes injects these
        - name: TAVILY_API_KEY
          valueFrom:
            secretKeyRef:
              name: web-search-secrets
              key: TAVILY_API_KEY
        - name: MAX_RESULTS
          value: "10"
```

### **What Happens at Pod Startup:**

1. **Kubernetes reads Secret:**
   ```
   Secret: web-search-secrets
   Data: { TAVILY_API_KEY: "tvly-abc123" }
   ```

2. **Kubernetes starts container with env vars:**
   ```bash
   docker run \
     -e TAVILY_API_KEY=tvly-abc123 \
     -e MAX_RESULTS=10 \
     myregistry/web-search:v1.0
   ```

3. **Container process sees environment variables:**
   ```bash
   # Inside container
   $ env | grep TAVILY
   TAVILY_API_KEY=tvly-abc123
   ```

4. **Python code reads them:**
   ```python
   import os
   key = os.getenv("TAVILY_API_KEY")  # "tvly-abc123" ✅
   ```

---

## 🔍 Verification: How to Check

### **Local Development**
```python
# server.py
import os
print("Environment variables:")
print(f"TAVILY_API_KEY: {os.getenv('TAVILY_API_KEY', 'NOT SET')}")
print(f"MAX_RESULTS: {os.getenv('MAX_RESULTS', 'NOT SET')}")
```

### **In Running Kubernetes Pod**
```bash
# Check env vars
kubectl exec -it web-search-pod -- env | grep TAVILY
# Output: TAVILY_API_KEY=tvly-abc123

# Check Python sees them
kubectl exec -it web-search-pod -- python3 -c "import os; print(os.getenv('TAVILY_API_KEY'))"
# Output: tvly-abc123
```

---

## 📋 Summary

| Method | .env File Needed? | load_dotenv() Needed? | Use Case |
|--------|-------------------|----------------------|----------|
| Local with .env | ✅ Yes | ✅ Yes | Development |
| Shell export | ❌ No | ❌ No | Development |
| Kubernetes | ❌ No | ❌ No | Production |

### **Key Takeaway:**
- `os.getenv()` reads **actual environment variables** (from `os.environ` dict)
- `.env` files are **just a convenience** for development
- `load_dotenv()` **reads .env file and sets os.environ**
- Kubernetes **sets os.environ directly** (no .env file involved)

### **Best Practice for Production Code:**
```python
# Optional .env support for dev, works without it in prod
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed (production)

# Works in both dev and prod!
import os
API_KEY = os.getenv("TAVILY_API_KEY")
```

---

## 🎯 Your Web Search MCP Flow

### **Development (Local Testing)**
```bash
# Create .env file
echo "TAVILY_API_KEY=tvly-test-key" > .env
echo "MAX_RESULTS=10" >> .env

# Run server
python server.py
# ✅ Works! Reads from .env
```

### **Production (Kubernetes)**
```bash
# 1. Configure via ARM API
POST /tools/{id}/configure
{
  "environment_variables": [
    {"name": "TAVILY_API_KEY", "value": "tvly-prod-key"}
  ]
}

# 2. Deploy
POST /tools/deploy { "tool_id": "{id}" }

# 3. GitHub Actions creates:
# - Kubernetes Secret with TAVILY_API_KEY=tvly-prod-key
# - Deployment that references the secret
# - Pod starts with env var injected

# 4. Python code in pod:
# os.getenv("TAVILY_API_KEY") → "tvly-prod-key"
# ✅ Works! No .env file in container!
```

**The magic:** Kubernetes makes env vars available to the process **before Python even starts**, so `os.getenv()` just works! 🎉
