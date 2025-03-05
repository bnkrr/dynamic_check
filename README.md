# 动态应用测量工具

## 项目描述
动态爬虫检验页面指纹

## 安装依赖
```bash
pip install -r requirements.txt # 安装依赖
playwright install              # 安装headless browser
```

## 使用方法
1. 配置参数
   编辑 `config.yaml` 文件，设置所需的测量参数。

2. 运行检测
```bash
python cli.py -t templates/example.yaml -u targets/urls.txt -o output.jsonl
python cli.py -t templates/example.yaml -u https://example.com
```

## 指纹检测器使用说明

本检测器提供多种网页指纹检测方法，通过Playwright实现浏览器自动化检测。

### 支持的检测类型

#### 1. Header检查
- **功能**: 验证指定HTTP响应头的存在性/值
- **参数**:
  - `name`: 头部名称（不区分大小写）
  - `value`: 可选，预期值（未设置时仅检查存在性）
- **示例配置:
```yaml
- type: header
  name: X-Powered-By
  value: PHP/7.4
```

#### 2. Cookie检查
- **功能**: 检测指定Cookie的值
- **参数**:
  - `name`: Cookie名称
  - `value`: 可选，预期值（未设置时仅检查存在性）
- **示例配置:
```yaml
- type: cookie
  name: session_id
  value: abc123
```

#### 3. 元素检查
- **功能**: 通过CSS选择器检测页面元素
- **参数**:
  - `selector`: CSS选择器
  - `attribute`: 可选，需检查的元素属性（未设置时检查文本内容）
  - `value`: 可选，预期值
- **示例配置:
```yaml
- type: element
  selector: div#auth-form
  attribute: class
  value: login-box
```

#### 4. JS变量检查
- **功能**: 检测全局JavaScript变量值
- **参数**:
  - `name`: 变量路径（支持点号语法）
  - `value`: 可选，预期值
- **示例配置:
```yaml
- type: js_variable
  name: window.config.apiEndpoint
```

#### 5. 标题检查
- **功能**: 验证页面标题完全匹配
- **参数**:
  - `value`: 预期标题文本
- **示例配置:
```yaml
- type: title
  value: 用户登录
```

#### 6. 内容检查
- **功能**: 使用正则表达式匹配页面内容
- **参数**:
  - `pattern`: 正则表达式模式
- **示例配置:
```yaml
- type: content
  pattern: "\\badmin\\b"
```

### 检测结果说明
每个检测项返回包含以下字段的JSON对象：
- `type`: 检测类型
- `success`: 是否满足检测条件
- `expected`: 配置的预期值
- `found`: 实际检测到的值
- `error`: 错误信息（检测失败时）

### 使用示例
完整检测配置示例：
```yaml
checks:
  - type: header
    name: Server
    value: nginx
  
  - type: cookie 
    name: tracking_enabled
  
  - type: element
    selector: meta[name="viewport"]
    attribute: content
  