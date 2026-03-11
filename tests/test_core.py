"""
Test suite for OAMS core functionality
"""

import pytest
import tempfile
import json
from datetime import datetime
from pathlib import Path

from oams import (
    AgentMemory, AgentIdentity, CoreMemory, WorkingMemory,
    PersistentMemory, SkillsManifest, OAMSMetadata,
    SoulDefinition, UserProfile, Preference,
    SkillConfig, CronJob
)


class TestOAMSMetadata:
    """Test OAMS metadata"""
    
    def test_default_creation(self):
        meta = OAMSMetadata()
        assert meta.standard_version == "1.0"
        assert meta.encryption_algo == "aes-256-gcm"
        assert meta.compression_algo == "zstd"
    
    def test_to_dict(self):
        meta = OAMSMetadata(
            source_platform="openclaw",
            source_agent_id="test-agent"
        )
        data = meta.to_dict()
        assert data["source_platform"] == "openclaw"
        assert data["source_agent_id"] == "test-agent"
    
    def test_from_dict(self):
        data = {
            "standard_version": "1.0",
            "export_timestamp": "2026-03-11T10:00:00",
            "source_platform": "openclaw",
            "source_agent_id": "test"
        }
        meta = OAMSMetadata.from_dict(data)
        assert meta.source_platform == "openclaw"


class TestAgentIdentity:
    """Test agent identity"""
    
    def test_creation(self):
        identity = AgentIdentity(
            name="TestAgent",
            display_name="Test Agent",
            version="1.0"
        )
        assert identity.name == "TestAgent"
        assert identity.display_name == "Test Agent"
    
    def test_to_dict(self):
        identity = AgentIdentity(name="Test")
        data = identity.to_dict()
        assert data["name"] == "Test"
        assert "created_date" in data


class TestCoreMemory:
    """Test core memory"""
    
    def test_creation(self):
        soul = SoulDefinition(
            vibe="friendly",
            speaking_style="casual",
            values=["honesty", "helpfulness"]
        )
        profile = UserProfile(name="User", location="Earth")
        core = CoreMemory(soul=soul, user_profile=profile)
        
        assert core.soul.vibe == "friendly"
        assert core.user_profile.name == "User"
    
    def test_to_dict(self):
        core = CoreMemory(
            soul=SoulDefinition(vibe="test"),
            user_profile=UserProfile(name="Test")
        )
        data = core.to_dict()
        assert data["soul"]["vibe"] == "test"
        assert data["user_profile"]["name"] == "Test"


class TestAgentMemory:
    """Test complete agent memory"""
    
    @pytest.fixture
    def sample_memory(self):
        """Create a sample agent memory"""
        return AgentMemory(
            metadata=OAMSMetadata(
                source_platform="test",
                migration_id="test-uuid"
            ),
            agent_identity=AgentIdentity(
                name="TestAgent",
                version="1.0"
            ),
            core_memory=CoreMemory(
                soul=SoulDefinition(vibe="test"),
                user_profile=UserProfile(name="TestUser")
            ),
            working_memory=WorkingMemory(),
            persistent_memory=PersistentMemory(),
            skills_manifest=SkillsManifest()
        )
    
    def test_creation(self, sample_memory):
        assert sample_memory.agent_identity.name == "TestAgent"
        assert sample_memory.core_memory.user_profile.name == "TestUser"
    
    def test_to_dict(self, sample_memory):
        data = sample_memory.to_dict()
        assert data["@context"] == "https://schema.openagent.org/memory/1.0"
        assert data["agent_identity"]["name"] == "TestAgent"
    
    def test_save_and_load(self, sample_memory, tmp_path):
        # Save
        file_path = tmp_path / "test.oams"
        sample_memory.save(str(file_path))
        
        # Verify file exists
        assert file_path.exists()
        
        # Load
        loaded = AgentMemory.load(str(file_path))
        assert loaded.agent_identity.name == "TestAgent"
        assert loaded.core_memory.soul.vibe == "test"
    
    def test_json_structure(self, sample_memory):
        """Verify JSON structure is correct"""
        data = sample_memory.to_dict()
        
        # Check required fields
        assert "@context" in data
        assert "@type" in data
        assert "metadata" in data
        assert "agent_identity" in data
        assert "core_memory" in data
        assert "working_memory" in data
        assert "persistent_memory" in data
        assert "skills_manifest" in data


class TestSkillsManifest:
    """Test skills manifest"""
    
    def test_creation(self):
        skills = [
            SkillConfig(name="skill1", version="1.0", location="skills/skill1"),
            SkillConfig(name="skill2", version="2.0", location="skills/skill2")
        ]
        crons = [
            CronJob(name="daily", schedule="0 0 * * *")
        ]
        manifest = SkillsManifest(skills=skills, cron_jobs=crons)
        
        assert len(manifest.skills) == 2
        assert len(manifest.cron_jobs) == 1
    
    def test_to_dict(self):
        manifest = SkillsManifest(
            skills=[SkillConfig(name="test", version="1.0", location="test")]
        )
        data = manifest.to_dict()
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "test"


class TestPreference:
    """Test preference"""
    
    def test_creation(self):
        pref = Preference(
            key="communication_style",
            value="concise",
            priority="high",
            confidence=0.95
        )
        assert pref.key == "communication_style"
        assert pref.value == "concise"
        assert pref.confidence == 0.95


class TestValidation:
    """Test validation scenarios"""
    
    def test_empty_agent_name(self):
        """Empty agent name should be handled"""
        identity = AgentIdentity(name="")
        assert identity.name == ""
    
    def test_missing_optional_fields(self):
        """Optional fields should have defaults"""
        meta = OAMSMetadata()
        assert meta.migration_id == ""
        assert meta.signature == ""


class TestFileOperations:
    """Test file I/O operations"""
    
    def test_save_creates_valid_json(self, tmp_path):
        """Saved file should be valid JSON"""
        memory = AgentMemory(
            metadata=OAMSMetadata(),
            agent_identity=AgentIdentity(name="Test"),
            core_memory=CoreMemory(),
            working_memory=WorkingMemory(),
            persistent_memory=PersistentMemory(),
            skills_manifest=SkillsManifest()
        )
        
        file_path = tmp_path / "test.oams"
        memory.save(str(file_path))
        
        # Verify it's valid JSON
        with open(file_path) as f:
            data = json.load(f)
        
        assert data["agent_identity"]["name"] == "Test"
    
    def test_load_nonexistent_file(self, tmp_path):
        """Loading nonexistent file should raise error"""
        with pytest.raises(FileNotFoundError):
            AgentMemory.load(str(tmp_path / "nonexistent.oams"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
