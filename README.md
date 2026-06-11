# Hermes Agent Skills

自定义 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 技能集合，用于学术研究自动化。

## 技能列表

### 🎨 guizang-ppt — 网页 PPT 生成器

生成横向翻页网页 PPT（单 HTML 文件），支持两种风格：
- **瑞士国际主义风格**：WebGL 网格背景 + ASCII 呼吸场 + IKB 克莱因蓝，含 20+ 种版式模板
- **电子杂志 × 电子墨水风格**：章节幕封、数据大字报、图片网格

**用法**：加载 skill 后直接用自然语言描述 PPT 需求即可，无需手动写 HTML。

### 📚 research-question-map — 研究问题图谱

从学术论文中自动提取研究问题，聚类、构建概念树、导出可点击的 Markmap 思维导图 HTML。
- 支持 PDF 批量解析 + DeepSeek API 提取研究问题
- 支持 CSV 直接导入（跳过 PDF 解析）
- 语义聚类（基于大模型）+ 概念树构建
- 输出：JSON 聚类结果 + CSV 审查表 + Markmap 思维导图

**用法**：
```bash
# PDF 模式
python scripts/run_pipeline.py --pdf-dir "papers/" --output-dir "output/"

# CSV 模式  
python scripts/run_pipeline.py --csv-input "论文列表.csv" --output-dir "output/"
```

## 安装

每个 skill 可独立使用。将 skill 目录复制到 Hermes Agent 的 skills 目录：

```bash
cp -r guizang-ppt ~/.hermes/skills/
cp -r research-question-map ~/.hermes/skills/
```

## 环境变量

在 `~/.hermes/.env` 中配置：

```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

## 许可

MIT License
