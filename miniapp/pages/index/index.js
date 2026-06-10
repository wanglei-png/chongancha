// pages/index/index.js
const api = require('../../utils/api')
const { trackEvent, reportPageView } = require('../../utils/analytics')

Page({

  /**
   * 页面的初始数据
   */
  data: {
    // 症状搜索相关
    symptoms: [],           // 全部症状列表（缓存）
    searchValue: '',        // 搜索框输入值
    searchResults: [],      // 过滤后的搜索结果
    showDropdown: false,    // 是否显示下拉列表
    searchFocused: false,   // 搜索框是否聚焦
    searchFocus: false,     // 控制 input focus 属性
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad() {
    reportPageView('index')
    this.fetchAllSymptoms()
  },

  /**
   * 从后端获取全部症状列表
   */
  fetchAllSymptoms() {
    api.get('/symptoms')
      .then((res) => {
        // 后端返回格式：{ symptoms: [...] } 或直接数组
        const symptoms = Array.isArray(res) ? res : (res.symptoms || [])
        this.setData({ symptoms })
      })
      .catch((err) => {
        console.error('获取症状列表失败:', err)
        // 静默失败，搜索功能不可用但不影响页面其他功能
      })
  },

  /**
   * 搜索框输入事件
   */
  onSearchInput(e) {
    const value = e.detail.value
    this.setData({ searchValue: value })

    if (value.trim() === '') {
      this.setData({
        searchResults: [],
        showDropdown: false,
      })
      return
    }

    // 本地过滤匹配：symptom_name 包含输入关键词（不区分大小写）
    // 排除 pending 状态的症状
    const keyword = value.trim().toLowerCase()
    const { symptoms } = this.data
    const results = symptoms.filter((item) => {
      // 跳过 pending 状态的症状
      if (item.audit_status === 'pending') return false
      const name = (item.symptom_name || item.name || '').toLowerCase()
      return name.includes(keyword)
    })

    // 最多显示 5 条
    this.setData({
      searchResults: results.slice(0, 5),
      showDropdown: true,
    })
  },

  /**
   * 搜索框聚焦事件
   */
  onSearchFocus() {
    this.setData({ searchFocused: true })
    // 如果有输入内容，显示下拉列表
    if (this.data.searchValue.trim() !== '') {
      this.setData({ showDropdown: true })
    }
  },

  /**
   * 搜索框失焦事件
   */
  onSearchBlur() {
    this.setData({ searchFocused: false })
    // 延迟隐藏下拉列表，让点击事件有机会触发
    setTimeout(() => {
      this.setData({ showDropdown: false })
    }, 200)
  },

  /**
   * 清除搜索框内容
   */
  onClearSearch() {
    this.setData({
      searchValue: '',
      searchResults: [],
      showDropdown: false,
    })
  },

  /**
   * 选择搜索匹配的症状
   */
  onSelectSymptom(e) {
    const dataset = e.currentTarget.dataset
    const symptomId = dataset.symptomId || ''
    const symptomName = dataset.symptomName || ''
    const emoji = dataset.emoji || ''

    // 埋点：症状选择
    trackEvent('symptom_select', { symptom_id: symptomId, symptom_name: symptomName })

    // 隐藏下拉列表
    this.setData({
      showDropdown: false,
      searchValue: '',
      searchResults: [],
    })

    // 跳转到 petinfo 页面，携带参数格式与症状选择页一致
    wx.navigateTo({
      url: `/pages/petinfo/petinfo?symptom_id=${encodeURIComponent(symptomId)}&symptom_name=${encodeURIComponent(symptomName)}&emoji=${encodeURIComponent(emoji)}`,
      fail: (err) => {
        console.error('跳转宠物信息页失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none',
        })
      },
    })
  },

  /**
   * 点击主按钮 - 跳转到症状选择页
   */
  goSymptom() {
    wx.navigateTo({
      url: '/pages/symptom/symptom',
      fail: (err) => {
        console.error('跳转症状页失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none',
        })
      }
    })
  },

  /**
   * 点击"我的" - 跳转到个人中心
   */
  goProfile() {
    wx.navigateTo({
      url: '/pages/profile/profile',
      fail: (err) => {
        console.error('跳转个人中心失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none',
        })
      }
    })
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {},

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {},

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {},

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {},

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {},

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {},

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    // 埋点：分享点击
    trackEvent('share_click', { page: 'index' })
  }
})
