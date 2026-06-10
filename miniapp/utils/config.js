/**
 * 应用配置
 * 后端地址配置在此文件中，方便切换
 */
const CONFIG = {
  // 后端 API 地址
  API_BASE_URL: 'http://127.0.0.1:8001',

  // API 版本前缀
  API_PREFIX: '/api/v1',

  // 请求超时时间（毫秒）
  REQUEST_TIMEOUT: 10000,
}

// 导出完整 URL 拼接函数
CONFIG.getUrl = function (path) {
  return `${this.API_BASE_URL}${this.API_PREFIX}${path}`
}

module.exports = CONFIG
