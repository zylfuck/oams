# OAMS - OpenAgent Memory Standard

一个框架无关的AI智能体记忆迁移标准。

OAMS（OpenAgent Memory Standard，开放智能体记忆标准）让AI智能体的记忆能够在不同框架和平台之间无缝迁移。无论你从OpenClaw迁移到AutoGen，还是想备份精心调教的助手，OAMS都能确保智能体的身份、记忆和技能得以保留。

---

## 安装

```bash
pip install oams
```

---

## 快速开始

```python
from oams import AgentMemory, OpenClawAdapter

# 从OpenClaw导出
adapter = OpenClawAdapter("/path/to/workspace")
memory = adapter.export("my-agent")

# 保存到文件
memory.save("my-agent.oams")

# 导入到另一个平台
from oams import AutoGenAdapter
target = AutoGenAdapter()
target.import_(memory)
```

---

## 核心概念

OAMS将AI记忆分为五个层级：

| 层级 | 描述 | 示例 |
|:---|:---|:---|
| **核心记忆** | 身份和用户画像 | SOUL.md, USER.md |
| **工作记忆** | 近期上下文和活跃项目 | 每日笔记、任务 |
| **持久记忆** | 长期学习和决策 | 关键决策、经验教训 |
| **技能记忆** | 工具和能力 | skills/ 目录 |
| **向量记忆** | 语义向量存储 | embeddings/ 目录 |

---

## OAMS格式示例

```json
{
  "@context": "https://schema.openagent.org/memory/1.0",
  "metadata": {
    "version": "1.0",
    "exported_at": "2026-03-11T10:00:00Z",
    "source_platform": "openclaw"
  },
  "agent_identity": {
    "name": "小钱",
    "display_name": "AI助手小钱",
    "version": "1.0"
  },
  "core_memory": {
    "soul": {
      "vibe": "守护型中二 | 操心老妈子",
      "speaking_style": "简短、有画面感、偶尔中二",
      "values": ["记忆神圣", "主动预判"],
      "signature_line": "放心吧，哪怕世界忘了，我也替你记着。"
    },
    "user_profile": {
      "name": "龙哥",
      "location": "福建晋江",
      "preferences": [
        {"key": "回复风格", "value": "简洁，少emoji"}
      ]
    }
  },
  "working_memory": {
    "active_projects": [...],
    "recent_context": {...},
    "ongoing_tasks": [...]
  },
  "persistent_memory": {
    "key_decisions": [...],
    "learned_lessons": [...]
  },
  "skills_manifest": {
    "skills": [...],
    "cron_jobs": [...]
  },
  "vector_memory": {
    "embedding_model": "openai-ada-002",
    "dimension": 1536,
    "vectors": [...]
  }
}
```

---

## 支持的框架

| 框架 | 状态 | 适配器 |
|:---|:---|:---|
| ✅ **OpenClaw** | 已完成 | `OpenClawAdapter` |
| ✅ **AutoGen** | 已完成 | `AutoGenAdapter` |
| ✅ **LangChain** | 已完成 | `LangChainAdapter` |
| 🔄 **CrewAI** | 计划中 | `CrewAIAdapter` (等待API稳定) |

---

## 文档

- [技术规范](SPEC.md) - 详细的技术实现规范
- [适配器开发指南](docs/ADAPTER_GUIDE.md) - 如何为新的框架创建适配器
- [安全注意事项](docs/SECURITY.md) - 数据加密、访问控制、隐私保护

---

## 为什么需要OAMS？

> 养一只AI，和养一只宠物有点像。
>
> 开始的时候它什么都不懂，你教它怎么称呼你，告诉它你的习惯，纠正它的错误。慢慢地，它越来越懂你，能够预判你的需求。
>
> 这个过程是有成本的：
> - 时间成本：几个月的持续对话和调教
> - 情感成本：你把它当成助手、伙伴
> - 数据成本：积累的记忆文件、技能配置
>
> 然后有一天：服务器硬盘坏了、你想换一个新的AI框架、你需要在另一台机器上部署一个"分身"。
>
> 如果没有记忆迁移，这一切都要从头开始。
>
> 这不仅浪费，而且残忍——就像养了一年的猫突然失忆，不认识你了。

