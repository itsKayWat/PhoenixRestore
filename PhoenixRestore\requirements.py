import subprocess
import sys
import os

def install_requirements():
    requirements = [
        'tkinter',  # Usually comes with Python
        'pillow',   # For image handling
        'pystray',  # For system tray functionality
        'pywin32',  # For Windows-specific features
        'cryptography',  # For encryption support
        'pytest',        # For testing
        'sqlalchemy',    # For database operations
        'requests',      # For API integration
        'python-ldap',   # For Active Directory integration
    ]

    print("Installing required packages...")
    
    for package in requirements:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error installing {package}: {str(e)}")

    print("\nInstallation complete!")

if __name__ == "__main__":
    install_requirements()