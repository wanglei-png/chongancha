// pages/symptom/symptom.js
const api = require('../../utils/api')
const { trackEvent, reportPageView } = require('../../utils/analytics')

Page({

  /**
   * 页面的初始数据
   */
  data: {
    symptoms: [],
    filteredSymptoms: [],  // 过滤后的症状列表（排除 pending）
    selectedIndex: null,
    isAnalyzing: false,
    isLoading: true,
    loadError: false,
    errorType: '',         // 错误类型：network/timeout/server/notfound/empty
    errorMessage: '',      // 错误提示文本
    showRetry: true,       // 是否显示重试按钮
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad() {
    reportPageView('symptom')
    this.fetchSymptoms()
  },

  /**
   * 从后端获取症状列表
   */
  fetchSymptoms() {
    this.setData({ isLoading: true, loadError: false, errorType: '', errorMessage: '' })

    api.get('/symptoms')
      .then((res) => {
        // 后端返回格式：{ symptoms: [...] } 或直接数组
        const symptoms = Array.isArray(res) ? res : (res.symptoms || [])
        // 过滤掉 pending 状态的症状（不显示）
        const filteredSymptoms = symptoms.filter(
          (item) => item.audit_status !== 'pending'
        )
        this.setData({
          symptoms,
          filteredSymptoms,
          isLoading: false,
        })
      })
      .catch((err) => {
        console.error('获取症状列表失败:', err)
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
    this.fetchSymptoms()
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
   * 选择症状
   */
  onSelectSymptom(e) {
    const { index } = e.currentTarget.dataset
    const { selectedIndex, isAnalyzing, filteredSymptoms } = this.data

    // 如果正在分析中，阻止操作
    if (isAnalyzing) return

    const symptom = filteredSymptoms[index]
    // 如果症状是 reviewing 状态，允许点击但不允许分析（显示提示）
    if (symptom.audit_status === 'reviewing') {
      wx.showToast({
        title: '该症状正在审核中，暂不可用',
        icon: 'none',
        duration: 2000,
      })
      return
    }

    // 如果已选中某个症状，且用户点击了另一个症状 → 快速连点，弹提示
    if (selectedIndex !== null && selectedIndex !== index) {
      wx.showToast({
        title: '建议先处理最紧急的一个症状',
        icon: 'none',
        duration: 2000,
      })
      return
    }

    // 切换选中状态（点击同一个取消选中，点击不同的切换）
    this.setData({
      selectedIndex: selectedIndex === index ? null : index,
    })
  },

  /**
   * 开始分析
   */
  onStartAnalyze() {
    const { selectedIndex, filteredSymptoms, isAnalyzing } = this.data

    if (isAnalyzing) return

    if (selectedIndex === null) {
      wx.showToast({
        title: '请先选择一个症状',
        icon: 'none',
      })
      return
    }

    // 设置分析中状态，防止重复点击
    this.setData({ isAnalyzing: true })

    // 获取选中的症状
    const selectedSymptom = filteredSymptoms[selectedIndex]

    // 埋点：症状选择
    const symptomId = selectedSymptom.symptom_id || selectedSymptom.id || ''
    const symptomName = selectedSymptom.symptom_name || selectedSymptom.name || ''
    const emoji = selectedSymptom.emoji || ''
    trackEvent('symptom_select', { symptom_id: symptomId, symptom_name: symptomName })

    wx.navigateTo({
      url: `/pages/petinfo/petinfo?symptom_id=${encodeURIComponent(symptomId)}&symptom_name=${encodeURIComponent(symptomName)}&emoji=${encodeURIComponent(emoji)}`,
      fail: (err) => {
        console.error('跳转宠物信息页失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none',
        })
        this.setData({ isAnalyzing: false })
      },
    })
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 从其他页面返回时重置状态
    this.setData({
      selectedIndex: null,
      isAnalyzing: false,
    })
  },
})