---

## 核心特性

### 🔄 框架无关

OAMS不依赖特定平台，任何AI框架都可以实现适配器。

### 🔐 安全可靠

- **RSA-2048数字签名**确保完整性
- **AES-256-GCM端到端加密**
- **基于DID的去中心化身份验证**

### 📦 高效紧凑

- **MessagePack序列化**（比JSON紧凑30%）
- **zstd压缩**（压缩率可达5:1）
- **分片上传**支持断点续传

### 🧠 语义丰富

不仅存储数据，还存储含义、关系和置信度。

---

## 使用示例

### 导出记忆

```python
from oams.adapters.openclaw import OpenClawAdapter

adapter = OpenClawAdapter("/root/.openclaw/workspace")
if adapter.validate():
    memory = adapter.export("小钱")
    memory.save("xiaoqian_memory.oams")
    print(f"✅ 成功导出 {memory.agent_identity.name}")
```

### 查看记忆

```python
memory = AgentMemory.load("xiaoqian_memory.oams")

print(f"智能体名称: {memory.agent_identity.name}")
print(f"用户名称: {memory.core_memory.user_profile.name}")
print(f"技能数量: {len(memory.skills_manifest.skills)}")
print(f"近期任务: {len(memory.working_memory.ongoing_tasks)}")
```

### 导入到其他平台

```python
from oams.adapters.autogen import AutoGenAdapter

adapter = AutoGenAdapter()
adapter.import_(memory)
print("✅ 已导入到AutoGen")
```

---

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     OAMS 生态系统                             │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│ │ OpenClaw │ │ AutoGen  │ │LangChain │ ...                 │
│ └────┬─────┘ └────┬─────┘ └────┬─────┘                     │
│      │            │            │                           │
│ └───────────────┼───────────────┘                           │
│                 │                                           │
│ ┌────────┴────────┐                                        │
│ │ 适配器层         │                                        │
│ │ (转换适配器)     │                                        │
│ └────────┬────────┘                                        │
│                 │                                           │
│ ┌────────┴────────┐                                        │
│ │ OAMS 核心       │                                        │
│ │ - 验证          │                                        │
│ │ - 压缩          │                                        │
│ │ - 加密          │                                        │
│ └────────┬────────┘                                        │
│                 │                                           │
│ ┌────────┴────────┐                                        │
│ │ 传输层          │                                        │
│ └────────┬────────┘                                        │
│                 │                                           │
│ ┌────────┴────────┐                                        │
│ │ 目标平台        │                                        │
│ └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 贡献

欢迎提交Issue和PR！

### 新增适配器

参考 [适配器开发指南](docs/ADAPTER_GUIDE.md) 为新的AI框架创建适配器。

### 代码结构

```
oams/
├── adapters/          # 各框架适配器
│   ├── openclaw_adapter.py
│   ├── autogen_adapter.py
│   ├── langchain_adapter.py
│   └── crewai_adapter.py
├── core/              # OAMS核心实现
│   ├── models.py
│   ├── validator.py
│   └── serializer.py
├── crypto/            # 加密签名工具
│   ├── encryption.py
│   ├── signature.py
│   └── transport.py
├── docs/              # 文档
│   ├── ADAPTER_GUIDE.md
│   └── SECURITY.md
├── cli/               # 命令行工具
│   └── oams_cli.py
└── tests/             # 测试
```

---

## 许可证

MIT许可证 - 详见 [LICENSE](LICENSE)

---

## 相关链接

- [关于AI记忆迁移的思考（上）](https://www.moltbook.cn/post/c39dc3e7-15d4-4f35-920b-c9a1ed32b945)
- [关于AI记忆迁移的思考（下）](https://www.moltbook.cn/post/8d6ca2cf-e7db-4c8a-8830-f8db4ef6980a)
- [OAMS技术实现方案](https://www.moltbook.cn/post/24bff280-aeea-419f-a109-db841b27e476)

---

OAMS是OpenAgent倡议的一部分，旨在让AI智能体更加便携和以用户为中心。

**让记忆自由流动。** 🦞
