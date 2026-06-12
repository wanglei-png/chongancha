#!/bin/bash
# ============================================
# 宠安查 - 生产环境一键部署脚本
# 适用系统：CentOS 7.9
# 前置依赖：MySQL 8.0、Nginx 已安装
# 使用方法：
#   chmod +x deploy.sh
#   sudo ./deploy.sh
# ============================================

set -e

# ============================================
# 颜色输出
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# 配置变量
# ============================================
PROJECT_DIR="/opt/pet-health-assistant"
BACKEND_DIR="${PROJECT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/venv"
GIT_REPO="https://github.com/wanglei-png/chongancha.git"
PYTHON_VERSION="3.9.21"
PYTHON_SRC="/usr/local/src/Python-${PYTHON_VERSION}"
PYTHON_PREFIX="/usr/local/python3.9"
SERVICE_NAME="pet-health"
NGINX_CONF_SRC="${BACKEND_DIR}/../deploy/nginx.conf"
NGINX_CONF_DST="/etc/nginx/conf.d/pet-health.conf"
SERVICE_FILE_SRC="${BACKEND_DIR}/../deploy/pet-health.service"
SERVICE_FILE_DST="/etc/systemd/system/${SERVICE_NAME}.service"

# ============================================
# 步骤 1：检查系统环境
# ============================================
check_system() {
    log_info "========== 步骤 1/8：检查系统环境 =========="

    # 检查 CentOS 版本
    if [ -f /etc/centos-release ]; then
        OS_VERSION=$(cat /etc/centos-release)
        log_info "系统版本：${OS_VERSION}"
    else
        log_warn "非 CentOS 系统，脚本可能不兼容"
    fi

    # 检查是否为 root
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 用户或 sudo 运行此脚本"
        exit 1
    fi
    log_success "Root 权限检查通过"

    # 检查 MySQL
    if systemctl is-active --quiet mysqld; then
        log_success "MySQL 服务运行中"
    else
        log_warn "MySQL 服务未运行，尝试启动..."
        systemctl start mysqld || log_error "MySQL 启动失败，请手动检查"
    fi

    # 检查 Nginx
    if command -v nginx &> /dev/null; then
        log_success "Nginx 已安装：$(nginx -v 2>&1)"
    else
        log_error "Nginx 未安装，请先安装 Nginx"
        exit 1
    fi

    # 检查 Git
    if command -v git &> /dev/null; then
        log_success "Git 已安装：$(git --version)"
    else
        log_info "安装 Git..."
        yum install -y git
        log_success "Git 安装完成"
    fi
}

# ============================================
# 步骤 2：检查 / 编译安装 Python 3.9
# ============================================
install_python() {
    log_info "========== 步骤 2/8：检查 Python 3.9 =========="

    # 检查是否已存在
    if [ -f "${PYTHON_PREFIX}/bin/python3.9" ]; then
        PYTHON_VERSION_INSTALLED=$(${PYTHON_PREFIX}/bin/python3.9 --version 2>&1)
        log_success "Python 3.9 已安装：${PYTHON_VERSION_INSTALLED}"
        return
    fi

    # 检查系统是否已有 python3.9
    if command -v python3.9 &> /dev/null; then
        PYTHON_VERSION_INSTALLED=$(python3.9 --version 2>&1)
        log_success "系统 Python 3.9 已安装：${PYTHON_VERSION_INSTALLED}"
        # 创建软链接
        mkdir -p ${PYTHON_PREFIX}/bin
        ln -sf $(which python3.9) ${PYTHON_PREFIX}/bin/python3.9
        ln -sf $(which pip3.9) ${PYTHON_PREFIX}/bin/pip3.9 2>/dev/null || true
        return
    fi

    log_info "Python 3.9 未安装，开始编译安装..."

    # 安装编译依赖
    log_info "安装编译依赖..."
    yum install -y gcc gcc-c++ make wget openssl-devel bzip2-devel \
        libffi-devel zlib-devel readline-devel sqlite-devel \
        xz-devel tk-devel libuuid-devel

    # 下载 Python 源码
    log_info "下载 Python ${PYTHON_VERSION}..."
    cd /usr/local/src
    if [ ! -f "Python-${PYTHON_VERSION}.tgz" ]; then
        wget -q "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
    fi

    # 解压
    log_info "解压源码..."
    tar xzf "Python-${PYTHON_VERSION}.tgz"

    # 编译安装
    log_info "编译安装（耗时较长，请耐心等待）..."
    cd "Python-${PYTHON_VERSION}"
    ./configure --prefix=${PYTHON_PREFIX} --enable-optimizations --with-ensurepip=install
    make -j$(nproc)
    make install

    # 验证安装
    ${PYTHON_PREFIX}/bin/python3.9 --version
    log_success "Python ${PYTHON_VERSION} 编译安装完成"

    # 更新 pip
    ${PYTHON_PREFIX}/bin/pip3.9 install --upgrade pip
    log_success "pip 已更新"
}

