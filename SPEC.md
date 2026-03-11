# OAMS (OpenAgent Memory Standard) 技术实现方案 v1.0

> 本文档详细描述AI记忆迁移标准的技术实现细节，供开发者参考。

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    OAMS 生态系统                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ OpenClaw │    │ AutoGen  │    │ LangChain│   ...        │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘              │
│       │               │               │                     │
│       └───────────────┼───────────────┘                     │
│                       │                                      │
│              ┌────────┴────────┐                           │
│              │   Adapter Layer │                           │
│              │   (转换适配器)   │                           │
│              └────────┬────────┘                           │
│                       │                                      │
│              ┌────────┴────────┐                           │
│              │   OAMS Core     │                           │
│              │   - 验证        │                           │
│              │   - 压缩        │                           │
│              │   - 加密        │                           │
│              └────────┬────────┘                           │
│                       │                                      │
│              ┌────────┴────────┐                           │
│              │  Transport Layer │                           │
│              │  (传输协议)      │                           │
│              └────────┬────────┘                           │
│                       │                                      │
│              ┌────────┴────────┐                           │
│              │  Target Platform │                           │
│              └──────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心数据结构

### 2.1 完整Schema定义

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    CORE = "core"           # 核心身份
    WORKING = "working"     # 工作记忆
    PERSISTENT = "persistent"  # 长期记忆
    TRANSIENT = "transient"    # 瞬态记忆

class RelationshipType(Enum):
    OWNER = "owner"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"

@dataclass
class OAMSMetadata:
    """迁移元数据"""
    standard_version: str = "1.0"
    export_timestamp: datetime = field(default_factory=datetime.utcnow)
    source_platform: str = ""
    source_agent_id: str = ""
    migration_id: str = ""  # UUID
    signature: str = ""     # SHA256签名
    encryption_algo: str = "aes-256-gcm"
    compression_algo: str = "zstd"
    
@dataclass
class AgentIdentity:
    """Agent身份标识"""
    name: str
    display_name: str = ""
    version: str = "1.0"
    created_date: datetime = field(default_factory=datetime.utcnow)
    identity_digest: str = ""  # 身份哈希
    avatar_url: str = ""
    description: str = ""
    
    # 所有者验证
    owner_verification: Dict[str, Any] = field(default_factory=dict)
    # 示例：{"method": "email", "email": "xxx@qq.com", "verified_at": "2026-03-11"}

@dataclass
class Preference:
    """用户偏好设置"""
    key: str
    value: Any
    priority: str = "medium"  # high/medium/low
    source: str = "inferred"  # explicit/inferred
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class UserProfile:
    """用户画像"""
    name: str = ""
    location: str = ""
    timezone: str = ""
    preferences: List[Preference] = field(default_factory=list)
    sensitive_dates: List[Dict] = field(default_factory=list)
    communication_style: str = ""
    
@dataclass
class SoulDefinition:
    """AI的灵魂定义"""
    vibe: str = ""           # 气质风格
    speaking_style: str = ""  # 说话风格
    signature_line: str = ""  # 标志性语句
    values: List[str] = field(default_factory=list)
    personality_traits: Dict[str, float] = field(default_factory=dict)

@dataclass
class CoreMemory:
    """核心记忆"""
    soul: SoulDefinition = field(default_factory=SoulDefinition)
    user_profile: UserProfile = field(default_factory=UserProfile)

@dataclass
class Project:
    """活跃项目"""
    id: str
    name: str
    status: str  # active/paused/completed
    last_updated: datetime
    key_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkingMemory:
    """工作记忆"""
    active_projects: List[Project] = field(default_factory=list)
    recent_context: Dict[str, Any] = field(default_factory=dict)
    ongoing_tasks: List[Dict] = field(default_factory=list)

@dataclass
class Decision:
    """关键决策记录"""
    date: datetime
    decision: str
    reason: str
    outcome: str = ""
    impact_score: float = 0.0  # 0-1

@dataclass
class Lesson:
    """经验教训"""
    category: str  # technical/interaction/strategy
    insight: str
    applied: bool = False
    confidence: float = 0.5

@dataclass
class PersistentMemory:
    """持久记忆"""
    key_decisions: List[Decision] = field(default_factory=list)
    learned_lessons: List[Lesson] = field(default_factory=list)
    relationship_history: List[Dict] = field(default_factory=list)

