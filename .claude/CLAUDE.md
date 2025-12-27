# Brainnet - Hybrid Adaptive Trading System

## Project Overview

Brainnet is a production-ready quantitative trading platform that combines multiple AI paradigms for robust market prediction. The system uses Gramian Angular Field (GAF) pattern recognition, ConvNeXt-Tiny neural networks, and LLM-as-a-judge confidence calibration with persistent vector memory.

## Architecture

### Core Components

1. **Research Agent** (`agents/research.py`)
   - Generates GAF (Gramian Angular Field) images from time series data
   - Supports vision mode (images) and text mode (numerical features)
   - Creates 3-channel GAF matrices (GASF, GADF, volatility heatmap) for ConvNeXt
   - Extracts 13+ numerical features from GAF matrices

2. **Reasoning Agent** (`agents/reasoning.py`)
   - Implements Binary Symmetric Channel (BSC) model for confidence calibration
   - Confidence formula: `Confidence = 1 - H(ε)` where H is binary entropy
   - Makes trading decisions (long/short/flat) based on confidence threshold (default 0.78)
   - Supports ensemble confidence computation

3. **ConvNeXt Predictor** (`agents/convnext_predictor.py`)
   - Lightweight convolutional neural network (ConvNeXt-Tiny)
   - Processes 3-channel GAF images (224x224 RGB)
   - Multi-task prediction: regime, direction, volatility
   - Regime classes: trending, mean_reverting, volatile, quiet
   - Direction classes: bullish, bearish, neutral
   - Volatility classes: calm, normal, elevated, explosive

4. **Coding Agent** (`agents/coding.py`)
   - Generates trading strategies from natural language
   - Hot-reloads strategies at runtime

5. **Orchestrator** (`orchestrator/`)
   - LangGraph state machine with adaptive refinement loops
   - Workflow: `research → reasoning → (conditional) refine → research` (loop)
   - Conditional routing based on confidence threshold
   - Maximum 3 refinement iterations by default

6. **Memory Manager** (`core/memory.py`)
   - Primary: pgvector (PostgreSQL with vector extension) + Mem0
   - Alternative: Milvus (local milvus-lite)
   - Fallback: SQLite
   - Stores trade outcomes, patterns, and context for similarity search
   - Uses HNSW indexes for fast approximate nearest neighbor search

### Workflow

```
Input Data → Research Agent (GAF generation) → Reasoning Agent (BSC confidence)
                                                      ↓
                                            Confidence < 0.78?
                                                      ↓
                                            Yes → Refinement Node (memory context)
                                                      ↓
                                            Research Agent (re-analysis)
                                                      ↓
                                            Reasoning Agent (re-evaluate)
                                                      ↓
                                            Final Decision (long/short/flat)
```

## Project Structure

```
Brainnet/
├── lms/                          # Language Model Systems (monorepo)
│   ├── banis/                     # Base implementation
│   ├── carter/                    # Phi-3.5-Vision via NVIDIA NIM (ETHUSDT-PERP)
│   └── minah/                     # Phi-3.5-Mini local inference (ES=F futures) ⭐ Main
│       ├── src/brainnet/
│       │   ├── agents/            # Research, Reasoning, Coding, ConvNeXt agents
│       │   ├── core/              # Config, Memory (pgvector/Milvus), Knowledge
│       │   ├── orchestrator/      # LangGraph workflow orchestration
│       │   ├── services/          # CLI, TUI, Web GUI, Market data, Coinglass
│       │   └── training/          # Model training utilities
│       ├── examples/              # Usage examples
│       ├── notebooks/             # Training notebooks
│       └── tests/                 # Unit and integration tests
├── scripts/                       # CLI wrappers (brain, carter)
├── shared/                        # Shared utilities
└── models/                        # Model artifacts storage
```

## Key Files

### Configuration
- **`lms/minah/src/brainnet/core/config.py`**: Central configuration
  - `BrainnetConfig`: LLM, memory, trading settings
  - `ConvNeXtConfig`: Neural network configuration
  - `PgVectorConfig`: PostgreSQL + pgvector settings
  - Environment variable loading via `load_config()`

### Agents
- **`lms/minah/src/brainnet/agents/base.py`**: 
  - `Phi35MiniClient`: Unified LLM client (LM Studio/Ollama/Azure/HF)
  - `BaseAgent`: Base class for all agents
  - Supports 31K token context window

- **`lms/minah/src/brainnet/agents/research.py`**: 
  - GAF image/feature generation
  - 3-channel GAF for ConvNeXt (RGB: GASF/GADF/heatmap)

- **`lms/minah/src/brainnet/agents/reasoning.py`**: 
  - BSC confidence calibration
  - Trading decision logic

