/**
 * 数据埋点工具
 * 封装事件上报函数，在关键用户行为节点调用
 */

const api = require('./api')

/**
 * 上报事件到自建后端
 * @param {string} eventType - 事件类型
 * @param {object} eventData - 事件附加数据
 */
function trackEvent(eventType, eventData = {}) {
  // 自建后端事件上报
  api.post('/events/track', {
    event_type: eventType,
    event_data: eventData,
  }).catch((err) => {
    // 埋点失败不影响主流程，静默处理
    console.warn(`[Analytics] 事件上报失败: ${eventType}`, err)
  })
}

/**
 * 微信小程序官方数据分析 - 页面浏览事件
 * @param {string} pageName - 页面名称
 */
function reportPageView(pageName) {
  try {
    wx.reportAnalytics('page_view', {
      page: pageName,
      timestamp: Date.now(),
    })
  } catch (e) {
    // wx.reportAnalytics 在开发工具中可能不支持，静默处理
    console.warn('[Analytics] wx.reportAnalytics 调用失败', e)
  }
}

module.exports = {
  trackEvent,
  reportPageView,
}