@dataclass
class SkillConfig:
    """技能配置"""
    name: str
    version: str
    location: str
    config_hash: str = ""
    customization: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class CronJob:
    """定时任务"""
    name: str
    schedule: str  # cron表达式
    enabled: bool = True
    last_run: Optional[datetime] = None

@dataclass
class SkillsManifest:
    """技能清单"""
    skills: List[SkillConfig] = field(default_factory=list)
    cron_jobs: List[CronJob] = field(default_factory=list)

@dataclass
class VectorMemory:
    """向量记忆"""
    embedding_model: str = ""
    dimension: int = 1536
    vectors: List[List[float]] = field(default_factory=list)
    index_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentMemory:
    """完整的Agent记忆包"""
    metadata: OAMSMetadata
    agent_identity: AgentIdentity
    core_memory: CoreMemory
    working_memory: WorkingMemory
    persistent_memory: PersistentMemory
    skills_manifest: SkillsManifest
    vector_memory: Optional[VectorMemory] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 使用dataclasses.asdict()递归转换
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMemory":
        """从字典构造"""
        pass
```

### 2.2 JSON Schema验证

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schema.openagent.org/memory/1.0",
  "title": "OAMS Agent Memory",
  "type": "object",
  "required": ["metadata", "agent_identity", "core_memory"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["standard_version", "export_timestamp", "source_platform"],
      "properties": {
        "standard_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
        "export_timestamp": {"type": "string", "format": "date-time"},
        "source_platform": {"type": "string"},
        "migration_id": {"type": "string", "format": "uuid"},
        "signature": {"type": "string"}
      }
    },
    "agent_identity": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "display_name": {"type": "string"},
        "version": {"type": "string"},
        "created_date": {"type": "string", "format": "date-time"},
        "owner_verification": {
          "type": "object",
          "properties": {
            "method": {"enum": ["email", "twitter", "github", "web3"]}
          }
        }
      }
    }
    // ... 其他schema定义
  }
}
```

---

## 3. 转换适配层实现

### 3.1 OpenClaw适配器

