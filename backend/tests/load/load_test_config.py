"""
高级负载测试配置
支持不同规模和类型的性能测试场景
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class LoadTestConfig:
    """负载测试配置类"""
    name: str
    users: int
    spawn_rate: int
    run_time: str
    host: str
    description: str
    performance_targets: Dict[str, float]
    
class LoadTestScenarios:
    """预定义的负载测试场景"""
    
    # 基础配置
    BASE_HOSTS = {
        "local": "http://localhost:8000",
        "staging": "https://web3search-staging.onrender.com", 
        "production": "https://web3search-api.onrender.com"
    }
    
    # 性能目标 (毫秒)
    PERFORMANCE_TARGETS = {
        "quick_chat_p95": 3000,
        "quick_chat_p99": 5000,
        "hotspots_p95": 1000,
        "autocomplete_p95": 500,
        "market_data_p95": 800,
        "deep_research_p95": 60000,
        "error_rate_max": 0.001,  # 0.1%
        "rps_min": 1000  # 最小吞吐量
    }
    
    @classmethod
    def get_scenarios(cls) -> List[LoadTestConfig]:
        """获取所有测试场景"""
        return [
            # 开发测试场景
            LoadTestConfig(
                name="dev_smoke",
                users=50,
                spawn_rate=5,
                run_time="60s",
                host=cls.BASE_HOSTS["local"],
                description="开发环境冒烟测试",
                performance_targets={
                    "quick_chat_p95": 5000,
                    "error_rate_max": 0.01
                }
            ),
            
            # 功能测试场景
            LoadTestConfig(
                name="functional",
                users=200,
                spawn_rate=20,
                run_time="120s", 
                host=cls.BASE_HOSTS["local"],
                description="功能完整性测试",
                performance_targets={
                    "quick_chat_p95": 4000,
                    "error_rate_max": 0.005
                }
            ),
            
            # 负载测试场景
            LoadTestConfig(
                name="load_test",
                users=1000,
                spawn_rate=50,
                run_time="300s",
                host=cls.BASE_HOSTS["local"],
                description="1000并发负载测试",
                performance_targets=cls.PERFORMANCE_TARGETS
            ),
            
            # 高负载测试场景
            LoadTestConfig(
                name="high_load",
                users=1500,
                spawn_rate=100,
                run_time="600s",
                host=cls.BASE_HOSTS["staging"],
                description="1500并发高负载测试",
                performance_targets={
                    **cls.PERFORMANCE_TARGETS,
                    "quick_chat_p95": 3500,
                    "rps_min": 1500
                }
            ),
            
            # 峰值测试场景
            LoadTestConfig(
                name="peak_test",
                users=2000,
                spawn_rate=200,
                run_time="180s",
                host=cls.BASE_HOSTS["staging"],
                description="2000并发峰值测试",
                performance_targets={
                    **cls.PERFORMANCE_TARGETS,
                    "quick_chat_p95": 4000,
                    "error_rate_max": 0.002
                }
            ),
            
            # 压力测试场景
            LoadTestConfig(
                name="stress_test",
                users=3000,
                spawn_rate=300,
                run_time="900s",
                host=cls.BASE_HOSTS["staging"],
                description="3000并发压力测试",
                performance_targets={
                    **cls.PERFORMANCE_TARGETS,
                    "quick_chat_p95": 5000,
                    "error_rate_max": 0.005,
                    "rps_min": 2000
                }
            ),
            
            # 生产环境验证
            LoadTestConfig(
                name="prod_validation",
                users=100,
                spawn_rate=10,
                run_time="120s",
                host=cls.BASE_HOSTS["production"],
                description="生产环境性能验证",
                performance_targets=cls.PERFORMANCE_TARGETS
            )
        ]
    
    @classmethod
    def get_scenario(cls, name: str) -> Optional[LoadTestConfig]:
        """根据名称获取测试场景"""
        for scenario in cls.get_scenarios():
            if scenario.name == name:
                return scenario
        return None
    
    @classmethod
    def generate_locust_commands(cls) -> Dict[str, str]:
        """生成Locust命令"""
        commands = {}
        scenarios = cls.get_scenarios()
        
        for scenario in scenarios:
            cmd = (
                f"locust -f locustfile.py "
                f"--host={scenario.host} "
                f"--headless "
                f"--users {scenario.users} "
                f"--spawn-rate {scenario.spawn_rate} "
                f"--run-time {scenario.run_time} "
                f"--html reports/{scenario.name}_report.html "
                f"--csv reports/{scenario.name}_stats"
            )
            commands[scenario.name] = cmd
            
        return commands

def print_test_scenarios():
    """打印所有测试场景"""
    scenarios = LoadTestScenarios.get_scenarios()
    
    print("🚀 Web3 Search Load Test Scenarios")
    print("=" * 60)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario.name.upper()}")
        print(f"   Description: {scenario.description}")
        print(f"   Users: {scenario.users}, Spawn: {scenario.spawn_rate}/s")
        print(f"   Duration: {scenario.run_time}")
        print(f"   Target: {scenario.host}")
        
        # 关键性能指标
        targets = scenario.performance_targets
        print(f"   Targets: P95<{targets.get('quick_chat_p95', 'N/A')}ms, "
              f"Error<{targets.get('error_rate_max', 'N/A')*100:.1f}%")

def generate_bash_script():
    """生成批量测试脚本"""
    commands = LoadTestScenarios.generate_locust_commands()
    
    script_content = """#!/bin/bash
# Web3 Search Load Testing Script
# 自动化负载测试执行脚本

set -e

# 创建报告目录
mkdir -p reports

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Web3 Search Load Tests${NC}"
echo "=================================================="

"""
    
    for name, cmd in commands.items():
        script_content += f"""
echo -e "${YELLOW}Running {name} test...${NC}"
echo "Command: {cmd}"
echo "Start time: $(date)"

# 执行测试
{cmd}

echo "End time: $(date)"
echo "✅ {name} completed"
echo "--------------------------------------------------"
"""
    
    script_content += """
echo -e "${GREEN}🎉 All load tests completed!${NC}"
echo "Reports are available in the 'reports/' directory"
"""
    
    return script_content

if __name__ == "__main__":
    print_test_scenarios()
    
    print("\n" + "=" * 60)
    print("📝 Generating bash script...")
    
    script = generate_bash_script()
    with open("run_load_tests.sh", "w") as f:
        f.write(script)
    
    print("✅ Script saved as 'run_load_tests.sh'")
    print("   Run: chmod +x run_load_tests.sh && ./run_load_tests.sh")
