# langchain_adapter.py
"""
LangChain → OAMS 适配器
将LangChain的智能体配置、向量存储和Prompt模板导出为OAMS格式
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# 假设OAMS核心类已经定义
from oams.core import (
    AgentMemory, OAMSMetadata, AgentIdentity, CoreMemory,
    WorkingMemory, PersistentMemory, SkillsManifest, VectorMemory,
    SoulDefinition, UserProfile, Preference, Project,
    Decision, Lesson, SkillConfig, CronJob
)
from oams.adapters.base import BaseAdapter


class LangChainAdapter(BaseAdapter):
    """
    LangChain → OAMS 适配器
    
    支持从LangChain的以下组件导出：
    - Agent配置（类型、工具、LLM）
    - Vector Store（向量记忆）
    - Prompt Templates（灵魂定义）
    - Memory组件（对话历史）
    - Tools配置（技能）
    """
    
    def __init__(self, 
                 agent_config_path: str = None,
                 vectorstore_path: str = None,
                 prompts_path: str = None,
                 memory_path: str = None):
        """
        初始化适配器
        
        Args:
            agent_config_path: LangChain agent配置文件
            vectorstore_path: 向量存储目录（Chroma/Pinecone/FAISS）
            prompts_path: Prompt模板目录
            memory_path: Memory存储路径
        """
        self.agent_config_path = Path(agent_config_path) if agent_config_path else None
        self.vectorstore_path = Path(vectorstore_path) if vectorstore_path else None
        self.prompts_path = Path(prompts_path) if prompts_path else None
        self.memory_path = Path(memory_path) if memory_path else None
        
        self.agent_config = {}
        self.vectorstore_metadata = {}
        self.prompts = {}
        self.memory_data = {}
    
    def validate(self) -> bool:
        """验证源数据完整性"""
        # LangChain可以只有部分组件
        valid_components = 0
        
        if self.agent_config_path and self.agent_config_path.exists():
            valid_components += 1
        
        if self.vectorstore_path and self.vectorstore_path.exists():
            valid_components += 1
            
        if self.prompts_path and self.prompts_path.exists():
            valid_components += 1
            
        if self.memory_path and self.memory_path.exists():
            valid_components += 1
        
        if valid_components == 0:
            raise ValueError("至少需要一个有效的LangChain组件路径")
        
        return True
    
    def export(self, agent_name: str = None) -> AgentMemory:
        """
        将LangChain Agent导出为OAMS格式
        
        Args:
            agent_name: 指定Agent名称
        """
        # 1. 加载所有组件
        self._load_all_components()
        
        # 2. 解析Agent身份
        identity = self._parse_identity(agent_name)
        
        # 3. 解析Prompt作为Soul
        soul = self._parse_soul()
        
        # 4. 解析用户画像
        user_profile = self._parse_user_profile()
        
        # 5. 解析工作记忆
        working = self._parse_working_memory()
        
        # 6. 解析持久记忆
        persistent = self._parse_persistent_memory()
        
        # 7. 解析技能清单
        skills = self._parse_skills()
        
        # 8. 解析向量记忆
        vector_memory = self._parse_vector_memory()
        
        # 构建完整记忆
        memory = AgentMemory(
            metadata=OAMSMetadata(
                standard_version="1.0",
                source_platform="langchain",
                source_agent_id=identity.get('name', agent_name or 'unknown'),
                migration_id=self._generate_uuid()
            ),
            agent_identity=AgentIdentity(
                name=identity.get('name', agent_name or 'LangChain Agent'),
                display_name=identity.get('name', agent_name or 'LangChain Agent'),
                description=identity.get('description', ''),
                version="1.0",
                created_date=datetime.utcnow(),
                owner_verification={}
            ),
            core_memory=CoreMemory(
                soul=soul,
                user_profile=user_profile
            ),
            working_memory=working,
            persistent_memory=persistent,
            skills_manifest=skills,
            vector_memory=vector_memory
        )
        
        return memory
    
    def _load_all_components(self) -> None:
        """加载所有LangChain组件"""
        # Agent配置
        if self.agent_config_path and self.agent_config_path.exists():
            with open(self.agent_config_path, 'r', encoding='utf-8') as f:
                self.agent_config = json.load(f)
        
        # Prompt模板
        if self.prompts_path and self.prompts_path.exists():
            self._load_prompts()
        
        # Memory数据
        if self.memory_path and self.memory_path.exists():
            self._load_memory()
        
        # 向量存储元数据
        if self.vectorstore_path and self.vectorstore_path.exists():
            self._load_vectorstore_metadata()
    
    def _load_prompts(self) -> None:
        """加载Prompt模板"""
        # 支持多种格式：json、txt、yaml
        for prompt_file in self.prompts_path.glob('*'):
            if prompt_file.suffix == '.json':
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts[prompt_file.stem] = json.load(f)
            elif prompt_file.suffix in ['.txt', '.md']:
                self.prompts[prompt_file.stem] = prompt_file.read_text(encoding='utf-8')
    
    def _load_memory(self) -> None:
        """加载Memory数据"""
        # 支持ConversationBufferMemory等格式
        memory_file = self.memory_path / 'conversation_memory.json'
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                self.memory_data = json.load(f)
    
    def _load_vectorstore_metadata(self) -> None:
        """加载向量存储元数据"""
        # Chroma
        chroma_file = self.vectorstore_path / 'chroma.sqlite3'
        if chroma_file.exists():
            self.vectorstore_metadata = {
                'type': 'chroma',
                'path': str(self.vectorstore_path),
                'dimension': 1536  # 默认OpenAI embedding维度
            }
        
        # FAISS
        faiss_file = self.vectorstore_path / 'index.faiss'
        if faiss_file.exists():
            self.vectorstore_metadata = {
                'type': 'faiss',
                'path': str(self.vectorstore_path),
                'dimension': 1536
            }
    
    def _parse_identity(self, agent_name: str = None) -> Dict[str, Any]:
        """解析Agent身份"""
        identity = {
            'name': agent_name or self.agent_config.get('name', 'LangChain Agent'),
        }
        
        # 从配置提取描述
        if 'description' in self.agent_config:
            identity['description'] = self.agent_config['description']
        
        # 从agent类型推断
        agent_type = self.agent_config.get('agent_type', '')
        if agent_type:
            identity['description'] = f"{agent_type} agent"
        
        return identity
    
    def _parse_soul(self) -> SoulDefinition:
        """从Prompt解析灵魂定义"""
        soul = SoulDefinition()
        
        # 使用系统prompt
        system_prompt = self.prompts.get('system', '')
        if isinstance(system_prompt, dict):
            system_prompt = system_prompt.get('template', '')
        
        if not system_prompt:
            # 尝试从agent配置中提取
            system_prompt = self.agent_config.get('system_message', '')
        
        if system_prompt:
            soul.vibe = system_prompt[:300]
            
            # 提取第一条指令作为signature
            lines = system_prompt.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 20:
                    soul.signature_line = line[:100]
                    break
            
            # 从prompt中提取说话风格
            import re
            # 查找角色描述
            role_match = re.search(r'You are (.+?)\.', system_prompt)
            if role_match:
                soul.speaking_style = f"作为{role_match.group(1)}"
            
            # 提取约束条件作为values
            constraints = re.findall(r'(Always|Never|Do not)\s+(.+?)(?:\.|\n)', system_prompt)
            soul.values = [f"{c[0]} {c[1]}" for c in constraints[:5]]
        
        return soul
    
    def _parse_user_profile(self) -> UserProfile:
        """解析用户画像"""
        profile = UserProfile()
        
        # 从vector store中的metadata提取
        if self.vectorstore_metadata.get('type') == 'chroma':
            # 尝试读取Chroma集合元数据
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(self.vectorstore_path))
                # 获取集合信息
                collections = client.list_collections()
                for collection in collections:
                    # 从metadata中提取用户信息
                    metadata = collection.metadata or {}
                    if 'user_name' in metadata:
                        profile.name = metadata['user_name']
                    if 'user_location' in metadata:
                        profile.location = metadata['user_location']
            except:
                pass
        
        return profile
    
    def _parse_working_memory(self) -> WorkingMemory:
        """解析工作记忆"""
        working = WorkingMemory()
        
        # 从ConversationMemory提取
        if 'chat_history' in self.memory_data:
            chat_history = self.memory_data['chat_history']
            
            recent_context = {
                'last_messages': [],
                'session_summary': ''
            }
            
            # 最近10条消息
            for msg in chat_history[-10:]:
                recent_context['last_messages'].append({
                    'type': msg.get('type', 'human'),
                    'content': msg.get('data', {}).get('content', '')[:150]
                })
            
            working.recent_context = recent_context
        
        # 从向量存储中提取活跃项目
        if self.vectorstore_path:
            working.active_projects.append(Project(
                id='vector_store',
                name='Vector Memory Store',
                status='active',
                last_updated=datetime.utcnow(),
                key_files=[str(self.vectorstore_path)],
                metadata={'type': self.vectorstore_metadata.get('type', 'unknown')}
            ))
        
        return working
    
    def _parse_persistent_memory(self) -> PersistentMemory:
        """解析持久记忆"""
        persistent = PersistentMemory()
        
        # 从向量存储的metadata中提取决策历史
        if self.vectorstore_path:
            metadata_file = self.vectorstore_path / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                    # 提取关键决策
                    for key, value in metadata.items():
                        if 'decision' in key.lower():
                            persistent.key_decisions.append(Decision(
                                date=datetime.utcnow(),
                                decision=str(value),
                                reason='from vectorstore metadata',
                                outcome='unknown',
                                impact_score=0.5
                            ))
        
        return persistent
    
    def _parse_skills(self) -> SkillsManifest:
        """解析技能清单"""
        manifest = SkillsManifest()
        
        # 从agent配置中提取tools
        tools = self.agent_config.get('tools', [])
        
        for tool in tools:
            if isinstance(tool, str):
                # 简单工具名称
                manifest.skills.append(SkillConfig(
                    name=tool,
                    version="1.0",
                    location=f"tools/{tool}",
                    config_hash=self._hash_string(tool),
                    enabled=True
                ))
            elif isinstance(tool, dict):
                # 详细工具配置
                tool_name = tool.get('name', tool.get('type', 'unknown'))
                manifest.skills.append(SkillConfig(
                    name=tool_name,
                    version=tool.get('version', '1.0'),
                    location=f"tools/{tool_name}",
                    config_hash=self._hash_string(json.dumps(tool)),
                    customization=tool.get('config', {}),
                    enabled=tool.get('enabled', True)
                ))
        
        # 从tools目录加载
        if self.agent_config_path:
            tools_dir = self.agent_config_path.parent / 'tools'
            if tools_dir.exists():
                for tool_file in tools_dir.glob('*.json'):
                    with open(tool_file, 'r', encoding='utf-8') as f:
                        tool_def = json.load(f)
                        manifest.skills.append(SkillConfig(
                            name=tool_def.get('name', tool_file.stem),
                            version=tool_def.get('version', '1.0'),
                            location=str(tool_file),
                            config_hash=self._hash_string(json.dumps(tool_def)),
                            customization=tool_def.get('parameters', {}),
                            enabled=True
                        ))
        
        return manifest
    
    def _parse_vector_memory(self) -> Optional[VectorMemory]:
        """解析向量记忆"""
        if not self.vectorstore_path:
            return None
        
        vector_memory = VectorMemory()
        
        # 确定embedding模型和维度
        if self.vectorstore_metadata.get('type') == 'chroma':
            vector_memory.embedding_model = 'openai-text-embedding-3-small'
            vector_memory.dimension = 1536
        elif self.vectorstore_metadata.get('type') == 'faiss':
            vector_memory.embedding_model = 'openai-text-embedding-ada-002'
            vector_memory.dimension = 1536
        
        # 导出向量数据（可选，如果数据量不大）
        # 注意：实际项目中可能需要分批导出
        if self.vectorstore_metadata.get('type') == 'chroma':
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(self.vectorstore_path))
                
                # 获取所有集合的向量
                all_vectors = []
                collections = client.list_collections()
                
                for collection in collections[:1]:  # 只取第一个集合
                    data = collection.get(include=['embeddings'])
                    if data and 'embeddings' in data:
                        vectors = data['embeddings']
                        # 限制导出的向量数量
                        all_vectors.extend(vectors[:100])  # 最多100个
                
                vector_memory.vectors = all_vectors
                vector_memory.index_metadata = {
                    'source_collections': len(collections),
                    'exported_vectors': len(all_vectors),
                    'total_vectors': sum(c.count() for c in collections)
                }
            except Exception as e:
                print(f"警告: 无法导出向量数据: {e}")
        
        return vector_memory
    
    def import_(self, oams: AgentMemory) -> None:
        """
        将OAMS格式导入为LangChain配置
        
        生成：
        - agent_config.json
        - prompts/system.txt
        - vectorstore/ (如果需要)
        """
        output_dir = Path('langchain_imported')
        output_dir.mkdir(exist_ok=True)
        
        # 1. 生成Agent配置
        config = {
            'name': oams.agent_identity.name,
            'description': oams.agent_identity.description,
            'agent_type': 'openai-functions',
            'llm': {
                'model': 'gpt-4',
                'temperature': 0.7
            }
        }
        
        with open(output_dir / 'agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 2. 生成System Prompt
        prompts_dir = output_dir / 'prompts'
        prompts_dir.mkdir(exist_ok=True)
        
        system_prompt = self._build_system_prompt(oams.core_memory.soul)
        with open(prompts_dir / 'system.txt', 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        
        # 3. 生成工具定义
        tools_dir = output_dir / 'tools'
        tools_dir.mkdir(exist_ok=True)
        
        for skill in oams.skills_manifest.skills:
            tool_def = {
                'name': skill.name,
                'description': f'Tool: {skill.name}',
                'parameters': {
                    'type': 'object',
                    'properties': skill.customization,
                    'required': list(skill.customization.keys())
                }
            }
            
            with open(tools_dir / f'{skill.name}.json', 'w', encoding='utf-8') as f:
                json.dump(tool_def, f, indent=2)
        
        # 4. 如果包含向量记忆，创建初始化脚本
        if oams.vector_memory and oams.vector_memory.vectors:
            init_script = output_dir / 'init_vectorstore.py'
            with open(init_script, 'w', encoding='utf-8') as f:
                f.write(f'''"""初始化向量存储"""
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# 注意：这里需要重新创建向量存储
# 原始向量数据包含 {len(oams.vector_memory.vectors)} 个向量
# embedding模型: {oams.vector_memory.embedding_model}
# 维度: {oams.vector_memory.dimension}

embeddings = OpenAIEmbeddings()
# 请添加文档后重新创建向量存储
''')
        
        print(f"✅ LangChain配置已生成: {output_dir.absolute()}")
    
    def _build_system_prompt(self, soul: SoulDefinition) -> str:
        """从Soul构建System Prompt"""
        parts = []
        
        if soul.signature_line:
            parts.append(f"You are {soul.signature_line}")
        
        if soul.vibe:
            parts.append(f"\n{soul.vibe}")
        
        if soul.values:
            parts.append("\n重要约束:")
            for value in soul.values:
                parts.append(f"- {value}")
        
        if soul.speaking_style:
            parts.append(f"\n风格: {soul.speaking_style}")
        
        return '\n'.join(parts)
    
    def _generate_uuid(self) -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())
    
    def _hash_string(self, content: str) -> str:
        """计算字符串哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# 使用示例
if __name__ == "__main__":
    # 导出示例
    adapter = LangChainAdapter(
        agent_config_path="./lc_agent_config.json",
        vectorstore_path="./chroma_db",
        prompts_path="./prompts",
        memory_path="./lc_memory"
    )
    
    if adapter.validate():
        memory = adapter.export("my_langchain_agent")
        
        # 保存为OAMS文件
        oams_file = "my_langchain_agent.oams"
        with open(oams_file, 'w', encoding='utf-8') as f:
            json.dump(memory.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 成功导出到 {oams_file}")
        
        # 打印向量统计
        if memory.vector_memory:
            print(f"向量数量: {len(memory.vector_memory.vectors)}")
            print(f"向量维度: {memory.vector_memory.dimension}")