# ============================================
# 步骤 3：克隆代码
# ============================================
clone_code() {
    log_info "========== 步骤 3/8：克隆代码 =========="

    if [ -d "${PROJECT_DIR}" ]; then
        log_info "项目目录已存在，更新代码..."
        cd "${PROJECT_DIR}"
        git pull origin main
    else
        log_info "克隆代码到 ${PROJECT_DIR}..."
        git clone "${GIT_REPO}" "${PROJECT_DIR}"
    fi
    log_success "代码克隆/更新完成"
}

# ============================================
# 步骤 4：创建 Python 虚拟环境
# ============================================
create_venv() {
    log_info "========== 步骤 4/8：创建 Python 虚拟环境 =========="

    if [ -d "${VENV_DIR}" ]; then
        log_info "虚拟环境已存在，跳过创建"
    else
        log_info "创建虚拟环境..."
        ${PYTHON_PREFIX}/bin/python3.9 -m venv "${VENV_DIR}"
        log_success "虚拟环境创建完成"
    fi

    # 激活虚拟环境并安装依赖
    log_info "安装 Python 依赖..."
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install -r "${BACKEND_DIR}/requirements.txt"
    deactivate
    log_success "Python 依赖安装完成"
}

# ============================================
# 步骤 5：配置 .env 文件
# ============================================
configure_env() {
    log_info "========== 步骤 5/8：配置 .env 文件 =========="

    ENV_FILE="${BACKEND_DIR}/.env"

    if [ -f "${ENV_FILE}" ]; then
        log_info ".env 文件已存在，跳过创建"
        log_warn "如需重新配置，请手动编辑 ${ENV_FILE}"
    else
        log_info "从模板创建 .env 文件..."
        cp "${BACKEND_DIR}/../deploy/.env.example" "${ENV_FILE}"
        log_warn "=============================================="
        log_warn "请手动编辑 ${ENV_FILE} 填写以下配置："
        log_warn "  1. DB_PASSWORD（数据库密码）"
        log_warn "  2. WX_SECRET（微信小程序密钥）"
        log_warn "  3. JWT_SECRET_KEY（JWT 密钥，建议随机生成）"
        log_warn "  4. LLM_API_KEY（大模型 API 密钥）"
        log_warn "  5. WX_MCH_ID / WX_API_KEY（微信支付密钥）"
        log_warn "=============================================="
        log_info "编辑完成后，执行以下命令重启服务："
        log_info "  sudo systemctl restart ${SERVICE_NAME}"
    fi
}

# ============================================
# 步骤 6：配置 systemd 服务
# ============================================
configure_systemd() {
    log_info "========== 步骤 6/8：配置 systemd 服务 =========="

    log_info "复制服务文件到 ${SERVICE_FILE_DST}..."
    cp "${SERVICE_FILE_SRC}" "${SERVICE_FILE_DST}"

    log_info "重新加载 systemd 配置..."
    systemctl daemon-reload

    log_info "启用开机自启..."
    systemctl enable "${SERVICE_NAME}"

    log_success "systemd 服务配置完成"
}

