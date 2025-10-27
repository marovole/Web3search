"""
重试机制和断路器测试套件（任务5.8）

测试场景：
1. 临时错误重试成功
2. 3次重试全部失败
3. 永久错误立即失败
4. 单次超时触发重试
5. 总超时终止
6. 延迟时间验证
7. 断路器状态转换
8. Sentry metrics记录
"""
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.core.retry import (
    is_retriable_error,
    retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerState,
    record_retry_metrics,
)
from app.core.exceptions import (
    APIRateLimitError,
    DataSourceUnavailable,
    ValidationError,
    ResourceNotFound,
    CircuitBreakerOpenError,
    RetryExhaustedError,
)


# ================================
# 测试1: 错误分类（is_retriable_error）
# ================================


def test_is_retriable_error_temporary():
    """测试临时错误识别（429, 503, timeout, connection）"""
    # 临时错误应该返回True
    assert is_retriable_error(APIRateLimitError("Rate limited", "test")) is True
    assert is_retriable_error(DataSourceUnavailable("Service down", "test")) is True
    assert is_retriable_error(ConnectionError("Connection lost")) is True
    assert is_retriable_error(TimeoutError("Request timeout")) is True
    assert is_retriable_error(asyncio.TimeoutError()) is True


def test_is_retriable_error_permanent():
    """测试永久错误识别（400, 401, 403, 404）"""
    # 永久错误应该返回False
    assert is_retriable_error(ValidationError("Invalid input", field="email")) is False
    assert is_retriable_error(ResourceNotFound("Not found", "User", 123)) is False


def test_is_retriable_error_status_code():
    """测试基于HTTP状态码的错误分类"""

    class HTTPError(Exception):
        def __init__(self, status_code):
            self.status_code = status_code

    # 临时错误状态码
    assert is_retriable_error(HTTPError(429)) is True
    assert is_retriable_error(HTTPError(502)) is True
    assert is_retriable_error(HTTPError(503)) is True
    assert is_retriable_error(HTTPError(504)) is True

    # 永久错误状态码
    assert is_retriable_error(HTTPError(400)) is False
    assert is_retriable_error(HTTPError(401)) is False
    assert is_retriable_error(HTTPError(403)) is False
    assert is_retriable_error(HTTPError(404)) is False


# ================================
# 测试2: 重试成功场景
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_success_after_retries():
    """测试临时错误重试后成功"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01, 0.01])
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise APIRateLimitError("Rate limited", "test")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert call_count == 3


# ================================
# 测试3: 重试全部失败
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_all_attempts_fail():
    """测试3次重试全部失败，抛出最后的异常"""

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01, 0.01])
    async def always_fails():
        raise APIRateLimitError("Persistent failure", "test")

    with pytest.raises(APIRateLimitError) as exc_info:
        await always_fails()

    assert "Persistent failure" in str(exc_info.value)


# ================================
# 测试4: 永久错误立即失败
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_permanent_error_no_retry():
    """测试永久错误不重试，立即抛出"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01, 0.01])
    async def validation_failure():
        nonlocal call_count
        call_count += 1
        raise ValidationError("Invalid data", field="email")

    with pytest.raises(ValidationError):
        await validation_failure()

    # 永久错误不应该重试
    assert call_count == 1


