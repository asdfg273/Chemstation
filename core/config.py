import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "auto_save": {
                "enabled": True,
                "interval": 5,  # 分钟
                "max_versions": 10
            },
            "network": {
                "timeout": 30,  # 秒
                "max_results": 20
            },
            "ai": {
                "api_key": "",
                "base_url": "https://api.siliconflow.cn/v1",
                "timeout": 60,  # 秒
                "max_history": 50
            },
            "API": {
                "provider": "Siliconflow",
                "silicon_flow_api_key": "",
                "silicon_flow_api_base": "https://api.siliconflow.cn/v1",
                "gemini_api_key": "",
                "ollama_api_base": "http://localhost:11434"
            }
        }
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()

    def save_config(self, config=None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key, default=None):
        """获取配置值，支持嵌套键，如 'auto_save.enabled'"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key, value):
        """设置配置值，支持嵌套键"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()

    def reset(self):
        """重置配置为默认值"""
        self.config = self.default_config.copy()
        self.save_config()

# 全局配置实例
config_manager = ConfigManager()
