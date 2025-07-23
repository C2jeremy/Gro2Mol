# 力场文件说明

本目录包含从moltemplate项目中导入的标准力场文件，用于支持GROMACS到LAMMPS的转换。

## 📁 可用力场

### 1. GAFF (General Amber Force Field)

#### `gaff2.lt`
- **描述**: General Amber Force Field 2
- **适用**: 有机小分子、药物分子
- **特点**: 改进的GAFF版本，更准确的参数
- **使用**: `-f gaff2`

#### `gaff.lt`  
- **描述**: General Amber Force Field (原版)
- **适用**: 有机小分子、药物分子
- **特点**: 经典的GAFF力场
- **使用**: `-f gaff`

### 2. OPLS (Optimized Potentials for Liquid Simulations)

#### `oplsaa.lt`
- **描述**: OPLS All-Atom Force Field
- **适用**: 蛋白质、液体、有机分子
- **特点**: 优化的液体模拟参数
- **使用**: `-f opls`

#### `loplsaa.lt`
- **描述**: LOPLS-AA (Live-Only OPLS-AA)
- **适用**: 特定类型的有机分子
- **特点**: OPLS-AA的简化版本
- **使用**: `-f lopls`

### 3. COMPASS

#### `compass_published.lt`
- **描述**: COMPASS Force Field (Published Version)
- **适用**: 聚合物、无机材料、界面
- **特点**: 综合性力场，适用范围广
- **使用**: `-f compass`

## 🚀 使用方法

### 标准力场模式

当您有ITP文件并知道要使用的力场时：

```bash
# 使用GAFF2力场
python main.py --itp-files molecule.itp -f gaff2 -o output_dir

# 使用OPLS-AA力场  
python main.py --itp-files molecule.itp -f opls -o output_dir

# 使用GAFF力场
python main.py --itp-files molecule.itp -f gaff -o output_dir
```

### 自定义力场模式

当您需要生成完整的力场定义时：

```bash
# 自定义力场模式
python main.py -t system.top -c system.gro --itp-files *.itp --custom-ff -o output_dir
```

## 📋 力场选择指南

| 分子类型 | 推荐力场 | 说明 |
|---------|---------|------|
| **有机小分子** | GAFF2 | 最新改进版本，准确性高 |
| **药物分子** | GAFF/GAFF2 | 专门为小分子设计 |
| **蛋白质** | OPLS-AA | 优化的蛋白质参数 |
| **液体系统** | OPLS-AA | 液体性质优化 |
| **聚合物** | COMPASS | 适合材料模拟 |
| **界面系统** | COMPASS | 复杂界面相互作用 |

## ⚙️ 技术说明

### 文件格式
- 所有文件采用moltemplate的`.lt`格式
- 兼容LAMMPS 2021年及以后版本
- 包含完整的原子类型、键、角、二面角定义

### 更新来源
- 文件来源: `/home/chenjiayu/DATA/moltemplate/moltemplate/moltemplate/force_fields/`
- 版本: moltemplate最新版本
- 更新时间: 2025年

### 兼容性
- ✅ LAMMPS 最新版本
- ✅ moltemplate 2.20+
- ✅ 本转换工具全版本

## 🔄 添加新力场

如需添加新的力场文件：

1. **从moltemplate获取**:
   ```bash
   cp /path/to/moltemplate/force_fields/newff.lt ./force_fields/
   ```

2. **更新工具支持**:
   在 `utils/force_field_manager.py` 中添加新力场信息

3. **测试兼容性**:
   ```bash
   python main.py --itp-files test.itp -f newff -o test_output
   ```

## 📚 参考文献

- **GAFF**: Wang et al., J. Comput. Chem. 25, 1157 (2004)
- **GAFF2**: He et al., J. Chem. Theory Comput. 16, 528 (2020)  
- **OPLS-AA**: Jorgensen et al., J. Am. Chem. Soc. 118, 11225 (1996)
- **COMPASS**: Sun, J. Phys. Chem. B 102, 7338 (1998)

## 📧 支持

如遇到力场相关问题，请检查：
1. 分子类型是否适合所选力场
2. ITP文件中的原子类型是否被力场支持
3. 查看详细日志输出 (`--verbose`) 