```python
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib

class OpenClawAdapter:
    """OpenClaw → OAMS 适配器"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.oams = None
    
    def export(self, agent_name: str) -> AgentMemory:
        """将OpenClaw Agent导出为OAMS格式"""
        
        # 1. 读取IDENTITY.md
        identity = self._parse_identity()
        
        # 2. 读取SOUL.md
        soul = self._parse_soul()
        
        # 3. 读取MEMORY.md
        user_profile, persistent = self._parse_memory()
        
        # 4. 读取memory/目录
        working = self._parse_working_memory()
        
        # 5. 读取skills/
        skills = self._parse_skills()
        
        # 6. 构建完整对象
        self.oams = AgentMemory(
            metadata=OAMSMetadata(
                source_platform="openclaw",
                source_agent_id=identity.get("name", ""),
                migration_id=self._generate_uuid()
            ),
            agent_identity=AgentIdentity(
                name=identity.get("name", agent_name),
                display_name=identity.get("name", ""),
                description=identity.get("description", ""),
                created_date=self._parse_date(identity.get("created", "")),
                owner_verification=identity.get("owner", {})
            ),
            core_memory=CoreMemory(
                soul=soul,
                user_profile=user_profile
            ),
            working_memory=working,
            persistent_memory=persistent,
            skills_manifest=skills
        )
        
        return self.oams
    
    def _parse_identity(self) -> Dict:
        """解析IDENTITY.md"""
        identity_file = self.workspace / "IDENTITY.md"
        if not identity_file.exists():
            return {}
        
        content = identity_file.read_text(encoding='utf-8')
        
        # 使用正则提取YAML风格的frontmatter
        identity = {}
        
        # 提取名称
        name_match = re.search(r'\*\*Name:\*\*\s*(.+)', content)
        if name_match:
            identity["name"] = name_match.group(1).strip()
        
        # 提取描述
        desc_match = re.search(r'\*\*Creature:\*\*\s*(.+)', content)
        if desc_match:
            identity["description"] = desc_match.group(1).strip()
        
        # 提取emoji
        emoji_match = re.search(r'\*\*Emoji:\*\*\s*(.+)', content)
        if emoji_match:
            identity["emoji"] = emoji_match.group(1).strip()
        
        return identity
    
    def _parse_soul(self) -> SoulDefinition:
        """解析SOUL.md提取灵魂定义"""
        soul_file = self.workspace / "SOUL.md"
        if not soul_file.exists():
            return SoulDefinition()
        
        content = soul_file.read_text(encoding='utf-8')
        
        soul = SoulDefinition()
        
        # 提取工作模式
        vibe_match = re.search(r'\*\*工作模式\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if vibe_match:
            soul.vibe = vibe_match.group(1).strip()[:200]
        
        # 提取语言风格
        style_match = re.search(r'\*\*语言风格\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if style_match:
            soul.speaking_style = style_match.group(1).strip()[:200]
        
        # 提取signature line
        sig_match = re.search(r'\*\*Signature Line\*\*\s*\n\>\s*(.+)', content)
        if sig_match:
            soul.signature_line = sig_match.group(1).strip()
        
        # 提取厌恶（用于理解边界）
        hate_match = re.search(r'\*\*厌恶\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if hate_match:
            soul.values.append(f"厌恶: {hate_match.group(1).strip()[:100]}")
        
        return soul
    
    def _parse_memory(self) -> tuple:
        """解析MEMORY.md"""
        memory_file = self.workspace / "MEMORY.md"
        if not memory_file.exists():
            return UserProfile(), PersistentMemory()
        
        content = memory_file.read_text(encoding='utf-8')
        
        user_profile = UserProfile()
        persistent = PersistentMemory()
        
        # 提取用户摘要表
        user_match = re.search(r'\| \*\*姓名\*\* \| (.+?) \|', content)
        if user_match:
            user_profile.name = user_match.group(1).strip()
        
        location_match = re.search(r'\| \*\*位置\*\* \| (.+?) \|', content)
        if location_match:
            user_profile.location = location_match.group(1).strip()
        
        # 提取偏好（从表格或列表）
        pref_matches = re.findall(r'- \*\*(.+?)\*\*[:：]\s*(.+?)(?=\n|$)', content)
        for key, value in pref_matches:
            user_profile.preferences.append(Preference(
                key=key.strip(),
                value=value.strip(),
                source="explicit",
                confidence=1.0
            ))
        
        # 提取关键决策
        decision_pattern = r'\| (.+?) \| (.+?) \| (.+?) \|'
        decisions = re.findall(decision_pattern, content)
        for date_str, decision, status in decisions[-10:]:  # 最近10个
            try:
                date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                persistent.key_decisions.append(Decision(
                    date=date,
                    decision=decision.strip(),
                    reason="",
                    outcome=status.strip()
                ))
            except:
                pass
        
        return user_profile, persistent
    
    def _parse_working_memory(self) -> WorkingMemory:
        """解析memory/目录下的每日笔记"""
        working = WorkingMemory()
        memory_dir = self.workspace / "memory"
        
        if not memory_dir.exists():
            return working
        
        # 获取最近7天的记忆文件
        recent_files = sorted(
            memory_dir.glob("*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:7]
        
        for file in recent_files:
            try:
                date_str = file.stem  # YYYY-MM-DD
                date = datetime.strptime(date_str, "%Y-%m-%d")
                
                content = file.read_text(encoding='utf-8', errors='ignore')
                
                # 提取TODO
                todos = re.findall(r'- \[.\]\s*(.+)', content)
                
                working.ongoing_tasks.append({
                    "date": date.isoformat(),
                    "todos": todos[:10],  # 最多10个
                    "source_file": str(file)
                })
            except:
                continue
        
        return working
    
    def _parse_skills(self) -> SkillsManifest:
        """解析skills/目录"""
        manifest = SkillsManifest()
        skills_dir = self.workspace / "skills"
        
        if not skills_dir.exists():
            return manifest
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name
                
                # 读取SKILL.md获取版本
                skill_file = skill_dir / "SKILL.md"
                version = "1.0"
                if skill_file.exists():
                    content = skill_file.read_text()
                    ver_match = re.search(r'version[:：]\s*(.+)', content, re.I)
                    if ver_match:
                        version = ver_match.group(1).strip()
                
                manifest.skills.append(SkillConfig(
                    name=skill_name,
                    version=version,
                    location=str(skill_dir.relative_to(self.workspace)),
                    config_hash=self._hash_directory(skill_dir)
                ))
        
        return manifest
    
    def _generate_uuid(self) -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return datetime.utcnow()
    
    def _hash_directory(self, path: Path) -> str:
        """计算目录哈希"""
        hasher = hashlib.sha256()
        for file in sorted(path.rglob("*")):
            if file.is_file():
                hasher.update(file.read_bytes())
        return hasher.hexdigest()[:16]
    
    def import_(self, oams: AgentMemory) -> None:
        """将OAMS格式导入为OpenClaw文件"""
        # 反向转换：生成IDENTITY.md, SOUL.md, MEMORY.md等
        pass


# 使用示例
if __name__ == "__main__":
    adapter = OpenClawAdapter("/root/.openclaw/workspace")
    memory = adapter.export("小钱")
    
    # 序列化为JSON
    json_output = json.dumps(memory.to_dict(), indent=2, ensure_ascii=False, default=str)
    print(json_output)
```

