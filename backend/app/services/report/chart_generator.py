"""
图表生成器
使用 matplotlib 和 plotly 生成图表，转换为 Base64 嵌入 Markdown
"""
import base64
from io import BytesIO
from typing import Dict, List, Optional, Any
import matplotlib
matplotlib.use('Agg')  # 无显示器环境
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 设置中文字体支持（可选，根据系统调整）
try:
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass


class ChartGenerator:
    """图表生成器（Base64 嵌入 Markdown）"""

    @staticmethod
    def generate_price_chart(data: Dict[str, Any]) -> str:
        """
        生成价格走势图

        Args:
            data: TimeframeSchema 数据

        Returns:
            str: Markdown 格式的图片（Base64 编码）
        """
        if not data or data.get("error"):
            return "_价格走势图暂时不可用_\n"

        windows = data.get("windows", [])
        if not windows:
            return "_未找到价格数据_\n"

        try:
            fig, ax = plt.figure(figsize=(10, 6)), plt.gca()

            # 准备数据
            dates = []
            prices = []
            volumes = []

            for window in windows:
                # 从时间窗推算日期（简化处理）
                timeframe = window.get("timeframe", "")
                if "7天" in timeframe or "7" in timeframe:
                    days_ago = 7
                elif "30天" in timeframe or "30" in timeframe:
                    days_ago = 30
                elif "90天" in timeframe or "90" in timeframe:
                    days_ago = 90
                else:
                    continue

                date = datetime.now() - timedelta(days=days_ago)
                dates.append(date)

                # 获取价格变化
                metrics = window.get("metrics", {})
                price_change_pct = metrics.get("price_change_pct", 0)
                # 假设基准价格为 100（实际应该从 technical 获取）
                price = 100 * (1 + price_change_pct / 100)
                prices.append(price)

                volume_change_pct = metrics.get("volume_change_pct", 0)
                volume = 1000000 * (1 + volume_change_pct / 100)
                volumes.append(volume)

            if not dates:
                return "_价格数据不足以生成图表_\n"

            # 添加当前日期和价格
            dates.append(datetime.now())
            prices.append(100)  # 当前价格基准

            # 绘制价格线
            ax.plot(dates, prices, marker='o', linewidth=2, label='价格', color='#2E86DE')
            ax.fill_between(dates, prices, alpha=0.3, color='#2E86DE')

            # 设置标题和标签
            ax.set_title('价格走势图', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('价格指数', fontsize=12)

            # 格式化 X 轴日期
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.xticks(rotation=45)

            # 网格和图例
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='best', fontsize=10)

            # 调整布局
            plt.tight_layout()

            # 转换为 Base64
            return ChartGenerator._fig_to_base64(fig)

        except Exception as e:
            plt.close('all')
            return f"_价格走势图生成失败: {str(e)}_\n"

    @staticmethod
    def generate_sentiment_chart(data: Dict[str, Any]) -> str:
        """
        生成情绪分布饼图

        Args:
            data: SentimentSchema 数据

        Returns:
            str: Markdown 格式的图片（Base64 编码）
        """
        if not data or data.get("error"):
            return "_情绪分布图暂时不可用_\n"

        social_metrics = data.get("social_metrics", [])
        if not social_metrics:
            return "_未找到社交媒体数据_\n"

        try:
            fig, ax = plt.subplots(figsize=(8, 8))

            # 准备数据
            platforms = []
            mentions = []
            colors = []

            color_map = {
                "Twitter": "#1DA1F2",
                "Reddit": "#FF4500",
                "Telegram": "#0088cc",
                "Discord": "#5865F2"
            }

            for metric in social_metrics:
                platform = metric.get("platform", "未知")
                mention_count = metric.get("mention_count", 0)

                if mention_count > 0:
                    platforms.append(platform)
                    mentions.append(mention_count)
                    colors.append(color_map.get(platform, "#95a5a6"))

            if not platforms:
                return "_情绪数据不足以生成图表_\n"

            # 绘制饼图
            wedges, texts, autotexts = ax.pie(
                mentions,
                labels=platforms,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                explode=[0.05] * len(platforms)  # 分离每个扇形
            )

            # 设置文本样式
            for text in texts:
                text.set_fontsize(12)
                text.set_fontweight('bold')

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')

            # 设置标题
            ax.set_title('社交媒体提及分布', fontsize=16, fontweight='bold', pad=20)

            # 调整布局
            plt.tight_layout()

            # 转换为 Base64
            return ChartGenerator._fig_to_base64(fig)

        except Exception as e:
            plt.close('all')
            return f"_情绪分布图生成失败: {str(e)}_\n"

    @staticmethod
    def generate_tvl_chart(data: Dict[str, Any]) -> str:
        """
        生成 TVL 趋势图（柱状图）

        Args:
            data: OnchainSchema 或 CompetitorSchema 数据

        Returns:
            str: Markdown 格式的图片（Base64 编码）
        """
        # 注意：这里需要从聚合数据中获取历史 TVL 数据
        # 由于当前 schema 没有历史数据，这里使用占位实现
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # 模拟数据（实际应该从数据源获取）
            dates = [(datetime.now() - timedelta(days=i*7)) for i in range(12, 0, -1)]
            tvl_values = [4.2, 4.5, 4.1, 3.9, 4.3, 4.6, 4.4, 4.7, 4.5, 4.8, 4.6, 4.9]

            # 绘制柱状图
            bars = ax.bar(dates, tvl_values, width=5, color='#27AE60', alpha=0.7, edgecolor='black')

            # 设置标题和标签
            ax.set_title('TVL 趋势图（过去12周）', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('TVL (Billion USD)', fontsize=12)

            # 格式化 X 轴
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.xticks(rotation=45)

            # 网格
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.set_axisbelow(True)

            # 调整布局
            plt.tight_layout()

            # 转换为 Base64
            return ChartGenerator._fig_to_base64(fig)

        except Exception as e:
            plt.close('all')
            return f"_TVL 趋势图生成失败: {str(e)}_\n"

    @staticmethod
    def generate_risk_heatmap(data: Dict[str, Any]) -> str:
        """
        生成风险热力图

        Args:
            data: RiskSchema 数据

        Returns:
            str: Markdown 格式的图片（Base64 编码）
        """
        if not data or data.get("error"):
            return "_风险热力图暂时不可用_\n"

        risks = data.get("risks", {})

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # 准备数据
            categories = []
            risk_scores = []

            severity_map = {"高": 3, "中": 2, "低": 1, "未知": 0}
            prob_map = {"高": 3, "中": 2, "低": 1, "未知": 0}

            category_names = {
                "regulatory": "监管风险",
                "technical": "技术风险",
                "competitive": "竞争风险",
                "market": "市场风险",
                "tokenomics": "代币风险"
            }

            for category, items in risks.items():
                if items:
                    # 计算该类别的平均风险分数
                    scores = []
                    for item in items:
                        severity = severity_map.get(item.get("severity", "未知"), 0)
                        probability = prob_map.get(item.get("probability", "未知"), 0)
                        scores.append(severity * probability)

                    if scores:
                        categories.append(category_names.get(category, category))
                        risk_scores.append(sum(scores) / len(scores))

            if not categories:
                return "_风险数据不足以生成热力图_\n"

            # 绘制水平柱状图
            colors = ['#E74C3C' if score > 6 else '#F39C12' if score > 3 else '#27AE60' for score in risk_scores]
            bars = ax.barh(categories, risk_scores, color=colors, edgecolor='black', alpha=0.8)

            # 设置标题和标签
            ax.set_title('风险评估热力图', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('风险分数', fontsize=12)
            ax.set_xlim(0, 10)

            # 网格
            ax.grid(True, alpha=0.3, linestyle='--', axis='x')
            ax.set_axisbelow(True)

            # 添加数值标签
            for i, (bar, score) in enumerate(zip(bars, risk_scores)):
                ax.text(score + 0.2, i, f'{score:.1f}', va='center', fontsize=10, fontweight='bold')

            # 调整布局
            plt.tight_layout()

            # 转换为 Base64
            return ChartGenerator._fig_to_base64(fig)

        except Exception as e:
            plt.close('all')
            return f"_风险热力图生成失败: {str(e)}_\n"

    @staticmethod
    def generate_valuation_comparison_chart(data: Dict[str, Any]) -> str:
        """
        生成估值对比柱状图

        Args:
            data: CompetitorSchema 数据

        Returns:
            str: Markdown 格式的图片（Base64 编码）
        """
        if not data or data.get("error"):
            return "_估值对比图暂时不可用_\n"

        vm = data.get("valuation_multiples", {})
        sector_vm = data.get("sector_median_multiples", {})

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # 准备数据
            metrics = ["P/S", "FDV/Revenue", "FDV/TVL"]
            target_values = [
                vm.get("ps_ratio", 0),
                vm.get("fdv_revenue", 0),
                vm.get("fdv_tvl", 0)
            ]
            sector_values = [
                sector_vm.get("ps_ratio", 0),
                sector_vm.get("fdv_revenue", 0),
                sector_vm.get("fdv_tvl", 0)
            ]

            # 过滤有效数据
            valid_metrics = []
            valid_target = []
            valid_sector = []

            for m, t, s in zip(metrics, target_values, sector_values):
                if t > 0 or s > 0:
                    valid_metrics.append(m)
                    valid_target.append(t)
                    valid_sector.append(s)

            if not valid_metrics:
                return "_估值数据不足以生成图表_\n"

            # 设置柱状图位置
            x = range(len(valid_metrics))
            width = 0.35

            # 绘制分组柱状图
            bars1 = ax.bar([i - width/2 for i in x], valid_target, width, label='目标项目', color='#3498DB', edgecolor='black')
            bars2 = ax.bar([i + width/2 for i in x], valid_sector, width, label='赛道中位数', color='#95A5A6', edgecolor='black')

            # 设置标题和标签
            ax.set_title('估值倍数对比', fontsize=16, fontweight='bold', pad=20)
            ax.set_ylabel('倍数', fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(valid_metrics, fontsize=11)

            # 图例
            ax.legend(loc='best', fontsize=10)

            # 网格
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.set_axisbelow(True)

            # 添加数值标签
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontsize=9)

            # 调整布局
            plt.tight_layout()

            # 转换为 Base64
            return ChartGenerator._fig_to_base64(fig)

        except Exception as e:
            plt.close('all')
            return f"_估值对比图生成失败: {str(e)}_\n"

    @staticmethod
    def _fig_to_base64(fig) -> str:
        """
        将 matplotlib 图表转换为 Base64 编码的 Markdown 图片

        Args:
            fig: matplotlib figure 对象

        Returns:
            str: Markdown 格式的 Base64 图片
        """
        try:
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            return f"![Chart](data:image/png;base64,{img_str})\n"
        except Exception as e:
            plt.close(fig)
            return f"_图表转换失败: {str(e)}_\n"


# ================================
# 全局实例
# ================================

chart_generator = ChartGenerator()
