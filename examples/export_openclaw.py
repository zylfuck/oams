# Example: Export OpenClaw Agent to OAMS

from oams.adapters.openclaw import OpenClawAdapter

# Initialize adapter with workspace path
adapter = OpenClawAdapter("/root/.openclaw/workspace")

# Validate source data
if adapter.validate():
    # Export agent memory
    memory = adapter.export("小钱")
    
    # Save to file
    memory.save("xiaoqian_memory.oams")
    print(f"✅ Exported {memory.agent_identity.name} successfully!")
    
    # Display summary
    print(f"\n📊 Memory Summary:")
    print(f"  - Identity: {memory.agent_identity.name}")
    print(f"  - User: {memory.core_memory.user_profile.name}")
    print(f"  - Skills: {len(memory.skills_manifest.skills)}")
    print(f"  - Tasks: {len(memory.working_memory.ongoing_tasks)}")
else:
    print("❌ Validation failed - required files missing")
