"""Version information for Compliance Copilot."""

__version__ = "0.1.0-alpha"

def get_version() -> str:
    """Return the current version as a string."""
    return __version__

def get_version_tuple() -> tuple:
    """Return version as tuple of integers for comparison."""
    clean_version = __version__.split('-')[0]
    return tuple(int(part) for part in clean_version.split('.'))

if __name__ == "__main__":
    print(f"Compliance Copilot version: {get_version()}")
