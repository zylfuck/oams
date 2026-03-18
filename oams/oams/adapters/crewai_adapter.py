# crewai_adapter.py
"""
CrewAI → OAMS 适配器（计划中）
将CrewAI的Crew、Agent、Task配置导出为OAMS格式

注意：此适配器目前为计划实现，需要CrewAI提供更稳定的API接口
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

from oams.core import (
    AgentMemory, OAMSMetadata, AgentIdentity, CoreMemory,
    WorkingMemory, PersistentMemory, SkillsManifest,
    SoulDefinition, UserProfile, Preference, Project,
    Decision, Lesson, SkillConfig, Task
)
from oams.adapters.base import BaseAdapter


class CrewAIAdapter(BaseAdapter):
    """
    CrewAI → OAMS 适配器（计划中）
    
    CrewAI独特概念：
    - Crew：一组协作的Agent
    - Agent：具有特定角色的工作者
    - Task：分配给Agent的任务
    - Process：任务执行流程（sequential/hierarchical）
    
    映射策略：
    - Crew名称 → Agent名称（组合）
    - Agent角色描述 → Soul.vibe
    - Task历史 → WorkingMemory
    - Tools → SkillsManifest
    """
    
    def __init__(self, crew_config_path: str = None, crew_memory_path: str = None):
        """
        初始化适配器
        
        Args:
            crew_config_path: Crew配置文件（Python或YAML）
            crew_memory_path: Crew执行历史存储路径
        """
        self.crew_config_path = Path(crew_config_path) if crew_config_path else None
        self.crew_memory_path = Path(crew_memory_path) if crew_memory_path else None
        
        self.crew_data = {}
        self.agents = []
        self.tasks = []
        self.execution_history = []
    
    def validate(self) -> bool:
        """验证源数据完整性"""
        if not self.crew_config_path and not self.crew_memory_path:
            raise ValueError("必须提供crew_config_path或crew_memory_path")
        
        # CrewAI配置通常是Python文件
        if self.crew_config_path:
            if not self.crew_config_path.exists():
                raise FileNotFoundError(f"Crew配置不存在: {self.crew_config_path}")
            
            if self.crew_config_path.suffix not in ['.py', '.yaml', '.yml', '.json']:
                raise ValueError("CrewAI配置必须是.py、.yaml或.json格式")
        
        return True
    
    def export(self, crew_name: str = None) -> List[AgentMemory]:
        """
        将CrewAI Crew导出为OAMS格式
        
        CrewAI的特殊性：一个Crew包含多个Agent
        因此返回List[AgentMemory]而非单个
        
        Args:
            crew_name: 指定Crew名称
        """
        # 加载配置
        self._load_crew_config()
        
        memories = []
        
        # 为每个Agent创建记忆
        for agent_data in self.agents:
            memory = self._export_single_agent(agent_data)
            memories.append(memory)
        
        return memories
    
    def _load_crew_config(self) -> None:
        """加载CrewAI配置"""
        if not self.crew_config_path:
            return
        
        if self.crew_config_path.suffix == '.py':
            self._parse_python_crew()
        elif self.crew_config_path.suffix in ['.yaml', '.yml']:
            self._parse_yaml_crew()
        elif self.crew_config_path.suffix == '.json':
            with open(self.crew_config_path, 'r', encoding='utf-8') as f:
                self.crew_data = json.load(f)
                self.agents = self.crew_data.get('agents', [])
                self.tasks = self.crew_data.get('tasks', [])
    
    def _parse_python_crew(self) -> None:
        """解析Python格式的Crew配置"""
        # 注意：这需要安全的代码分析或AST解析
        # 当前为简化实现
        content = self.crew_config_path.read_text(encoding='utf-8')
        
        # 提取Agent定义
        import re
        agent_pattern = r'Agent\(\s*[^)]*role\s*=\s*["\'](.+?)["\'][^)]*\)'
        roles = re.findall(agent_pattern, content)
        
        for role in roles:
            self.agents.append({
                'role': role,
                'name': role.replace(' ', '_').lower(),
                'source': 'parsed_from_python'
            })
        
        # 提取Task定义
        task_pattern = r'Task\(\s*[^)]*description\s*=\s*["\'](.+?)["\'][^)]*\)'
        task_descs = re.findall(task_pattern, content)
        
        for desc in task_descs:
            self.tasks.append({
                'description': desc,
                'status': 'unknown'
            })
    
    def _parse_yaml_crew(self) -> None:
        """解析YAML格式的Crew配置"""
        import yaml
        
        with open(self.crew_config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.crew_data = data
        self.agents = data.get('agents', [])
        self.tasks = data.get('tasks', [])
    
    def _export_single_agent(self, agent_data: Dict) -> AgentMemory:
        """导出单个Agent"""
        agent_name = agent_data.get('name', agent_data.get('role', 'Unknown'))
        
        # 1. 解析身份
        identity = self._parse_agent_identity(agent_data)
        
        # 2. 解析角色为Soul
        soul = self._parse_agent_soul(agent_data)
        
        # 3. 解析任务历史
        working = self._parse_task_memory(agent_data)
        
        # 4. 解析工具
        skills = self._parse_agent_tools(agent_data)
        
        memory = AgentMemory(
            metadata=OAMSMetadata(
                standard_version="1.0",
                source_platform="crewai",
                source_agent_id=agent_name,
                migration_id=self._generate_uuid()
            ),
            agent_identity=AgentIdentity(
                name=agent_name,
                display_name=agent_data.get('role', agent_name),
                description=agent_data.get('backstory', ''),
                version="1.0",
                created_date=datetime.utcnow(),
                owner_verification={}
            ),
            core_memory=CoreMemory(
                soul=soul,
                user_profile=UserProfile()  # CrewAI Agent通常没有用户画像
            ),
            working_memory=working,
            persistent_memory=PersistentMemory(),
            skills_manifest=skills
        )
        
        return memory
    
    def _parse_agent_identity(self, agent_data: Dict) -> Dict:
        """解析Agent身份"""
        return {
            'name': agent_data.get('name', 'crew_agent'),
            'role': agent_data.get('role', ''),
            'goal': agent_data.get('goal', ''),
            'backstory': agent_data.get('backstory', '')
        }
    
    def _parse_agent_soul(self, agent_data: Dict) -> SoulDefinition:
        """从角色定义解析Soul"""
        soul = SoulDefinition()
        
        # 角色作为vibe
        role = agent_data.get('role', '')
        backstory = agent_data.get('backstory', '')
        goal = agent_data.get('goal', '')
        
        soul.vibe = f"{role}. {backstory[:150]}"
        
        # Goal作为signature
        if goal:
            soul.signature_line = goal[:100]
        
        # 从backstory提取values
        import re
        values = re.findall(r'(\w+):\s*(.+?)(?:\n|$)', backstory)
        soul.values = [f"{v[0]}: {v[1]}" for v in values[:5]]
        
        # 说话风格
        soul.speaking_style = f"作为{role}的协作方式"
        
        return soul
    
    def _parse_task_memory(self, agent_data: Dict) -> WorkingMemory:
        """解析任务执行历史"""
        working = WorkingMemory()
        
        # 加载执行历史
        if self.crew_memory_path:
            history_file = self.crew_memory_path / 'execution_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    
                    # 找到该Agent的任务
                    agent_tasks = [
                        h for h in history 
                        if h.get('agent') == agent_data.get('name')
                    ]
                    
                    for task in agent_tasks[-10:]:  # 最近10个任务
                        working.ongoing_tasks.append({
                            'description': task.get('task', ''),
                            'status': task.get('status', 'completed'),
                            'output': task.get('output', '')[:200],
                            'timestamp': task.get('timestamp', '')
                        })
        
        return working
    
    def _parse_agent_tools(self, agent_data: Dict) -> SkillsManifest:
        """解析Agent工具"""
        manifest = SkillsManifest()
        
        tools = agent_data.get('tools', [])
        for tool_name in tools:
            manifest.skills.append(SkillConfig(
                name=tool_name,
                version="1.0",
                location=f"tools/{tool_name}",
                config_hash=self._hash_string(tool_name),
                enabled=True
            ))
        
        return manifest
    
    def import_(self, oams: AgentMemory) -> None:
        """
        将OAMS导入为CrewAI配置
        
        生成：
        - crew_config.py
        - agents/{agent_name}.yaml
        """
        output_dir = Path('crewai_imported')
        output_dir.mkdir(exist_ok=True)
        
        # 生成Agent配置
        agent_yaml = f"""# CrewAI Agent配置
