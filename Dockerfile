FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY exposureguard_mcp ./exposureguard_mcp
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .

# MCP server speaks JSON-RPC over stdio; Glama will pipe stdin/stdout.
CMD ["python", "-m", "exposureguard_mcp"]