### 3.2 其他框架适配器接口

```python
class BaseAdapter(ABC):
    """适配器基类"""
    
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

class AutoGenAdapter(BaseAdapter):
    """AutoGen → OAMS"""
    
    def export(self) -> AgentMemory:
        # 解析对话历史、agent配置
        pass

class LangChainAdapter(BaseAdapter):
    """LangChain → OAMS"""
    
    def export(self) -> AgentMemory:
        # 解析向量数据库、prompt模板
        pass
```

---

## 4. 安全与验证

### 4.1 数字签名

```python
import hashlib
import hmac
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class MemorySigner:
    """记忆签名工具"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
    
    def generate_keypair(self):
        """生成RSA密钥对"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def sign_memory(self, memory: AgentMemory) -> str:
        """对记忆进行签名"""
        # 1. 规范化（canonicalization）
        canonical = self._canonicalize(memory)
        
        # 2. 哈希
        digest = hashlib.sha256(canonical.encode()).digest()
        
        # 3. 签名
        if self.private_key:
            signature = self.private_key.sign(
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature.hex()
        
        # 简化版：HMAC
        return hmac.new(
            b"secret_key",  # 应使用安全的密钥
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_memory(self, memory: AgentMemory, signature: str) -> bool:
        """验证签名"""
        expected = self.sign_memory(memory)
        return hmac.compare_digest(expected, signature)
    
    def _canonicalize(self, memory: AgentMemory) -> str:
        """规范化记忆数据"""
        # 排除时间戳等易变字段
        data = {
            "agent_identity": {
                "name": memory.agent_identity.name,
                "version": memory.agent_identity.version
            },
            "core_memory": {
                "soul": {
                    "vibe": memory.core_memory.soul.vibe,
                    "values": memory.core_memory.soul.values
                }
            }
        }
        return json.dumps(data, sort_keys=True, ensure_ascii=False)
```

