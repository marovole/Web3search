#!/usr/bin/env python3
"""
前端UI自动化测试 - Quick Chat模式测试（测试4-7）
测试项：
4. Quick Chat发送消息
5. Quick Chat消息渲染
6. 多轮对话
7. 加载状态
"""

from playwright.sync_api import sync_playwright
import time
import sys

def test_quickchat_mode():
    """测试Quick Chat模式"""
    results = {
        'test_4_send_message': False,
        'test_5_message_render': False,
        'test_6_multi_turn': False,
        'test_7_loading_state': False,
    }

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # 收集控制台日志
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

        try:
            # 访问页面
            page.goto('http://localhost:3000', wait_until='networkidle')
            time.sleep(1)

            # 确保在Quick Chat模式
            quick_button = page.locator('button:has-text("Quick Chat")')
            if quick_button.count() > 0:
                quick_button.first.click()
                time.sleep(0.5)

            print("=" * 60)
            print("测试4: Quick Chat发送消息")
            print("=" * 60)

            # 输入并发送消息
            textarea = page.locator('textarea')
            if textarea.count() > 0:
                test_query = "分析BTC"
                textarea.first.fill(test_query)
                textarea.first.press('Enter')
                time.sleep(0.5)

                # 检查用户消息是否显示
                user_messages = page.locator('.message-user')
                if user_messages.count() > 0:
                    print(f"✓ 用户消息已显示（数量: {user_messages.count()}）")

                    # 检查消息内容
                    last_user_msg = user_messages.last.text_content()
                    if test_query in last_user_msg:
                        print(f"✓ 用户消息内容正确: {last_user_msg}")
                    else:
                        print(f"⚠ 用户消息内容不匹配: {last_user_msg}")

                    # 截图
                    page.screenshot(path='/tmp/test4_user_message.png', full_page=True)
                else:
                    print("✗ 未找到用户消息")

                # 等待AI回复（Mock API延迟1秒）
                print("等待AI回复（Mock API延迟1秒）...")
                time.sleep(2)

                # 检查AI消息
                ai_messages = page.locator('.message-assistant')
                if ai_messages.count() > 0:
                    print(f"✓ AI回复已显示（数量: {ai_messages.count()}）")
                    ai_content = ai_messages.last.text_content()

                    # 检查关键字
                    if '价格' in ai_content or 'BTC' in ai_content or 'Bitcoin' in ai_content:
                        print("✓ AI回复内容相关（包含BTC/价格关键字）")
                        results['test_4_send_message'] = True
                    else:
                        print(f"⚠ AI回复内容可能不相关: {ai_content[:100]}...")

                    page.screenshot(path='/tmp/test4_ai_response.png', full_page=True)
                else:
                    print("✗ 未收到AI回复")

            else:
                print("✗ 未找到输入框")

            print()

            # ============================================================
            print("=" * 60)
            print("测试5: Quick Chat消息渲染")
            print("=" * 60)

            # 检查最后一条AI消息的渲染
            ai_messages = page.locator('.message-assistant')
            if ai_messages.count() > 0:
                last_ai_msg = ai_messages.last

                # 检查粗体文字
                bold_elements = last_ai_msg.locator('strong')
                if bold_elements.count() > 0:
                    print(f"✓ 包含粗体文字（数量: {bold_elements.count()}）")
                else:
                    print("⚠ 未找到粗体文字")

                # 检查列表项
                list_items = last_ai_msg.locator('ul li, ol li')
                if list_items.count() > 0:
                    print(f"✓ 包含列表项（数量: {list_items.count()}）")
                else:
                    print("⚠ 未找到列表项")

                # 检查段落
                paragraphs = last_ai_msg.locator('p')
                if paragraphs.count() > 0:
                    print(f"✓ 包含段落（数量: {paragraphs.count()}）")
                else:
                    print("⚠ 未找到段落")

                # 如果有以上任意一个，认为渲染成功
                if bold_elements.count() > 0 or list_items.count() > 0:
                    results['test_5_message_render'] = True
                    print("✓ Markdown渲染正常")
                else:
                    print("⚠ Markdown渲染可能有问题")

            print()

            # ============================================================
            print("=" * 60)
            print("测试6: 多轮对话")
            print("=" * 60)

            # 记录当前消息数量
            messages_before = page.locator('.message-user, .message-assistant').count()
            print(f"当前消息数量: {messages_before}")

            # 发送第二条消息
            textarea = page.locator('textarea')
            if textarea.count() > 0:
                second_query = "ETH如何？"
                textarea.first.fill(second_query)
                textarea.first.press('Enter')
                time.sleep(0.5)

                # 等待AI回复
                time.sleep(2)

                # 检查消息数量是否增加
                messages_after = page.locator('.message-user, .message-assistant').count()
                print(f"发送后消息数量: {messages_after}")

                if messages_after > messages_before:
                    print(f"✓ 消息数量增加（+{messages_after - messages_before}）")

                    # 检查消息顺序（旧消息在上）
                    all_messages = page.locator('.message-user, .message-assistant')
                    first_msg = all_messages.first.text_content()
                    last_msg = all_messages.last.text_content()

                    print(f"第一条消息: {first_msg[:50]}...")
                    print(f"最后一条消息: {last_msg[:50]}...")

                    # 检查滚动位置（应该自动滚动到底部）
                    is_at_bottom = page.evaluate('''() => {
                        const chatArea = document.querySelector('.overflow-y-auto');
                        if (chatArea) {
                            const scrollTop = chatArea.scrollTop;
                            const scrollHeight = chatArea.scrollHeight;
                            const clientHeight = chatArea.clientHeight;
                            return scrollTop + clientHeight >= scrollHeight - 50;
                        }
                        return false;
                    }''')

                    if is_at_bottom:
                        print("✓ 自动滚动到最新消息")
                    else:
                        print("⚠ 未自动滚动到底部")

                    results['test_6_multi_turn'] = True
                    page.screenshot(path='/tmp/test6_multi_turn.png', full_page=True)
                else:
                    print("✗ 消息数量未增加")

            print()

            # ============================================================
            print("=" * 60)
            print("测试7: 加载状态")
            print("=" * 60)

            # 发送新消息并立即检查加载状态
            textarea = page.locator('textarea')
            if textarea.count() > 0:
                textarea.first.fill("测试加载状态")

                # 检查发送前按钮状态
                send_button = page.locator('button:has-text("发送"), button[type="submit"]')
                if send_button.count() > 0:
                    is_disabled_before = send_button.first.is_disabled()
                    print(f"发送前按钮状态: {'禁用' if is_disabled_before else '启用'}")

                # 发送消息
                textarea.first.press('Enter')

                # 立即检查（消息发送后）
                time.sleep(0.1)

                # 检查输入框是否禁用
                is_input_disabled = textarea.first.is_disabled()
                print(f"发送后输入框状态: {'禁用' if is_input_disabled else '启用'}")

                # 检查发送按钮是否禁用
                if send_button.count() > 0:
                    is_button_disabled = send_button.first.is_disabled()
                    print(f"发送后按钮状态: {'禁用' if is_button_disabled else '启用'}")

                # 检查是否有加载动画
                loading_animations = page.locator('.animate-pulse')
                if loading_animations.count() > 0:
                    print(f"✓ 显示加载动画（数量: {loading_animations.count()}）")
                else:
                    print("⚠ 未找到加载动画")

                page.screenshot(path='/tmp/test7_loading.png', full_page=True)

                # 等待加载完成
                time.sleep(2)

                # 检查恢复状态
                is_input_enabled = not textarea.first.is_disabled()
                is_button_enabled = not send_button.first.is_disabled() if send_button.count() > 0 else True

                if is_input_enabled and is_button_enabled:
                    print("✓ 加载完成后状态恢复正常")
                    results['test_7_loading_state'] = True
                else:
                    print("⚠ 加载完成后状态未恢复")

                page.screenshot(path='/tmp/test7_after_loading.png', full_page=True)

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
    print("Quick Chat模式测试结果总结")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")

    passed_count = sum(results.values())
    total_count = len(results)
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

    # 检查控制台日志
    print(f"\n控制台日志数量: {len(console_logs)}")
    if console_logs:
        print("前5条日志:")
        for log in console_logs[:5]:
            print(f"  - {log}")

    return all(results.values())

if __name__ == '__main__':
    success = test_quickchat_mode()
    sys.exit(0 if success else 1)
