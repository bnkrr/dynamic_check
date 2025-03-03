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
python cli.py -c config.yaml
```