# ================================
# 测试5: 单次超时触发重试
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_single_timeout():
    """测试单次请求超时后重试"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01, 0.01], single_timeout=0.05)
    async def slow_function():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            await asyncio.sleep(0.1)  # 第一次调用超时
        return "success"

    result = await slow_function()
    assert result == "success"
    assert call_count == 2  # 超时1次 + 成功1次


# ================================
# 测试6: 总超时终止
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_total_timeout():
    """测试总超时时间耗尽后终止"""

    @retry_with_backoff(max_attempts=10, delays=[0.1] * 10, total_timeout=0.2)
    async def always_fails():
        raise APIRateLimitError("Failure", "test")

    start_time = time.time()
    with pytest.raises(TimeoutError) as exc_info:
        await always_fails()

    elapsed_time = time.time() - start_time
    # 应该在总超时时间附近终止（允许误差）
    assert 0.15 < elapsed_time < 0.4
    assert "Total timeout" in str(exc_info.value)


# ================================
# 测试7: 延迟时间验证
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_delay_sequence():
    """测试重试延迟序列正确（1s, 2s, 4s）"""
    delays_recorded = []

    @retry_with_backoff(max_attempts=4, delays=[0.05, 0.1, 0.15])
    async def track_delays():
        delays_recorded.append(time.time())
        raise APIRateLimitError("Failure", "test")

    start_time = time.time()
    with pytest.raises(APIRateLimitError):
        await track_delays()

    # 验证实际延迟接近预期（允许误差）
    if len(delays_recorded) >= 3:
        delay1 = delays_recorded[1] - delays_recorded[0]
        delay2 = delays_recorded[2] - delays_recorded[1]
        assert 0.03 < delay1 < 0.08  # 第一次延迟 ~0.05s
        assert 0.08 < delay2 < 0.15  # 第二次延迟 ~0.1s


# ================================
# 测试8: 断路器状态转换
# ================================


@pytest.mark.asyncio
async def test_circuit_breaker_closed_to_open():
    """测试CLOSED → OPEN状态转换（连续5次失败）"""
    cb = CircuitBreaker("test_service", failure_threshold=5, timeout=1)

    @cb.protect
    async def failing_service():
        raise APIRateLimitError("Failure", "test")

    # 前4次失败，断路器保持CLOSED
    for i in range(4):
        with pytest.raises(APIRateLimitError):
            await failing_service()
        assert cb.state == CircuitBreakerState.CLOSED

    # 第5次失败，断路器转为OPEN
    with pytest.raises(APIRateLimitError):
        await failing_service()
    assert cb.state == CircuitBreakerState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_open_rejects_calls():
    """测试OPEN状态拒绝调用"""
    cb = CircuitBreaker("test_service_reject", failure_threshold=2, timeout=10)

    @cb.protect
    async def failing_service():
        raise APIRateLimitError("Failure", "test")

    # 触发断路器熔断
    for _ in range(2):
        with pytest.raises(APIRateLimitError):
            await failing_service()

    # 断路器OPEN后，应该抛出CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await failing_service()
    assert "test_service_reject" in str(exc_info.value)


@pytest.mark.asyncio
async def test_circuit_breaker_open_to_half_open():
    """测试OPEN → HALF_OPEN状态转换（超时后）"""
    cb = CircuitBreaker("test_service_half_open", failure_threshold=2, timeout=0.1)

    @cb.protect
    async def service_call():
        return "success"

    # 触发断路器熔断
    cb._failure_count = 2
    cb._transition_to_open()
    assert cb.state == CircuitBreakerState.OPEN

    # 等待超时
    await asyncio.sleep(0.15)

    # 检查状态，应该自动转换到HALF_OPEN
    assert cb.state == CircuitBreakerState.HALF_OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_to_closed():
    """测试HALF_OPEN → CLOSED状态转换（测试成功）"""
    cb = CircuitBreaker("test_service_recover", failure_threshold=2, timeout=0.1)

    @cb.protect
    async def service_call():
        return "success"

    # 手动设置到HALF_OPEN状态
    cb._state = CircuitBreakerState.HALF_OPEN
    cb._half_open_calls = 0

    # 成功调用，应该恢复到CLOSED
    result = await service_call()
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_to_open():
    """测试HALF_OPEN → OPEN状态转换（测试失败）"""
    cb = CircuitBreaker("test_service_fail_again", failure_threshold=2, timeout=0.1)

    @cb.protect
    async def failing_service():
        raise APIRateLimitError("Still failing", "test")

    # 手动设置到HALF_OPEN状态
    cb._state = CircuitBreakerState.HALF_OPEN
    cb._half_open_calls = 0

    # 失败调用，应该重新熔断
    with pytest.raises(APIRateLimitError):
        await failing_service()
    assert cb.state == CircuitBreakerState.OPEN


# ================================
# 测试9: Sentry metrics记录
# ================================


@patch("app.core.retry.sentry_sdk")
def test_record_retry_metrics_success_after_retries(mock_sentry):
    """测试记录重试成功的metrics"""
    record_retry_metrics(
        operation="fetch_data",
        attempt=3,
        success=True,
        error_type=None,
        is_retriable=None,
    )

    # 验证Sentry调用
    mock_sentry.set_measurement.assert_called_once_with("retry.attempt.count", 3)
    mock_sentry.capture_message.assert_called_once()
    args = mock_sentry.capture_message.call_args
    assert "succeeded after 3 attempts" in args[0][0]
    assert args[1]["level"] == "info"


@patch("app.core.retry.sentry_sdk")
def test_record_retry_metrics_max_retries_exceeded(mock_sentry):
    """测试记录重试次数耗尽的metrics"""
    record_retry_metrics(
        operation="fetch_data",
        attempt=3,
        success=False,
        error_type="APIRateLimitError",
        is_retriable=True,
    )

    mock_sentry.set_measurement.assert_called_once_with("retry.attempt.count", 3)
    mock_sentry.capture_message.assert_called_once()
    args = mock_sentry.capture_message.call_args
    assert "Max retries exceeded" in args[0][0]
    assert args[1]["level"] == "warning"
    assert args[1]["tags"]["error_type"] == "APIRateLimitError"


@patch("app.core.retry.sentry_sdk")
def test_record_retry_metrics_permanent_error(mock_sentry):
    """测试记录永久错误的metrics"""
    record_retry_metrics(
        operation="fetch_data",
        attempt=1,
        success=False,
        error_type="ValidationError",
        is_retriable=False,
    )

    mock_sentry.capture_message.assert_called_once()
    args = mock_sentry.capture_message.call_args
    assert "Permanent error, no retry" in args[0][0]
    assert args[1]["tags"]["is_retriable"] == "false"


# ================================
# 测试10: 同步函数支持
# ================================


def test_retry_with_backoff_sync_function():
    """测试同步函数重试"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01, 0.01])
    def sync_flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise APIRateLimitError("Rate limited", "test")
        return "success"

    result = sync_flaky_function()
    assert result == "success"
    assert call_count == 3


