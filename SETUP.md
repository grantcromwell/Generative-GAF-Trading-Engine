# Brainnet Setup Guide

## Virtual Environment Setup ✅

A project-wide virtual environment has been configured at `.venv/` using **Python 3.11.14**.

### Quick Start

```bash
# Navigate to project
cd /Users/gdove/Desktop/codebases/Brainnet

# Activate environment
source activate.sh

# Verify setup
python --version  # Should show Python 3.11.14
which python      # Should point to .venv/bin/python
```

### Auto-Activation

The virtual environment is configured to auto-activate in new zsh terminals via `~/.zshrc`. When you open a new terminal and navigate to the Brainnet directory, the environment will activate automatically.

## Running Brainnet

### Interactive GUI (Recommended)

```bash
brainnet gui
```

This launches the interactive terminal UI where you can:
- Select from crypto, futures, ETFs, and commodities
- Choose different timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- View detailed GAF analysis with confidence scores

### Single Analysis

```bash
# Analyze a specific symbol
brainnet run --symbol ES=F

# Or use the analyze command
brainnet analyze --symbol BTC-USD --interval 5m
```

### Continuous Trading Loop

```bash
# Run continuous analysis every 5 minutes
brainnet loop --symbol ES=F --interval 5m --delay 300
```

### ConvNeXt Neural Analysis

```bash
# Single ConvNeXt analysis
brainnet convnext --symbol ES=F --interval 5m

# ConvNeXt-only mode (skip LLM)
brainnet convnext --symbol BTC-USD --no-llm --device cuda

# Continuous ConvNeXt loop
brainnet convnext-loop --symbol ETH-USD --delay 300

# Show ConvNeXt model info
brainnet convnext-info
```

### WebSocket API Server

```bash
brainnet server --port 8000
```

## Available Commands

Run `brainnet --help` to see all available commands:

```
Commands:
  analyze        Run single analysis on a symbol
  convnext       Run ConvNeXt-enhanced GAF analysis
  convnext-info  Show ConvNeXt model information
  convnext-loop  Run continuous ConvNeXt trading loop
  gui            Launch the terminal GUI selector
  loop           Run continuous trading loop
  run            Run a single analysis
  server         Start the API server
```

## Configuration

Configuration is managed via environment variables. Create a `.env` file in the project root:

```bash
# LM Studio/Ollama Configuration
OLLAMA_BASE_URL=http://127.0.0.1:1234
OLLAMA_MODEL=phi-3.5-mini-instruct
LLM_BACKEND=local

# Model Settings
AGENT_MAX_TOKENS=31000
AGENT_TEMPERATURE=0.1
USE_VISION=false

# Memory (pgvector - PostgreSQL with vector extension)
MEMORY_DB=pgvector
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=your_password
PGVECTOR_DB=brainnet

# Trading
CONFIDENCE_THRESHOLD=0.78
MAX_REFINEMENTS=3
```

## Dependencies Installed

The following packages are installed in the virtual environment:

### Core
- langgraph (multi-agent orchestration)
- mem0ai (memory management)
- pyts (GAF generation)
- yfinance (market data)
- openai (LLM client)

### ML/Neural Networks
- torch, torchvision (ConvNeXt)
- transformers (HuggingFace)
- scikit-learn, scipy

### Vector Storage
- pgvector (PostgreSQL vector extension)
- pymilvus, milvus-lite (alternative vector DB)

### Web/API
- fastapi, uvicorn (WebSocket server)
- click (CLI framework)

### Data Processing
- pandas, numpy, matplotlib
- pillow (image processing)

## Troubleshooting

### Import Errors

If you see import errors, make sure the virtual environment is activated:

```bash
source activate.sh
```

### Permission Errors

If you encounter permission errors with `.env` file, make sure it exists and is readable:

```bash
touch .env
chmod 644 .env
```

### Python Version Mismatch

The project requires Python 3.10+. The virtual environment uses Python 3.11.14. If you need to recreate it:

```bash
rm -rf .venv
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r lms/minah/requirements.txt
pip install -e lms/minah/
```

### LM Studio Not Running

If you get connection errors, make sure LM Studio or Ollama is running:

```bash
# Check if server is running
curl http://localhost:1234/v1/models
```

## Project Structure

```
Brainnet/
├── .venv/                  # Virtual environment (Python 3.11.14)
├── activate.sh             # Activation script
├── lms/
│   ├── minah/             # Primary implementation
│   ├── carter/            # Alternative implementation
│   └── banis/             # Another variant
├── models/                 # Model weights storage
├── scripts/
│   └── brain              # Quick launcher script
└── shared/                 # Shared code
```

## Performance Metrics

Based on backtesting (see `REPORT.md`):

| Strategy | Symbol  | Sharpe Ratio | Total Return |
|----------|---------|--------------|--------------|
| Banis    | ES=F    | 0.61         | +18.88%      |
| Carter   | ETH-USD | 0.02         | -17.48%      |
| Minah    | BTC-USD | -0.16        | -9.72%       |

The ES futures strategy (Banis) shows the best risk-adjusted performance.

## Next Steps

1. **Configure LM Studio**: Download and start LM Studio with `phi-3.5-mini-instruct` model
2. **Set up pgvector** (optional): For persistent memory across sessions
3. **Run your first analysis**: `brainnet gui` or `brainnet run --symbol ES=F`
4. **Explore ConvNeXt**: Try neural pattern recognition with `brainnet convnext`

## Support

For issues or questions:
- Check the main `README.md` for detailed documentation
- Review `REPORT.md` for performance analysis
- Examine example scripts in `lms/minah/examples/`

