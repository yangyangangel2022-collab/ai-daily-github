import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import anthropic
import feedparser
import requests
from bs4 import BeautifulSoup

class AINewsCrawlerWithReport:
    def __init__(self, claude_api_key):
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.articles = []
        self.threshold = datetime.now() - timedelta(hours=48)
    
    def is_fresh(self, date):
        """检查是否在 48 小时内"""
        if not date:
            return False
        return date > self.threshold
    
    def crawl_all_sources(self):
        """爬取所有源"""
        print("🕷️ 开始爬取数据...")
        
        sources = {
            "P1_美国科技": [
                {"name": "OpenAI Blog", "rss_url": "https://openai.com/news/rss.xml", "priority": "P1", "category": "美国科技"},
                {"name": "Anthropic Research", "url": "https://www.anthropic.com/research", "priority": "P1", "category": "美国科技"},
                {"name": "Google AI Blog", "rss_url": "https://ai.googleblog.com/feeds/posts/default", "priority": "P1", "category": "美国科技"},
                {"name": "Google Research", "url": "https://research.google/", "priority": "P1", "category": "美国科技"},
                {"name": "Meta AI", "url": "https://ai.facebook.com/", "priority": "P1", "category": "美国科技"},
                {"name": "Microsoft AI", "url": "https://www.microsoft.com/en-us/ai", "priority": "P1", "category": "美国科技"},
                {"name": "Apple Developer", "url": "https://developer.apple.com/news/", "priority": "P1", "category": "美国科技"},
                {"name": "X.AI", "url": "https://x.ai/", "priority": "P1", "category": "美国科技"},
            ],
            "P1_中国AI": [
                {"name": "DeepSeek", "url": "https://github.com/deepseek-ai/", "priority": "P1", "category": "中国AI"},
                {"name": "通义千问", "url": "https://www.qianwen.com/", "priority": "P1", "category": "中国AI"},
                {"name": "豆包", "url": "https://www.doubao.com/", "priority": "P1", "category": "中国AI"},
                {"name": "MiniMax", "url": "https://www.minimax.io/", "priority": "P1", "category": "中国AI"},
                {"name": "智谱AI", "url": "https://www.zhipu.ai/", "priority": "P1", "category": "中国AI"},
                {"name": "文心一言", "url": "https://yiyan.baidu.com/", "priority": "P1", "category": "中国AI"},
                {"name": "Kimi", "url": "https://www.kimi.com/", "priority": "P1", "category": "中国AI"},
                {"name": "Yi", "url": "https://yi.com/", "priority": "P1", "category": "中国AI"},
                {"name": "百川", "url": "https://www.baichuan-ai.com/", "priority": "P1", "category": "中国AI"},
                {"name": "混元", "url": "https://hunyuan.tencent.com/", "priority": "P1", "category": "中国AI"},
            ],
            "P1_开源": [
                {"name": "GitHub Trending", "url": "https://github.com/trending/machine-learning", "priority": "P1", "category": "开源"},
                {"name": "HuggingFace", "url": "https://huggingface.co/papers", "priority": "P1", "category": "开源"},
                {"name": "Papers with Code", "url": "https://paperswithcode.com/", "priority": "P1", "category": "开源"},
            ],
            "P2_KOL": [
                {"name": "deeplearning.ai", "url": "https://www.deeplearning.ai/", "priority": "P2", "category": "教育"},
                {"name": "The Batch", "url": "https://www.deeplearning.ai/the-batch/", "priority": "P2", "category": "教育"},
                {"name": "Hacker News", "url": "https://news.ycombinator.com/", "priority": "P2", "category": "技术社区"},
                {"name": "r/MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/", "priority": "P2", "category": "技术社区"},
            ],
            "P3_媒体": [
                {"name": "The Verge", "url": "https://www.theverge.com/", "priority": "P3", "category": "英文综合"},
                {"name": "TechCrunch", "url": "https://techcrunch.com/", "priority": "P3", "category": "英文综合"},
                {"name": "VentureBeat AI", "url": "https://venturebeat.com/ai/", "priority": "P3", "category": "AI垂直"},
                {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/", "priority": "P3", "category": "AI垂直"},
                {"name": "机器之心", "url": "https://www.jiqizhixin.com/", "priority": "P3", "category": "中文媒体"},
                {"name": "量子位", "url": "https://www.qbitai.com/", "priority": "P3", "category": "中文媒体"},
            ]
        }
        
        # 爬取 RSS
        for category, source_list in sources.items():
            for source in source_list:
                if source.get("rss_url"):
                    self._crawl_rss(source)
                else:
                    self._crawl_website(source)
        
        print(f"✅ 爬取完成: {len(self.articles)} 篇文章")
        return self.articles
    
    def _crawl_rss(self, source):
        """爬取 RSS 源"""
        try:
            feed = feedparser.parse(source["rss_url"])
            for entry in feed.entries[:5]:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime(*entry.published_parsed[:6])
                else:
                    pub_time = datetime.now()
                
                if not self.is_fresh(pub_time):
                    continue
                
                self.articles.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:300],
                    "source": source["name"],
                    "date": pub_time.isoformat(),
                    "priority": source["priority"],
                    "category": source["category"],
                    "content": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
                })
        except Exception as e:
            print(f"❌ RSS 错误 {source.get('name')}: {e}")
    
    def _crawl_website(self, source):
        """爬取网站"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(source.get("url", ""), timeout=5, headers=headers)
            # 简单的 HTML 分析...
            # 这里可以根据需要添加更详细的网页解析
        except Exception as e:
            print(f"❌ 网站爬虫错误 {source.get('name')}: {e}")
    
    def call_claude_for_html_generation(self, articles):
        """调用 Claude 生成 HTML"""
        
        print("🤖 Claude 生成 HTML 中...")
        
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
        
        generation_prompt = f"""
