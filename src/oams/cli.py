"""
OAMS CLI - Command Line Interface for OpenAgent Memory Standard

Usage:
    oams export --source openclaw --workspace /path/to/workspace --agent my-agent --output memory.oams
    oams import --target autogen --input memory.oams
    oams validate --input memory.oams
    oams inspect --input memory.oams
    oams diff memory1.oams memory2.oams
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from oams import AgentMemory


def cmd_export(args):
    """Export agent memory to OAMS format"""
    source = args.source.lower()
    
    if source == "openclaw":
        from oams.adapters.openclaw import OpenClawAdapter
        adapter = OpenClawAdapter(args.workspace)
        if not adapter.validate():
            print("❌ Validation failed - required files missing")
            return 1
        memory = adapter.export(args.agent)
    else:
        print(f"❌ Unsupported source: {source}")
        return 1
    
    # Save to file
    output_path = Path(args.output)
    memory.save(str(output_path))
    
    print(f"✅ Exported {memory.agent_identity.name} successfully!")
    print(f"📁 Saved to: {output_path.absolute()}")
    print(f"📊 Size: {output_path.stat().st_size / 1024:.1f} KB")
    return 0


def cmd_import(args):
    """Import agent memory from OAMS format"""
    target = args.target.lower()
    
    # Load memory
    memory = AgentMemory.load(args.input)
    
    if target == "openclaw":
        from oams.adapters.openclaw import OpenClawAdapter
        adapter = OpenClawAdapter(args.workspace)
        adapter.import_(memory)
    else:
        print(f"❌ Unsupported target: {target}")
        return 1
    
    print(f"✅ Imported {memory.agent_identity.name} successfully!")
    return 0


def cmd_validate(args):
    """Validate OAMS file"""
    try:
        memory = AgentMemory.load(args.input)
        
        # Run validations
        errors = []
        
        if not memory.agent_identity.name:
            errors.append("Missing agent name")
        
        if not memory.metadata.standard_version:
            errors.append("Missing standard version")
        
        if args.strict and not memory.metadata.signature:
            errors.append("Missing signature (strict mode)")
        
        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        print("✅ Valid OAMS file")
        print(f"   Agent: {memory.agent_identity.name}")
        print(f"   Version: {memory.metadata.standard_version}")
        print(f"   Exported: {memory.metadata.export_timestamp}")
        return 0
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


def cmd_inspect(args):
    """Inspect OAMS file contents"""
    try:
        memory = AgentMemory.load(args.input)
        
        print(f"{'='*60}")
        print(f"📦 OAMS Memory Package")
        print(f"{'='*60}")
        
        # Metadata
        print(f"\n📋 Metadata:")
        print(f"   Standard Version: {memory.metadata.standard_version}")
        print(f"   Exported At: {memory.metadata.export_timestamp}")
        print(f"   Source Platform: {memory.metadata.source_platform}")
        print(f"   Migration ID: {memory.metadata.migration_id}")
        
        # Identity
        print(f"\n👤 Agent Identity:")
        print(f"   Name: {memory.agent_identity.name}")
        print(f"   Display Name: {memory.agent_identity.display_name or 'N/A'}")
        print(f"   Version: {memory.agent_identity.version}")
        print(f"   Created: {memory.agent_identity.created_date}")
        
        # Core Memory
        print(f"\n🧠 Core Memory:")
        print(f"   Soul Vibe: {memory.core_memory.soul.vibe[:50]}..." if memory.core_memory.soul.vibe else "   Soul Vibe: N/A")
        print(f"   Values: {', '.join(memory.core_memory.soul.values[:3])}")
        print(f"   User: {memory.core_memory.user_profile.name or 'N/A'}")
        print(f"   Preferences: {len(memory.core_memory.user_profile.preferences)}")
        
        # Working Memory
        print(f"\n💼 Working Memory:")
        print(f"   Active Projects: {len(memory.working_memory.active_projects)}")
        print(f"   Ongoing Tasks: {len(memory.working_memory.ongoing_tasks)}")
        
        # Skills
        print(f"\n🛠️ Skills:")
        print(f"   Total Skills: {len(memory.skills_manifest.skills)}")
        for skill in memory.skills_manifest.skills[:3]:
            print(f"     - {skill.name} (v{skill.version})")
        if len(memory.skills_manifest.skills) > 3:
            print(f"     ... and {len(memory.skills_manifest.skills) - 3} more")
        
        print(f"\n{'='*60}")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to inspect: {e}")
        return 1


def cmd_diff(args):
    """Compare two OAMS files"""
    try:
        memory1 = AgentMemory.load(args.file1)
        memory2 = AgentMemory.load(args.file2)
        
        print(f"{'='*60}")
        print(f"🔍 Diff: {args.file1} vs {args.file2}")
        print(f"{'='*60}")
        
        differences = []
        
        # Compare identity
        if memory1.agent_identity.name != memory2.agent_identity.name:
            differences.append(f"Name: {memory1.agent_identity.name} → {memory2.agent_identity.name}")
        
        # Compare version
        if memory1.agent_identity.version != memory2.agent_identity.version:
            differences.append(f"Version: {memory1.agent_identity.version} → {memory2.agent_identity.version}")
        
        # Compare skills count
        skills_diff = len(memory1.skills_manifest.skills) - len(memory2.skills_manifest.skills)
        if skills_diff != 0:
            differences.append(f"Skills count: {len(memory1.skills_manifest.skills)} → {len(memory2.skills_manifest.skills)} ({skills_diff:+d})")
        
        # Compare preferences
        prefs_diff = len(memory1.core_memory.user_profile.preferences) - len(memory2.core_memory.user_profile.preferences)
        if prefs_diff != 0:
            differences.append(f"Preferences: {len(memory1.core_memory.user_profile.preferences)} → {len(memory2.core_memory.user_profile.preferences)} ({prefs_diff:+d})")
        
        if differences:
            print("\n📊 Differences found:")
            for diff in differences:
                print(f"   • {diff}")
        else:
            print("\n✅ No differences found")
        
        print(f"\n{'='*60}")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to diff: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog='oams',
        description='OpenAgent Memory Standard CLI'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export agent memory')
    export_parser.add_argument('--source', required=True, choices=['openclaw'], help='Source platform')
    export_parser.add_argument('--workspace', required=True, help='Path to workspace')
    export_parser.add_argument('--agent', required=True, help='Agent name')
    export_parser.add_argument('--output', '-o', required=True, help='Output file')
    export_parser.set_defaults(func=cmd_export)
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import agent memory')
    import_parser.add_argument('--target', required=True, choices=['openclaw'], help='Target platform')
    import_parser.add_argument('--input', '-i', required=True, help='Input OAMS file')
    import_parser.add_argument('--workspace', required=True, help='Path to workspace')
    import_parser.set_defaults(func=cmd_import)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate OAMS file')
    validate_parser.add_argument('--input', '-i', required=True, help='OAMS file to validate')
    validate_parser.add_argument('--strict', action='store_true', help='Strict validation')
    validate_parser.set_defaults(func=cmd_validate)
    
    # Inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect OAMS file')
    inspect_parser.add_argument('--input', '-i', required=True, help='OAMS file to inspect')
    inspect_parser.set_defaults(func=cmd_inspect)
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Compare two OAMS files')
    diff_parser.add_argument('file1', help='First OAMS file')
    diff_parser.add_argument('file2', help='Second OAMS file')
    diff_parser.set_defaults(func=cmd_diff)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
