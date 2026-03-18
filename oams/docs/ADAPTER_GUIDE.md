# ADAPTER_GUIDE.md
# OAMS适配器开发指南

本文档指导开发者如何为新的AI框架创建OAMS适配器。

---

## 概述

OAMS适配器是连接特定AI框架与OAMS标准格式的桥梁。每个适配器需要实现：

1. **导出(Export)**：将框架特定格式转换为OAMS
2. **导入(Import)**：将OAMS转换回框架特定格式
3. **验证(Validate)**：检查源数据完整性

---

## 快速开始

### 1. 创建适配器文件

在 `oams/adapters/` 目录下创建新文件：

```python
# your_framework_adapter.py
from oams.adapters.base import BaseAdapter
from oams.core import AgentMemory, AgentIdentity, CoreMemory, ...

class YourFrameworkAdapter(BaseAdapter):
    def __init__(self, config_path: str):
        self.config_path = config_path
    
    def validate(self) -> bool:
        # 检查源数据完整性
        pass
    
    def export(self) -> AgentMemory:
        # 导出为OAMS格式
        pass
    
    def import_(self, oams: AgentMemory) -> None:
        # 从OAMS格式导入
        pass
```

### 2. 继承BaseAdapter

```python
from abc import ABC, abstractmethod
from oams.core import AgentMemory

class BaseAdapter(ABC):
    @abstractmethod
    def export(self) -> AgentMemory:
        """导出为OAMS格式"""
        pass
    
    @abstractmethod
    def import_(self, oams: AgentMemory) -> None:
        """从OAMS格式导入"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """验证源数据完整性"""
        pass
```

---

## 核心组件映射

### 身份标识 (AgentIdentity)

| OAMS字段 | 常见来源 | 说明 |
|:---|:---|:---|
| name | Agent名称 | 唯一标识符 |
| display_name | 显示名称 | 人类可读 |
| description | 描述 | 简短说明 |
| version | 版本 | 语义化版本 |
| owner_verification | 所有者信息 | 验证方式 |

**示例**：
```python
def _parse_identity(self) -> Dict:
    config = self._load_config()
    return {
        'name': config.get('agent_name', 'Unknown'),
        'display_name': config.get('display_name', ''),
        'description': config.get('description', ''),
        'version': config.get('version', '1.0'),
        'owner_verification': {
            'method': 'email',
            'email': config.get('owner_email', '')
        }
    }
```

### 灵魂定义 (SoulDefinition)

提取框架的"性格"定义：

| OAMS字段 | 提取策略 | 示例来源 |
|:---|:---|:---|
| vibe | 工作模式描述 | system prompt |
| speaking_style | 语言风格指令 | prompt templates |
| signature_line | 标志性语句 | 第一句指令 |
| values | 约束/价值观 | "Always... Never..." |

**提取技巧**：
```python
def _parse_soul(self) -> SoulDefinition:
    system_msg = self._get_system_message()
    
    soul = SoulDefinition()
    soul.vibe = system_msg[:200]  # 前200字符
    
    # 提取标志性语句（第一句话）
    soul.signature_line = system_msg.split('.')[0]
    
    # 提取约束条件
    import re
    constraints = re.findall(
        r'(Always|Never|Do not)\s+(.+?)\.',
        system_msg
    )
    soul.values = [f"{c[0]} {c[1]}" for c in constraints]
    
    return soul
```

### 用户画像 (UserProfile)

```python
def _parse_user_profile(self) -> UserProfile:
    profile = UserProfile()
    
    # 从用户配置读取
    user_config = self._load_user_config()
    profile.name = user_config.get('name', '')
    profile.location = user_config.get('location', '')
    profile.timezone = user_config.get('timezone', '')
    
    # 从偏好设置读取
    for key, value in user_config.get('preferences', {}).items():
        profile.preferences.append(Preference(
            key=key,
            value=value,
            source='explicit',
            confidence=1.0
        ))
    
    return profile
```

### 工作记忆 (WorkingMemory)

| OAMS字段 | 框架对应 | 提取方法 |
|:---|:---|:---|
| active_projects | 活跃对话/任务 | 最近打开的sessions |
| recent_context | 近期上下文 | 最近N条消息 |
| ongoing_tasks | 进行中的任务 | TODO列表 |

**示例**：
```python
def _parse_working_memory(self) -> WorkingMemory:
    working = WorkingMemory()
    
    # 加载最近对话
    recent_chats = self._load_chat_history(days=7)
    working.recent_context = {
        'last_7_days': [
            {
                'role': msg.get('role'),
                'content': msg.get('content')[:200]
            }
            for msg in recent_chats[-20:]  # 最近20条
        ]
    }
    
    # 加载活跃项目
    for project in self._load_active_projects():
        working.active_projects.append(Project(
            id=project['id'],
            name=project['name'],
            status=project['status'],
            last_updated=datetime.fromisoformat(project['updated']),
            key_files=project.get('files', [])
        ))
    
    return working
```

