import os
import time
import shutil
from datetime import datetime
from core.config import config_manager

class JournalManager:
    def __init__(self, journal_dir="journal_backups"):
        self.journal_dir = journal_dir
        self.main_journal_file = "journal.txt"
        self.auto_save_enabled = config_manager.get("auto_save.enabled", True)
        self.auto_save_interval = config_manager.get("auto_save.interval", 5) * 60  # 转换为秒
        self.max_versions = config_manager.get("auto_save.max_versions", 10)
        
        # 创建备份目录
        if not os.path.exists(self.journal_dir):
            os.makedirs(self.journal_dir)
        
        # 上次保存时间
        self.last_save_time = time.time()
        
        # 初始化主日志文件
        if not os.path.exists(self.main_journal_file):
            with open(self.main_journal_file, 'w', encoding='utf-8') as f:
                f.write("# 实验日志\n\n")
    
    def get_current_time_str(self):
        """获取当前时间字符串，用于版本文件名"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def save_journal(self, content, force=False):
        """保存日志内容，支持自动保存和手动保存"""
        current_time = time.time()
        
        # 检查是否需要自动保存
        if not force and self.auto_save_enabled:
            if current_time - self.last_save_time < self.auto_save_interval:
                return False
        
        try:
            # 保存主日志文件
            with open(self.main_journal_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 创建版本备份
            version_file = os.path.join(self.journal_dir, f"journal_{self.get_current_time_str()}.txt")
            shutil.copy2(self.main_journal_file, version_file)
            
            # 清理旧版本
            self.cleanup_old_versions()
            
            # 更新上次保存时间
            self.last_save_time = current_time
            
            return True
        except Exception as e:
            print(f"保存日志失败: {e}")
            return False
    
    def load_journal(self):
        """加载主日志文件内容"""
        try:
            with open(self.main_journal_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载日志失败: {e}")
            return "# 实验日志\n\n"
    
    def cleanup_old_versions(self):
        """清理旧版本，保留最近的max_versions个版本"""
        try:
            # 获取所有版本文件
            version_files = [f for f in os.listdir(self.journal_dir) 
                           if f.startswith("journal_") and f.endswith(".txt")]
            
            # 按修改时间排序（最新的在前）
            version_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.journal_dir, x)), reverse=True)
            
            # 删除超过max_versions的旧版本
            for old_file in version_files[self.max_versions:]:
                os.remove(os.path.join(self.journal_dir, old_file))
        except Exception as e:
            print(f"清理旧版本失败: {e}")
    
    def get_version_history(self):
        """获取版本历史记录，返回列表：[(版本文件名, 修改时间, 文件大小), ...]"""
        try:
            version_files = [f for f in os.listdir(self.journal_dir) 
                           if f.startswith("journal_") and f.endswith(".txt")]
            
            history = []
            for file in version_files:
                file_path = os.path.join(self.journal_dir, file)
                mod_time = os.path.getmtime(file_path)
                file_size = os.path.getsize(file_path)
                history.append((file, mod_time, file_size))
            
            # 按修改时间排序（最新的在前）
            history.sort(key=lambda x: x[1], reverse=True)
            
            return history
        except Exception as e:
            print(f"获取版本历史失败: {e}")
            return []
    
    def get_version_content(self, version_file):
        """获取指定版本的日志内容"""
        try:
            file_path = os.path.join(self.journal_dir, version_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return None
        except Exception as e:
            print(f"获取版本内容失败: {e}")
            return None
    
    def restore_version(self, version_file):
        """恢复指定版本的日志"""
        try:
            version_path = os.path.join(self.journal_dir, version_file)
            if os.path.exists(version_path):
                # 先保存当前版本
                self.save_journal(self.load_journal(), force=True)
                
                # 恢复指定版本
                shutil.copy2(version_path, self.main_journal_file)
                
                # 更新上次保存时间
                self.last_save_time = time.time()
                
                return True
            else:
                return False
        except Exception as e:
            print(f"恢复版本失败: {e}")
            return False
    
    def delete_version(self, version_file):
        """删除指定版本"""
        try:
            file_path = os.path.join(self.journal_dir, version_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            else:
                return False
        except Exception as e:
            print(f"删除版本失败: {e}")
            return False
    
    def set_auto_save(self, enabled):
        """设置自动保存开关"""
        self.auto_save_enabled = enabled
        config_manager.set("auto_save.enabled", enabled)
    
    def set_auto_save_interval(self, interval):
        """设置自动保存间隔（分钟）"""
        self.auto_save_interval = interval * 60  # 转换为秒
        config_manager.set("auto_save.interval", interval)
    
    def get_last_save_time(self):
        """获取上次保存时间"""
        return self.last_save_time
    
    def get_auto_save_status(self):
        """获取自动保存状态"""
        return {
            "enabled": self.auto_save_enabled,
            "interval": self.auto_save_interval // 60,  # 转换回分钟
            "last_save": self.last_save_time
        }
    
    def get_version_info(self, version_file):
        """获取版本文件的详细信息"""
        try:
            file_path = os.path.join(self.journal_dir, version_file)
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                file_size = os.path.getsize(file_path)
                return {
                    "filename": version_file,
                    "mod_time": mod_time,
                    "mod_time_str": datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": file_size,
                    "size_str": f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.2f} MB"
                }
            else:
                return None
        except Exception as e:
            print(f"获取版本信息失败: {e}")
            return None