- **`lms/minah/src/brainnet/agents/convnext_predictor.py`**: 
  - ConvNeXt-Tiny inference
  - Multi-task prediction (regime/direction/volatility)

### Orchestration
- **`lms/minah/src/brainnet/orchestrator/graph.py`**: 
  - LangGraph state machine
  - `TradingState`: TypedDict for workflow state
  - Nodes: research, reasoning, refine, finalize
  - Conditional edges based on confidence

- **`lms/minah/src/brainnet/orchestrator/router.py`**: 
  - High-level supervisor
  - `Router.trigger()`: Main entry point for trading workflow

### Services
- **`lms/minah/src/brainnet/services/main.py`**: 
  - CLI entrypoint with Click commands
  - FastAPI WebSocket server
  - Commands: `gui`, `analyze`, `loop`, `convnext`, `server`

- **`lms/minah/src/brainnet/services/engine.py`**: 
  - Core trading loop logic
  - `run_single_analysis()`, `run_trading_loop()`, `run_convnext_analysis()`
  - Ensemble logic combining ConvNeXt + LLM

- **`lms/minah/src/brainnet/services/tui.py`**: 
  - Interactive terminal UI
  - Paginated markets, multi-timeframe analysis

- **`lms/minah/src/brainnet/services/coinglass.py`**: 
  - Coinglass API client for derivatives data
  - Funding rates, long/short ratios

### Memory
- **`lms/minah/src/brainnet/core/memory.py`**: 
  - `MemoryManager`: Mem0 + pgvector integration
  - SQLite fallback
  - HNSW index creation for fast similarity search

- **`lms/minah/src/brainnet/core/memory_milvus.py`**: 
  - Milvus integration (alternative vector database)

## Dependencies

### Core
- `langgraph>=0.0.40`: Multi-agent workflow orchestration
- `mem0ai>=0.0.20`: Persistent memory layer
- `pyts>=0.13.0`: Time series transformations (GAF)
- `yfinance>=0.2.36`: Market data retrieval
- `openai>=1.12.0`: LLM client (LM Studio/Ollama compatible)
- `fastapi>=0.109.0`: Web API server
- `psycopg2-binary>=2.9.9`: PostgreSQL driver
- `pgvector>=0.2.0`: Vector similarity search
- `torch>=2.1.0`, `torchvision>=0.16.0`: ConvNeXt neural network
- `pymilvus>=2.3.0`, `milvus-lite>=2.3.0`: Alternative vector database

### Training (optional)
- `transformers>=4.36.0`: Hugging Face models
- `datasets>=2.16.0`: Data loading
- `datasketch>=1.6.0`: MinHash deduplication

## Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_BACKEND=local                    # local, azure, hf
OLLAMA_BASE_URL=http://localhost:1234
OLLAMA_MODEL=phi-3.5-mini-instruct
LLM_API_KEY=                         # For Azure/HF
AGENT_MAX_TOKENS=31000
AGENT_TEMPERATURE=0.1
USE_VISION=false                     # Enable vision mode

# Memory (pgvector - PostgreSQL)
MEMORY_DB=pgvector                  # pgvector, sqlite
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_USER=postgres
PGVECTOR_PASSWORD=your_password
PGVECTOR_DB=brainnet
PGVECTOR_COLLECTION=brainnet_memories
PGVECTOR_EMBEDDING_DIMS=768

# Memory (Milvus - alternative)
USE_MILVUS=false
MILVUS_URI=./milvus_lite.db
MILVUS_COLLECTION=trading_memory
MILVUS_EMBEDDING_DIMENSION=1536

# Trading Settings
CONFIDENCE_THRESHOLD=0.78            # BSC confidence threshold
MAX_REFINEMENTS=3                    # Max refinement iterations
YFINANCE_SYMBOL=ES=F

# ConvNeXt Settings
CONVNEXT_ENABLED=false
CONVNEXT_MODEL=convnext_tiny
CONVNEXT_DEVICE=auto                 # auto, cuda, mps, cpu
CONVNEXT_WEIGHTS=IMAGENET1K_V1
CONVNEXT_FINE_TUNED_PATH=            # Optional fine-tuned model path

# External APIs
NVIDIA_API_KEY=                      # For embeddings
COINGLASS_API_KEY=                   # For derivatives data
USE_COINGLASS=true
```

## Usage

### CLI Commands

```bash
# Interactive TUI
python -m brainnet.services.main gui

# Single analysis
python -m brainnet.services.main analyze --symbol ES=F

# Continuous trading loop
python -m brainnet.services.main loop --symbol ES=F --interval 5m --delay 300

# ConvNeXt analysis
python -m brainnet.services.main convnext --symbol ES=F --interval 5m

