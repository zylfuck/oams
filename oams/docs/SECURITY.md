# SECURITY.md
# OAMS安全注意事项

本文档描述OAMS（OpenAgent Memory Standard）的安全考虑和最佳实践。

---

## 安全原则

OAMS遵循以下安全原则：

1. **用户控制**：用户完全拥有并控制自己的AI记忆
2. **最小权限**：只导出必要的数据，不泄露敏感信息
3. **端到端保护**：传输和存储全程加密
4. **可验证性**：所有迁移可审计、可验证
5. **透明性**：用户清楚知道哪些数据被迁移

---

## 数据分类

### 🔴 高度敏感（需加密）

| 数据类型 | 示例 | 保护措施 |
|:---|:---|:---|
| API密钥 | OpenAI API Key, AWS密钥 | AES-256加密，永不导出明文 |
| 密码 | 邮箱密码, 系统密码 | 哈希存储，不导出 |
| 私密对话 | 个人日记, 医疗记录 | 用户确认后导出 |
| 身份信息 | 身份证号, 银行卡号 | 标记敏感，可选导出 |

### 🟡 中度敏感（建议保护）

| 数据类型 | 示例 | 保护措施 |
|:---|:---|:---|
| 用户偏好 | 喜欢的颜色, 习惯 | 正常导出，签名保护 |
| 工作项目 | 代码, 文档路径 | 脱敏处理后导出 |
| 社交网络 | 联系人列表 | 哈希化处理 |
| 位置信息 | 家庭地址, 常去地点 | 模糊化处理 |

### 🟢 低度敏感（标准保护）

| 数据类型 | 示例 | 保护措施 |
|:---|:---|:---|
| 性格定义 | 语气风格, 价值观 | 数字签名防篡改 |
| 公开信息 | 技能清单, 公开帖子 | 标准OAMS格式 |
| 学习记录 | 学到的技巧 | 只读导出 |

---

## 加密机制

### 传输加密

所有迁移过程使用 **TLS 1.3** 加密传输：

```python
# 强制HTTPS
if not endpoint.startswith('https://'):
    raise SecurityError("必须使用HTTPS端点")

# 证书验证
import ssl
context = ssl.create_default_context()
context.verify_mode = ssl.CERT_REQUIRED
```

### 存储加密

OAMS文件支持多层加密：

#### 1. 标准加密（推荐）
```python
from oams.crypto import MemoryEncryption

# 使用用户密码派生密钥
encryption = MemoryEncryption.derive_from_password(user_password)
encrypted = encryption.encrypt(memory_data)
```

#### 2. 高级加密（企业级）
```python
from oams.crypto import MemoryEncryption

# 使用硬件安全模块(HSM)
encryption = MemoryEncryption.from_hsm(hsm_client)
encrypted = encryption.encrypt(
    memory_data,
    associated_data={"owner": user_id, "timestamp": timestamp}
)
```

#### 3. 端到端加密
```python
# 源端加密
source_encryption = MemoryEncryption()
encrypted_at_source = source_encryption.encrypt(memory)

# 只有目标端能解密
target_encryption = MemoryEncryption(source_encryption.key)
decrypted = target_encryption.decrypt(encrypted_at_source)
```

### 数字签名

确保数据完整性：

```python
from oams.crypto import MemorySigner

signer = MemorySigner()
signer.generate_keypair()

# 源端签名
signature = signer.sign_memory(memory)
memory.metadata.signature = signature

# 目标端验证
if not signer.verify_memory(memory, signature):
    raise SecurityError("数据可能被篡改")
```

---

## 访问控制

### 身份验证

迁移前必须验证所有者身份：

```python
class OwnerVerification:
    METHODS = ['email', 'totp', 'web3', 'biometric']
    
    @staticmethod
    def verify(method: str, credentials: dict) -> bool:
        if method == 'email':
            # 发送验证码到注册邮箱
            return EmailVerification.verify(
                email=credentials['email'],
                code=credentials['code']
            )
        
        elif method == 'totp':
            # TOTP二次验证
            return TOTPVerification.verify(
                secret=credentials['secret'],
                code=credentials['code']
            )
        
        elif method == 'web3':
            # 区块链签名验证
            return Web3Verification.verify(
                address=credentials['address'],
                signature=credentials['signature']
            )
        
        return False
```

### 多重签名

高价值迁移需要多方确认：

```python
class MultiSigMigration:
    def __init__(self, required_signatures: int = 2):
        self.required = required_signatures
        self.signatures = []
    
    def add_signature(self, party: str, signature: str) -> bool:
        # 验证签名
        if self._verify_party_signature(party, signature):
            self.signatures.append((party, signature))
        
        return len(self.signatures) >= self.required
    
    def can_migrate(self) -> bool:
        return len(self.signatures) >= self.required
```

---

## 隐私保护

### 数据脱敏

导出前自动脱敏：

