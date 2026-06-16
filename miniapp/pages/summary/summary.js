// pages/summary/summary.js
const api = require('../../utils/api')
const { reportPageView } = require('../../utils/analytics')

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

    // 加载状态
    isLoading: true,
    loadError: false,
    errorType: '',         // 错误类型：network/timeout/server/notfound/empty
    errorMessage: '',      // 错误提示文本
    showRetry: true,       // 是否显示重试按钮

    // 摘要日期
    summaryDate: '',

    // 摘要文本
    summaryText: '',
    // 原始摘要文本（用于判断是否被修改）
    originalText: '',

    // V2.1 相似症状推荐
    similarSymptomsList: [],

    // 订阅弹窗
    showSubModal: false,
    selectedSub: 'monthly',
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    reportPageView('summary')

    // 接收参数
    const symptom_id = options.symptom_id ? decodeURIComponent(options.symptom_id) : ''
    const symptom_name = options.symptom_name ? decodeURIComponent(options.symptom_name) : ''
    const emoji = options.emoji ? decodeURIComponent(options.emoji) : ''
    let petInfo = null

    if (options.petInfo) {
      try {
        petInfo = JSON.parse(decodeURIComponent(options.petInfo))
      } catch (e) {
        console.error('解析宠物信息失败：', e)
      }
    }

    this.setData({
      symptom_id,
      symptom_name,
      emoji,
      petInfo,
    })

    // 调用后端生成摘要
    this.fetchSummary(symptom_id, petInfo)
  },

  /**
   * 调用 POST /api/v1/summary/generate 生成病情摘要
   */
  fetchSummary(symptomId, petInfo) {
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

    // 构建请求参数
    const requestData = {
      symptom_id: symptomId,
      pet_name: petInfo?.name || petInfo?.petName || '',
      breed: petInfo?.breed || '',
      age: petInfo?.ageStage || petInfo?.age || '',
      weight: petInfo?.weight || '',
      duration: '',
      actions_taken: ['暂时禁食4-6小时', '提供少量清水'],
      observations: '',
      other_symptoms: '',
      status: '精神尚可',
    }

    // MVP 阶段跳过 JWT 认证，后端已允许匿名访问
    api.post('/summary/generate', requestData)
      .then((res) => {
        const now = new Date()
        const pad = (n) => String(n).padStart(2, '0')
        const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`

        // 处理相似症状推荐（V2.1）
        let similarList = []
        if (res.similar_symptoms && Array.isArray(res.similar_symptoms)) {
          similarList = res.similar_symptoms.map(item => ({
            symptom_id: item.symptom_id || '',
            symptom_name: item.symptom_name || '',
            similarity: item.similarity || 0
          }))
        }

        this.setData({
          summaryText: res.summary || '',
          originalText: res.summary || '',
          summaryDate: dateStr,
          similarSymptomsList: similarList,
          isLoading: false,
        })
      })
      .catch((err) => {
        console.error('生成摘要失败:', err)
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
   * 重新加载
   */
  onRetry() {
    this.fetchSummary(this.data.symptom_id, this.data.petInfo)
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
   * 文本编辑输入
   */
  onTextInput(e) {
    this.setData({
      summaryText: e.detail.value,
    })
  },

  /**
   * 复制全文
   */
  onCopyText() {
    const { summaryText } = this.data

    wx.setClipboardData({
      data: summaryText,
      success: () => {
        wx.showToast({
          title: '摘要已复制，可直接发给兽医',
          icon: 'none',
          duration: 2000,
        })
      },
      fail: (err) => {
        console.error('复制失败：', err)
        wx.showToast({
          title: '复制失败，请重试',
          icon: 'none',
        })
      },
    })
  },

  /**
   * 点击订阅引导 - 弹出订阅选择弹窗
   */
  onTapSubscribe() {
    this.setData({
      showSubModal: true,
      selectedSub: 'monthly',
    })
  },

  /**
   * 关闭订阅弹窗
   */
  onCloseSubModal() {
    this.setData({ showSubModal: false })
  },

  /**
   * 阻止事件冒泡
   */
  stopPropagation() {},

  /**
   * 选择月付方案
   */
  onSelectMonthly() {
    this.setData({ selectedSub: 'monthly' })
  },

  /**
   * 选择年付方案
   */
  onSelectYearly() {
    this.setData({ selectedSub: 'yearly' })
  },

  /**
   * 确认订阅
   */
  onConfirmSub() {
    const { selectedSub } = this.data
    const planName = selectedSub === 'monthly' ? '月付￥19' : '年付￥159'
    wx.showToast({
      title: `已选择${planName}方案`,
      icon: 'none',
      duration: 2000,
    })
    this.setData({ showSubModal: false })
  },

  /**
   * 点击相似症状标签（V2.1）
   */
  onTapSimilarSymptom(e) {
    const symptomId = e.currentTarget.dataset.symptomId
    if (!symptomId) return

    wx.navigateTo({
      url: `/pages/result/result?symptom_id=${encodeURIComponent(symptomId)}`,
    })
  },

  /**
   * 返回上一页
   */
  onGoBack() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.redirectTo({
          url: '/pages/result/result',
        })
      },
    })
  },
})