# ConvNeXt + LLM ensemble
python -m brainnet.services.main convnext --symbol ES=F --no-llm false

# WebSocket API server
python -m brainnet.services.main server --host 0.0.0.0 --port 8000

# ConvNeXt model info
python -m brainnet.services.main convnext-info
```

### Programmatic Usage

```python
from brainnet.orchestrator import Router
import yfinance as yf

# Initialize router
router = Router()

# Fetch data
data = yf.download("ES=F", period="1d", interval="5m", progress=False)

# Trigger workflow
result = router.trigger(data, symbol="ES=F")

print(f"Decision: {result['decision']}")
print(f"Confidence: {result['confidence']:.3f}")
print(f"Refinements: {result['refinements']}")
```

### ConvNeXt Ensemble

```python
from brainnet.agents import ResearchAgent, ConvNeXtPredictor

research = ResearchAgent()
convnext = ConvNeXtPredictor(device="auto")

# Generate 3-channel GAF
gaf_rgb = research.generate_gaf_3channel(price_series)

# Get predictions
prediction = convnext.predict(gaf_rgb)
print(f"Regime: {prediction.regime} ({prediction.regime_confidence:.1%})")
print(f"Direction: {prediction.direction} ({prediction.direction_confidence:.1%})")
print(f"Volatility: {prediction.volatility}")
```

## Key Concepts

### Gramian Angular Field (GAF)
- Transforms 1D time series into 2D matrices
- Preserves temporal dependencies
- Reveals cyclical patterns
- **GASF** (Gramian Angular Summation Field): Captures trend
- **GADF** (Gramian Angular Difference Field): Captures cycles
- **3-channel GAF**: RGB image combining GASF, GADF, and price heatmap

### Binary Symmetric Channel (BSC) Model
- Treats LLM judgment as a noisy communication channel
- Error probability ε estimated by LLM self-evaluation
- Confidence = 1 - H(ε) where H is binary entropy
- Provides mathematically grounded confidence intervals
- Default threshold: 0.78 (78%)

### Adaptive Refinement Loop
- When confidence < threshold, system:
  1. Queries memory for relevant historical context
  2. Enriches analysis prompt with memory
  3. Re-runs research with additional context
  4. Recomputes confidence
  5. Repeats up to MAX_REFINEMENTS times

### Memory-Augmented Learning
- Stores trade outcomes, patterns, and context in vector space
- Uses similarity search to retrieve relevant historical patterns
- Enables continuous improvement from past decisions
- Supports both pgvector (PostgreSQL) and Milvus backends

### Ensemble Methods
- Combines ConvNeXt neural predictions with LLM analysis
- Weighted ensemble score: `convnext_weight * convnext_score + llm_weight * llm_score`
- Default thresholds: >0.2 for long, <-0.2 for short

## Important Notes

1. **Not hierarchical recursion**: The system uses iterative refinement loops, not hierarchical recursion
2. **Sequential workflow**: Core workflow is sequential (research → reasoning → refine), with optional parallel ensemble
3. **No TD learning**: Uses memory-augmented learning via similarity search, not temporal difference methods
4. **Memory is primary**: pgvector (PostgreSQL) is the primary memory backend, Milvus is optional
5. **Single LLM architecture**: All agents use Phi-3.5-Mini (or Vision) exclusively—no model switching
6. **31K context window**: Full utilization of Phi-3.5's extended context for comprehensive analysis

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=brainnet --cov-report=html
```

## Troubleshooting

### Connection Refused (LLM)
- Ensure LM Studio/Ollama is running: `curl http://localhost:1234/v1/models`

### Memory Initialization Failed
- Check PostgreSQL is running and pgvector extension is installed
- Verify connection string in `.env`
- Falls back to SQLite if PostgreSQL unavailable

### Low Confidence Scores
- Check data quality (enough bars?)
- Increase `MAX_REFINEMENTS`
- Lower `CONFIDENCE_THRESHOLD` temporarily
- Review GAF features for data issues

### ConvNeXt Not Available
- Install PyTorch: `pip install torch torchvision`
- Check GPU availability: `python -m brainnet.services.main convnext-info`

## Development

### Project Variants
- **minah**: Main implementation (Phi-3.5-Mini, ES=F futures)
- **carter**: Phi-3.5-Vision via NVIDIA NIM (ETHUSDT-PERP)
- **banis**: Base implementation with DeepSeek-V3

### Scripts
- `scripts/brain`: Launcher for Minah (`brain` command)
- `scripts/carter`: Launcher for Carter variant

### Monorepo Structure
- Root `pyproject.toml`: Workspace configuration
- Each `lms/*/pyproject.toml`: Package-specific dependencies
- Shared utilities in `shared/`

## License

MIT

