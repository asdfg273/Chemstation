import os
import json
from datetime import datetime
from core.config import config_manager

class HistoryManager:
    """AI交互历史管理器"""
    
    def __init__(self, history_dir="data/ai_history"):
        self.history_dir = history_dir
        
        # 创建历史记录目录
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
        
        # 最大历史记录数量
        self.max_history = config_manager.get("ai.max_history", 50)
        
        # 当前会话ID
        self.current_session_id = None
        self.current_history = []
    
    def create_new_session(self, session_name=None):
        """创建新的会话"""
        # 生成会话ID
        if session_name:
            # 使用自定义会话名称，添加时间戳以确保唯一性
            self.current_session_id = f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            # 使用时间戳作为会话ID
            self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 初始化当前历史记录
        self.current_history = []
        
        return self.current_session_id
    
    def add_message(self, role, content):
        """添加消息到当前会话"""
        if not self.current_session_id:
            # 如果没有当前会话，创建一个新会话
            self.create_new_session()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.current_history.append(message)
        
        # 保存历史记录
        self.save_current_history()
        
        return message
    
    def get_current_history(self):
        """获取当前会话历史"""
        return self.current_history.copy()
    
    def get_history_by_session(self, session_id):
        """根据会话ID获取历史记录"""
        history_file = os.path.join(self.history_dir, f"{session_id}.json")
        
        if not os.path.exists(history_file):
            return None
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载会话历史失败: {e}")
            return None
    
    def save_current_history(self):
        """保存当前会话历史"""
        if not self.current_session_id:
            return False
        
        history_file = os.path.join(self.history_dir, f"{self.current_session_id}.json")
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_history, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存会话历史失败: {e}")
            return False
    
    def load_session(self, session_id):
        """加载指定会话"""
        history = self.get_history_by_session(session_id)
        if history:
            self.current_session_id = session_id
            self.current_history = history
            return True
        else:
            return False
    
    def list_sessions(self):
        """列出所有会话"""
        sessions = []
        
        try:
            # 获取所有历史记录文件
            files = [f for f in os.listdir(self.history_dir) if f.endswith('.json')]
            
            for file in files:
                session_id = os.path.splitext(file)[0]
                history_file = os.path.join(self.history_dir, file)
                
                # 获取文件修改时间
                mod_time = os.path.getmtime(history_file)
                mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                # 获取会话历史的基本信息
                history = self.get_history_by_session(session_id)
                if history:
                    # 计算消息数量
                    message_count = len(history)
                    # 获取第一个和最后一个消息的时间
                    first_message_time = history[0]["timestamp"] if history else ""
                    last_message_time = history[-1]["timestamp"] if history else ""
                    
                    sessions.append({
                        "session_id": session_id,
                        "message_count": message_count,
                        "created_at": first_message_time,
                        "last_modified": last_message_time,
                        "file_modified": mod_time_str
                    })
            
            # 按最后修改时间降序排序
            sessions.sort(key=lambda x: x["last_modified"], reverse=True)
            
            return sessions
        except Exception as e:
            print(f"列出会话失败: {e}")
            return []
    
    def delete_session(self, session_id):
        """删除指定会话"""
        history_file = os.path.join(self.history_dir, f"{session_id}.json")
        
        if not os.path.exists(history_file):
            return False
        
        try:
            os.remove(history_file)
            
            # 如果删除的是当前会话，重置当前会话
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.current_history = []
            
            return True
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False
    
    def clear_current_history(self):
        """清空当前会话历史"""
        if self.current_session_id:
            self.current_history = []
            self.save_current_history()
            return True
        else:
            return False
    
    def export_history(self, session_id=None, file_path=None):
        """导出历史记录到文件"""
        if not file_path:
            file_path = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if session_id:
            # 导出指定会话的历史记录
            history = self.get_history_by_session(session_id)
            if not history:
                return None
            
            export_data = {
                "session_id": session_id,
                "messages": history
            }
        elif self.current_session_id:
            # 导出当前会话的历史记录
            export_data = {
                "session_id": self.current_session_id,
                "messages": self.current_history
            }
        else:
            # 导出所有会话的历史记录
            export_data = {
                "all_sessions": True,
                "sessions": {}
            }
            
            sessions = self.list_sessions()
            for session in sessions:
                session_id = session["session_id"]
                history = self.get_history_by_session(session_id)
                if history:
                    export_data["sessions"][session_id] = history
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            return file_path
        except Exception as e:
            print(f"导出历史记录失败: {e}")
            return None
    
    def import_history(self, file_path):
        """从文件导入历史记录"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if "all_sessions" in imported_data and imported_data["all_sessions"]:
                # 导入所有会话
                for session_id, history in imported_data["sessions"].items():
                    # 保存导入的历史记录
                    history_file = os.path.join(self.history_dir, f"{session_id}.json")
                    with open(history_file, 'w', encoding='utf-8') as f:
                        json.dump(history, f, indent=4, ensure_ascii=False)
            else:
                # 导入单个会话
                session_id = imported_data.get("session_id", f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                history = imported_data.get("messages", [])
                
                # 保存导入的历史记录
                history_file = os.path.join(self.history_dir, f"{session_id}.json")
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导入历史记录失败: {e}")
            return False
    
    def search_history(self, keyword, session_id=None):
        """搜索历史记录"""
        results = []
        
        if session_id:
            # 在指定会话中搜索
            history = self.get_history_by_session(session_id)
            if history:
                for i, message in enumerate(history):
                    if keyword.lower() in message["content"].lower():
                        results.append({
                            "session_id": session_id,
                            "message_index": i,
                            "message": message
                        })
        else:
            # 在所有会话中搜索
            sessions = self.list_sessions()
            for session in sessions:
                history = self.get_history_by_session(session["session_id"])
                if history:
                    for i, message in enumerate(history):
                        if keyword.lower() in message["content"].lower():
                            results.append({
                                "session_id": session["session_id"],
                                "message_index": i,
                                "message": message
                            })
        
        return results
    
    def cleanup_old_history(self):
        """清理旧的历史记录，只保留最新的N个会话"""
        try:
            sessions = self.list_sessions()
            
            if len(sessions) > self.max_history:
                # 需要清理的会话数量
                sessions_to_delete = len(sessions) - self.max_history
                
                # 获取需要删除的会话ID（最旧的会话）
                old_sessions = sessions[-sessions_to_delete:]
                
                for session in old_sessions:
                    self.delete_session(session["session_id"])
            
            return True
        except Exception as e:
            print(f"清理旧历史记录失败: {e}")
            return False
    
    def get_current_session_info(self):
        """获取当前会话信息"""
        if not self.current_session_id:
            return None
        
        return {
            "session_id": self.current_session_id,
            "message_count": len(self.current_history),
            "created_at": self.current_history[0]["timestamp"] if self.current_history else "",
            "last_message": self.current_history[-1]["timestamp"] if self.current_history else ""
        }
    
    def switch_session(self, session_id):
        """切换到指定会话"""
        if session_id not in [s["session_id"] for s in self.list_sessions()]:
            # 会话不存在
            return False
        
        # 保存当前会话
        if self.current_session_id:
            self.save_current_history()
        
        # 加载新会话
        return self.load_session(session_id)
    
    def get_session_name(self, session_id):
        """获取会话的可读名称"""
        # 从会话ID中提取名称（如果有）
        if "_" in session_id:
            # 分割会话ID，尝试提取有意义的名称
            parts = session_id.split("_")
            # 检查前几个部分是否构成一个合理的名称
            potential_name = "_".join(parts[:-2])  # 假设最后两个部分是时间戳
            if len(potential_name) > 0 and not potential_name.isdigit():
                return potential_name
        
        # 如果无法提取有意义的名称，返回会话ID的前15个字符
        return session_id[:15] + "..." if len(session_id) > 15 else session_id