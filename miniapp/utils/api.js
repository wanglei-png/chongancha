/**
 * API 请求封装
 * 所有后端 API 调用统一通过此模块发起
 */

const CONFIG = require('./config')

/**
 * 发起 HTTP 请求
 * @param {string} method - 请求方法 GET/POST/PUT/DELETE
 * @param {string} path - API 路径（不含前缀），如 /symptoms
 * @param {object} data - 请求体数据（POST/PUT）
 * @param {object} options - 额外选项
 * @param {boolean} options.skipAuth - 是否跳过认证（MVP 阶段默认 true）
 * @returns {Promise<object>} 响应数据
 */
function request(method, path, data = null, options = {}) {
  const { skipAuth = true } = options

  return new Promise((resolve, reject) => {
    const url = CONFIG.getUrl(path)

    const header = {
      'Content-Type': 'application/json',
    }

    // MVP 阶段跳过 JWT token
    // const token = wx.getStorageSync('token')
    // if (token && !skipAuth) {
    //   header['Authorization'] = `Bearer ${token}`
    // }

    wx.request({
      url,
      method,
      data,
      header,
      timeout: CONFIG.REQUEST_TIMEOUT,
      success: (res) => {
        const { statusCode, data: responseData } = res

        if (statusCode >= 200 && statusCode < 300) {
          resolve(responseData)
        } else if (statusCode === 401) {
          // 未授权，跳转到登录页（MVP 阶段暂不处理）
          console.warn('API 返回 401 未授权:', path)
          reject(new Error('登录已过期，请重新登录'))
        } else if (statusCode === 404) {
          reject(new Error('请求的资源不存在'))
        } else if (statusCode >= 500) {
          reject(new Error('服务器繁忙，请稍后重试'))
        } else {
          const errMsg = responseData?.detail || `请求失败 (${statusCode})`
          reject(new Error(errMsg))
        }
      },
      fail: (err) => {
        console.error('网络请求失败:', err)
        reject(new Error('网络异常，请稍后重试'))
      },
    })
  })
}

/**
 * GET 请求
 */
function get(path, options = {}) {
  return request('GET', path, null, options)
}

/**
 * POST 请求
 */
function post(path, data, options = {}) {
  return request('POST', path, data, options)
}

/**
 * PUT 请求
 */
function put(path, data, options = {}) {
  return request('PUT', path, data, options)
}

/**
 * DELETE 请求
 */
function del(path, options = {}) {
  return request('DELETE', path, null, options)
}

module.exports = {
  get,
  post,
  put,
  del,
  request,
}
