# 🧪 pytest完整教程总结

## 📚 pytest基础概念

### 什么是pytest？
pytest是Python最流行的测试框架，它：
- **简单易用**: 只需用`assert`语句
- **自动发现**: 自动找到测试文件和函数
- **详细报告**: 提供清晰的失败信息
- **插件丰富**: 强大的扩展生态系统

## 🚀 快速开始

### 1. 安装
```bash
pip install pytest
```

### 2. 最简单的测试
```python
# test_example.py
def test_simple():
    assert 1 + 1 == 2
```

### 3. 运行测试
```bash
pytest                    # 运行所有测试
pytest test_example.py    # 运行特定文件
pytest -v                 # 详细输出
pytest -k "test_name"     # 运行名称匹配的测试
```

## 📝 测试编写规则

### 文件命名
- 测试文件：`test_*.py` 或 `*_test.py`
- 测试函数：`test_*()`
- 测试类：`Test*`

### 基本断言
```python
def test_assertions():
    # 基本断言
    assert expression
    assert expression, "错误消息"
    
    # 常用断言
    assert value == expected
    assert value in collection
    assert value > threshold
    assert not condition
    
    # 近似相等（浮点数）
    import pytest
    assert 0.1 + 0.2 == pytest.approx(0.3)
```

### 异常测试
```python
def test_exceptions():
    import pytest
    
    # 测试异常是否抛出
    with pytest.raises(ValueError):
        raise ValueError("错误")
    
    # 测试异常消息
    with pytest.raises(ValueError, match="特定消息"):
        raise ValueError("包含特定消息的错误")
```

## 🎯 参数化测试

### 基本参数化
```python
@pytest.mark.parametrize("input, expected", [
    (1, 2),
    (2, 3),
    (3, 4),
])
def test_increment(input, expected):
    assert input + 1 == expected
```

### 多参数参数化
```python
@pytest.mark.parametrize("a, b, result", [
    (1, 2, 3),
    (2, 3, 5),
    (5, 5, 10),
])
def test_addition(a, b, result):
    assert a + b == result
```

### 参数化ID
```python
@pytest.mark.parametrize("input, expected", [
    (1, 2),
    (2, 3),
], ids=["case1", "case2"])
def test_with_ids(input, expected):
    assert input + 1 == expected
```

## 🔧 Fixtures（夹具）

### 基本Fixture
```python
@pytest.fixture
def sample_data():
    return [1, 2, 3, 4, 5]

def test_with_fixture(sample_data):
    assert len(sample_data) == 5
```

### Fixture作用域
```python
@pytest.fixture(scope="function")  # 每个测试函数（默认）
@pytest.fixture(scope="class")     # 每个测试类
@pytest.fixture(scope="module")    # 每个测试模块
@pytest.fixture(scope="session")   # 整个测试会话
def database_connection():
    # 设置
    conn = create_connection()
    yield conn  # 提供给测试
    # 清理
    conn.close()
```

### 自动使用Fixture
```python
@pytest.fixture(autouse=True)
def setup_environment():
    # 每个测试前自动执行
    setup_test_environment()
    yield
    # 每个测试后自动执行
    cleanup_test_environment()
```

### 参数化Fixture
```python
@pytest.fixture(params=["sqlite", "mysql", "postgresql"])
def database_type(request):
    return request.param

def test_database_operations(database_type):
    # 会为每个数据库类型运行一次
    assert database_type in ["sqlite", "mysql", "postgresql"]
```

## 🏷️ 标记（Markers）

### 内置标记
```python
@pytest.mark.skip(reason="暂时跳过")
def test_skip():
    pass

@pytest.mark.skipif(condition, reason="条件跳过")
def test_conditional_skip():
    pass

@pytest.mark.xfail(reason="预期失败")
def test_expected_fail():
    assert False

@pytest.mark.parametrize("param", [1, 2, 3])
def test_parametrized(param):
    assert param > 0
```

### 自定义标记
```python
# 定义自定义标记
@pytest.mark.slow
def test_slow_operation():
    time.sleep(1)

@pytest.mark.integration
def test_integration():
    pass

# 运行特定标记的测试
# pytest -m slow
# pytest -m "not slow"
# pytest -m "slow or integration"
```

## 🎭 Mock和Patch

### 基本Mock
```python
from unittest.mock import Mock

def test_with_mock():
    # 创建Mock对象
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked_result"
    
    # 使用Mock
    result = mock_obj.method()
    assert result == "mocked_result"
    
    # 验证调用
    mock_obj.method.assert_called_once()
```

### Patch装饰器
```python
from unittest.mock import patch

@patch('module.function')
def test_with_patch(mock_function):
    mock_function.return_value = "mocked"
    result = module.function()
    assert result == "mocked"
```

