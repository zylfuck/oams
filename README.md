# OAMS - OpenAgent Memory Standard

English | [中文](README.zh.md)

> A framework-agnostic standard for AI agent memory migration.

## Overview

OAMS (OpenAgent Memory Standard) enables seamless migration of AI agent memories across different frameworks and platforms. Whether you're moving from OpenClaw to AutoGen, or backing up your carefully tuned assistant, OAMS ensures your agent's identity, memories, and skills are preserved.

## Quick Start

```python
from oams import AgentMemory, OpenClawAdapter

# Export from OpenClaw
adapter = OpenClawAdapter("/path/to/workspace")
memory = adapter.export("my-agent")

# Save to file
memory.save("my-agent.oams")

# Import to another platform
from oams import AutoGenAdapter
target = AutoGenAdapter()
target.import_(memory)
```

## Core Concepts

### Memory Layers

| Layer | Description | Example |
|-------|-------------|---------|
| **Core Memory** | Identity and user profile | SOUL.md, USER.md |
| **Working Memory** | Recent context and active projects | Daily notes, tasks |
| **Persistent Memory** | Long-term learnings and decisions | Key decisions, lessons |
| **Skill Memory** | Tools and capabilities | skills/ directory |

### The OAMS Format

```json
{
  "@context": "https://schema.openagent.org/memory/1.0",
  "metadata": {
    "version": "1.0",
    "exported_at": "2026-03-11T10:00:00Z"
  },
  "agent_identity": {...},
  "core_memory": {...},
  "working_memory": {...},
  "persistent_memory": {...},
  "skills_manifest": {...}
}
```

## Installation

```bash
pip install oams
```

## Supported Platforms

- ✅ OpenClaw
- ✅ AutoGen (WIP)
- ✅ LangChain (WIP)
- 🔄 CrewAI (Planned)

## Documentation

- [Technical Specification](SPEC.md)
- [Adapter Development Guide](docs/ADAPTER_GUIDE.md)
- [Security Considerations](docs/SECURITY.md)

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*OAMS is part of the OpenAgent initiative to make AI agents more portable and user-centric.*
