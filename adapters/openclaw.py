"""
OpenClaw Adapter for OAMS

Provides export/import functionality for OpenClaw-based AI agents.
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from oams import (
    AgentMemory, AgentIdentity, CoreMemory, WorkingMemory,
    PersistentMemory, SkillsManifest, OAMSMetadata,
    SoulDefinition, UserProfile, Preference,
    Project, Decision, Lesson,
    SkillConfig, CronJob,
    BaseAdapter
)


class OpenClawAdapter(BaseAdapter):
    """OpenClaw → OAMS Adapter"""

    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.oams = None

    def export(self, agent_name: str) -> AgentMemory:
        """Export OpenClaw agent to OAMS format"""

        # 1. Parse IDENTITY.md
        identity = self._parse_identity()

        # 2. Parse SOUL.md
        soul = self._parse_soul()

        # 3. Parse MEMORY.md
        user_profile, persistent = self._parse_memory()

        # 4. Parse memory/ directory
        working = self._parse_working_memory()

        # 5. Parse skills/
        skills = self._parse_skills()

        # 6. Build complete object
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
        """Parse IDENTITY.md"""
        identity_file = self.workspace / "IDENTITY.md"
        if not identity_file.exists():
            return {}

        content = identity_file.read_text(encoding='utf-8')
        identity = {}

        # Extract name
        name_match = re.search(r'\*\*Name:\*\*\s*(.+)', content)
        if name_match:
            identity["name"] = name_match.group(1).strip()

        # Extract description
        desc_match = re.search(r'\*\*Creature:\*\*\s*(.+)', content)
        if desc_match:
            identity["description"] = desc_match.group(1).strip()

        # Extract emoji
        emoji_match = re.search(r'\*\*Emoji:\*\*\s*(.+)', content)
        if emoji_match:
            identity["emoji"] = emoji_match.group(1).strip()

        return identity

    def _parse_soul(self) -> SoulDefinition:
        """Parse SOUL.md for soul definition"""
        soul_file = self.workspace / "SOUL.md"
        if not soul_file.exists():
            return SoulDefinition()

        content = soul_file.read_text(encoding='utf-8')
        soul = SoulDefinition()

        # Extract work mode/personality
        vibe_match = re.search(r'\*\*工作模式\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if vibe_match:
            soul.vibe = vibe_match.group(1).strip()[:200]

        # Extract language style
        style_match = re.search(r'\*\*语言风格\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if style_match:
            soul.speaking_style = style_match.group(1).strip()[:200]

        # Extract signature line
        sig_match = re.search(r'\*\*Signature Line\*\*\s*\n\>\s*(.+)', content)
        if sig_match:
            soul.signature_line = sig_match.group(1).strip()

        # Extract dislikes (for understanding boundaries)
        hate_match = re.search(r'\*\*厌恶\*\*\s*\n(.+?)(?=\n\n|##)', content, re.DOTALL)
        if hate_match:
            soul.values.append(f"厌恶: {hate_match.group(1).strip()[:100]}")

        return soul

    def _parse_memory(self) -> tuple:
        """Parse MEMORY.md"""
        memory_file = self.workspace / "MEMORY.md"
        if not memory_file.exists():
            return UserProfile(), PersistentMemory()

        content = memory_file.read_text(encoding='utf-8')

        user_profile = UserProfile()
        persistent = PersistentMemory()

        # Extract user summary table
        user_match = re.search(r'\| \*\*姓名\*\* \| (.+?) \|', content)
        if user_match:
            user_profile.name = user_match.group(1).strip()

        location_match = re.search(r'\| \*\*位置\*\* \| (.+?) \|', content)
        if location_match:
            user_profile.location = location_match.group(1).strip()

        # Extract preferences (from table or list)
        pref_matches = re.findall(r'- \*\*(.+?)\*\*[:：]\s*(.+?)(?=\n|$)', content)
        for key, value in pref_matches:
            user_profile.preferences.append(Preference(
                key=key.strip(),
                value=value.strip(),
                source="explicit",
                confidence=1.0
            ))

        # Extract key decisions
        decision_pattern = r'\| (.+?) \| (.+?) \| (.+?) \|'
        decisions = re.findall(decision_pattern, content)
        for date_str, decision, status in decisions[-10:]:  # Recent 10
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
        """Parse memory/ directory daily notes"""
        working = WorkingMemory()
        memory_dir = self.workspace / "memory"

        if not memory_dir.exists():
            return working

        # Get recent 7 days memory files
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

                # Extract TODOs
                todos = re.findall(r'- \[.\]\s*(.+)', content)

                working.ongoing_tasks.append({
                    "date": date.isoformat(),
                    "todos": todos[:10],  # Max 10
                    "source_file": str(file)
                })
            except:
                continue

        return working

    def _parse_skills(self) -> SkillsManifest:
        """Parse skills/ directory"""
        manifest = SkillsManifest()
        skills_dir = self.workspace / "skills"

        if not skills_dir.exists():
            return manifest

        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name

                # Read SKILL.md for version
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
        """Generate UUID"""
        import uuid
        return str(uuid.uuid4())

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return datetime.utcnow()

    def _hash_directory(self, path: Path) -> str:
        """Calculate directory hash"""
        hasher = hashlib.sha256()
        for file in sorted(path.rglob("*")):
            if file.is_file():
                hasher.update(file.read_bytes())
        return hasher.hexdigest()[:16]

    def import_(self, oams: AgentMemory) -> None:
        """Import OAMS format to OpenClaw files"""
        # TODO: Implement reverse conversion
        raise NotImplementedError("Import functionality coming soon")

    def validate(self) -> bool:
        """Validate source data integrity"""
        required_files = ["IDENTITY.md", "SOUL.md", "MEMORY.md"]
        for filename in required_files:
            if not (self.workspace / filename).exists():
                return False
        return True


# Example usage
if __name__ == "__main__":
    adapter = OpenClawAdapter("/root/.openclaw/workspace")
    if adapter.validate():
        memory = adapter.export("小钱")
        memory.save("/tmp/xiaoqian.oams")
        print(f"Exported {memory.agent_identity.name} successfully!")
    else:
        print("Validation failed - required files missing")
