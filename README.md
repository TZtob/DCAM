# DCAM - DDN Cluster Asset Management

## 项目简介

DCAM (DDN Cluster Asset Management) 是一个专业的DDN存储集群资产管理系统，用于管理和分析DDN EXAScaler存储系统的配置、容量和状态信息。

## 主要功能

### 🏢 客户管理
- 客户信息维护和管理
- 客户与存储系统的关联管理
- 客户级别的资产统计

### 💾 系统管理
- DDN EXAScaler系统配置管理
- TOML配置文件和SFA信息文件的导入处理
- 自动化的OST容量计算和统计
- 支持多种SFA文件格式(IDEA/AION等)

### 📊 容量分析
- 智能OST容量提取和计算
- 支持多种容量格式自动识别
- 设备级和集群级容量统计
- 容量趋势分析和报告

### 🔧 配置生成
- 自动生成集群YAML配置文件
- 网络信息自动提取(InfiniBand/Ethernet)
- 设备序列号和版本信息管理
- 可扩展的配置模板系统

### 📁 文件管理
- 上传文件的自动归档和管理
- 按客户和系统分类存储
- 文件版本控制和备份

## 技术架构

- **后端框架**: Flask (Python)
- **前端技术**: Bootstrap + jQuery
- **数据存储**: JSON文件数据库
- **文件处理**: tarfile, json处理
- **配置管理**: YAML/TOML格式支持

## 快速开始

### 环境要求

- Python 3.7+
- Flask
- PyYAML
- 其他依赖见 `requirements.txt`

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/dcam.git
   cd dcam
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化数据目录**
   ```bash
   mkdir -p data/{customers,systems,backups}
   ```

4. **启动应用**
   ```bash
   python app.py
   ```

5. **访问系统**
   ```
   http://localhost:5000
   ```

## 系统使用

### 1. 客户管理
- 访问 `/customers` 创建和管理客户信息
- 每个客户可以关联多个存储系统

### 2. 系统导入
- 访问 `/import` 上传TOML配置文件和SFA信息文件
- 系统自动解析并计算容量信息
- 支持的文件格式:
  - `.toml` - EXAScaler配置文件
  - `.tar.gz` - SFA信息压缩包

### 3. 容量分析
- 系统自动识别OST卷并计算容量
- 支持多种容量格式:
  - IDEA系统: `Cap=15.4 TiB`
  - AION系统: `Capacity='713.8 TiB'`
  - 直接字节数格式

### 4. 配置生成
```bash
python generate_cluster_yaml.py --cluster-name <name> <toml_file> --sfainfo <sfa_files...>
```

## 项目结构

```
dcam/
├── app.py                          # 主应用程序
├── generate_cluster_yaml.py        # YAML配置生成器
├── config.py                      # 应用配置
├── requirements.txt               # Python依赖
├── templates/                     # HTML模板
│   ├── index.html                # 主页面
│   ├── customers.html            # 客户管理
│   ├── new_system.html           # 系统创建
│   └── system_detail.html        # 系统详情
├── static/                       # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
└── data/                        # 数据存储
    ├── customers/               # 客户数据
    └── systems/                # 系统数据
```

## 核心特性

### 🎯 智能容量解析
- **多格式支持**: 自动识别不同SFA文件格式
- **容量计算**: 精确的OST卷容量统计
- **错误处理**: 完善的解析错误提示

### 📦 文件归档管理
- **自动归档**: 上传文件按客户/系统分类存储
- **版本管理**: 支持同一系统的多次导入
- **路径规范**: `data/customers/{customer}/{system}/uploads/`

### 🔄 系统兼容性
- **IDEA系统**: 支持传统的Cap字段格式
- **AION系统**: 支持新的Capacity字段格式
- **向后兼容**: 保持对旧格式的完整支持

## 部署说明

### 开发环境
```bash
export FLASK_ENV=development
python app.py
```

### 生产环境
推荐使用 Gunicorn + Nginx 部署：

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

详见 `DEPLOYMENT.md` 文件。

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 版本历史

- **v1.0.0** - 初始版本，基本的客户和系统管理功能
- **v1.1.0** - 添加容量自动计算功能
- **v1.2.0** - 支持AION系统格式，文件归档管理
- **v1.3.0** - 完善容量解析逻辑，支持多种SFA格式

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: DDN Team
- 问题反馈: 请使用 GitHub Issues

---

## DDN EXAScaler 支持

本系统专为 DDN EXAScaler 存储系统设计，支持：

- **SFA系列**: SFA400NVX2E, SFA7990XE 等
- **EXAScaler版本**: 5.x, 6.x 系列
- **网络接口**: InfiniBand, Ethernet
- **文件系统**: Lustre OST/MDT 管理

如有技术问题，请参考 DDN 官方文档或联系技术支持。