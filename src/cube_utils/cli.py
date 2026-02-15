import click


@click.group()
def main():
    """MTG cube draft utilities."""


@main.command()
def packs():
    """Generate draft packs."""
    click.echo("packs command (not yet implemented)")


@main.command()
def guide():
    """Generate draft guide skeleton."""
    click.echo("guide command (not yet implemented)")