### 上下文管理器Patch
```python
def test_with_context_patch():
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = "fake_time"
        result = get_current_time()
        assert result == "fake_time"
```

## ⚙️ 配置文件

### pytest.ini
```ini
[tool:pytest]
# 测试发现
testpaths = tests
python_files = test_*.py
python_functions = test_*

# 标记定义
markers =
    slow: slow running tests
    integration: integration tests
    smoke: quick smoke tests

# 选项
addopts = 
    --strict-markers
    -ra
    --tb=short

# 过滤警告
filterwarnings =
    ignore::DeprecationWarning
```

### pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
markers = [
    "slow: slow running tests",
    "integration: integration tests",
]
addopts = ["--strict-markers", "-ra"]
```

## 📊 常用命令行选项

### 基本运行
```bash
pytest                          # 运行所有测试
pytest tests/                   # 运行指定目录
pytest test_file.py             # 运行指定文件
pytest test_file.py::test_func  # 运行指定函数
```

### 输出控制
```bash
pytest -v                # 详细输出
pytest -s                # 显示print输出
pytest -q                # 安静模式
pytest --tb=short        # 简短的traceback
pytest --tb=no           # 不显示traceback
```

### 测试选择
```bash
pytest -k "test_name"              # 按名称过滤
pytest -m "slow"                   # 按标记过滤
pytest -m "not slow"               # 排除标记
pytest -m "slow or integration"    # 多个标记
```

### 失败处理
```bash
pytest -x                # 第一次失败后停止
pytest --maxfail=2       # 失败2次后停止
pytest --lf              # 只运行上次失败的测试
pytest --ff              # 先运行上次失败的测试
```

### 并行运行（需要pytest-xdist）
```bash
pip install pytest-xdist
pytest -n auto           # 自动并行
pytest -n 4              # 4个进程并行
```

## 🔍 调试

### 使用pdb调试
```bash
pytest --pdb             # 失败时进入pdb
pytest --pdb-trace       # 每个测试开始时进入pdb
```

### 在代码中设置断点
```python
def test_debug():
    import pdb; pdb.set_trace()  # 设置断点
    assert True
```

## 📈 测试覆盖率

### 安装和使用
```bash
pip install pytest-cov

# 运行覆盖率测试
pytest --cov=myproject
pytest --cov=myproject --cov-report=html  # HTML报告
pytest --cov=myproject --cov-report=term-missing  # 显示缺失行
```

## 🎪 高级功能

### 自定义Pytest插件
```python
# conftest.py
@pytest.fixture
def global_fixture():
    return "available_everywhere"

def pytest_configure(config):
    # 配置钩子
    pass

def pytest_collection_modifyitems(items):
    # 修改收集的测试项
    pass
```

### 测试类
```python
class TestCalculator:
    def setup_method(self):
        # 每个测试方法前运行
        self.calc = Calculator()
    
    def test_add(self):
        assert self.calc.add(2, 3) == 5
    
    def test_subtract(self):
        assert self.calc.subtract(5, 3) == 2
```

### 条件测试
```python
import sys

@pytest.mark.skipif(sys.version_info < (3, 8), reason="需要Python 3.8+")
def test_new_feature():
    # 只在Python 3.8+运行
    pass
```

## 🎯 最佳实践

### 1. 测试组织
- 按功能模块组织测试文件
- 使用清晰的测试函数名
- 每个测试只验证一个行为

### 2. Fixture设计
- 保持Fixture简单和专注
- 使用适当的作用域
- 避免过度嵌套

### 3. 断言风格
- 使用简单的assert语句
- 提供有意义的错误消息
- 避免复杂的断言逻辑

### 4. 测试数据
- 使用Fixture提供测试数据
- 保持测试数据简单
- 避免硬编码值

### 5. Mock使用
- 只Mock外部依赖
- 验证重要的Mock调用
- 避免过度Mock

### 6. 标记使用
- 为慢测试添加标记
- 区分单元测试和集成测试
- 使用描述性的标记名

## 📚 有用的插件

```bash
# 常用插件
pip install pytest-xdist      # 并行运行
pip install pytest-cov       # 覆盖率
pip install pytest-html      # HTML报告
pip install pytest-mock      # Mock工具
pip install pytest-timeout   # 超时控制
pip install pytest-sugar     # 美化输出
pip install pytest-benchmark # 性能测试
```

## 🔗 学习资源

- [pytest官方文档](https://docs.pytest.org/)
- [Real Python pytest教程](https://realpython.com/pytest-python-testing/)
- [pytest最佳实践](https://docs.pytest.org/en/stable/goodpractices.html)

---

这个教程涵盖了pytest的主要功能和用法。建议从简单的断言开始，逐步学习参数化、Fixture和高级功能。实践是最好的学习方法！