# AI每日情报日报 - 完整生成指令 v2.24 Patch2

## 🎯 核心任务
采50+信源过去24h AI内容，评分筛选，按6大板块组织，生成响应式HTML文件（支持桌面+移动端）

---

## 📊 信源体系（50+信源）

优先级1：一手源头

美国科技公司: OpenAI Blog, Anthropic Research, Google Research Blog, Google AI Blog, Meta AI Blog, Microsoft AI Blog, Apple Developer, X.AI Blog
中国AI公司: DeepSeek官网/GitHub, 通义千问, 豆包, 海螺AI(MiniMax), 智谱AI, 文心一言, 月之暗面(Kimi), 零一万物(Yi), 百川智能, 混元大模型
开源社区: GitHub Trending, HuggingFace Papers & Models, Papers with Code

优先级2：关键意见领袖与深度内容

顶级研究者: @AndrewYNg, @ylecun, @geoffreyhinton, @sama, @karpathy, @jimfan
教育内容: deeplearning.ai, The Batch（吴恩达周报）, Coursera AI, fast.ai, The Rundown AI（日报）
技术社区: Hacker News, r/MachineLearning, r/LocalLLaMA
深度访谈: Lex Fridman Podcast, Acquired, a16z Podcast, All-In Podcast, No Priors

优先级3：专业媒体

英文综合: The Verge, TechCrunch, Ars Technica, Wired, Bloomberg Tech
AI垂直: VentureBeat AI, MIT Tech Review, IEEE Spectrum, The Decoder, TLDR AI
中文媒体: 机器之心, 量子位, 36氪AI, 极客公园, InfoQ AI前线

---

## 🎯 评分与筛选系统

### ⏰ 第一步：时效硬性门槛
- 发布时间 **> 48小时** → 直接排除
- **唯一例外**：重大事件（融资/模型发布/政策）在48h内被大量媒体集中报道
- **周末例外**：若事件发生在周六/日，放宽至72小时

### 📊 第二步：评分维度
- **底层变量性** (0-3分): 是否改变行业基础假设
- **稀缺性** (0-2分): 信息是否独家或罕见
- **可操作性** (0-2分): 是否能直接指导创业决策
- **时效性** (0-2分): 是否突发/最新
- **权威性** (0-1分): 来源是否可信

### 📋 第三步：筛选规则
- ≥9分 必选
- 8-8.9分 酌情
- <8分 舍弃

---

## 📑 6大板块结构

### 板块1: 💡 META_INSIGHT 元洞察
- **主题色**: 紫色 #a78bfa
- **内容要求**:
  - 今日趋势扫描(3-4条)
  - 跨板块关联(A→B→C格式)
  - 创业方向建议(短期/中期/长期)
  - 风险预警(1-2条)
- **默认状态**: 展开（其他板块折叠）
- **卡片样式**: 保留深色背景卡片(var(--surface2))，左侧紫色边框

### 板块2-6: 其他板块
- **主题色**:
  - 行业动态 #60a5fa（蓝色）
  - 投资融资 #3b82f6（深蓝）
  - 技术突破 #22c55e（绿色）
  - 产品上线 #2dd4bf（青色）
  - 教育资讯 #38bdf8（天蓝）
- **默认状态**: 折叠
- **新闻样式**: v2.24扁平设计

---

## 🔒 板块图标（固定不变）

| 板块 | 图标 | 英文标识 |
|------|------|---------|
| 元洞察 | 💡 | META_INSIGHT |
| 行业动态 | 📡 | INDUSTRY |
| 投资融资 | 💰 | INVESTMENT |
| 技术突破 | 🚀 | BREAKTHROUGH |
| 产品上线 | ✨ | PRODUCT |
| 教育资讯 | 🎓 | EDUCATION |

---

## 🎨 视觉设计规范 v2.24 Patch2

### Header设计
```html
<header class="header">
    <div class="header-badge">LIVE · AI INTELLIGENCE DAILY</div>
    <h1><span class="gradient-text">AI每日情报</span></h1>
    <div class="header-meta">
        <span>{{DATE}}</span>
        <span>实时抓取</span>
    </div>
</header>"""