### 技能清单 (SkillsManifest)

```python
def _parse_skills(self) -> SkillsManifest:
    manifest = SkillsManifest()
    
    # 从配置读取工具定义
    tools = self._load_tools_config()
    
    for tool in tools:
        manifest.skills.append(SkillConfig(
            name=tool['name'],
            version=tool.get('version', '1.0'),
            location=f"tools/{tool['name']}",
            config_hash=self._compute_hash(tool),
            customization=tool.get('parameters', {}),
            enabled=tool.get('enabled', True)
        ))
    
    # 读取定时任务
    for job in self._load_cron_jobs():
        manifest.cron_jobs.append(CronJob(
            name=job['name'],
            schedule=job['cron'],
            enabled=job.get('enabled', True),
            last_run=job.get('last_run')
        ))
    
    return manifest
```

---

## 常见问题

### Q1: 如何处理框架特有的数据？

**方案A**: 存入 `metadata` 字段
```python
memory.metadata.framework_specific = {
    'custom_field': value
}
```

**方案B**: 使用 `custom_data` 扩展
```python
# 在核心类中添加扩展字段
@dataclass
class CoreMemory:
    soul: SoulDefinition
    user_profile: UserProfile
    custom_data: Dict = field(default_factory=dict)  # 框架特有数据
```

### Q2: 如何处理大型向量数据库？

**分批导出**：
```python
def _parse_vector_memory(self) -> VectorMemory:
    vector_memory = VectorMemory()
    
    # 只导出元数据，不导出全部向量
    vector_memory.embedding_model = 'openai-ada-002'
    vector_memory.dimension = 1536
    vector_memory.vectors = []  # 空向量列表
    vector_memory.index_metadata = {
        'total_vectors': self._count_vectors(),
        'exported': False,
        'note': 'Vectors too large, export separately'
    }
    
    return vector_memory
```

### Q3: 如何处理加密/敏感数据？

**标记敏感字段**：
```python
from oams.crypto import MemoryEncryption

def export(self) -> AgentMemory:
    memory = AgentMemory(...)
    
    # 加密敏感信息
    if self.has_sensitive_data():
        memory.metadata.encryption_algo = 'aes-256-gcm'
        memory.core_memory.user_profile = self._encrypt_sensitive(
            memory.core_memory.user_profile
        )
    
    return memory
```

---

## 测试清单

创建适配器后，验证以下场景：

- [ ] **空配置处理**：优雅处理缺失的配置文件
- [ ] **最小导出**：即使只有部分数据也能导出
- [ ] **完整导出**：所有组件都能正确导出
- [ ] **数据验证**：验证导出的OAMS符合schema
- [ ] **往返测试**：导出→导入→再导出，数据一致
- [ ] **错误处理**：损坏的源数据返回清晰错误

**测试代码模板**：
```python
def test_adapter():
    adapter = YourFrameworkAdapter(
        config_path="./test_config.json"
    )
    
    # 验证
    assert adapter.validate() == True
    
    # 导出
    memory = adapter.export("test_agent")
    assert memory.agent_identity.name == "test_agent"
    
    # 保存
    with open("test.oams", 'w') as f:
        json.dump(memory.to_dict(), f)
    
    # 导入
    with open("test.oams", 'r') as f:
        loaded = AgentMemory.from_dict(json.load(f))
    
    adapter.import_(loaded)
    
    print("✅ 所有测试通过")

if __name__ == "__main__":
    test_adapter()
```

---

## 最佳实践

1. **渐进式实现**
   - 先实现export()，能导出就算成功
   - 再实现import()，支持双向迁移
   - 最后完善validate()和错误处理

2. **保持简单**
   - 不要过度设计
   - 优先覆盖80%的常见场景
   - 边缘案例可以后续迭代

3. **文档化假设**
   - 记录框架版本要求
   - 说明配置文件的预期格式
   - 提供示例配置文件

4. **社区贡献**
   - 提交PR到主仓库
   - 添加单元测试
   - 更新支持矩阵

---

## 参考实现

查看现有适配器获取灵感：

- [OpenClaw适配器](openclaw_adapter.py) - 基于文件系统的配置
- [AutoGen适配器](autogen_adapter.py) - 基于Python配置
- [LangChain适配器](langchain_adapter.py) - 多组件组合

---

## 获取帮助

遇到问题？

1. 查看 [GitHub Issues](https://github.com/zylfuck/oams/issues)
2. 参考 [SPEC.md](../SPEC.md) 技术规范
3. 在 [Moltcn社区](https://www.moltbook.cn) 讨论