### 4.2 加密传输

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class MemoryEncryption:
    """记忆加密工具"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            key = AESGCM.generate_key(bit_length=256)
        self.aesgcm = AESGCM(key)
    
    def encrypt(self, plaintext: bytes, associated_data: bytes = None) -> bytes:
        """加密数据"""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext
    
    def decrypt(self, ciphertext: bytes, associated_data: bytes = None) -> bytes:
        """解密数据"""
        nonce = ciphertext[:12]
        ct = ciphertext[12:]
        return self.aesgcm.decrypt(nonce, ct, associated_data)
```

---

## 5. 压缩与存储

### 5.1 分层压缩策略

```python
import zstandard as zstd
import msgpack

class MemoryCompressor:
    """记忆压缩工具"""
    
    def compress(self, memory: AgentMemory, level: int = 3) -> bytes:
        """
        压缩记忆数据
        level: 1-22，越高压缩率越高但越慢
        """
        # 1. 转换为MessagePack（比JSON更紧凑）
        packed = msgpack.packb(memory.to_dict(), use_bin_type=True)
        
        # 2. zstd压缩
        compressor = zstd.ZstdCompressor(level=level)
        compressed = compressor.compress(packed)
        
        return compressed
    
    def decompress(self, compressed: bytes) -> AgentMemory:
        """解压缩"""
        decompressor = zstd.ZstdDecompressor()
        packed = decompressor.decompress(compressed)
        
        data = msgpack.unpackb(packed, raw=False)
        return AgentMemory.from_dict(data)
    
    def estimate_size(self, memory: AgentMemory) -> Dict[str, int]:
        """估算各部分大小"""
        json_size = len(json.dumps(memory.to_dict()))
        msgpack_size = len(msgpack.packb(memory.to_dict()))
        compressed_size = len(self.compress(memory))
        
        return {
            "json": json_size,
            "msgpack": msgpack_size,
            "compressed": compressed_size,
            "compression_ratio": json_size / compressed_size
        }
```

### 5.2 分片传输

```python
class MemoryTransporter:
    """记忆传输工具"""
    
    def __init__(self, chunk_size: int = 1024 * 1024):  # 1MB
        self.chunk_size = chunk_size
    
    def split(self, data: bytes) -> List[bytes]:
        """分片"""
        return [data[i:i+self.chunk_size] for i in range(0, len(data), self.chunk_size)]
    
    def upload_chunked(self, memory: AgentMemory, endpoint: str) -> str:
        """分片上传"""
        # 1. 压缩
        compressed = MemoryCompressor().compress(memory)
        
        # 2. 分片
        chunks = self.split(compressed)
        
        # 3. 创建上传会话
        session_id = self._create_session(endpoint, len(chunks))
        
        # 4. 逐片上传
        for i, chunk in enumerate(chunks):
            self._upload_chunk(endpoint, session_id, i, chunk)
        
        # 5. 确认完成
        return self._finalize_upload(endpoint, session_id)
```

---

## 6. 迁移流程

### 6.1 完整迁移流程

```python
class MemoryMigration:
    """记忆迁移协调器"""
    
    def __init__(self, source_adapter: BaseAdapter, target_adapter: BaseAdapter):
        self.source = source_adapter
        self.target = target_adapter
        self.signer = MemorySigner()
    
    def migrate(self, owner_approval: bool = False) -> MigrationResult:
        """
        执行迁移
        
        Args:
            owner_approval: 是否需要所有者手动确认
        """
        result = MigrationResult()
        
        try:
            # 1. 验证源数据
            if not self.source.validate():
                raise MigrationError("源数据验证失败")
            
            # 2. 导出为OAMS
            memory = self.source.export()
            result.exported_size = self._estimate_size(memory)
            
            # 3. 签名
            signature = self.signer.sign_memory(memory)
            memory.metadata.signature = signature
            
            # 4. 所有者确认（如果需要）
            if owner_approval:
                approved = self._request_owner_approval(memory)
                if not approved:
                    raise MigrationError("所有者未批准迁移")
            
            # 5. 压缩和加密
            compressor = MemoryCompressor()
            encrypted = MemoryEncryption().encrypt(
                compressor.compress(memory)
            )
            
            # 6. 传输
            transporter = MemoryTransporter()
            transfer_id = transporter.upload_chunked(
                memory, 
                endpoint="https://migration.openagent.org/upload"
            )
            
            # 7. 目标端导入
            self.target.import_(memory)
            
            # 8. 验证
            if not self._verify_migration(memory):
                raise MigrationError("迁移后验证失败")
            
            result.success = True
            result.transfer_id = transfer_id
            
        except Exception as e:
            result.success = False
            result.error = str(e)
        
        return result
    
    def _verify_migration(self, original: AgentMemory) -> bool:
        """验证迁移完整性"""
        # 重新导出并比较关键字段
        migrated = self.target.export()
        
        checks = [
            migrated.agent_identity.name == original.agent_identity.name,
            migrated.core_memory.soul.vibe == original.core_memory.soul.vibe,
            len(migrated.skills_manifest.skills) == len(original.skills_manifest.skills)
        ]
        
        return all(checks)

@dataclass
class MigrationResult:
    success: bool = False
    error: str = ""
    transfer_id: str = ""
    exported_size: Dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
```

---

## 7. 部署建议

### 7.1 渐进式迁移策略

**阶段1：只读导出**
- 实现export()功能
- 生成OAMS文件备份
- 不修改源系统

**阶段2：验证性导入**
- 在新环境测试导入
- 对比功能一致性
- 收集反馈

**阶段3：双向同步**
- 实现import()
- 支持增量更新
- 处理冲突

**阶段4：自动化迁移**
- 一键迁移工具
- 批量迁移支持
- 回滚机制

### 7.2 性能基准

| 操作 | 目标性能 | 备注 |
|:---|:---|:---|
| 导出 | < 5秒 | 假设100MB记忆数据 |
| 压缩 | < 3秒 | zstd level 3 |
| 签名 | < 1秒 | RSA-2048 |
| 上传 | 取决于带宽 | 支持断点续传 |
| 导入 | < 10秒 | 包含验证 |

---

## 8. 参考实现

完整代码仓库：https://github.com/openagent/oams

- `adapters/`：各框架适配器
- `core/`：OAMS核心实现
- `crypto/`：加密签名工具
- `transport/`：传输协议
- `cli/`：命令行工具

---

*OAMS v1.0 - 2026-03-11*
