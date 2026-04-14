# RelationshipOS Benchmark

This folder contains two benchmark entrypoints:

- `python -m benchmarks`
  General-purpose benchmark runner for internal experiments.
- `python -m benchmarks.official_edge_demo`
  Official investor-facing edge benchmark runner.

## Official External Benchmark

The current official benchmark path is the edge-focused demo subset:

- Runtime profile: `edge_desktop_4b`
- Event store: `memory`
- Baseline: `MiniMax M2-her`
- Memory baseline: `MiniMax M2-her + Mem0 OSS`
- System: `RelationshipOS`

Official suites:

- `factual_recall_lite`
- `cross_user_attribution`
- `latency_budget`

This is the benchmark we use for demos and investor conversations because it is:

- easy to reproduce
- isolated from local Postgres history
- aligned with the strongest edge-ready product value

## Environment

System arm:

```bash
export RELATIONSHIP_OS_LLM_BACKEND=litellm
export RELATIONSHIP_OS_LLM_MODEL=openai/llama-3-1-8b-instruct
export RELATIONSHIP_OS_LLM_API_BASE=https://api.apiyi.com/v1
export RELATIONSHIP_OS_LLM_API_KEY=...
```

Official MiniMax benchmark chat:

```bash
export BENCHMARK_CHAT_PROVIDER=minimax
export BENCHMARK_CHAT_MODEL=M2-her
export BENCHMARK_CHAT_API_BASE=https://api.minimax.io
export BENCHMARK_CHAT_API_KEY=...
```

Optional judge override:

```bash
export BENCHMARK_JUDGE_MODEL=openai/llama-3-1-8b-instruct
export BENCHMARK_JUDGE_API_BASE=https://api.apiyi.com/v1
export BENCHMARK_JUDGE_API_KEY=...
```

Mem0 local settings:

```bash
export BENCHMARK_MEM0_ENABLED=true
export BENCHMARK_MEM0_EMBED_MODEL=intfloat/multilingual-e5-small
export BENCHMARK_MEM0_EMBED_DIMS=384
export BENCHMARK_MEM0_QDRANT_PATH=benchmark_results/.mem0/qdrant
```

## Official Run

One command to start a clean server, run the official edge benchmark, and generate the latest report bundle:

```bash
uv run python -m benchmarks.official_edge_demo

The official runner loads `.env` first and then applies any shell overrides, so you can keep local keys in `.env` and still override them per run when needed.
```

The runner will:

- launch `RelationshipOS` with `RELATIONSHIP_OS_EVENT_STORE_BACKEND=memory`
- force `RELATIONSHIP_OS_RUNTIME_PROFILE=edge_desktop_4b`
- run the official suites with `--timeout 300`
- write timestamped results into `benchmark_results/official_edge_demo/`
- write stable copies into `benchmark_results/official_edge_demo/latest/`

Stable latest files:

- `benchmark_results/official_edge_demo/latest/latest.json`
- `benchmark_results/official_edge_demo/latest/latest.md`
- `benchmark_results/official_edge_demo/latest/latest.html`
- `benchmark_results/official_edge_demo/latest/latest_中文复盘.md`

## Internal Experimental Runs

For ad-hoc runs, use the generic runner:

```bash
PYTHONPATH=src uv run python -m benchmarks \
  --suite deep_memory,emotional,proactive_governance \
  --languages en \
  --max-cases-per-suite 1
```

## Result Layout

- `benchmarks/`
  Benchmark code
- `benchmark_results/`
  Current official and recent benchmark outputs
- `benchmark_archive_YYYYMMDD/`
  Archived historical benchmark runs

## Notes

- Official external reporting uses the edge benchmark path, not the full-runtime/Postgres path.
- The official system demo model is `openai/llama-3-1-8b-instruct`.
- `qwen3-8b` remains useful for experiments, but it is not the official demo default.
