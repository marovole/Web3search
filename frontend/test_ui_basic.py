#!/usr/bin/env python3
"""
前端UI自动化测试 - 基础功能测试（测试1-3）
测试项：
1. 页面加载
2. 模式切换
3. 输入框功能
"""

from playwright.sync_api import sync_playwright
import time
import sys

def test_basic_functionality():
    """测试基础功能"""
    results = {
        'test_1_page_load': False,
        'test_2_mode_switch': False,
        'test_3_input_box': False,
    }

    with sync_playwright() as p:
        # 启动浏览器（headless模式）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 收集控制台日志
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

        try:
            print("=" * 60)
            print("测试1: 页面加载")
            print("=" * 60)

            # 访问页面
            page.goto('http://localhost:3000', wait_until='networkidle')
            time.sleep(2)

            # 截图
            page.screenshot(path='/tmp/test1_page_load.png', full_page=True)
            print("✓ 截图已保存: /tmp/test1_page_load.png")

            # 检查页面标题
            title = page.title()
            print(f"✓ 页面标题: {title}")

            # 检查控制台日志中是否有Mock模式提示
            mock_mode_enabled = any('Mock API Mode Enabled' in log for log in console_logs)
            if mock_mode_enabled:
                print("✓ 控制台显示Mock模式已启用")
            else:
                print("⚠ 未检测到Mock模式日志")
                print(f"控制台日志: {console_logs[:5]}")

            # 检查关键元素是否存在
            mode_switch = page.locator('text=Quick Chat').count() > 0
            input_box = page.locator('textarea').count() > 0

            if mode_switch and input_box:
                print("✓ 模式切换器和输入框已渲染")
                results['test_1_page_load'] = True
            else:
                print("✗ 缺少关键UI元素")

            print()

            # ============================================================
            print("=" * 60)
            print("测试2: 模式切换")
            print("=" * 60)

            # 检查初始模式
            quick_button = page.locator('button:has-text("Quick Chat")')
            deep_button = page.locator('button:has-text("Deep Research")')

            print(f"✓ Quick Chat按钮数量: {quick_button.count()}")
            print(f"✓ Deep Research按钮数量: {deep_button.count()}")

            # 获取localStorage中的模式
            storage_mode = page.evaluate('() => localStorage.getItem("chatMode")')
            print(f"✓ localStorage中的模式: {storage_mode}")

            # 点击Deep Research
            if deep_button.count() > 0:
                deep_button.first.click()
                time.sleep(1)
                page.screenshot(path='/tmp/test2_deep_mode.png', full_page=True)
                print("✓ 已切换到Deep Research模式")

                # 验证localStorage更新
                new_mode = page.evaluate('() => localStorage.getItem("chatMode")')
                if new_mode == 'deep':
                    print("✓ localStorage已更新为deep")

                    # 刷新页面验证持久化
                    page.reload(wait_until='networkidle')
                    time.sleep(1)
                    final_mode = page.evaluate('() => localStorage.getItem("chatMode")')

                    if final_mode == 'deep':
                        print("✓ 刷新后模式保持（持久化成功）")
                        results['test_2_mode_switch'] = True
                    else:
                        print("✗ 刷新后模式丢失")
                else:
                    print("✗ localStorage未正确更新")
            else:
                print("✗ 未找到Deep Research按钮")

            print()

            # ============================================================
            print("=" * 60)
            print("测试3: 输入框功能")
            print("=" * 60)

            # 切换回Quick Chat模式
            quick_button.first.click()
            time.sleep(1)

            # 定位输入框
            textarea = page.locator('textarea')

            if textarea.count() > 0:
                # 输入文本
                test_text = "分析BTC"
                textarea.first.fill(test_text)
                time.sleep(0.5)

                # 检查字符计数
                char_count_element = page.locator('text=/\\d+ \\/ 1000/')
                if char_count_element.count() > 0:
                    char_count = char_count_element.first.text_content()
                    print(f"✓ 字符计数显示: {char_count}")
                else:
                    print("⚠ 未找到字符计数元素")

                page.screenshot(path='/tmp/test3_input_text.png', full_page=True)
                print(f"✓ 已输入文本: {test_text}")

                # 测试长文本（超过1000字符）
                long_text = "A" * 1001
                textarea.first.fill(long_text)
                time.sleep(0.5)

                # 检查发送按钮是否禁用
                send_button = page.locator('button:has-text("发送")')
                if send_button.count() > 0:
                    is_disabled = send_button.first.is_disabled()
                    if is_disabled:
                        print("✓ 超过1000字符时发送按钮禁用")
                    else:
                        print("⚠ 超过1000字符时发送按钮未禁用")

                # 测试Enter发送（恢复短文本）
                textarea.first.fill("测试Enter")
                textarea.first.press('Enter')
                time.sleep(0.5)

                # 检查输入框是否清空
                current_value = textarea.first.input_value()
                if current_value == "":
                    print("✓ 按Enter后输入框已清空（消息已发送）")
                    results['test_3_input_box'] = True
                else:
                    print("⚠ 按Enter后输入框未清空")

                page.screenshot(path='/tmp/test3_after_send.png', full_page=True)
            else:
                print("✗ 未找到输入框")

            print()

        except Exception as e:
            print(f"\n✗ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 关闭浏览器
            browser.close()

    # 打印测试结果
    print("=" * 60)
    print("基础功能测试结果总结")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")

    passed_count = sum(results.values())
    total_count = len(results)
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

    return all(results.values())

if __name__ == '__main__':
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
