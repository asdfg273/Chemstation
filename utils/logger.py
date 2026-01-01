import logging
import json
import os
from datetime import datetime
from functools import wraps

class APILogger:
    """API调用日志系统"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 日志文件路径
        log_file = os.path.join(self.log_dir, f"api_log_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 创建日志记录器
        self.logger = logging.getLogger("APILogger")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_api_call(self, endpoint, method, params=None, headers=None, response=None, 
                    status_code=None, response_time=None, error=None, api_type="unknown"):
        """记录API调用"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "api_type": api_type,
            "endpoint": endpoint,
            "method": method,
            "params": params if params else {},
            "headers": headers if headers else {},
            "status_code": status_code,
            "response_time": response_time,
            "error": str(error) if error else None,
            "response_summary": self._get_response_summary(response)
        }
        
        # 记录日志
        log_message = json.dumps(log_data, ensure_ascii=False)
        if error:
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)
    
    def _get_response_summary(self, response):
        """获取响应摘要"""
        if not response:
            return None
        
        if isinstance(response, dict):
            # 只返回关键信息，避免日志过大
            summary = {}
            if "choices" in response:
                summary["choices_count"] = len(response["choices"])
                if response["choices"]:
                    summary["first_choice_type"] = type(response["choices"][0]).__name__
            elif "data" in response:
                summary["data_count"] = len(response["data"])
            elif "PC_Compounds" in response:
                summary["compounds_count"] = len(response["PC_Compounds"])
            summary["keys"] = list(response.keys())[:5]  # 最多显示5个键
            return summary
        elif isinstance(response, list):
            return f"List with {len(response)} items"
        elif hasattr(response, "status_code"):
            # requests.Response对象
            return {
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(response.content) if hasattr(response, "content") else 0
            }
        else:
            return str(type(response).__name__)
    
    def api_log_decorator(self, api_type="unknown"):
        """API调用装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                endpoint = kwargs.get("url", "")
                method = kwargs.get("method", "GET")
                
                # 提取参数
                params = kwargs.get("params", {})
                data = kwargs.get("data", {})
                json_data = kwargs.get("json", {})
                headers = kwargs.get("headers", {})
                
                full_params = {}
                if params:
                    full_params["params"] = params
                if data:
                    full_params["data"] = data
                if json_data:
                    full_params["json"] = json_data
                
                try:
                    response = func(*args, **kwargs)
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    # 提取状态码
                    status_code = response.status_code if hasattr(response, "status_code") else None
                    
                    # 记录成功日志
                    self.log_api_call(
                        endpoint=endpoint,
                        method=method,
                        params=full_params,
                        headers=headers,
                        response=response,
                        status_code=status_code,
                        response_time=response_time,
                        api_type=api_type
                    )
                    
                    return response
                except Exception as e:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    # 记录错误日志
                    self.log_api_call(
                        endpoint=endpoint,
                        method=method,
                        params=full_params,
                        headers=headers,
                        error=e,
                        response_time=response_time,
                        api_type=api_type
                    )
                    
                    raise
            return wrapper
        return decorator

# 创建全局API日志记录器实例
api_logger = APILogger()