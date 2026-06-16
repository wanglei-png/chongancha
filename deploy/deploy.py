#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================
宠急查 - 生产环境打包部署脚本
============================================

功能：
  1. 在本地打包 backend/ 和 deploy/ 目录
  2. 通过 SSH 上传到远程服务器
  3. 停止服务 → 备份旧代码 → 解压新代码 → 重启服务
  4. 自动健康检查验证

使用方法：
  # 标准部署（使用配置文件中的服务器信息）
  python deploy.py

  # 指定配置文件
  python deploy.py --config my_config.ini

  # 仅打包不上传
  python deploy.py --pack-only

  # 跳过打包，使用已有 tarball
  python deploy.py --tarball /tmp/pet-health-deploy.tar.gz

  # 强制部署（不确认）
  python deploy.py --yes

前置条件：
  - 本机：Python 3.8+、sshpass 已安装（brew install hudochenkov/sshpass/sshpass）
  - 服务器：MySQL、Redis、Nginx、Python 3.9+ 已安装并配置好
"""

import argparse
import configparser
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime
from pathlib import Path

# ============================================
# 颜色与日志工具
# ============================================


class Color:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def log_info(msg):
    print(f"{Color.BLUE}[INFO]{Color.NC} {msg}")


def log_success(msg):
    print(f"{Color.GREEN}[  OK]{Color.NC} {msg}")


def log_warn(msg):
    print(f"{Color.YELLOW}[WARN]{Color.NC} {msg}")


def log_error(msg):
    print(f"{Color.RED}[FAIL]{Color.NC} {msg}")


def log_step(step_num, total, msg):
    print(f"\n{Color.CYAN}{Color.BOLD}{'='*50}{Color.NC}")
    print(f"{Color.CYAN}{Color.BOLD}  步骤 {step_num}/{total}：{msg}{Color.NC}")
    print(f"{Color.CYAN}{Color.BOLD}{'='*50}{Color.NC}")


def confirm(msg):
    """交互确认，--yes 模式下自动确认"""
    if GLOBAL_OPTS.get("yes", False):
        return True
    resp = input(f"{Color.YELLOW}[确认]{Color.NC} {msg} (y/N): ").strip().lower()
    return resp in ("y", "yes")


GLOBAL_OPTS = {}

# ============================================
# 项目路径（相对于脚本所在目录）
# ============================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # pet-health-assistant 根目录

# 打包时需要包含的目录
PACK_DIRS = ["backend", "deploy"]

# 排除的文件/目录模式
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".DS_Store",
    "._*",
    ".idea",
    ".vscode",
    "venv",
    ".venv",
    "models_cache",
    "milvus_pet_health.db",
    ".milvus_pet_health.db.lock",
    "*.log",
    "*.egg-info",
    "=2.6.0",  # pip 下载残留目录
]

# ============================================
# 默认服务器配置
# ============================================

DEFAULT_CONFIG = {
    "server": {
        "host": "116.62.175.15",
        "port": "22",
        "user": "root",
        "password": "9sK#7pR$2tG&5xQ@8zL",
    },
    "deploy": {
        "remote_path": "/opt/pet-health-assistant",
        "service_name": "pet-health",
        "backend_port": "8001",
        "health_endpoint": "/health",
        "venv_path": "/opt/pet-health-assistant/backend/venv",
    },
}

# systemd 服务文件内容
SERVICE_FILE_CONTENT = """\
[Unit]
Description=宠安查后端服务 - Pet Health Assistant API
After=network.target mysqld.service nginx.service
Wants=mysqld.service nginx.service

[Service]
Type=simple
User=root
Group=root

# 工作目录
WorkingDirectory=/opt/pet-health-assistant/backend

# Python 虚拟环境路径
Environment=PATH=/opt/pet-health-assistant/backend/venv/bin:/usr/local/python3.9/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
Environment=PYTHONUNBUFFERED=1

# 启动命令
ExecStart=/opt/pet-health-assistant/backend/venv/bin/uvicorn main:app \\
    --host 127.0.0.1 \\
    --port 8001 \\
    --workers 2 \\
    --log-level info \\
    --access-log \\
    --no-server-header

