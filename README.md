# GROMACS to LAMMPS 转换工具

这是一个通过moltemplate将GROMACS工程文件转换为LAMMPS工程文件的工具。

## 功能特性

- 🔄 **全面转换**: 支持.top、.itp、.gro、.pdb文件格式
- ⚡ **双力场模式**: 支持标准力场(GAFF2、OPLS等)和自定义力场
- 🛠️ **自动化流程**: 一键生成moltemplate文件和运行脚本
- 📝 **详细日志**: 提供转换过程的详细信息和进度反馈

## 支持的文件格式

### 输入文件（GROMACS）
- `.top` - 拓扑文件
- `.itp` - 分子定义文件
- `.gro` - GROMACS坐标文件
- `.pdb` - 蛋白质数据库文件

### 输出文件（moltemplate）
- `.lt` - moltemplate文件
- `.sh/.py` - 运行脚本
- `.xyz` - 坐标文件
- `force_field_info.txt` - 力场信息

## 安装

### 依赖要求
- Python 3.7+
- moltemplate
- LAMMPS (可选，用于运行生成的文件)

### 安装moltemplate
```bash
# 使用conda安装
conda install -c conda-forge moltemplate

# 或使用pip安装
pip install moltemplate
```

## 使用方法

### 基本用法

```bash
python main.py -t system.top -c system.gro
```

### 使用标准力场

```bash
# 使用GAFF2力场
python main.py -t system.top -c system.gro -f gaff2

# 使用OPLS力场
python main.py -t system.top -c system.gro -f opls
```

### 使用自定义力场

```bash
# 包含ITP文件的自定义力场
python main.py -t system.top -c system.gro --itp-files molecule.itp --custom-ff
```

### 完整示例

```bash
python main.py \
  -t system.top \
  -c system.gro \
  --itp-files molecule1.itp molecule2.itp \
  -f gaff2 \
  -o output_dir \
  --output-name my_system \
  --verbose
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `-t, --topology` | GROMACS拓扑文件 | `system.top` |
| `-c, --coordinate` | 坐标文件(.gro或.pdb) | `system.gro` |
| `-f, --force-field` | 力场类型 | `gaff2`, `opls` |
| `--itp-files` | 额外的ITP文件 | `mol1.itp mol2.itp` |
| `-o, --output` | 输出目录 | `output/` |
| `--output-name` | 输出文件前缀 | `my_system` |
| `--custom-ff` | 使用自定义力场 | - |
| `-v, --verbose` | 详细输出 | - |

## 支持的标准力场

| 力场 | 描述 | moltemplate文件 |
|------|------|----------------|
| `gaff2` | General Amber Force Field 2 | `gaff2.lt` |
| `gaff` | General Amber Force Field | `gaff.lt` |
| `opls` | OPLS-AA Force Field | `oplsaa.lt` |
| `amber` | Amber Force Field | `amber.lt` |
| `charmm` | CHARMM Force Field | `charmm.lt` |

## 工作流程

1. **解析GROMACS文件**
   - 读取.top文件获取系统组成
   - 解析.itp文件获取分子定义
   - 读取坐标文件获取原子位置

2. **处理力场信息**
   - 标准力场：使用预定义的moltemplate力场文件
   - 自定义力场：从ITP文件提取力场参数

3. **生成moltemplate文件**
   - 创建分子.lt文件
   - 生成系统.lt文件
   - 转换坐标文件

4. **生成运行脚本**
   - 创建shell脚本和Python脚本
   - 自动检查moltemplate安装

## 输出文件结构

```
output/
├── molecule1.lt          # 分子定义文件
├── molecule2.lt          # 分子定义文件
├── system.lt             # 系统文件
├── system.xyz            # 坐标文件
├── run_moltemplate.sh    # Shell运行脚本
├── run_moltemplate.py    # Python运行脚本
└── force_field_info.txt  # 力场信息
```

## 运行moltemplate

生成文件后，可以使用以下方式运行moltemplate：

```bash
# 方式1：使用生成的shell脚本
cd output/
./run_moltemplate.sh

# 方式2：使用Python脚本
python run_moltemplate.py

# 方式3：直接运行moltemplate
moltemplate.sh system.lt
```

## 故障排除

### 常见问题

1. **找不到moltemplate**
   ```
   错误: 未找到 moltemplate.sh
   ```
   解决：确保已安装moltemplate并在PATH中

2. **力场文件缺失**
   ```
   错误: 找不到力场文件 gaff2.lt
   ```
   解决：检查moltemplate安装和力场文件位置

3. **原子类型不匹配**
   ```
   警告: 缺少以下原子类型的力场参数
   ```
   解决：使用自定义力场模式或检查原子类型映射

### 调试模式

使用`--verbose`参数获取详细的调试信息：

```bash
python main.py -t system.top -c system.gro --verbose
```

## 贡献

欢迎提交问题报告和功能请求！

## 许可证

本项目使用MIT许可证。

## 更新日志

### v1.0.0
- 初始版本
- 支持基本的GROMACS到moltemplate转换
- 支持标准力场和自定义力场
- 提供完整的文档和示例 