import json
import os
from pathlib import Path

# Configuration file path
CONFIG_FILE = "./config/settings.json"

# Default configuration values
DEFAULT_CONFIG = {
    "whisper_model_size": "base",
    "use_ollama": False,
    "ollama_model": "llama3",
    "ollama_host": "localhost:11434"
}

class ConfigManager:
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or return defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    final_config = DEFAULT_CONFIG.copy()
                    final_config.update(loaded_config)
                    return final_config
            else:
                # Create config file with defaults if it doesn't exist
                self.save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save it"""
        self.config[key] = value
        self.save_config(self.config)
    
    def update(self, new_config):
        """Update multiple configuration values"""
        self.config.update(new_config)
        self.save_config(self.config)

# Global configuration instance
config_manager = ConfigManager()