// pages/result/result.js
const api = require('../../utils/api')
const { trackEvent, reportPageView } = require('../../utils/analytics')

Page({

  /**
   * 页面的初始数据
   */
  data: {
    // 从上一页传入
    symptom_id: '',
    symptom_name: '',
    emoji: '',
    petInfo: null,

    // 宠物摘要文字
    petSummary: '通用指引',

    // 加载状态
    isLoading: true,
    loadError: false,
    errorType: '',         // 错误类型：network/timeout/server/notfound/empty
    errorMessage: '',      // 错误提示文本
    showRetry: true,       // 是否显示重试按钮

    // 后端返回的数据
    homeObservation: [],
    homeObservationTotal: 0,
    prohibitions: [],
    redFlags: [],

    // 审核信息
    auditStatus: 'approved',
    auditStatusText: '✅ 已审核',
    auditIcon: '✅',
    auditText: '经执业兽医师审核',
    auditDate: '2026-06-05',

    // 付费状态
    isUnlocked: false,
    showPayModal: false,
    hasTriggeredPayModal: false,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    reportPageView('result')

    // 接收参数
    const symptom_id = options.symptom_id ? decodeURIComponent(options.symptom_id) : ''
    const symptom_name = options.symptom_name ? decodeURIComponent(options.symptom_name) : ''
    const emoji = options.emoji ? decodeURIComponent(options.emoji) : ''
    let petInfo = null
    let petSummary = '通用指引'

    if (options.petInfo) {
      try {
        petInfo = JSON.parse(decodeURIComponent(options.petInfo))
        // 构建宠物摘要：宠物名称（fallback 品种名或"宠物"）
        const petName = petInfo.petName || petInfo.breed || '宠物'
        const parts = [petName]
        if (petInfo.breed) parts.push(petInfo.breed)
        if (petInfo.ageStage) {
          if (petInfo.ageDetail) {
            parts.push(`${petInfo.ageDetail}`)
          } else {
            parts.push(petInfo.ageStage)
          }
        }
        if (petInfo.weight) parts.push(petInfo.weight)
        petSummary = parts.length > 0 ? parts.join('·') : '通用指引'
      } catch (e) {
        console.error('解析宠物信息失败：', e)
      }
    }

    this.setData({
      symptom_id,
      symptom_name,
      emoji,
      petInfo,
      petSummary,
    })

    // 调用后端获取免费结果
    this.fetchFreeResult(symptom_id)
  },

  /**
   * 根据 audit_status 更新审核信息显示
   */
  updateAuditDisplay(auditStatus) {
    const status = auditStatus || 'approved'
    let auditIcon, auditText, auditStatusText

    switch (status) {
      case 'approved':
        auditIcon = '✅'
        auditText = '经执业兽医师审核'
        auditStatusText = '✅ 已审核'
        break
      case 'reviewing':
        auditIcon = '🔄'
        auditText = '审核中，内容仅供参考'
        auditStatusText = '🔄 审核中'
        break
      case 'pending':
      default:
        auditIcon = '⏳'
        auditText = '待审核，内容仅供参考'
        auditStatusText = '⏳ 待审核'
        break
    }

    this.setData({
      auditStatus: status,
      auditIcon,
      auditText,
      auditStatusText,
    })
  },

  /**
   * 调用 POST /api/v1/symptoms/query-free 获取免费结果
   */
  fetchFreeResult(symptomId) {
    if (!symptomId) {
      this.setData({
        isLoading: false,
        loadError: true,
        errorType: 'notfound',
        errorMessage: '该症状暂无数据',
        showRetry: false,
      })
      return
    }

    this.setData({ isLoading: true, loadError: false, errorType: '', errorMessage: '' })

    const requestData = {
      symptom_id: symptomId,
    }

    // 如果有宠物信息，映射字段名
    if (this.data.petInfo) {
      const pet = this.data.petInfo
      requestData.species = pet.species === '猫' ? 'cat' : pet.species === '狗' ? 'dog' : pet.species
      requestData.breed = pet.breed || ''
      requestData.age_type = pet.ageStage || ''  // 映射 ageStage → age_type
      // 提取数字部分作为 float
      if (pet.weight) {
        const weightMatch = pet.weight.match(/([\d.]+)/)
        if (weightMatch) {
          requestData.weight = parseFloat(weightMatch[1])
        }
      }
    }

    api.post('/symptoms/query-free', requestData)
      .then((res) => {
        this.updateAuditDisplay(res.audit_status)
        this.setData({
          homeObservation: res.home_observation || [],
          homeObservationTotal: res.home_observation_total || 0,
          prohibitions: res.absolute_prohibitions || [],
          redFlags: res.red_flags || [],
          auditDate: '2026-06-05',
          isLoading: false,
        })
      })
      .catch((err) => {
        console.error('获取免费结果失败:', err)
        const errorMessage = err.message || api.getErrorMessage(err)
        const errorType = err.type || 'unknown'
        const showRetry = api.shouldShowRetry(err)

        this.setData({
          isLoading: false,
          loadError: true,
          errorType,
          errorMessage,
          showRetry,
        })
      })
  },

  /**
   * 调用 POST /api/v1/symptoms/query 获取完整结果（付费后调用）
   */
  fetchFullResult(symptomId) {
    if (!symptomId) return
    this.setData({ isLoading: true })

    const requestData = {
      symptom_id: symptomId,
    }

    // 如果有宠物信息，映射字段名
    if (this.data.petInfo) {
      const pet = this.data.petInfo
      requestData.species = pet.species === '猫' ? 'cat' : pet.species === '狗' ? 'dog' : pet.species
      requestData.breed = pet.breed || ''
      requestData.age_type = pet.ageStage || ''
      if (pet.weight) {
        const weightMatch = pet.weight.match(/([\d.]+)/)
        if (weightMatch) {
          requestData.weight = parseFloat(weightMatch[1])
        }
      }
    }

    api.post('/symptoms/query', requestData)
      .then((res) => {
        this.updateAuditDisplay(res.audit_status)
        this.setData({
          homeObservation: res.home_observation || [],
          homeObservationTotal: (res.home_observation || []).length,
          prohibitions: res.absolute_prohibitions || [],
          redFlags: res.red_flags || [],
          auditDate: '2026-06-05',
          isLoading: false,
        })
      })
      .catch((err) => {
        console.error('获取完整结果失败:', err)
        this.setData({ isLoading: false })
        wx.showToast({
          title: err.message || '加载完整内容失败',
          icon: 'none',
          duration: 2000,
        })
      })
  },

  /**
   * 重新加载
   */
  onRetry() {
    this.fetchFreeResult(this.data.symptom_id)
  },

  /**
   * 返回首页
   */
  onGoHome() {
    wx.switchTab({
      url: '/pages/index/index',
    })
  },

  /**
   * 阻止事件冒泡（弹窗内部点击）
   */
  stopPropagation() {},

  /**
   * 显示付费弹窗
   */
  showPayModalFn() {
    if (this.data.isUnlocked) return
    // 埋点：付费弹窗展示
    trackEvent('pay_modal_show', { symptom_id: this.data.symptom_id })
    this.setData({ showPayModal: true })
  },

  /**
   * 关闭付费弹窗
   */
  onClosePayModal() {
    this.setData({ showPayModal: false })
  },

  /**
   * 模拟支付成功（MVP 阶段直接解锁）
   * 解锁后调用 fetchFullResult 获取完整数据
   */
  onPay() {
    wx.showLoading({ title: '支付处理中...' })

    // 埋点：支付点击
    trackEvent('pay_click', { symptom_id: this.data.symptom_id, product_type: 'symptom_unlock' })

    // 模拟支付延迟
    setTimeout(() => {
      wx.hideLoading()
      this.setData({
        isUnlocked: true,
        showPayModal: false,
        hasTriggeredPayModal: true,
      })

      // 埋点：支付成功
      trackEvent('pay_success', { symptom_id: this.data.symptom_id, order_no: `ORD${Date.now()}` })

      wx.showToast({
        title: '解锁成功',
        icon: 'success',
        duration: 1500,
      })

      // 重新获取完整数据（包含所有居家观察建议）
      this.fetchFullResult(this.data.symptom_id)
    }, 1200)
  },

  /**
   * 点击摘要按钮 - 未付费弹出付费弹窗，已付费跳转摘要页
   */
  onTapSummaryBtn() {
    if (this.data.isUnlocked) {
      this.onGenerateSummary()
    } else {
      this.showPayModalFn()
    }
  },

  /**
   * 生成病情摘要 - 携带参数跳转到 summary 页
   */
  onGenerateSummary() {
    const { symptom_id, symptom_name, emoji, petInfo } = this.data

    // 埋点：摘要生成
    trackEvent('summary_generate', { symptom_id, symptom_name })

    const params = []
    if (symptom_id) params.push(`symptom_id=${encodeURIComponent(symptom_id)}`)
    if (symptom_name) params.push(`symptom_name=${encodeURIComponent(symptom_name)}`)
    if (emoji) params.push(`emoji=${encodeURIComponent(emoji)}`)
    if (petInfo) {
      params.push(`petInfo=${encodeURIComponent(JSON.stringify(petInfo))}`)
    }

    wx.navigateTo({
      url: `/pages/summary/summary?${params.join('&')}`,
      fail: (err) => {
        console.error('跳转摘要页失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none',
        })
      },
    })
  },

  /**
   * 返回症状选择页
   */
  onBackToSymptom() {
    wx.navigateBack({
      delta: 2,
      fail: () => {
        // 如果无法返回（页面栈不足），直接跳转
        wx.redirectTo({
          url: '/pages/symptom/symptom',
        })
      },
    })
  },

  /**
   * 页面滚动监听 - 当"建议就医的触发条件"区域进入视口时触发付费弹窗
   * 使用选择器查询 .warning-card 的位置，当第一个卡片进入视口时触发
   * 这意味着用户已经看完了"居家观察建议"和"绝对禁止行为"区域
   */
  onPageScroll(e) {
    if (this.data.isUnlocked || this.data.hasTriggeredPayModal) return

    const query = wx.createSelectorQuery()
    // 查询"建议就医的触发条件"区域的第一个元素
    query.select('.warning-card').boundingClientRect((rect) => {
      if (rect && rect.top < wx.getSystemInfoSync().windowHeight) {
        this.setData({
          hasTriggeredPayModal: true,
          showPayModal: true,
        })
      }
    }).exec()
  },
})