# 重启策略
Restart=always
RestartSec=5

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
"""


# ============================================
# SSH / SCP 命令执行器
# ============================================

class SSHExecutor:
    """通过 sshpass 执行远程 SSH/SCP 命令"""

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._check_sshpass()

    def _check_sshpass(self):
        """检查 sshpass 是否安装"""
        if not shutil.which("sshpass"):
            log_error("sshpass 未安装！")
            print()
            print("  macOS 安装方法：")
            print("    brew install hudochenkov/sshpass/sshpass")
            print()
            print("  Linux 安装方法：")
            print("    yum install sshpass    # CentOS/RHEL")
            print("    apt install sshpass     # Ubuntu/Debian")
            sys.exit(1)

    def _base_ssh_args(self):
        return [
            "sshpass", "-p", self.password,
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-p", str(self.port),
            f"{self.user}@{self.host}",
        ]

    def _base_scp_args(self, direction="upload"):
        args = [
            "sshpass", "-p", self.password,
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-P", str(self.port),
        ]
        return args

    def run(self, cmd, timeout=120, capture=True):
        """执行远程命令，返回 (returncode, stdout, stderr)"""
        full_cmd = self._base_ssh_args() + [cmd]
        log_info(f"远程执行: {cmd[:120]}{'...' if len(cmd) > 120 else ''}")
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=capture,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            log_error(f"命令执行超时 ({timeout}s): {cmd[:80]}...")
            return -1, "", "timeout"

    def scp_upload(self, local_path, remote_path):
        """上传文件到服务器"""
        full_cmd = self._base_scp_args() + [str(local_path), f"{self.user}@{self.host}:{remote_path}"]
        log_info(f"上传: {Path(local_path).name} -> {remote_path}")
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            log_error(f"上传超时: {local_path}")
            return -1, "", "timeout"

    def test_connection(self):
        """测试 SSH 连接"""
        code, out, err = self.run('echo "SSH_OK"', timeout=15)
        return code == 0 and "SSH_OK" in out


# ============================================
# 核心部署流程
# ============================================

def load_config(config_path=None):
    """加载配置文件，缺失值使用默认值"""
    config = configparser.ConfigParser()

    # 写入默认值
    for section, values in DEFAULT_CONFIG.items():
        config[section] = values

    # 从配置文件覆盖
    if config_path and Path(config_path).exists():
        log_info(f"加载配置文件: {config_path}")
        config.read(config_path, encoding="utf-8")
    else:
        log_info("使用默认配置")

    return config


def pack_project(output_path=None):
    """
    打包 backend/ 和 deploy/ 为 tar.gz

    返回打包文件的路径
    """
    tarball = output_path or f"/tmp/pet-health-deploy-{datetime.now().strftime('%Y%m%d%H%M%S')}.tar.gz"

    log_info(f"打包目录: {[f'{PROJECT_ROOT / d}' for d in PACK_DIRS]}")
    log_info(f"排除模式: {EXCLUDE_PATTERNS}")

    # 收集要打包的文件
    files_to_pack = []
    for dir_name in PACK_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            log_warn(f"目录不存在，跳过: {dir_path}")
            continue
        for root, dirs, files in os.walk(dir_path):
            # 过滤排除的目录
            dirs[:] = [
                d for d in dirs
                if not any(matches_pattern(d, pat) for pat in EXCLUDE_PATTERNS)
            ]
            for f in files:
                if any(matches_pattern(f, pat) for pat in EXCLUDE_PATTERNS):
                    continue
                full_path = Path(root) / f
                # 存档内的路径：相对于项目根目录
                arcname = full_path.relative_to(PROJECT_ROOT)
                files_to_pack.append((full_path, str(arcname)))

    if not files_to_pack:
        log_error("没有找到需要打包的文件！")
        sys.exit(1)

    # 创建 tar.gz
    log_info(f"正在打包 {len(files_to_pack)} 个文件...")
    with tarfile.open(tarball, "w:gz") as tar:
        for full_path, arcname in files_to_pack:
            tar.add(full_path, arcname=arcname)

    size_mb = os.path.getsize(tarball) / (1024 * 1024)
    log_success(f"打包完成: {tarball} ({size_mb:.2f} MB)")

    return tarball


def matches_pattern(name, pattern):
    """简单通配符匹配"""
    from fnmatch import fnmatch
    return fnmatch(name, pattern)


def upload_and_deploy(ssh: SSHExecutor, tarball: str, config: configparser.ConfigParser):
    """
    完整的远程部署流程：
    1. 上传 tarball
    2. 停止服务
    3. 备份旧代码
    4. 解压新代码
    5. 清理 macOS 特殊文件
    6. 更新 systemd 服务文件
    7. 重启服务
    8. 健康检查
    """
    remote_path = config.get("deploy", "remote_path")
    service_name = config.get("deploy", "service_name")
    backend_port = config.get("deploy", "backend_port")
    health_endpoint = config.get("deploy", "health_endpoint")

    total_steps = 8

    # ---- 步骤 1：上传 tarball ----
    log_step(1, total_steps, "上传打包文件到服务器")
    remote_tarball = "/tmp/pet-health-deploy.tar.gz"
    code, _, err = ssh.scp_upload(tarball, remote_tarball)
    if code != 0:
        log_error(f"上传失败: {err}")
        sys.exit(1)
    log_success(f"文件已上传到服务器: {remote_tarball}")

    # ---- 步骤 2：停止服务 ----
    log_step(2, total_steps, f"停止 {service_name} 服务")
    code, out, err = ssh.run(f"systemctl stop {service_name} 2>/dev/null; echo DONE")
    if "DONE" in out:
        log_success(f"服务已停止（或之前未运行）")
    else:
        log_warn(f"停止服务可能失败: {err}")

    # ---- 步骤 3：备份旧代码 ----
    log_step(3, total_steps, "备份旧代码")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_dir = f"{remote_path}/backend.bak.{timestamp}"
    code, out, err = ssh.run(
        f"if [ -d {remote_path}/backend ]; then "
        f"mv {remote_path}/backend {backup_dir} && echo BACKED_UP; "
        f"else echo NO_OLD_CODE; fi",
        timeout=30
    )
    if "BACKED_UP" in out:
        log_success(f"旧代码已备份: {backup_dir}")
        # 只保留最近 3 个备份
        ssh.run(
            f"cd {remote_path} && ls -d backend.bak.* 2>/dev/null | sort -r | tail -n +4 | xargs rm -rf",
            timeout=15
        )
    elif "NO_OLD_CODE" in out:
        log_info("没有旧代码需要备份（全新部署）")
    else:
        log_warn(f"备份过程异常: {err}")

    # 确保目标目录存在
    ssh.run(f"mkdir -p {remote_path}", timeout=10)

    # ---- 步骤 4：解压新代码 ----
    log_step(4, total_steps, "解压新代码到服务器")
    code, out, err = ssh.run(
        f"cd {remote_path} && tar xzf {remote_tarball} && echo EXTRACT_OK",
        timeout=60
    )
    if "EXTRACT_OK" in out:
        log_success("代码解压完成")

        # 显示解压后的文件结构
        code, out, err = ssh.run(
            f"find {remote_path}/backend -maxdepth 2 -type f | head -20",
            timeout=10
        )
        if out:
            log_info(f"解压后文件（前20个）:")
            for line in out.split("\n")[:20]:
                log_info(f"  {line}")
    else:
        log_error(f"解压失败: {err}")
        sys.exit(1)

    # 清理上传的 tarball
    ssh.run(f"rm -f {remote_tarball}")

    # ---- 步骤 5：清理 macOS 特殊文件 ----
    log_step(5, total_steps, "清理 macOS 特殊文件和旧备份")
    ssh.run(f"find {remote_path} -name '._*' -delete 2>/dev/null")
    ssh.run(f"find {remote_path} -name '.DS_Store' -delete 2>/dev/null")
    # 清理解压出的顶层多余文件
    ssh.run(f"rm -f {remote_path}/.gitignore")
    log_success("清理完成")

    # ---- 步骤 6：更新 systemd 服务文件 ----
    log_step(6, total_steps, "更新 systemd 服务文件")
    service_path = f"/etc/systemd/system/{service_name}.service"

    # 将服务文件内容通过 base64 传输（避免引号和特殊字符问题）
    import base64
    service_b64 = base64.b64encode(SERVICE_FILE_CONTENT.encode("utf-8")).decode("ascii")
    code, out, err = ssh.run(
        f'echo "{service_b64}" | base64 -d > {service_path} && echo SERVICE_OK',
        timeout=15
    )
    if "SERVICE_OK" in out:
        log_success(f"服务文件已更新: {service_path}")
        # 重新加载 systemd
        ssh.run("systemctl daemon-reload", timeout=15)
        ssh.run(f"systemctl enable {service_name}", timeout=10)
    else:
        log_error(f"服务文件更新失败: {err}")
        sys.exit(1)

    # 检查 .env 文件是否存在
    code, out, err = ssh.run(
        f"test -f {remote_path}/backend/.env && echo ENV_EXISTS || echo ENV_MISSING",
        timeout=10
    )
    if "ENV_EXISTS" in out:
        log_success(".env 配置文件已存在，保留现有配置")
    else:
        log_warn(".env 配置文件不存在！")
        log_warn(f"请手动创建 {remote_path}/backend/.env 文件")
        log_warn("可参考 deploy/.env.example 模板")

    # ---- 步骤 7：启动服务 ----
    log_step(7, total_steps, f"启动 {service_name} 服务")
    code, out, err = ssh.run(
        f"systemctl restart {service_name}",
        timeout=30
    )
    log_info("等待服务启动（5秒）...")
    time.sleep(5)

    # 检查服务状态
    code, out, err = ssh.run(
        f"systemctl is-active {service_name}",
        timeout=10
    )
    if "active" in out:
        log_success(f"{service_name} 服务运行中")
    else:
        log_error(f"{service_name} 服务启动失败！")
        log_info("查看服务日志以排查问题：")
        log_info(f"  journalctl -u {service_name} -n 50 --no-pager")
        # 输出最近的日志
        code, out, err = ssh.run(
            f"journalctl -u {service_name} -n 30 --no-pager",
            timeout=15
        )
        if out:
            print(f"\n{Color.YELLOW}--- 最近服务日志 ---{Color.NC}")
            for line in out.split("\n"):
                print(f"  {line}")
            print(f"{Color.YELLOW}--- 日志结束 ---{Color.NC}\n")
        sys.exit(1)

    # ---- 步骤 8：健康检查 ----
    log_step(8, total_steps, "执行健康检查")

    # 本地直接访问测试
    check_url = f"http://{config.get('server', 'host')}{health_endpoint}"
    log_info(f"健康检查地址: {check_url}")

    retries = 3
    for i in range(retries):
        try:
            resp = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--connect-timeout", "5", "--max-time", "10", check_url],
                capture_output=True, text=True, timeout=15
            )
            http_code = resp.stdout.strip()
            if http_code == "200":
                log_success(f"健康检查通过 (HTTP {http_code})")
                break
            elif i < retries - 1:
                log_warn(f"健康检查返回 HTTP {http_code}，{3}秒后重试...")
                time.sleep(3)
            else:
                log_warn(f"健康检查返回 HTTP {http_code}（服务已启动，可能需要时间初始化向量模型）")
        except Exception as e:
            if i < retries - 1:
                log_warn(f"健康检查失败: {e}，3秒后重试...")
                time.sleep(3)
            else:
                log_warn(f"健康检查异常: {e}（服务已启动，建议稍后手动检查）")

    # 额外测试 API 端点
    api_url = f"http://{config.get('server', 'host')}/api/v1/symptoms"
    try:
        resp = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "5", "--max-time", "10", api_url],
            capture_output=True, text=True, timeout=15
        )
        http_code = resp.stdout.strip()
        log_info(f"API 测试 /api/v1/symptoms: HTTP {http_code}")
    except Exception:
        pass

    # API 文档测试
    docs_url = f"http://{config.get('server', 'host')}/docs"
    try:
        resp = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "5", "--max-time", "10", docs_url],
            capture_output=True, text=True, timeout=15
        )
        http_code = resp.stdout.strip()
        log_info(f"API 文档 /docs: HTTP {http_code}")
    except Exception:
        pass


def show_summary(config: configparser.ConfigParser):
    """显示部署摘要"""
    server_host = config.get("server", "host")
    remote_path = config.get("deploy", "remote_path")
    service_name = config.get("deploy", "service_name")
    backend_port = config.get("deploy", "backend_port")

    print()
    print(f"{Color.GREEN}{'='*50}{Color.NC}")
    print(f"{Color.GREEN}{Color.BOLD}  宠急查后端部署完成！{Color.NC}")
    print(f"{Color.GREEN}{'='*50}{Color.NC}")
    print()
    print(f"  {Color.BOLD}服务信息：{Color.NC}")
    print(f"  - 服务器地址:  {server_host}")
    print(f"  - 项目路径:    {remote_path}/backend")
    print(f"  - 后端端口:    127.0.0.1:{backend_port}")
    print(f"  - 服务名称:    {service_name}")
    print()
    print(f"  {Color.BOLD}访问地址：{Color.NC}")
    print(f"  - 健康检查:    http://{server_host}/health")
    print(f"  - API 文档:    http://{server_host}/docs")
    print(f"  - 症状接口:    http://{server_host}/api/v1/symptoms")
    print()
    print(f"  {Color.BOLD}常用命令：{Color.NC}")
    print(f"  - 查看状态:    systemctl status {service_name}")
    print(f"  - 查看日志:    journalctl -u {service_name} -f")
    print(f"  - 重启服务:    systemctl restart {service_name}")
    print(f"  - 停止服务:    systemctl stop {service_name}")
    print(f"  - 重载Nginx:   nginx -s reload")
    print()
    print(f"  {Color.BOLD}配置文件：{Color.NC}")
    print(f"  - 环境变量:    {remote_path}/backend/.env")
    print(f"  - Systemd:     /etc/systemd/system/{service_name}.service")
    print(f"  - Nginx:       /etc/nginx/conf.d/pet-health.conf")
    print()
    print(f"{Color.GREEN}{'='*50}{Color.NC}")


# ============================================
# 命令行入口
# ============================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="宠急查 - 生产环境打包部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python deploy.py                     # 标准部署
  python deploy.py --pack-only          # 仅打包不上传
  python deploy.py --yes                 # 跳过确认直接部署
  python deploy.py --config prod.ini   # 使用指定配置
        """,
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径（INI 格式），默认使用内置配置",
    )
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="仅打包，不上传部署",
    )
    parser.add_argument(
        "--tarball", "-t",
        type=str,
        default=None,
        help="使用已有的 tarball 文件（跳过打包步骤）",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="跳过交互确认",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="指定打包输出的 tarball 路径",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    GLOBAL_OPTS["yes"] = args.yes

    # 打印标题
    print()
    print(f"{Color.GREEN}{Color.BOLD}{'='*50}{Color.NC}")
    print(f"{Color.GREEN}{Color.BOLD}  宠急查 - 后端打包部署工具{Color.NC}")
    print(f"{Color.GREEN}{Color.BOLD}{'='*50}{Color.NC}")
    print()

    # 加载配置
    config = load_config(args.config)
    server_host = config.get("server", "host")
    server_user = config.get("server", "user")
    server_port = config.getint("server", "port", fallback=22)
    server_password = config.get("server", "password")
    remote_path = config.get("deploy", "remote_path")

    log_info(f"目标服务器: {server_user}@{server_host}:{server_port}")
    log_info(f"远程路径:   {remote_path}")
    log_info(f"本地项目:   {PROJECT_ROOT}")
    print()

    # ---- 打包阶段 ----
    tarball = args.tarball
    if not tarball:
        if args.output:
            tarball = args.output
        tarball = pack_project(tarball)
    else:
        if not Path(tarball).exists():
            log_error(f"指定的 tarball 不存在: {tarball}")
            sys.exit(1)
        size_mb = os.path.getsize(tarball) / (1024 * 1024)
        log_info(f"使用已有 tarball: {tarball} ({size_mb:.2f} MB)")

    # 如果仅打包
    if args.pack_only:
        log_success(f"打包完成: {tarball}")
        print()
        print(f"  手动上传命令：")
        print(f"  sshpass -p 'PASSWORD' scp {tarball} {server_user}@{server_host}:/tmp/")
        print()
        sys.exit(0)

    # ---- 部署阶段 ----
    print()

    if not confirm(f"即将部署到 {server_user}@{server_host}，确认继续？"):
        log_info("部署已取消")
        sys.exit(0)

    # 初始化 SSH 执行器
    ssh = SSHExecutor(
        host=server_host,
        port=server_port,
        user=server_user,
        password=server_password,
    )

    # 测试连接
    log_info("测试 SSH 连接...")
    if not ssh.test_connection():
        log_error("SSH 连接失败！请检查服务器地址和凭据")
        sys.exit(1)
    log_success("SSH 连接正常")

    # 执行部署
    start_time = time.time()
    try:
        upload_and_deploy(ssh, tarball, config)
    except KeyboardInterrupt:
        log_error("部署被用户中断 (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        log_error(f"部署过程中发生异常: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time

    # 显示摘要
    show_summary(config)

    log_info(f"部署耗时: {elapsed:.1f} 秒")


if __name__ == "__main__":
    main()
