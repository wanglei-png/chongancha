/**
 * API 请求封装
 * 所有后端 API 调用统一通过此模块发起
 * 
 * 统一错误处理，返回标准化错误对象：
 * - 网络断开：{ type: 'network', message: '网络异常，请检查网络连接' }
 * - 请求超时：{ type: 'timeout', message: '请求超时，请稍后重试' }
 * - 后端 500：{ type: 'server', message: '服务器繁忙，请稍后重试' }
 * - 后端 404：{ type: 'notfound', message: '该症状暂无数据' }
 * - 数据为空：{ type: 'empty', message: '暂无数据' }
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

    // 记录请求开始时间
    const startTime = Date.now()

    wx.request({
      url,
      method,
      data,
      header,
      timeout: CONFIG.REQUEST_TIMEOUT,
      success: (res) => {
        const { statusCode, data: responseData } = res
        const elapsed = Date.now() - startTime

        if (statusCode >= 200 && statusCode < 300) {
          // 成功响应，但检查数据是否为空
          if (responseData === null || responseData === undefined) {
            reject({
              type: 'empty',
              message: '暂无数据',
              detail: '服务器返回了空数据',
            })
          } else if (Array.isArray(responseData) && responseData.length === 0) {
            // 数组为空也算空数据
            reject({
              type: 'empty',
              message: '暂无数据',
              detail: '返回的列表为空',
            })
          } else if (typeof responseData === 'object' && !Array.isArray(responseData)) {
            // 对象类型，检查关键字段是否都为空
            const values = Object.values(responseData)
            const allEmpty = values.every(
              (v) => v === null || v === undefined || (Array.isArray(v) && v.length === 0) || v === ''
            )
            if (allEmpty && Object.keys(responseData).length > 0) {
              // 如果所有字段都为空，但对象本身有字段（如 {symptoms: []}），不视为空
              // 只有当对象完全没有有用数据时才拒绝
              const hasData = values.some(
                (v) => v !== null && v !== undefined && !(Array.isArray(v) && v.length === 0) && v !== ''
              )
              if (!hasData) {
                reject({
                  type: 'empty',
                  message: '暂无数据',
                  detail: '返回的数据均为空',
                })
                return
              }
            }
            resolve(responseData)
          } else {
            resolve(responseData)
          }
        } else if (statusCode === 401) {
          // 未授权，跳转到登录页（MVP 阶段暂不处理）
          console.warn('API 返回 401 未授权:', path)
          reject({
            type: 'auth',
            message: '登录已过期，请重新登录',
            statusCode: 401,
          })
        } else if (statusCode === 404) {
          reject({
            type: 'notfound',
            message: '该症状暂无数据',
            statusCode: 404,
            detail: responseData?.detail || '请求的资源不存在',
          })
        } else if (statusCode >= 500) {
          reject({
            type: 'server',
            message: '服务器繁忙，请稍后重试',
            statusCode: statusCode,
            detail: responseData?.detail || '服务器内部错误',
          })
        } else {
          const errMsg = responseData?.detail || `请求失败 (${statusCode})`
          reject({
            type: 'unknown',
            message: errMsg,
            statusCode: statusCode,
          })
        }
      },
      fail: (err) => {
        console.error('网络请求失败:', err)

        // 判断错误类型
        if (err.errno === 600001 || err.errMsg?.includes('timeout') || err.errMsg?.includes('time_out')) {
          // 请求超时
          reject({
            type: 'timeout',
            message: '请求超时，请稍后重试',
            detail: `请求超过 ${CONFIG.REQUEST_TIMEOUT / 1000} 秒未响应`,
          })
        } else if (err.errno === 600002 || err.errMsg?.includes('fail') || err.errMsg?.includes('ETIMEDOUT')) {
          // 网络连接失败
          reject({
            type: 'network',
            message: '网络异常，请检查网络连接',
            detail: err.errMsg || '无法连接到服务器',
          })
        } else {
          // 其他网络错误
          reject({
            type: 'network',
            message: '网络异常，请检查网络连接',
            detail: err.errMsg || '未知网络错误',
          })
        }
      },
    })
  })
}

/**
 * 根据错误对象获取友好的错误提示文本
 * @param {object|Error} err - 错误对象
 * @returns {string} 友好的错误提示
 */
function getErrorMessage(err) {
  if (!err) return '未知错误'

  // 如果是标准化的错误对象
  if (typeof err === 'object' && err.message) {
    return err.message
  }

  // 如果是 Error 实例
  if (err instanceof Error) {
    return err.message || '未知错误'
  }

  return '未知错误'
}

/**
 * 根据错误类型获取对应的操作按钮文本
 * @param {object} err - 错误对象
 * @returns {string} 按钮文本
 */
function getErrorAction(err) {
  if (!err) return '重试'

  const type = err.type || ''
  switch (type) {
    case 'notfound':
      return '返回首页'
    case 'empty':
      return '返回'
    default:
      return '重试'
  }
}

/**
 * 根据错误类型判断是否显示重试按钮
 * @param {object} err - 错误对象
 * @returns {boolean}
 */
function shouldShowRetry(err) {
  if (!err) return true
  const type = err.type || ''
  // 404 和数据为空不显示重试，显示返回按钮
  return type !== 'notfound' && type !== 'empty'
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
  getErrorMessage,
  getErrorAction,
  shouldShowRetry,
}
