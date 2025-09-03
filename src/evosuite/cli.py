"""EvoSuite command-line interface."""

import click
from pathlib import Path
from typing import Optional

from .agent_os.config import load_agent_os_config
from .agent_os.coordinator import AgentCoordinator


@click.group()
@click.version_option()
def main():
    """EvoSuite: Evolutionary Optimization Framework."""
    pass


@main.command()
@click.option("--workspace", "-w", type=click.Path(exists=True, path_type=Path), 
              default=Path.cwd(), help="Workspace directory")
@click.option("--show-provenance", is_flag=True, help="Show configuration provenance")
def config(workspace: Path, show_provenance: bool):
    """Show current configuration."""
    cfg = load_agent_os_config(workspace)
    
    if show_provenance:
        click.echo(f"Configuration sources: {cfg.get('_provenance', [])}")
        click.echo()
    
    # Remove internal keys for display
    display_cfg = {k: v for k, v in cfg.items() if not k.startswith('_')}
    
    import json
    click.echo(json.dumps(display_cfg, indent=2))


@main.command()
@click.option("--workspace", "-w", type=click.Path(exists=True, path_type=Path),
              default=Path.cwd(), help="Workspace directory")
def init(workspace: Path):
    """Initialize Agent OS environment."""
    click.echo(f"Initializing Agent OS in {workspace}")
    
    # Create .agent-os directory structure
    agent_os_dir = workspace / ".agent-os"
    agent_os_dir.mkdir(exist_ok=True)
    
    for subdir in ["specs", "tasks", "standards"]:
        (agent_os_dir / subdir).mkdir(exist_ok=True)
    
    # Create basic config if not exists
    config_file = agent_os_dir / "config.yaml"
    if not config_file.exists():
        config_content = """# Agent OS Configuration
version: 1
logging:
  level: INFO
sampling:
  default_profile: deterministic_single
"""
        config_file.write_text(config_content)
    
    click.echo("✅ Agent OS initialized successfully")


@main.command()
def plugins():
    """List available plugins."""
    try:
        import pkg_resources
        plugins = list(pkg_resources.iter_entry_points('evosuite.plugins'))
        
        if plugins:
            click.echo("Available plugins:")
            for plugin in plugins:
                click.echo(f"  {plugin.name} = {plugin.module_name}")
        else:
            click.echo("No plugins found. Install evosuite-plugins-official or evosuite-providers.")
    except ImportError:
        click.echo("Plugin discovery requires setuptools/pkg_resources")


if __name__ == "__main__":
    main()