name: {oams.agent_identity.name}
role: {oams.agent_identity.display_name}
goal: {oams.core_memory.soul.signature_line or '协助完成任务'}
backstory: |
  {oams.core_memory.soul.vibe}

# 工具
tools:
{chr(10).join(['  - ' + s.name for s in oams.skills_manifest.skills])}

# 设置
allow_delegation: true
verbose: true
"""
        
        agents_dir = output_dir / 'agents'
        agents_dir.mkdir(exist_ok=True)
        
        with open(agents_dir / f'{oams.agent_identity.name}.yaml', 'w', encoding='utf-8') as f:
            f.write(agent_yaml)
        
        print(f"✅ CrewAI配置已生成: {output_dir.absolute()}")
    
    def _generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())
    
    def _hash_string(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# 注意事项（计划中实现）
"""
TODO List for Full Implementation:

1. 等待CrewAI稳定API
   - 当前CrewAI的API变化较快
   - 需要等1.0版本后正式实现

2. 需要解决的技术问题：
   - Python配置文件的AST安全解析
   - Crew级别vs Agent级别的映射
   - 多Agent协作历史的存储
   - Task依赖关系的表达

3. 建议的临时方案：
   - 使用YAML配置而非Python
   - 手动导出关键Agent
   - 通过memory_path补充历史

4. 未来功能：
   - 支持Crew级别迁移（多Agent一起）
   - Process配置导出（sequential/hierarchical）
   - 任务依赖图（DAG）导出
"""

if __name__ == "__main__":
    print("CrewAI Adapter - 计划中实现")
    print("当前状态：等待CrewAI 1.0稳定API")
    print("预计可用：2026年Q2")
