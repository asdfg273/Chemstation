import requests
import json
import time
from core.config import config_manager
from abc import ABC, abstractmethod
from utils.logger import api_logger

class SearchEngine(ABC):
    """搜索引擎抽象基类"""
    
    def __init__(self):
        self.timeout = config_manager.get("network.timeout", 30)
        self.max_results = config_manager.get("network.max_results", 20)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    @abstractmethod
    def search(self, query, **kwargs):
        """执行搜索，返回结构化结果"""
        pass
    
    def _send_request(self, url, method="GET", params=None, data=None, headers=None):
        """发送HTTP请求，处理响应"""
        start_time = time.time()
        response = None
        error = None
        
        try:
            if headers:
                self.headers.update(headers)
            
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=self.headers,
                timeout=self.timeout,
                verify=False  # 忽略SSL验证，仅用于开发环境
            )
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            error = e
            print(f"网络请求失败: {e}")
            return None
        finally:
            # 记录API调用日志
            end_time = time.time()
            response_time = end_time - start_time
            status_code = response.status_code if response else None
            
            # 隐藏敏感信息
            safe_headers = headers.copy() if headers else {}
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "***"
            if "apikey" in safe_headers:
                safe_headers["apikey"] = "***"
            
            api_logger.log_api_call(
                endpoint=url,
                method=method,
                params={"params": params, "data": data},
                headers=safe_headers,
                response=response,
                status_code=status_code,
                response_time=response_time,
                error=error,
                api_type="search"
            )

class GoogleScholarSearch(SearchEngine):
    """Google Scholar搜索引擎"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://scholar.google.com/scholar"
    
    def search(self, query, num_results=None, year_range=None):
        """搜索学术文献"""
        if num_results is None:
            num_results = self.max_results
        
        params = {
            "q": query,
            "hl": "zh-CN",
            "num": num_results
        }
        
        if year_range:
            params["as_ylo"] = year_range[0]
            params["as_yhi"] = year_range[1]
        
        response = self._send_request(self.base_url, params=params)
        if not response:
            return []
        
        # 这里简化处理，实际需要使用BeautifulSoup解析HTML
        # 由于Google Scholar反爬严格，这里返回模拟数据
        return self._parse_response(response.text)
    
    def _parse_response(self, html):
        """解析搜索结果"""
        # 实际实现需要使用BeautifulSoup或其他HTML解析库
        # 这里返回模拟数据
        return [
            {
                "title": "示例学术论文标题1",
                "authors": ["作者1", "作者2"],
                "journal": "化学学报",
                "year": 2023,
                "citations": 45,
                "abstract": "这是一篇关于化学研究的示例论文摘要...",
                "url": "https://example.com/paper1",
                "type": "academic"
            },
            {
                "title": "示例学术论文标题2",
                "authors": ["作者3", "作者4"],
                "journal": "材料科学进展",
                "year": 2022,
                "citations": 32,
                "abstract": "这是另一篇关于材料科学的示例论文摘要...",
                "url": "https://example.com/paper2",
                "type": "academic"
            }
        ]

class PubChemSearch(SearchEngine):
    """PubChem化学数据库搜索"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    def search(self, query, search_type="name"):
        """搜索化学物质"""
        # 支持的搜索类型：name, smiles, inchi, formula, cas
        if search_type not in ["name", "smiles", "inchi", "formula", "cas"]:
            search_type = "name"
        
        url = f"{self.base_url}/compound/{search_type}/{query}/JSON"
        response = self._send_request(url)
        if not response:
            return []
        
        try:
            data = response.json()
            return self._parse_response(data)
        except json.JSONDecodeError as e:
            print(f"解析JSON失败: {e}")
            return []
    
    def _parse_response(self, data):
        """解析PubChem API响应"""
        results = []
        if "PC_Compounds" in data:
            for compound in data["PC_Compounds"]:
                result = {
                    "cid": compound.get("id", {}).get("id", {}).get("cid", ""),
                    "name": "",
                    "formula": "",
                    "molecular_weight": "",
                    "smiles": "",
                    "inchi": "",
                    "type": "chemical"
                }
                
                # 解析化合物名称
                for prop in compound.get("props", []):
                    if prop.get("urn", {}).get("label") == "IUPAC Name" and prop.get("urn", {}).get("name") == "Preferred":
                        result["name"] = prop.get("value", {}).get("sval", "")
                    elif prop.get("urn", {}).get("label") == "Molecular Formula":
                        result["formula"] = prop.get("value", {}).get("sval", "")
                    elif prop.get("urn", {}).get("label") == "Molecular Weight":
                        result["molecular_weight"] = prop.get("value", {}).get("fval", "")
                
                # 解析SMILES和InChI
                for contrib in compound.get("atoms", {}).get("aid", []):
                    pass  # 简化处理
                
                results.append(result)
        
        return results

class ChemSpiderSearch(SearchEngine):
    """ChemSpider化学数据库搜索"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.rsc.org/compounds/v1"
        self.api_key = config_manager.get("network.chemspider_api_key", "")
    
    def search(self, query, search_type="name"):
        """搜索化学物质"""
        if not self.api_key:
            print("ChemSpider API密钥未配置")
            return []
        
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/filter/{search_type}"
        params = {
            "query": query
        }
        
        response = self._send_request(url, method="POST", params=params, headers=headers)
        if not response:
            return []
        
        try:
            data = response.json()
            return self._parse_response(data)
        except json.JSONDecodeError as e:
            print(f"解析JSON失败: {e}")
            return []
    
    def _parse_response(self, data):
        """解析ChemSpider API响应"""
        # 实际实现需要进一步调用获取化合物详情的API
        # 这里返回模拟数据
        return [
            {
                "csid": "123456",
                "name": "示例化合物1",
                "formula": "C6H12O6",
                "molecular_weight": 180.16,
                "smiles": "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O",
                "inchi": "InChI=1S/C6H12O6/c7-1-2-3(8)4(9)5(10)6(11)12-2/h2-11H,1H2/t2-,3+,4-,5+,6?/m1/s1",
                "cas": "50-99-7",
                "type": "chemical"
            }
        ]

class SearchEngineFactory:
    """搜索引擎工厂类"""
    
    @staticmethod
    def get_search_engine(engine_type):
        """获取搜索引擎实例"""
        engines = {
            "google_scholar": GoogleScholarSearch,
            "pubchem": PubChemSearch,
            "chemspider": ChemSpiderSearch
        }
        
        engine_class = engines.get(engine_type.lower())
        if engine_class:
            return engine_class()
        else:
            raise ValueError(f"不支持的搜索引擎类型: {engine_type}")
