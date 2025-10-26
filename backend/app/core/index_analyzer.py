"""
索引使用分析工具

用于分析数据库索引使用情况、识别未使用的索引和需要添加的索引
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class IndexAnalyzer:
    """索引分析器"""

    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def get_all_indexes(self) -> List[Dict[str, Any]]:
        """
        获取数据库中所有索引信息

        Returns:
            索引列表，每个索引包含：
            - schema: 模式名
            - table: 表名
            - index_name: 索引名
            - index_type: 索引类型
            - columns: 索引列
            - is_unique: 是否唯一索引
            - size_bytes: 索引大小（字节）
        """
        query = text("""
            SELECT
                schemaname as schema,
                tablename as table,
                indexname as index_name,
                indexdef as index_def
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)

        result = await self.session.execute(query)
        indexes = []

        for row in result.fetchall():
            index_info = {
                "schema": row.schema,
                "table": row.table,
                "index_name": row.index_name,
                "index_def": row.index_def,
            }

            # 分析索引定义
            index_def = row.index_def.lower()
            index_info["is_unique"] = "unique" in index_def
            index_info["is_primary"] = "pkey" in row.index_name.lower()

            # 提取索引类型
            if "btree" in index_def:
                index_info["index_type"] = "btree"
            elif "hash" in index_def:
                index_info["index_type"] = "hash"
            elif "gin" in index_def:
                index_info["index_type"] = "gin"
            elif "gist" in index_def:
                index_info["index_type"] = "gist"
            else:
                index_info["index_type"] = "unknown"

            indexes.append(index_info)

        # 获取索引大小
        for index in indexes:
            size_query = text("""
                SELECT pg_relation_size(:index_name) as size_bytes
            """)
            size_result = await self.session.execute(
                size_query,
                {"index_name": f"public.{index['index_name']}"}
            )
            size_row = size_result.fetchone()
            if size_row:
                index["size_bytes"] = size_row.size_bytes
                index["size_mb"] = round(size_row.size_bytes / 1024 / 1024, 2)

        return indexes

    async def get_index_usage_stats(self) -> List[Dict[str, Any]]:
        """
        获取索引使用统计信息

        Returns:
            索引使用统计列表，每个包含：
            - schema: 模式名
            - table: 表名
            - index_name: 索引名
            - idx_scan: 索引扫描次数
            - idx_tup_read: 通过索引读取的行数
            - idx_tup_fetch: 通过索引获取的行数
            - size_bytes: 索引大小
        """
        query = text("""
            SELECT
                schemaname as schema,
                tablename as table,
                indexrelname as index_name,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_relation_size(indexrelid) as size_bytes
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan, tablename, indexrelname
        """)

        result = await self.session.execute(query)
        stats = []

        for row in result.fetchall():
            stat = {
                "schema": row.schema,
                "table": row.table,
                "index_name": row.index_name,
                "idx_scan": row.idx_scan or 0,
                "idx_tup_read": row.idx_tup_read or 0,
                "idx_tup_fetch": row.idx_tup_fetch or 0,
                "size_bytes": row.size_bytes or 0,
                "size_mb": round((row.size_bytes or 0) / 1024 / 1024, 2),
            }
            stats.append(stat)

        return stats

    async def find_unused_indexes(self, min_scans: int = 10) -> List[Dict[str, Any]]:
        """
        查找未使用或很少使用的索引

        Args:
            min_scans: 最小扫描次数阈值

        Returns:
            未使用的索引列表
        """
        usage_stats = await self.get_index_usage_stats()

        unused_indexes = []
        for stat in usage_stats:
            # 跳过主键和唯一约束索引（通常不能删除）
            if "pkey" in stat["index_name"].lower():
                continue
            if "key" in stat["index_name"].lower():
                continue

            # 识别很少使用的索引
            if stat["idx_scan"] < min_scans:
                stat["recommendation"] = "考虑删除此索引（几乎未使用）"
                stat["reason"] = f"只被扫描 {stat['idx_scan']} 次"
                unused_indexes.append(stat)

        return unused_indexes

    async def find_duplicate_indexes(self) -> List[Dict[str, Any]]:
        """
        查找重复或冗余的索引

        Returns:
            可能重复的索引列表
        """
        all_indexes = await self.get_all_indexes()

        # 按表分组
        tables = {}
        for idx in all_indexes:
            table = idx["table"]
            if table not in tables:
                tables[table] = []
            tables[table].append(idx)

        duplicates = []

        # 检查每个表的索引
        for table, indexes in tables.items():
            for i, idx1 in enumerate(indexes):
                for idx2 in indexes[i + 1:]:
                    # 简单的重复检测：索引定义相似
                    if self._indexes_similar(idx1, idx2):
                        duplicates.append({
                            "table": table,
                            "index1": idx1["index_name"],
                            "index2": idx2["index_name"],
                            "def1": idx1["index_def"],
                            "def2": idx2["index_def"],
                            "recommendation": "可能存在重复，考虑保留一个"
                        })

        return duplicates

    def _indexes_similar(self, idx1: Dict, idx2: Dict) -> bool:
        """检查两个索引是否相似"""
        # 跳过主键
        if idx1["is_primary"] or idx2["is_primary"]:
            return False

        # 简单的相似性检查：索引定义的关键部分相同
        def1_key = idx1["index_def"].split("USING")[1] if "USING" in idx1["index_def"] else idx1["index_def"]
        def2_key = idx2["index_def"].split("USING")[1] if "USING" in idx2["index_def"] else idx2["index_def"]

        # 提取列名部分
        def1_cols = def1_key.split("(")[1].split(")")[0] if "(" in def1_key else ""
        def2_cols = def2_key.split("(")[1].split(")")[0] if "(" in def2_key else ""

        return def1_cols == def2_cols

    async def analyze_table_scans(self) -> List[Dict[str, Any]]:
        """
        分析表扫描统计，识别可能需要索引的查询

        Returns:
            表扫描统计列表
        """
        query = text("""
            SELECT
                schemaname as schema,
                relname as table,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY seq_scan DESC, relname
        """)

        result = await self.session.execute(query)
        stats = []

        for row in result.fetchall():
            stat = {
                "schema": row.schema,
                "table": row.table,
                "seq_scan": row.seq_scan or 0,
                "seq_tup_read": row.seq_tup_read or 0,
                "idx_scan": row.idx_scan or 0,
                "idx_tup_fetch": row.idx_tup_fetch or 0,
                "inserts": row.inserts or 0,
                "updates": row.updates or 0,
                "deletes": row.deletes or 0,
                "live_tuples": row.live_tuples or 0,
            }

            # 计算顺序扫描比例
            total_scans = stat["seq_scan"] + stat["idx_scan"]
            if total_scans > 0:
                stat["seq_scan_ratio"] = round(stat["seq_scan"] / total_scans, 2)
            else:
                stat["seq_scan_ratio"] = 0

            # 生成建议
            recommendations = []
            if stat["seq_scan"] > 100 and stat["seq_scan_ratio"] > 0.5:
                recommendations.append(
                    f"表 {stat['table']} 有大量顺序扫描（{stat['seq_scan']}次），"
                    f"考虑添加索引以提高查询性能"
                )

            if stat["seq_tup_read"] > 100000:
                recommendations.append(
                    f"顺序读取了 {stat['seq_tup_read']} 行，可能需要优化查询或添加索引"
                )

            stat["recommendations"] = recommendations

            stats.append(stat)

        return stats

    async def get_index_recommendations(self) -> Dict[str, Any]:
        """
        生成索引优化建议报告

        Returns:
            完整的索引优化建议报告
        """
        unused_indexes = await self.find_unused_indexes()
        duplicate_indexes = await self.find_duplicate_indexes()
        table_scans = await self.analyze_table_scans()

        # 识别需要索引的表
        tables_need_indexes = [
            stat for stat in table_scans
            if stat["recommendations"]
        ]

        report = {
            "summary": {
                "total_unused_indexes": len(unused_indexes),
                "total_duplicate_indexes": len(duplicate_indexes),
                "tables_need_indexes": len(tables_need_indexes),
            },
            "unused_indexes": unused_indexes,
            "duplicate_indexes": duplicate_indexes,
            "tables_need_optimization": tables_need_indexes,
            "recommendations": []
        }

        # 生成优先级建议
        if unused_indexes:
            total_wasted_mb = sum(idx["size_mb"] for idx in unused_indexes)
            report["recommendations"].append({
                "priority": "high",
                "category": "unused_indexes",
                "message": f"发现 {len(unused_indexes)} 个未使用的索引，"
                          f"占用 {total_wasted_mb:.2f} MB 空间。"
                          f"考虑删除以节省存储和提高写入性能。"
            })

        if duplicate_indexes:
            report["recommendations"].append({
                "priority": "medium",
                "category": "duplicate_indexes",
                "message": f"发现 {len(duplicate_indexes)} 对可能重复的索引。"
                          f"考虑删除冗余索引以减少维护开销。"
            })

        if tables_need_indexes:
            report["recommendations"].append({
                "priority": "high",
                "category": "missing_indexes",
                "message": f"发现 {len(tables_need_indexes)} 个表有大量顺序扫描。"
                          f"考虑添加适当的索引以提高查询性能。"
            })

        return report


async def analyze_database_indexes() -> Dict[str, Any]:
    """
    分析数据库索引并生成报告

    便捷函数，用于快速分析数据库索引

    Returns:
        索引分析报告

    Example:
        >>> report = await analyze_database_indexes()
        >>> print(f"未使用的索引: {report['summary']['total_unused_indexes']}")
    """
    async with IndexAnalyzer() as analyzer:
        return await analyzer.get_index_recommendations()


async def get_index_stats() -> List[Dict[str, Any]]:
    """
    获取索引使用统计

    Returns:
        索引使用统计列表
    """
    async with IndexAnalyzer() as analyzer:
        return await analyzer.get_index_usage_stats()


async def find_unused_indexes() -> List[Dict[str, Any]]:
    """
    查找未使用的索引

    Returns:
        未使用的索引列表
    """
    async with IndexAnalyzer() as analyzer:
        return await analyzer.find_unused_indexes()
