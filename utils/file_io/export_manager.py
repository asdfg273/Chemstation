import csv
import os
from datetime import datetime

class ExportManager:
    """结果导出管理器"""
    
    def __init__(self):
        self.export_dir = "export_results"
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def export_csv(self, data, filename=None, headers=None):
        """导出数据为CSV格式"""
        if not data:
            return None
        
        # 自动生成文件名
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 确保文件名以.csv结尾
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        # 完整文件路径
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # 如果没有指定标题，自动从第一个数据项中提取键
                if not headers:
                    headers = list(data[0].keys())
                
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                
                # 写入标题行
                writer.writeheader()
                
                # 写入数据行
                for row in data:
                    # 确保只写入标题中包含的字段
                    row_data = {k: v for k, v in row.items() if k in headers}
                    writer.writerow(row_data)
            
            return filepath
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return None
    
    def export_pdf(self, data, filename=None, title="查询结果"):
        """导出数据为PDF格式"""
        # 这里简化处理，实际需要使用reportlab或其他PDF生成库
        # 由于PDF生成较为复杂，这里返回模拟数据
        
        if not data:
            return None
        
        # 自动生成文件名
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 确保文件名以.pdf结尾
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        # 完整文件路径
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            # 实际实现需要使用reportlab或其他PDF生成库
            # 这里创建一个简单的文本文件模拟PDF生成
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                for i, item in enumerate(data, 1):
                    f.write(f"## 结果 {i}\n")
                    for key, value in item.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n" + "="*50 + "\n\n")
            
            return filepath
        except Exception as e:
            print(f"导出PDF失败: {e}")
            return None
    
    def export_text(self, data, filename=None, title="查询结果"):
        """导出数据为文本格式"""
        if not data:
            return None
        
        # 自动生成文件名
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 确保文件名以.txt结尾
        if not filename.lower().endswith('.txt'):
            filename += '.txt'
        
        # 完整文件路径
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                for i, item in enumerate(data, 1):
                    f.write(f"## 结果 {i}\n")
                    for key, value in item.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n" + "="*50 + "\n\n")
            
            return filepath
        except Exception as e:
            print(f"导出文本失败: {e}")
            return None
    
    def get_export_formats(self):
        """获取支持的导出格式"""
        return [
            {"name": "CSV", "extension": ".csv", "func": self.export_csv},
            {"name": "PDF", "extension": ".pdf", "func": self.export_pdf},
            {"name": "文本文件", "extension": ".txt", "func": self.export_text}
        ]
    
    def export_data(self, data, export_format, filename=None, headers=None, title="查询结果"):
        """根据指定格式导出数据"""
        formats = {
            "csv": lambda: self.export_csv(data, filename, headers),
            "pdf": lambda: self.export_pdf(data, filename, title),
            "txt": lambda: self.export_text(data, filename, title)
        }
        
        export_func = formats.get(export_format.lower())
        if export_func:
            return export_func()
        else:
            print(f"不支持的导出格式: {export_format}")
            return None
