import subprocess
from django.core.management.base import BaseCommand


def patched_execute(self, *args, **kwargs):
    # Run flake8 checks before any command execution
    try:
        print("Running flake8 checks...")
        subprocess.run(["flake8"], check=True)
        print("Flake8 checks passed!\n")
    except subprocess.CalledProcessError:
        print("Flake8 checks failed. Fix issues before running commands.\n")
        exit(1)  # Exit with error if checks fail

    # Proceed with the original execution
    original_execute(self, *args, **kwargs)


# Save the original execute method
original_execute = BaseCommand.execute
# Monkey patch the execute method
BaseCommand.execute = patched_execute
