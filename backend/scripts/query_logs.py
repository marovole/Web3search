#!/usr/bin/env python3
"""
日志查询工具

用于查询和分析JSON格式的日志文件

Usage:
    python scripts/query_logs.py --request-id abc-123
    python scripts/query_logs.py --level ERROR --since "2024-01-01 10:00:00"
    python scripts/query_logs.py --user-id 456 --symbol BTC
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# 日志目录
LOG_DIR = Path("logs")


class LogQuery:
    """日志查询器"""

    def __init__(self, log_file: Path):
        """
        初始化查询器

        Args:
            log_file: 日志文件路径
        """
        self.log_file = log_file

    def query(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
        conversation_id: Optional[str] = None,
        level: Optional[str] = None,
        event: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        查询日志

        Args:
            request_id: 请求ID
            user_id: 用户ID
            symbol: 加密货币符号
            conversation_id: 会话ID
            level: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
            event: 事件名称
            since: 开始时间
            until: 结束时间
            limit: 返回结果数量限制
            pattern: 消息内容匹配模式（正则表达式）

        Returns:
            匹配的日志记录列表
        """
        results = []
        count = 0

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    log_entry = json.loads(line)
                except json.JSONDecodeError:
                    # 跳过非JSON行
                    continue

                # 应用过滤器
                if not self._matches(
                    log_entry,
                    request_id=request_id,
                    user_id=user_id,
                    symbol=symbol,
                    conversation_id=conversation_id,
                    level=level,
                    event=event,
                    since=since,
                    until=until,
                    pattern=pattern,
                ):
                    continue

                results.append(log_entry)
                count += 1

                # 检查限制
                if limit and count >= limit:
                    break

        return results

    def _matches(
        self,
        log_entry: Dict[str, Any],
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
        conversation_id: Optional[str] = None,
        level: Optional[str] = None,
        event: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        pattern: Optional[str] = None,
    ) -> bool:
        """
        检查日志记录是否匹配过滤条件

        Args:
            log_entry: 日志记录
            其他参数：过滤条件

        Returns:
            True表示匹配，False表示不匹配
        """
        # request_id过滤
        if request_id and log_entry.get("request_id") != request_id:
            return False

        # user_id过滤
        if user_id is not None and log_entry.get("user_id") != user_id:
            return False

        # symbol过滤
        if symbol and log_entry.get("symbol") != symbol:
            return False

        # conversation_id过滤
        if conversation_id and log_entry.get("conversation_id") != conversation_id:
            return False

        # 日志级别过滤
        if level and log_entry.get("log_level", "").upper() != level.upper():
            return False

        # 事件名称过滤
        if event and log_entry.get("event") != event:
            return False

        # 时间范围过滤
        timestamp_str = log_entry.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                if since and timestamp < since:
                    return False

                if until and timestamp > until:
                    return False
            except (ValueError, TypeError):
                pass

        # 消息内容模式匹配
        if pattern:
            message = log_entry.get("event", "")
            if not re.search(pattern, message, re.IGNORECASE):
                return False

        return True

    def get_request_trace(self, request_id: str) -> List[Dict[str, Any]]:
        """
        获取完整的请求追踪

        Args:
            request_id: 请求ID

        Returns:
            该请求的所有日志记录（按时间排序）
        """
        logs = self.query(request_id=request_id)
        # 按时间戳排序
        logs.sort(key=lambda x: x.get("timestamp", ""))
        return logs

    def get_error_summary(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取错误摘要

        Args:
            since: 开始时间
            until: 结束时间

        Returns:
            错误统计信息
        """
        errors = self.query(level="ERROR", since=since, until=until)

        # 统计错误类型
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "recent_errors": errors[-10:] if len(errors) > 10 else errors,
        }


def format_log_entry(entry: Dict[str, Any], verbose: bool = False) -> str:
    """
    格式化日志记录为可读字符串

    Args:
        entry: 日志记录
        verbose: 是否显示详细信息

    Returns:
        格式化后的字符串
    """
    timestamp = entry.get("timestamp", "N/A")
    level = entry.get("log_level", "INFO").upper()
    event = entry.get("event", "")
    request_id = entry.get("request_id", "")

    # 基本信息
    parts = [
        f"[{timestamp}]",
        f"[{level}]",
        f"[{request_id[:8] if request_id else 'N/A'}]",
        event,
    ]

    # 添加上下文信息
    context_parts = []
    if "user_id" in entry:
        context_parts.append(f"user={entry['user_id']}")
    if "symbol" in entry:
        context_parts.append(f"symbol={entry['symbol']}")
    if "duration_ms" in entry:
        context_parts.append(f"duration={entry['duration_ms']}ms")

    if context_parts:
        parts.append(f"({', '.join(context_parts)})")

    # 错误信息
    if "error" in entry:
        parts.append(f"error={entry['error']}")

    result = " ".join(parts)

    # 详细模式：显示完整JSON
    if verbose:
        result += "\n" + json.dumps(entry, indent=2, ensure_ascii=False)

    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="日志查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 按request_id查询
  python scripts/query_logs.py --request-id abc-123

  # 查询错误日志
  python scripts/query_logs.py --level ERROR --limit 20

  # 查询特定用户的日志
  python scripts/query_logs.py --user-id 456

  # 查询特定时间范围
  python scripts/query_logs.py --since "2024-01-01 10:00:00" --until "2024-01-01 12:00:00"

  # 查询特定加密货币
  python scripts/query_logs.py --symbol BTC

  # 获取请求追踪
  python scripts/query_logs.py --request-id abc-123 --trace

  # 获取错误摘要
  python scripts/query_logs.py --error-summary
        """
    )

    parser.add_argument(
        "--log-file",
        help="日志文件路径（默认：logs/web3search_*.log）"
    )

    parser.add_argument(
        "--request-id",
        help="请求ID"
    )

    parser.add_argument(
        "--user-id",
        type=int,
        help="用户ID"
    )

    parser.add_argument(
        "--symbol",
        help="加密货币符号"
    )

    parser.add_argument(
        "--conversation-id",
        help="会话ID"
    )

    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别"
    )

    parser.add_argument(
        "--event",
        help="事件名称"
    )

    parser.add_argument(
        "--since",
        help="开始时间（格式：YYYY-MM-DD HH:MM:SS）"
    )

    parser.add_argument(
        "--until",
        help="结束时间（格式：YYYY-MM-DD HH:MM:SS）"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="返回结果数量限制"
    )

    parser.add_argument(
        "--pattern",
        help="消息内容匹配模式（正则表达式）"
    )

    parser.add_argument(
        "--trace",
        action="store_true",
        help="显示完整的请求追踪（需要配合--request-id）"
    )

    parser.add_argument(
        "--error-summary",
        action="store_true",
        help="显示错误摘要"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细信息（完整JSON）"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="输出文件路径（如果不指定则输出到stdout）"
    )

    args = parser.parse_args()

    # 确定日志文件
    if args.log_file:
        log_file = Path(args.log_file)
    else:
        # 使用最新的日志文件
        log_files = list(LOG_DIR.glob("web3search_*.log"))
        if not log_files:
            print("❌ 未找到日志文件", file=sys.stderr)
            sys.exit(1)
        log_file = max(log_files, key=lambda f: f.stat().st_mtime)

    print(f"📂 读取日志文件: {log_file}")

    # 创建查询器
    querier = LogQuery(log_file)

    # 解析时间
    since = None
    if args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"❌ 无效的时间格式: {args.since}", file=sys.stderr)
            sys.exit(1)

    until = None
    if args.until:
        try:
            until = datetime.strptime(args.until, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"❌ 无效的时间格式: {args.until}", file=sys.stderr)
            sys.exit(1)

    # 执行查询
    if args.error_summary:
        # 错误摘要
        summary = querier.get_error_summary(since=since, until=until)
        print("\n📊 错误摘要:")
        print(f"  总错误数: {summary['total_errors']}")
        print("\n  错误类型分布:")
        for error_type, count in summary['error_types'].items():
            print(f"    - {error_type}: {count}")
        print("\n  最近的错误:")
        for error in summary['recent_errors']:
            print(f"    {format_log_entry(error)}")

    elif args.trace and args.request_id:
        # 请求追踪
        logs = querier.get_request_trace(args.request_id)
        print(f"\n🔍 请求追踪 (request_id={args.request_id}):")
        print(f"  共 {len(logs)} 条日志\n")
        for log in logs:
            print(format_log_entry(log, verbose=args.verbose))

    else:
        # 普通查询
        results = querier.query(
            request_id=args.request_id,
            user_id=args.user_id,
            symbol=args.symbol,
            conversation_id=args.conversation_id,
            level=args.level,
            event=args.event,
            since=since,
            until=until,
            limit=args.limit,
            pattern=args.pattern,
        )

        print(f"\n✅ 找到 {len(results)} 条日志\n")

        # 输出结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 结果已保存到: {args.output}")
        else:
            for result in results:
                print(format_log_entry(result, verbose=args.verbose))


if __name__ == "__main__":
    main()
