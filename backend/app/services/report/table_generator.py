"""
动态表格生成器
生成 Markdown 格式的各类数据表格
"""
from typing import Dict, List, Optional, Any


class TableGenerator:
    """Markdown 表格生成器"""

    @staticmethod
    def generate_competitor_table(data: Dict[str, Any]) -> str:
        """
        生成竞品对比表格

        Args:
            data: CompetitorSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_竞品数据暂时不可用_\n"

        competitors = data.get("competitors", [])
        if not competitors:
            return "_未找到竞品数据_\n"

        # 表格标题
        lines = ["| 项目 | 代币 | 市值 | TVL | 24h交易量 | 用户数 | 30d收入 |"]
        lines.append("|------|------|------|-----|----------|--------|---------|")

        # 数据行
        for comp in competitors:
            name = comp.get("name", "未知")
            symbol = comp.get("symbol", "-")
            market_cap = TableGenerator._format_number(comp.get("market_cap"))
            tvl = TableGenerator._format_number(comp.get("tvl"))
            volume = TableGenerator._format_number(comp.get("daily_volume"))
            users = TableGenerator._format_number(comp.get("user_count"), is_int=True)
            revenue = TableGenerator._format_number(comp.get("revenue_30d"))

            lines.append(f"| {name} | {symbol} | {market_cap} | {tvl} | {volume} | {users} | {revenue} |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_valuation_table(data: Dict[str, Any]) -> str:
        """
        生成估值倍数对比表格

        Args:
            data: CompetitorSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_估值数据暂时不可用_\n"

        vm = data.get("valuation_multiples", {})
        sector_vm = data.get("sector_median_multiples", {})

        if not vm and not sector_vm:
            return "_未找到估值倍数数据_\n"

        # 表格标题
        lines = ["| 指标 | 目标项目 | 赛道中位数 | 溢价/折扣 |"]
        lines.append("|------|---------|-----------|----------|")

        # 数据行
        metrics = [
            ("P/S 比率", "ps_ratio"),
            ("FDV/Revenue", "fdv_revenue"),
            ("FDV/TVL", "fdv_tvl"),
            ("P/E 比率", "pe_ratio")
        ]

        for label, key in metrics:
            target_value = vm.get(key)
            sector_value = sector_vm.get(key)

            if target_value is None and sector_value is None:
                continue

            target_str = f"{target_value:.2f}" if target_value is not None else "N/A"
            sector_str = f"{sector_value:.2f}" if sector_value is not None else "N/A"

            # 计算溢价/折扣
            if target_value is not None and sector_value is not None and sector_value > 0:
                premium = ((target_value - sector_value) / sector_value) * 100
                premium_str = f"{premium:+.1f}%"
            else:
                premium_str = "N/A"

            lines.append(f"| {label} | {target_str} | {sector_str} | {premium_str} |")

        if len(lines) == 2:  # 只有标题行
            return "_未找到有效的估值倍数数据_\n"

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_levels_table(data: Dict[str, Any]) -> str:
        """
        生成支撑阻力位表格

        Args:
            data: TechnicalSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_技术面数据暂时不可用_\n"

        key_levels = data.get("key_levels", {})
        price_metrics = data.get("price_metrics", {})

        resistance = key_levels.get("resistance", [])
        support = key_levels.get("support", [])
        current_price = price_metrics.get("current_price")

        if not resistance and not support:
            return "_未找到支撑阻力位数据_\n"

        # 表格标题
        lines = ["| 类型 | 价位 | 强度 |"]
        lines.append("|------|------|------|")

        # 阻力位（从高到低）
        for i, level in enumerate(sorted(resistance, reverse=True), 1):
            strength = "强" if i == 1 else "中" if i == 2 else "弱"
            lines.append(f"| 阻力位 | ${level:,.4f} | {strength} |")

        # 当前价格
        if current_price:
            lines.append(f"| **当前价** | **${current_price:,.4f}** | - |")

        # 支撑位（从高到低）
        for i, level in enumerate(sorted(support, reverse=True), 1):
            strength = "强" if i == 1 else "中" if i == 2 else "弱"
            lines.append(f"| 支撑位 | ${level:,.4f} | {strength} |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_unlock_table(data: Dict[str, Any]) -> str:
        """
        生成代币解锁时间表

        Args:
            data: TokenomicsSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_代币经济学数据暂时不可用_\n"

        unlock_schedule = data.get("unlock_schedule", [])
        supply_structure = data.get("supply_structure", {})

        if not unlock_schedule:
            return "_未找到代币解锁数据_\n"

        circulating_supply = supply_structure.get("circulating_supply", 1)

        # 表格标题
        lines = ["| 日期 | 解锁数量 | 受益方 | 流通占比 |"]
        lines.append("|------|---------|--------|---------|")

        # 数据行（最多显示前 10 个）
        for unlock in unlock_schedule[:10]:
            date = unlock.get("date", "未知")
            amount = unlock.get("amount", 0)
            beneficiary = unlock.get("beneficiary", "未知")

            # 计算占流通供应的百分比
            if circulating_supply > 0:
                pct = (amount / circulating_supply) * 100
                pct_str = f"{pct:.2f}%"
            else:
                pct_str = "N/A"

            amount_str = f"{amount:,.0f}" if amount > 0 else "N/A"

            lines.append(f"| {date} | {amount_str} | {beneficiary} | {pct_str} |")

        # 如果有超过 10 个解锁事件，添加提示
        if len(unlock_schedule) > 10:
            lines.append(f"\n_注：表格仅显示前 10 个解锁事件，共 {len(unlock_schedule)} 个事件_\n")

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_catalyst_calendar_table(data: Dict[str, Any]) -> str:
        """
        生成催化剂日历表格

        Args:
            data: RiskSchema 或 ConclusionSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_催化剂数据暂时不可用_\n"

        catalyst_calendar = data.get("catalyst_calendar", [])

        if not catalyst_calendar:
            return "_未找到催化剂日历数据_\n"

        # 表格标题
        lines = ["| 日期 | 事件 | 影响 | 描述 |"]
        lines.append("|------|------|------|------|")

        # 数据行
        for event in catalyst_calendar:
            date = event.get("date", "未知")
            event_name = event.get("event", "未知事件")
            impact = event.get("impact", "未知")
            description = event.get("description", "-")

            # 限制描述长度
            if len(description) > 50:
                description = description[:47] + "..."

            lines.append(f"| {date} | {event_name} | {impact} | {description} |")

        return "\n".join(lines) + "\n"

    @staticmethod
    def generate_risk_matrix_table(data: Dict[str, Any]) -> str:
        """
        生成风险矩阵表格（风险 × 概率）

        Args:
            data: RiskSchema 数据

        Returns:
            str: Markdown 表格
        """
        if not data or data.get("error"):
            return "_风险数据暂时不可用_\n"

        risks = data.get("risks", {})

        # 收集所有风险项
        all_risks = []
        for category, items in risks.items():
            if items:
                for item in items:
                    all_risks.append({
                        "category": category,
                        "risk": item.get("risk", "未知风险"),
                        "severity": item.get("severity", "未知"),
                        "probability": item.get("probability", "未知"),
                        "impact": item.get("price_impact", "未知")
                    })

        if not all_risks:
            return "_未找到风险数据_\n"

        # 表格标题
        lines = ["| 风险类别 | 风险 | 严重程度 | 概率 | 价格影响 |"]
        lines.append("|---------|------|---------|------|---------|")

        # 数据行
        category_names = {
            "regulatory": "监管",
            "technical": "技术",
            "competitive": "竞争",
            "market": "市场",
            "tokenomics": "代币经济"
        }

        for risk in all_risks[:10]:  # 最多显示 10 个风险
            category = category_names.get(risk["category"], risk["category"])
            risk_name = risk["risk"]
            severity = risk["severity"]
            probability = risk["probability"]
            impact = risk["impact"]

            lines.append(f"| {category} | {risk_name} | {severity} | {probability} | {impact} |")

        if len(all_risks) > 10:
            lines.append(f"\n_注：表格仅显示前 10 个风险，共 {len(all_risks)} 个风险_\n")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_number(value: Optional[float], is_int: bool = False, prefix: str = "$") -> str:
        """
        格式化数字（千分位、单位转换）

        Args:
            value: 数字值
            is_int: 是否为整数
            prefix: 前缀（如 $）

        Returns:
            str: 格式化后的字符串
        """
        if value is None:
            return "N/A"

        if value == 0:
            return "0"

        # 单位转换
        if abs(value) >= 1_000_000_000_000:  # Trillion
            formatted = f"{value / 1_000_000_000_000:.2f}T"
        elif abs(value) >= 1_000_000_000:  # Billion
            formatted = f"{value / 1_000_000_000:.2f}B"
        elif abs(value) >= 1_000_000:  # Million
            formatted = f"{value / 1_000_000:.2f}M"
        elif abs(value) >= 1_000:  # Thousand
            formatted = f"{value / 1_000:.2f}K"
        else:
            if is_int:
                formatted = f"{int(value):,}"
            else:
                formatted = f"{value:,.2f}"

        # 添加前缀
        if prefix and abs(value) >= 1_000:
            return f"{prefix}{formatted}"
        elif is_int:
            return formatted
        else:
            return f"{prefix}{formatted}" if prefix else formatted


# ================================
# 全局实例
# ================================

table_generator = TableGenerator()
