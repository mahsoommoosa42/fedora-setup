"""fedora-setup — Python-based Fedora developer workstation configuration.

All logic lives in Python; ``setup.sh`` and ``cleanup.sh`` are thin shell
wrappers that exec ``python3 -m fedora_setup`` and
``python3 -m fedora_setup.cleanup`` respectively.
"""

__all__ = ["__version__"]
__version__ = "0.2.0"
