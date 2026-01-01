import os
import json
from core.config import config_manager

class PromptManager:
    """提示词管理器"""
    
    def __init__(self, prompt_dir="data/prompt_templates"):
        self.prompt_dir = prompt_dir
        
        # 创建提示词目录
        if not os.path.exists(self.prompt_dir):
            os.makedirs(self.prompt_dir)
        
        # 预设领域列表
        self.domains = [
            "材料科学",
            "化学工程",
            "有机化学",
            "无机化学",
            "分析化学",
            "物理化学",
            "环境化学",
            "生物化学"
        ]
        
        # 初始化示例提示词
        self.init_example_prompts()
    
    def init_example_prompts(self):
        """初始化示例提示词"""
        # 示例提示词模板
        examples = {
            "材料科学": [
                {
                    "name": "材料合成方案设计",
                    "prompt": "请设计一种合成[材料名称]的方案，包括反应路径、实验条件、预期产率和可能的副产物。\n\n要求：\n1. 详细的步骤说明\n2. 关键反应条件（温度、压力、催化剂等）\n3. 安全注意事项\n4. 表征方法建议",
                    "tags": ["合成", "材料", "方案设计"],
                    "created_at": "2024-01-01"
                },
                {
                    "name": "材料性能预测",
                    "prompt": "请预测[材料名称]的主要物理和化学性能，包括：\n1. 力学性能\n2. 热性能\n3. 电学性能\n4. 化学稳定性\n5. 应用前景\n\n已知信息：\n[已知信息]",
                    "tags": ["性能预测", "材料", "表征"],
                    "created_at": "2024-01-01"
                }
            ],
            "化学工程": [
                {
                    "name": "反应工艺优化",
                    "prompt": "请优化以下化学反应的工艺条件：\n\n反应名称：[反应名称]\n反应物：[反应物]\n当前条件：[当前条件]\n存在问题：[存在问题]\n\n要求：\n1. 优化后的工艺参数\n2. 优化理由\n3. 预期效果\n4. 验证方法",
                    "tags": ["工艺优化", "反应工程", "化学工程"],
                    "created_at": "2024-01-01"
                },
                {
                    "name": "反应器设计",
                    "prompt": "请设计一个用于[反应名称]的反应器，考虑以下因素：\n1. 反应器类型选择\n2. 尺寸计算\n3. 材质选择\n4. 搅拌方式\n5. 温度和压力控制\n\n反应参数：\n[反应参数]",
                    "tags": ["反应器设计", "化学工程", "设计"],
                    "created_at": "2024-01-01"
                }
            ],
            "有机化学": [
                {
                    "name": "反应路径预测",
                    "prompt": "请预测[反应物]到[产物]的可能反应路径，包括：\n1. 主要反应步骤\n2. 中间体结构\n3. 反应机理\n4. 可能的竞争反应\n5. 反应条件建议",
                    "tags": ["反应路径", "有机合成", "机理"],
                    "created_at": "2024-01-01"
                },
                {
                    "name": "同分异构体分析",
                    "prompt": "请分析[分子式]的所有可能同分异构体，包括：\n1. 结构简式\n2. IUPAC名称\n3. 物理性质差异\n4. 化学性质差异\n5. 鉴定方法",
                    "tags": ["同分异构体", "有机化学", "结构分析"],
                    "created_at": "2024-01-01"
                }
            ],
            "分析化学": [
                {
                    "name": "谱图解析辅助",
                    "prompt": "请解析以下[谱图类型]谱图数据，提供：\n1. 主要吸收峰/特征峰的归属\n2. 可能的分子结构推断\n3. 与标准谱图的比较\n4. 结论建议\n\n谱图数据：\n[谱图数据]",
                    "tags": ["谱图解析", "分析化学", "表征"],
                    "created_at": "2024-01-01"
                },
                {
                    "name": "分析方法选择",
                    "prompt": "请为[分析目标]选择合适的分析方法，考虑以下因素：\n1. 方法原理\n2. 灵敏度\n3. 选择性\n4. 精密度\n5. 分析时间\n6. 仪器要求\n\n样品信息：\n[样品信息]",
                    "tags": ["分析方法", "分析化学", "方法选择"],
                    "created_at": "2024-01-01"
                }
            ]
        }
        
        # 保存示例提示词到文件
        for domain, prompts in examples.items():
            domain_file = os.path.join(self.prompt_dir, f"{domain}.json")
            if not os.path.exists(domain_file):
                with open(domain_file, 'w', encoding='utf-8') as f:
                    json.dump(prompts, f, indent=4, ensure_ascii=False)
    
    def get_domains(self):
        """获取所有领域列表"""
        return self.domains
    
    def get_prompts_by_domain(self, domain):
        """获取指定领域的提示词列表"""
        domain_file = os.path.join(self.prompt_dir, f"{domain}.json")
        if not os.path.exists(domain_file):
            return []
        
        try:
            with open(domain_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载{domain}领域提示词失败: {e}")
            return []
    
    def save_prompt(self, domain, prompt_data):
        """保存提示词到指定领域"""
        if domain not in self.domains:
            # 添加新领域
            self.domains.append(domain)
        
        domain_file = os.path.join(self.prompt_dir, f"{domain}.json")
        
        # 获取现有提示词
        prompts = self.get_prompts_by_domain(domain)
        
        # 添加新提示词
        prompts.append(prompt_data)
        
        try:
            with open(domain_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存提示词失败: {e}")
            return False
    
    def update_prompt(self, domain, prompt_name, new_prompt_data):
        """更新指定提示词"""
        prompts = self.get_prompts_by_domain(domain)
        
        for i, prompt in enumerate(prompts):
            if prompt["name"] == prompt_name:
                prompts[i] = new_prompt_data
                break
        else:
            return False
        
        domain_file = os.path.join(self.prompt_dir, f"{domain}.json")
        
        try:
            with open(domain_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"更新提示词失败: {e}")
            return False
    
    def delete_prompt(self, domain, prompt_name):
        """删除指定提示词"""
        prompts = self.get_prompts_by_domain(domain)
        
        new_prompts = [prompt for prompt in prompts if prompt["name"] != prompt_name]
        
        if len(new_prompts) == len(prompts):
            return False  # 没有找到要删除的提示词
        
        domain_file = os.path.join(self.prompt_dir, f"{domain}.json")
        
        try:
            with open(domain_file, 'w', encoding='utf-8') as f:
                json.dump(new_prompts, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"删除提示词失败: {e}")
            return False
    
    def search_prompts(self, keyword):
        """搜索提示词"""
        results = []
        
        for domain in self.domains:
            prompts = self.get_prompts_by_domain(domain)
            for prompt in prompts:
                if keyword.lower() in prompt["name"].lower() or keyword.lower() in prompt["prompt"].lower():
                    results.append({
                        "domain": domain,
                        **prompt
                    })
        
        return results
    
    def get_prompt_by_name(self, domain, prompt_name):
        """根据名称获取指定领域的提示词"""
        prompts = self.get_prompts_by_domain(domain)
        for prompt in prompts:
            if prompt["name"] == prompt_name:
                return prompt
        return None
    
    def import_prompts(self, file_path):
        """从文件导入提示词"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_prompts = json.load(f)
            
            # 导入提示词到对应的领域
            for prompt_data in imported_prompts:
                domain = prompt_data.get("domain", "通用")
                # 移除domain字段，因为它存储在文件名中
                if "domain" in prompt_data:
                    del prompt_data["domain"]
                self.save_prompt(domain, prompt_data)
            
            return True
        except Exception as e:
            print(f"导入提示词失败: {e}")
            return False
    
    def export_prompts(self, domain=None, file_path=None):
        """导出提示词到文件"""
        if not file_path:
            file_path = "prompts_export.json"
        
        if domain:
            # 导出单个领域的提示词
            prompts = self.get_prompts_by_domain(domain)
            export_data = [{"domain": domain, **prompt} for prompt in prompts]
        else:
            # 导出所有领域的提示词
            export_data = []
            for domain in self.domains:
                prompts = self.get_prompts_by_domain(domain)
                export_data.extend([{"domain": domain, **prompt} for prompt in prompts])
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            return file_path
        except Exception as e:
            print(f"导出提示词失败: {e}")
            return None