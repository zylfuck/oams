# autogen_adapter.py
"""
AutoGen → OAMS 适配器
将AutoGen的智能体配置和对话历史导出为OAMS格式
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

# 假设OAMS核心类已经定义
from oams.core import (
    AgentMemory, OAMSMetadata, AgentIdentity, CoreMemory,
    WorkingMemory, PersistentMemory, SkillsManifest,
    SoulDefinition, UserProfile, Preference, Project,
    Decision, Lesson, SkillConfig, CronJob
)
from oams.adapters.base import BaseAdapter


class AutoGenAdapter(BaseAdapter):
    """
    AutoGen → OAMS 适配器
    
    支持从AutoGen的以下组件导出：
    - ConversableAgent 配置
    - GroupChat 历史
    - 自定义技能（skills）
    - 记忆存储（memory store）
    """
    
    def __init__(self, config_path: str = None, memory_path: str = None):
        """
        初始化适配器
        
        Args:
            config_path: AutoGen配置文件路径（JSON或Python）
            memory_path: AutoGen记忆存储目录
        """
        self.config_path = Path(config_path) if config_path else None
        self.memory_path = Path(memory_path) if memory_path else None
        self.agent_config = {}
        self.chat_history = []
        self.memory_store = {}
        
    def validate(self) -> bool:
        """验证源数据完整性"""
        if not self.config_path and not self.memory_path:
            raise ValueError("必须提供config_path或memory_path")
        
        # 检查配置文件
        if self.config_path:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            # 尝试解析配置
            try:
                self._load_config()
            except Exception as e:
                raise ValueError(f"配置文件解析失败: {e}")
        
        # 检查记忆存储
        if self.memory_path and not self.memory_path.exists():
            raise FileNotFoundError(f"记忆存储路径不存在: {self.memory_path}")
        
        return True
    
    def _load_config(self) -> None:
        """加载AutoGen配置"""
        if self.config_path.suffix == '.json':
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.agent_config = json.load(f)
        elif self.config_path.suffix == '.py':
            # 对于Python配置文件，尝试安全地提取关键信息
            content = self.config_path.read_text(encoding='utf-8')
            self.agent_config = self._parse_python_config(content)
    
    def _parse_python_config(self, content: str) -> Dict:
        """从Python配置文件中提取信息"""
        config = {}
        
        # 提取agent名称
        name_match = re.search(r'name\s*=\s*["\'](.+?)["\']', content)
        if name_match:
            config['name'] = name_match.group(1)
        
        # 提取system message（作为soul的一部分）
        sys_msg_match = re.search(r'system_message\s*=\s*["\'](.+?)["\']', content, re.DOTALL)
        if sys_msg_match:
            config['system_message'] = sys_msg_match.group(1)
        
        # 提取LLM配置
        llm_match = re.search(r'llm_config\s*=\s*(\{.+?\})', content, re.DOTALL)
        if llm_match:
            try:
                config['llm_config'] = eval(llm_match.group(1))
            except:
                pass
        
        return config
    
    def export(self, agent_name: str = None) -> AgentMemory:
        """
        将AutoGen Agent导出为OAMS格式
        
        Args:
            agent_name: 指定要导出的Agent名称
        """
        if not self.agent_config:
            self._load_config()
        
        # 1. 解析Agent身份
        identity = self._parse_identity(agent_name)
        
        # 2. 解析System Message作为Soul
        soul = self._parse_soul()
        
        # 3. 解析用户画像
        user_profile = self._parse_user_profile()
        
        # 4. 解析工作记忆（对话历史）
        working = self._parse_working_memory()
        
        # 5. 解析持久记忆
        persistent = self._parse_persistent_memory()
        
        # 6. 解析技能清单
        skills = self._parse_skills()
        
        # 构建完整记忆
        memory = AgentMemory(
            metadata=OAMSMetadata(
                standard_version="1.0",
                source_platform="autogen",
                source_agent_id=identity.get('name', agent_name or 'unknown'),
                migration_id=self._generate_uuid()
            ),
            agent_identity=AgentIdentity(
                name=identity.get('name', agent_name or 'AutoGen Agent'),
                display_name=identity.get('name', agent_name or 'AutoGen Agent'),
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
            skills_manifest=skills
        )
        
        return memory
    
    def _parse_identity(self, agent_name: str = None) -> Dict[str, Any]:
        """解析Agent身份"""
        identity = {
            'name': agent_name or self.agent_config.get('name', 'AutoGen Agent'),
            'description': self.agent_config.get('description', ''),
        }
        
        # 从system message提取描述
        if 'system_message' in self.agent_config:
            sys_msg = self.agent_config['system_message']
            identity['description'] = sys_msg[:200]  # 前200字符
        
        return identity
    
    def _parse_soul(self) -> SoulDefinition:
        """从system message解析灵魂定义"""
        soul = SoulDefinition()
        
        system_message = self.agent_config.get('system_message', '')
        if not system_message:
            return soul
        
        # 提取气质风格（前200字符作为vibe）
        soul.vibe = system_message[:200]
        
        # 提取说话风格
        # 查找类似"You should..."或"Always..."的指令
        import re
        style_patterns = re.findall(r'(?:You should|Always|Never|Please)\s+(.+?)(?:\.|\n)', system_message)
        if style_patterns:
            soul.speaking_style = '; '.join(style_patterns[:5])  # 最多5条
        
        # 提取values
        values = []
        if 'honest' in system_message.lower():
            values.append('诚实')
        if 'helpful' in system_message.lower():
            values.append('乐于助人')
        if 'accurate' in system_message.lower():
            values.append('准确')
        soul.values = values
        
        # signature line（system message的第一句）
        first_sentence = system_message.split('.')[0] if '.' in system_message else system_message[:100]
        soul.signature_line = first_sentence.strip()
        
        return soul
    
    def _parse_user_profile(self) -> UserProfile:
        """解析用户画像"""
        profile = UserProfile()
        
        # AutoGen通常没有明确的用户画像，但可以从对话历史推断
        if self.memory_path:
            user_data_file = self.memory_path / 'user_profile.json'
            if user_data_file.exists():
                with open(user_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile.name = data.get('name', '')
                    profile.location = data.get('location', '')
                    profile.timezone = data.get('timezone', '')
                    
                    # 解析偏好
                    for key, value in data.get('preferences', {}).items():
                        profile.preferences.append(Preference(
                            key=key,
                            value=value,
                            source='explicit',
                            confidence=1.0
                        ))
        
        return profile
    
    def _parse_working_memory(self) -> WorkingMemory:
        """解析工作记忆（对话历史）"""
        working = WorkingMemory()
        
        if not self.memory_path:
            return working
        
        # 加载聊天历史
        chat_file = self.memory_path / 'chat_history.json'
        if chat_file.exists():
            with open(chat_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
                # 最近7天对话
                recent_context = {
                    'last_7_days_messages': [],
                    'key_topics': []
                }
                
                for msg in history[-100:]:  # 最近100条
                    recent_context['last_7_days_messages'].append({
                        'role': msg.get('role', ''),
                        'content': msg.get('content', '')[:200],  # 摘要
                        'timestamp': msg.get('timestamp', '')
                    })
                
                working.recent_context = recent_context
        
        # 活跃项目
        projects_file = self.memory_path / 'projects.json'
        if projects_file.exists():
            with open(projects_file, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
                for proj in projects_data:
                    working.active_projects.append(Project(
                        id=proj.get('id', ''),
                        name=proj.get('name', ''),
                        status=proj.get('status', 'active'),
                        last_updated=datetime.fromisoformat(proj.get('last_updated', datetime.utcnow().isoformat())),
                        key_files=proj.get('files', []),
                        metadata=proj.get('metadata', {})
                    ))
        
        return working
    
    def _parse_persistent_memory(self) -> PersistentMemory:
        """解析持久记忆"""
        persistent = PersistentMemory()
        
        if not self.memory_path:
            return persistent
        
        # 关键决策
        decisions_file = self.memory_path / 'decisions.json'
        if decisions_file.exists():
            with open(decisions_file, 'r', encoding='utf-8') as f:
                decisions = json.load(f)
                for dec in decisions[-20:]:  # 最近20个决策
                    persistent.key_decisions.append(Decision(
                        date=datetime.fromisoformat(dec.get('date', datetime.utcnow().isoformat())),
                        decision=dec.get('decision', ''),
                        reason=dec.get('reason', ''),
                        outcome=dec.get('outcome', ''),
                        impact_score=dec.get('impact', 0.5)
                    ))
        
        # 经验教训
        lessons_file = self.memory_path / 'lessons.json'
        if lessons_file.exists():
            with open(lessons_file, 'r', encoding='utf-8') as f:
                lessons = json.load(f)
                for lesson in lessons:
                    persistent.learned_lessons.append(Lesson(
                        category=lesson.get('category', 'general'),
                        insight=lesson.get('insight', ''),
                        applied=lesson.get('applied', False),
                        confidence=lesson.get('confidence', 0.5)
                    ))
        
        return persistent
    
    def _parse_skills(self) -> SkillsManifest:
        """解析技能清单"""
        manifest = SkillsManifest()
        
        # 从配置中提取技能
        functions = self.agent_config.get('function_map', {})
        for func_name in functions:
            manifest.skills.append(SkillConfig(
                name=func_name,
                version="1.0",
                location=f"functions/{func_name}",
                config_hash=self._hash_string(str(functions[func_name])),
                customization={},
                enabled=True
            ))
        
        # 从skills目录加载
        if self.memory_path:
            skills_dir = self.memory_path / 'skills'
            if skills_dir.exists():
                for skill_file in skills_dir.glob('*.json'):
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        skill_data = json.load(f)
                        manifest.skills.append(SkillConfig(
                            name=skill_data.get('name', skill_file.stem),
                            version=skill_data.get('version', '1.0'),
                            location=str(skill_file.relative_to(self.memory_path)),
                            config_hash=self._hash_string(json.dumps(skill_data)),
                            customization=skill_data.get('config', {}),
                            enabled=skill_data.get('enabled', True)
                        ))
        
        return manifest
    
    def import_(self, oams: AgentMemory) -> None:
        """
        将OAMS格式导入为AutoGen配置
        
        生成：
        - agent_config.json
        - system_message.txt
        - function_definitions/
        """
        output_dir = Path('autogen_imported')
        output_dir.mkdir(exist_ok=True)
        
        # 1. 生成Agent配置
        config = {
            'name': oams.agent_identity.name,
            'description': oams.agent_identity.description,
            'system_message': self._build_system_message(oams.core_memory.soul),
            'llm_config': {
                'temperature': 0.7,
                'model': 'gpt-4'
            }
        }
        
        with open(output_dir / 'agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 2. 生成用户画像
        user_profile = {
            'name': oams.core_memory.user_profile.name,
            'preferences': {
                pref.key: pref.value 
                for pref in oams.core_memory.user_profile.preferences
            }
        }
        
        with open(output_dir / 'user_profile.json', 'w', encoding='utf-8') as f:
            json.dump(user_profile, f, indent=2, ensure_ascii=False)
        
        # 3. 生成技能定义
        functions_dir = output_dir / 'functions'
        functions_dir.mkdir(exist_ok=True)
        
        for skill in oams.skills_manifest.skills:
            func_def = {
                'name': skill.name,
                'description': f'Function {skill.name}',
                'parameters': skill.customization
            }
            
            with open(functions_dir / f'{skill.name}.json', 'w', encoding='utf-8') as f:
                json.dump(func_def, f, indent=2)
        
        print(f"✅ AutoGen配置已生成: {output_dir.absolute()}")
    
    def _build_system_message(self, soul: SoulDefinition) -> str:
        """从Soul构建System Message"""
        parts = []
        
        if soul.signature_line:
            parts.append(soul.signature_line)
        
        if soul.vibe:
            parts.append(f"\n风格: {soul.vibe}")
        
        if soul.values:
            parts.append(f"\n价值观: {', '.join(soul.values)}")
        
        if soul.speaking_style:
            parts.append(f"\n说话方式: {soul.speaking_style}")
        
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
    adapter = AutoGenAdapter(
        config_path="./autogen_config.json",
        memory_path="./autogen_memory"
    )
    
    if adapter.validate():
        memory = adapter.export("my_autogen_agent")
        
        # 保存为OAMS文件
        oams_file = "my_agent.oams"
        with open(oams_file, 'w', encoding='utf-8') as f:
            json.dump(memory.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 成功导出到 {oams_file}")
    
    # 导入示例
    # with open("xiaoqian.oams", 'r') as f:
    #     oams_data = json.load(f)
    #     memory = AgentMemory.from_dict(oams_data)
    #     adapter.import_(memory)