def test_circuit_breaker_sync_function():
    """测试断路器保护同步函数"""
    cb = CircuitBreaker("test_sync_cb", failure_threshold=2, timeout=1)

    @cb.protect
    def sync_service():
        raise APIRateLimitError("Failure", "test")

    # 触发断路器
    for _ in range(2):
        with pytest.raises(APIRateLimitError):
            sync_service()

    # 断路器应该拒绝调用
    with pytest.raises(CircuitBreakerOpenError):
        sync_service()


# ================================
# 测试11: 自定义错误分类器
# ================================


@pytest.mark.asyncio
async def test_retry_with_backoff_custom_checker():
    """测试自定义错误分类函数"""

    def custom_checker(e):
        # 自定义规则：只有ValueError可重试
        return isinstance(e, ValueError)

    call_count = 0

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01], retriable_checker=custom_checker)
    async def custom_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Retriable error")
        return "success"

    result = await custom_function()
    assert result == "success"
    assert call_count == 2


# ================================
# 测试12: 断路器单例模式
# ================================


def test_circuit_breaker_singleton():
    """测试断路器单例模式"""
    cb1 = CircuitBreaker.get_instance("shared_service", failure_threshold=5)
    cb2 = CircuitBreaker.get_instance("shared_service")

    # 应该返回同一个实例
    assert cb1 is cb2
    assert cb1.failure_threshold == 5

    # 不同名称应该返回不同实例
    cb3 = CircuitBreaker.get_instance("different_service")
    assert cb1 is not cb3


# ================================
# 测试13: 日志记录验证
# ================================


@pytest.mark.asyncio
async def test_retry_logging(caplog):
    """测试重试日志记录包含所有必要信息"""
    import logging

    caplog.set_level(logging.WARNING)

    @retry_with_backoff(max_attempts=3, delays=[0.01, 0.01])
    async def failing_function():
        raise APIRateLimitError("Test error", "test")

    with pytest.raises(APIRateLimitError):
        await failing_function()

    # 验证日志包含关键字段
    log_records = [record for record in caplog.records if "retrying" in record.message]
    assert len(log_records) >= 2  # 至少2次重试日志

    # 检查日志extra字段
    for record in log_records:
        assert hasattr(record, "function")
        assert hasattr(record, "attempt")
        assert hasattr(record, "delay")
        assert hasattr(record, "next_retry_time")
        assert hasattr(record, "error_type")
        assert hasattr(record, "is_retriable")
