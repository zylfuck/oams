"""
OAMS Core - OpenAgent Memory Standard

This module provides the core data structures and functionality for
AI agent memory migration.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import json
import hashlib


class MemoryType(Enum):
    CORE = "core"
    WORKING = "working"
    PERSISTENT = "persistent"
    TRANSIENT = "transient"


class RelationshipType(Enum):
    OWNER = "owner"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"


@dataclass
class OAMSMetadata:
    """Migration metadata"""
    standard_version: str = "1.0"
    export_timestamp: datetime = field(default_factory=datetime.utcnow)
    source_platform: str = ""
    source_agent_id: str = ""
    migration_id: str = ""
    signature: str = ""
    encryption_algo: str = "aes-256-gcm"
    compression_algo: str = "zstd"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "standard_version": self.standard_version,
            "export_timestamp": self.export_timestamp.isoformat(),
            "source_platform": self.source_platform,
            "source_agent_id": self.source_agent_id,
            "migration_id": self.migration_id,
            "signature": self.signature,
            "encryption_algo": self.encryption_algo,
            "compression_algo": self.compression_algo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAMSMetadata":
        return cls(
            standard_version=data.get("standard_version", "1.0"),
            export_timestamp=datetime.fromisoformat(data.get("export_timestamp", "")),
            source_platform=data.get("source_platform", ""),
            source_agent_id=data.get("source_agent_id", ""),
            migration_id=data.get("migration_id", ""),
            signature=data.get("signature", ""),
            encryption_algo=data.get("encryption_algo", "aes-256-gcm"),
            compression_algo=data.get("compression_algo", "zstd"),
        )


@dataclass
class AgentIdentity:
    """Agent identity information"""
    name: str
    display_name: str = ""
    version: str = "1.0"
    created_date: datetime = field(default_factory=datetime.utcnow)
    identity_digest: str = ""
    avatar_url: str = ""
    description: str = ""
    owner_verification: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "created_date": self.created_date.isoformat(),
            "identity_digest": self.identity_digest,
            "avatar_url": self.avatar_url,
            "description": self.description,
            "owner_verification": self.owner_verification,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            version=data.get("version", "1.0"),
            created_date=datetime.fromisoformat(data.get("created_date", "")),
            identity_digest=data.get("identity_digest", ""),
            avatar_url=data.get("avatar_url", ""),
            description=data.get("description", ""),
            owner_verification=data.get("owner_verification", {}),
        )


@dataclass
class Preference:
    """User preference setting"""
    key: str
    value: Any
    priority: str = "medium"
    source: str = "inferred"
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserProfile:
    """User profile information"""
    name: str = ""
    location: str = ""
    timezone: str = ""
    preferences: List[Preference] = field(default_factory=list)
    sensitive_dates: List[Dict] = field(default_factory=list)
    communication_style: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "timezone": self.timezone,
            "preferences": [
                {
                    "key": p.key,
                    "value": p.value,
                    "priority": p.priority,
                    "source": p.source,
                    "confidence": p.confidence,
                    "timestamp": p.timestamp.isoformat(),
                }
                for p in self.preferences
            ],
            "sensitive_dates": self.sensitive_dates,
            "communication_style": self.communication_style,
        }


@dataclass
class SoulDefinition:
    """AI soul/personality definition"""
    vibe: str = ""
    speaking_style: str = ""
    signature_line: str = ""
    values: List[str] = field(default_factory=list)
    personality_traits: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vibe": self.vibe,
            "speaking_style": self.speaking_style,
            "signature_line": self.signature_line,
            "values": self.values,
            "personality_traits": self.personality_traits,
        }


@dataclass
class CoreMemory:
    """Core memory containing soul and user profile"""
    soul: SoulDefinition = field(default_factory=SoulDefinition)
    user_profile: UserProfile = field(default_factory=UserProfile)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "soul": self.soul.to_dict(),
            "user_profile": self.user_profile.to_dict(),
        }


@dataclass
class Project:
    """Active project"""
    id: str
    name: str
    status: str
    last_updated: datetime
    key_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkingMemory:
    """Working memory for recent context"""
    active_projects: List[Project] = field(default_factory=list)
    recent_context: Dict[str, Any] = field(default_factory=dict)
    ongoing_tasks: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "last_updated": p.last_updated.isoformat(),
                    "key_files": p.key_files,
                    "metadata": p.metadata,
                }
                for p in self.active_projects
            ],
            "recent_context": self.recent_context,
            "ongoing_tasks": self.ongoing_tasks,
        }


@dataclass
class Decision:
    """Key decision record"""
    date: datetime
    decision: str
    reason: str
    outcome: str = ""
    impact_score: float = 0.0


@dataclass
class Lesson:
    """Learned lesson"""
    category: str
    insight: str
    applied: bool = False
    confidence: float = 0.5


@dataclass
class PersistentMemory:
    """Persistent long-term memory"""
    key_decisions: List[Decision] = field(default_factory=list)
    learned_lessons: List[Lesson] = field(default_factory=list)
    relationship_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_decisions": [
                {
                    "date": d.date.isoformat(),
                    "decision": d.decision,
                    "reason": d.reason,
                    "outcome": d.outcome,
                    "impact_score": d.impact_score,
                }
                for d in self.key_decisions
            ],
            "learned_lessons": [
                {
                    "category": l.category,
                    "insight": l.insight,
                    "applied": l.applied,
                    "confidence": l.confidence,
                }
                for l in self.learned_lessons
            ],
            "relationship_history": self.relationship_history,
        }


@dataclass
class SkillConfig:
    """Skill configuration"""
    name: str
    version: str
    location: str
    config_hash: str = ""
    customization: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class CronJob:
    """Scheduled task"""
    name: str
    schedule: str
    enabled: bool = True
    last_run: Optional[datetime] = None


@dataclass
class SkillsManifest:
    """Skills manifest"""
    skills: List[SkillConfig] = field(default_factory=list)
    cron_jobs: List[CronJob] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skills": [
                {
                    "name": s.name,
                    "version": s.version,
                    "location": s.location,
                    "config_hash": s.config_hash,
                    "customization": s.customization,
                    "enabled": s.enabled,
                }
                for s in self.skills
            ],
            "cron_jobs": [
                {
                    "name": c.name,
                    "schedule": c.schedule,
                    "enabled": c.enabled,
                    "last_run": c.last_run.isoformat() if c.last_run else None,
                }
                for c in self.cron_jobs
            ],
        }


@dataclass
class VectorMemory:
    """Vector memory (optional)"""
    embedding_model: str = ""
    dimension: int = 1536
    vectors: List[List[float]] = field(default_factory=list)
    index_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Complete agent memory package"""
    metadata: OAMSMetadata
    agent_identity: AgentIdentity
    core_memory: CoreMemory
    working_memory: WorkingMemory
    persistent_memory: PersistentMemory
    skills_manifest: SkillsManifest
    vector_memory: Optional[VectorMemory] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "@context": "https://schema.openagent.org/memory/1.0",
            "@type": "AgentMemory",
            "metadata": self.metadata.to_dict(),
            "agent_identity": self.agent_identity.to_dict(),
            "core_memory": self.core_memory.to_dict(),
            "working_memory": self.working_memory.to_dict(),
            "persistent_memory": self.persistent_memory.to_dict(),
            "skills_manifest": self.skills_manifest.to_dict(),
            "vector_memory": self.vector_memory.to_dict() if self.vector_memory else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMemory":
        """Create from dictionary"""
        return cls(
            metadata=OAMSMetadata.from_dict(data.get("metadata", {})),
            agent_identity=AgentIdentity.from_dict(data.get("agent_identity", {})),
            core_memory=CoreMemory(
                soul=SoulDefinition(**data.get("core_memory", {}).get("soul", {})),
                user_profile=UserProfile(**data.get("core_memory", {}).get("user_profile", {})),
            ),
            working_memory=WorkingMemory(**data.get("working_memory", {})),
            persistent_memory=PersistentMemory(**data.get("persistent_memory", {})),
            skills_manifest=SkillsManifest(**data.get("skills_manifest", {})),
            vector_memory=VectorMemory(**data.get("vector_memory")) if data.get("vector_memory") else None,
        )

    def save(self, filepath: str, compress: bool = False):
        """Save memory to file"""
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load(cls, filepath: str) -> "AgentMemory":
        """Load memory from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


class BaseAdapter:
    """Base adapter class"""

    def export(self, agent_name: str) -> AgentMemory:
        """Export to OAMS format"""
        raise NotImplementedError

    def import_(self, memory: AgentMemory) -> None:
        """Import from OAMS format"""
        raise NotImplementedError

    def validate(self) -> bool:
        """Validate source data integrity"""
        raise NotImplementedError


__all__ = [
    "AgentMemory",
    "AgentIdentity",
    "CoreMemory",
    "WorkingMemory",
    "PersistentMemory",
    "SkillsManifest",
    "OAMSMetadata",
    "BaseAdapter",
    "MemoryType",
    "RelationshipType",
]
