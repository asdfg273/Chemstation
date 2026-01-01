# chem_assistant/tests/test_api_gateway.py

import pytest
import httpx

# 导入我们要测试的模块和我们定义的模型
from chem_assistant.core.models import Compound
from chem_assistant.api_gateway.cn_mirror import pubchem_cn

# 使用 pytest.mark.asyncio 来标记这是一个异步测试函数
@pytest.mark.asyncio
async def test_search_compound_success(mocker):
    """
    测试用例 1: 成功搜索到一个化合物 (例如 'aspirin')
    'mocker' 是 pytest-mock 提供的一个工具，用于创建模拟对象。
    """
    # --- 准备阶段 (Arrange) ---
    # 1. 模拟API返回的CID信息
    mock_response_cid = mocker.Mock()
    mock_response_cid.json.return_value = {'IdentifierList': {'CID': [2244]}}
    mock_response_cid.raise_for_status.return_value = None # 告诉模拟对象，调用raise_for_status()时什么也别做

    # 2. 模拟API返回的属性信息
    mock_response_props = mocker.Mock()
    mock_response_props.json.return_value = {
        'PropertyTable': {
            'Properties': [{
                'CID': 2244, 'IUPACName': '2-(acetyloxy)benzoic acid',
                'MolecularFormula': 'C9H8O4', 'MolecularWeight': '180.16',
                'CanonicalSMILES': 'CC(=O)OC1=CC=CC=C1C(=O)O'
            }]
        }
    }
    mock_response_props.raise_for_status.return_value = None

    # 3. "劫持" httpx.AsyncClient.get 方法
    # 让它在被调用时，按顺序返回我们准备好的模拟响应
    mock_get = mocker.AsyncMock(side_effect=[mock_response_cid, mock_response_props])
    mocker.patch('httpx.AsyncClient.get', mock_get)

    # --- 执行阶段 (Act) ---
    # 调用我们正在测试的函数
    result = await pubchem_cn.search_compound_by_name("aspirin")

    # --- 断言阶段 (Assert) ---
    # 检查返回结果是否符合预期
    assert isinstance(result, Compound)
    assert result.cid == 2244
    assert result.name == "aspirin"
    assert result.molecular_weight == 180.16
    assert result.iupac_name == "2-(acetyloxy)benzoic acid"


@pytest.mark.asyncio
async def test_search_compound_not_found_404(mocker):
    """
    测试用例 2: 搜索一个不存在的化合物，API返回404错误
    """
    # --- 准备阶段 ---
    # 1. 准备一个模拟的请求对象，用于构建错误
    mock_request = mocker.Mock(spec=httpx.Request)
    mock_request.url = "http://fake.url"
    
    # 2. 模拟 raise_for_status() 方法，让它抛出我们想要的 HTTPStatusError
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=mock_request, response=mocker.Mock(status_code=404)
    )
    
    # 3. "劫持" get 方法，让它返回这个会抛出错误的模拟响应
    mocker.patch('httpx.AsyncClient.get', mocker.AsyncMock(return_value=mock_response))

    # --- 执行阶段 ---
    result = await pubchem_cn.search_compound_by_name("asdfghjkl")

    # --- 断言阶段 ---
    # 确认函数在这种情况下返回了 None
    assert result is None


@pytest.mark.asyncio
async def test_search_compound_network_error(mocker):
    """
    测试用例 3: 模拟网络连接错误
    """
    # --- 准备阶段 ---
    # "劫持" get 方法，让它直接抛出 RequestError
    mocker.patch('httpx.AsyncClient.get', mocker.AsyncMock(side_effect=httpx.RequestError("Connection failed", request=mocker.Mock())))
    
    # --- 执行阶段 ---
    result = await pubchem_cn.search_compound_by_name("caffeine")
    
    # --- 断言阶段 ---
    assert result is None
