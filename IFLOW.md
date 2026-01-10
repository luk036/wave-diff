# IFLOW.md - 波形差异分析项目上下文

## 项目概述

`wave-diff` 是一个专注于波形和文本差异分析的 Python 项目，提供了一系列实验性工具来比较和分析不同类型的数据序列。项目使用编辑距离算法（如 Levenshtein 距离）和动态时间规整（DTW）技术，实现了对波形信号和文本数据的精确比较。

## 项目结构

```
wave-diff/
├── experiments/           # 实验工具目录
│   ├── waveform_diff.py   # 主要波形比较工具
│   ├── diff_distance.py   # 文本编辑距离计算工具
│   ├── diff_tool.py       # 通用文本差异工具
│   ├── gemini_diff.py     # 音频信号差异分析工具
│   ├── glitch_demo.py     # 信号故障演示工具
│   ├── glitch2_demo.py    # 故障演示工具变体
│   ├── waveform_diff_old.py # 旧版波形比较工具
│   ├── waveform_comparison_report.txt # 示例比较报告
│   └── IFLOW.md          # 实验目录详细说明
└── IFLOW.md              # 本文件
```

## 核心功能模块

### 1. 波形分析工具 (waveform_diff.py)
- **主要功能**: 使用编辑距离技术和动态时间规整比较两个波形
- **支持信号类型**: 正弦波、方波、三角波、啁啾信号、ECG模拟信号
- **核心算法**: 动态时间规整(DTW)、编辑操作检测、滑动窗口比较
- **输出结果**: 可视化比较图表、详细文本报告、操作统计

### 2. 文本差异工具 (diff_distance.py)
- **功能**: 计算文本文件间的 Levenshtein 编辑距离
- **支持级别**: 字符级、单词级和行级编辑距离
- **特色功能**: 编辑操作路径回溯、动态规划矩阵可视化

### 3. 通用差异工具 (diff_tool.py)
- **功能**: 提供多种格式的文本差异比较
- **输出格式**: 简单、统一、上下文和HTML格式
- **特点**: 可配置上下文行数、支持输出到文件

### 4. 音频分析工具 (gemini_diff.py)
- **功能**: 专门用于音频信号的差异分析
- **处理流程**: 音频加载、单声道转换、时长裁剪、降采样、归一化
- **算法**: 标准DTW算法实现数值Levenshtein距离

## 技术架构

### 核心算法实现
1. **编辑距离算法**:
   - Levenshtein距离用于文本比较
   - 修改版本用于波形幅度差异比较
   - 支持匹配、插入、删除、替换四种操作

2. **动态时间规整(DTW)**:
   - 处理不同长度或时间偏移的波形对齐
   - 简化实现避免内存问题
   - 支持路径回溯和可视化

3. **信号处理**:
   - 波形归一化处理
   - 合成信号生成（正弦、方波、三角等）
   - 滑动窗口局部差异检测

### 数据处理流程
```
波形处理: 输入文件/合成信号 → 归一化 → DTW对齐 → 编辑操作检测 → 可视化/报告
文本处理: 文件读取 → 分割(字符/单词/行) → DP矩阵计算 → 编辑路径回溯 → 结果输出
音频处理: WAV文件 → 单声道转换 → 裁剪 → 降采样 → 归一化 → DTW比较
```

## 依赖管理

### 必需依赖
- **numpy**: 数值计算和数组操作
- **matplotlib**: 图形可视化和绘图

### 可选依赖
- **scipy**: 高级信号处理、音频文件处理
  - 如果不可用，项目提供简化的替代实现

### 安装命令
```bash
pip install numpy matplotlib scipy
```

## 使用示例

### 波形比较
```bash
# 比较两个信号文件
python experiments/waveform_diff.py signal1.txt signal2.txt

# 比较合成信号
python experiments/waveform_diff.py sine square --synthetic

# 自定义参数比较
python experiments/waveform_diff.py file1.txt file2.txt --threshold 0.05 --window 100 --no-warping
```

### 文本差异分析
```bash
# 基本比较
python experiments/diff_distance.py file1.txt file2.txt

# 显示详细编辑操作
python experiments/diff_distance.py file1.txt file2.txt --detailed

# 显示DP矩阵
python experiments/diff_distance.py file1.txt file2.txt --matrix
```

### 通用差异工具
```bash
# 统一格式差异（类似git diff）
python experiments/diff_tool.py file1.txt file2.txt --format unified

# HTML格式差异
python experiments/diff_tool.py file1.txt file2.txt --format html -o diff.html
```

## 应用场景

1. **信号处理**: 传感器数据对比、音频信号分析、生物医学信号比较
2. **文本分析**: 代码差异检测、文档版本比较、数据清洗验证
3. **质量控制**: 产品测试数据对比、异常检测、偏差分析
4. **算法研究**: 编辑距离和DTW算法的实验验证和可视化
5. **教育培训**: 算法原理演示、信号处理教学

## 项目特点

1. **实验性质**: 所有工具都位于experiments目录，具有实验和研究性质
2. **模块化设计**: 每个工具专注于特定比较任务，功能独立
3. **可视化友好**: 提供丰富的图形输出和统计信息
4. **容错性强**: 优雅处理缺失依赖和异常输入
5. **教育价值**: 清晰的算法实现和可视化，适合学习和研究

## 开发约定

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用类型提示（Type Hints）提高代码可读性
- 详细的文档字符串说明函数用途和参数

### 测试策略
- 使用内置的简单示例进行基本功能测试
- 每个工具都包含 `main()` 函数支持命令行使用
- 支持合成数据生成，无需外部测试文件即可验证功能

### 扩展指南
- 新的比较算法应在相应类中实现，保持代码结构一致
- 可视化功能应保持向后兼容
- 错误处理应提供有意义的用户反馈

## 性能优化

1. **内存管理**: DTW实现限制最大长度以避免内存问题
2. **显示优化**: 大型数据集的可视化自动截取前N个样本
3. **计算效率**: 使用numpy向量化操作提高性能

## 未来发展方向

1. **算法优化**: 实现更高效的DTW变体（如FastDTW）
2. **功能扩展**: 支持更多信号类型和文件格式
3. **性能提升**: 并行计算和GPU加速支持
4. **用户界面**: 开发图形用户界面提高可用性
5. **项目结构**: 随着工具成熟，考虑将部分实验工具移出experiments目录

## 项目状态

当前项目处于实验开发阶段，主要工具都在experiments目录中进行开发和测试。项目提供了完整的波形和文本差异分析解决方案，适合研究、教育和实际应用场景。