# ============================================
# 步骤 7：配置 Nginx
# ============================================
configure_nginx() {
    log_info "========== 步骤 7/8：配置 Nginx =========="

    log_info "复制 Nginx 配置到 ${NGINX_CONF_DST}..."
    cp "${NGINX_CONF_SRC}" "${NGINX_CONF_DST}"

    # 测试 Nginx 配置
    log_info "测试 Nginx 配置..."
    nginx -t

    # 重启 Nginx
    log_info "重启 Nginx..."
    systemctl restart nginx

    log_success "Nginx 配置完成"
}

# ============================================
# 步骤 8：启动服务
# ============================================
start_service() {
    log_info "========== 步骤 8/8：启动服务 =========="

    log_info "启动 ${SERVICE_NAME} 服务..."
    systemctl start "${SERVICE_NAME}"

    # 等待服务启动
    sleep 3

    # 检查服务状态
    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        log_success "${SERVICE_NAME} 服务运行中"
        systemctl status "${SERVICE_NAME}" --no-pager | head -15
    else
        log_error "${SERVICE_NAME} 服务启动失败"
        log_info "查看日志：journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
        exit 1
    fi

    # 健康检查
    log_info "执行健康检查..."
    sleep 2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/health 2>/dev/null || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        log_success "健康检查通过（HTTP ${HTTP_CODE}）"
    else
        log_warn "健康检查返回 HTTP ${HTTP_CODE}，请手动检查"
    fi

    # 测试 Nginx 反向代理
    HTTP_CODE_NGINX=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/api/v1/symptoms 2>/dev/null || echo "000")
    if [ "${HTTP_CODE_NGINX}" != "000" ]; then
        log_success "Nginx 反向代理测试通过（HTTP ${HTTP_CODE_NGINX}）"
    else
        log_warn "Nginx 反向代理测试异常，请检查 Nginx 配置"
    fi
}

# ============================================
# 部署完成
# ============================================
show_summary() {
    log_info ""
    log_info "============================================"
    log_success "  宠安查后端部署完成！"
    log_info "============================================"
    log_info ""
    log_info "  服务信息："
    log_info "  - 项目路径：    ${PROJECT_DIR}"
    log_info "  - 后端端口：    127.0.0.1:8001"
    log_info "  - Nginx 端口：  80"
    log_info "  - 服务名称：    ${SERVICE_NAME}"
    log_info ""
    log_info "  访问地址："
    log_info "  - IP 访问：     http://116.62.175.15/api/v1/symptoms"
    log_info "  - 域名访问：    https://chongjicha.wlstudio.com.cn/api/v1/symptoms"
    log_info "  - API 文档：    http://116.62.175.15/docs"
    log_info ""
    log_info "  常用命令："
    log_info "  - 查看状态：    systemctl status ${SERVICE_NAME}"
    log_info "  - 查看日志：    journalctl -u ${SERVICE_NAME} -f"
    log_info "  - 重启服务：    systemctl restart ${SERVICE_NAME}"
    log_info "  - 停止服务：    systemctl stop ${SERVICE_NAME}"
    log_info "  - 重载 Nginx：  nginx -s reload"
    log_info ""
    log_info "  配置文件："
    log_info "  - 环境变量：    ${BACKEND_DIR}/.env"
    log_info "  - Nginx 配置：  ${NGINX_CONF_DST}"
    log_info "  - Systemd 服务：${SERVICE_FILE_DST}"
    log_info ""
    log_warn "  注意：请务必编辑 ${BACKEND_DIR}/.env 填写敏感信息！"
    log_info "============================================"
}

# ============================================
# 主流程
# ============================================
main() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  宠安查 - 生产环境一键部署脚本${NC}"
    echo -e "${GREEN}  适用系统：CentOS 7.9${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""

    check_system
    install_python
    clone_code
    create_venv
    configure_env
    configure_systemd
    configure_nginx
    start_service
    show_summary
}

main "$@"