```python
class DataSanitizer:
    @staticmethod
    def sanitize(memory: AgentMemory) -> AgentMemory:
        # 1. 移除API密钥
        memory = DataSanitizer._remove_api_keys(memory)
        
        # 2. 模糊化位置信息
        memory = DataSanitizer._obfuscate_location(memory)
        
        # 3. 哈希化身份信息
        memory = DataSanitizer._hash_identities(memory)
        
        # 4. 截断私密对话
        memory = DataSanitizer._truncate_private_chats(memory)
        
        return memory
    
    @staticmethod
    def _remove_api_keys(memory: AgentMemory) -> AgentMemory:
        """移除所有API密钥"""
        # 扫描skills配置
        for skill in memory.skills_manifest.skills:
            if 'api_key' in skill.customization:
                skill.customization['api_key'] = '[REDACTED]'
        
        return memory
    
    @staticmethod
    def _obfuscate_location(memory: AgentMemory) -> AgentMemory:
        """模糊化位置到城市级别"""
        location = memory.core_memory.user_profile.location
        # 保留城市，移除详细地址
        memory.core_memory.user_profile.location = \
            DataSanitizer._extract_city(location)
        return memory
```

### 选择性导出

用户可选择导出内容：

```python
class ExportOptions:
    def __init__(self):
        self.include_core_memory = True
        self.include_working_memory = True
        self.include_persistent_memory = True
        self.include_skills = True
        self.include_vector_memory = False  # 默认不导出
        self.sanitize_sensitive = True
        self.encrypt_output = True
    
    def apply(self, memory: AgentMemory) -> AgentMemory:
        """根据选项过滤记忆"""
        if not self.include_vector_memory:
            memory.vector_memory = None
        
        if self.sanitize_sensitive:
            memory = DataSanitizer.sanitize(memory)
        
        return memory
```

---

## 审计日志

所有迁移操作记录审计日志：

```python
@dataclass
class AuditLog:
    timestamp: datetime
    operation: str  # export/import/migrate
    source_platform: str
    target_platform: str
    agent_name: str
    owner_id: str
    data_hash: str  # 记忆数据的哈希
    signature: str  # 操作签名
    success: bool
    error_message: str = ""

class AuditLogger:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
    
    def log(self, entry: AuditLog):
        """记录审计日志"""
        with open(self.log_path, 'a') as f:
            f.write(json.dumps({
                'timestamp': entry.timestamp.isoformat(),
                'operation': entry.operation,
                'source': entry.source_platform,
                'target': entry.target_platform,
                'agent': entry.agent_name,
                'owner': self._hash_owner(entry.owner_id),
                'data_hash': entry.data_hash,
                'success': entry.success
            }) + '\n')
    
    def query(self, owner_id: str = None, days: int = 30) -> List[AuditLog]:
        """查询审计记录"""
        # 返回用户的所有迁移记录
        pass
```

---

## 威胁模型

### 可能的攻击场景

| 威胁 | 风险等级 | 防护措施 |
|:---|:---|:---|
| **中间人攻击** | 高 | TLS 1.3 + 证书固定 |
| **数据泄露** | 高 | AES-256加密 + 访问控制 |
| **身份冒充** | 高 | 多重身份验证 |
| **数据篡改** | 中 | 数字签名验证 |
| **重放攻击** | 中 | 时间戳 + 随机数 |
| **侧信道攻击** | 低 | 恒定时间算法 |

### 安全建议

1. **定期轮换密钥**
   ```python
   # 每90天轮换加密密钥
   if key_age > timedelta(days=90):
       rotate_encryption_keys()
   ```

2. **限制重试次数**
   ```python
   # 防止暴力破解
   if failed_attempts > 5:
       lock_account(duration=timedelta(minutes=30))
   ```

3. **监控异常活动**
   ```python
   # 检测异常迁移模式
   if migrations_per_hour > 10:
       alert_security_team()
   ```

---

## 合规性

### GDPR合规

- ✅ **数据可携带权**：用户可导出自己数据
- ✅ **被遗忘权**：用户可请求删除迁移记录
- ✅ **数据处理透明**：清晰说明哪些数据被处理
- ✅ **数据最小化**：只迁移必要数据

### 其他法规

| 法规 | 要求 | OAMS支持 |
|:---|:---|:---|
| CCPA | 用户有权知道数据用途 | 审计日志 |
| HIPAA | 医疗数据加密 | AES-256加密 |
| SOC2 | 访问控制 | 多重身份验证 |

---

## 安全最佳实践

### 对于用户

1. **使用强密码**保护OAMS文件
2. **定期备份**记忆数据
3. **验证目标平台**可信度
4. **审查导出内容**再迁移
5. **启用双重验证**

### 对于开发者

1. **不硬编码密钥**在代码中
2. **使用参数化查询**防止注入
3. **验证所有输入**数据
4. **最小权限原则**运行服务
5. **定期安全审计**

### 对于平台运营者

1. **定期安全培训**员工
2. **渗透测试**系统
3. **漏洞赏金计划**
4. **应急响应计划**
5. **合规性审计**

---

## 报告安全问题

发现安全漏洞？请按以下方式报告：

1. **不要**在公开渠道披露
2. 发送邮件至：security@openagent.org
3. 包含详细复现步骤
4. 等待回复（通常在48小时内）
5.  coordinated disclosure

---

## 安全更新

订阅安全公告：

- [GitHub Security Advisories](https://github.com/zylfuck/oams/security)
- 邮件列表：security-announce@openagent.org

---

**记住**：安全是共同责任。用户、开发者和平台都需要尽自己的一份力。

---

*最后更新: 2026-03-18*
