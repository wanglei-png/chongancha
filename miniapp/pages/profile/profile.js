// pages/profile/profile.js
const api = require('../../utils/api')
const { reportPageView } = require('../../utils/analytics')

Page({

  /**
   * 页面的初始数据
   */
  data: {
    // 用户信息
    userInfo: {
      avatarUrl: '',
      nickName: ''
    },

    // 宠物列表（从后端 API 加载）
    pets: [],
    isLoading: false,

    // 订阅信息
    subInfo: {
      isActive: false,
      planName: '',
      expireDate: ''
    },

    // 头像加载状态
    avatarLoadFailed: false,

    // 订阅弹窗
    showSubModal: false,
    selectedSub: 'monthly'
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    reportPageView('profile')
    this.loadUserInfo()
    this.loadPets()
    this.loadSubInfo()
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 每次显示时刷新数据
    this.loadPets()
  },

  /**
   * 加载用户信息
   */
  loadUserInfo() {
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.setData({ userInfo })
    }
  },

  /**
   * 从后端 API 加载宠物列表
   */
  loadPets() {
    this.setData({ isLoading: true })
    api.get('/pets').then(res => {
      const pets = Array.isArray(res) ? res : []
      this.setData({ pets, isLoading: false })
    }).catch(err => {
      console.error('加载宠物列表失败：', err)
      // 即使 API 返回空数据错误，也清空列表
      this.setData({ pets: [], isLoading: false })
    })
  },

  /**
   * 加载订阅信息
   */
  loadSubInfo() {
    const subInfo = wx.getStorageSync('subInfo') || {
      isActive: false,
      planName: '',
      expireDate: ''
    }
    this.setData({ subInfo })
  },

  /**
   * 头像加载失败 - 降级显示占位符
   */
  onAvatarError() {
    this.setData({ avatarLoadFailed: true })
  },

  /**
   * 点击用户区域 - 登录/查看个人信息
   */
  onTapUser() {
    const { userInfo } = this.data
    if (!userInfo.nickName) {
      // 未登录，模拟微信登录（不设置头像URL，显示占位符）
      wx.showLoading({ title: '登录中...' })
      setTimeout(() => {
        wx.hideLoading()
        const mockUser = {
          avatarUrl: '',
          nickName: '宠物家长'
        }
        wx.setStorageSync('userInfo', mockUser)
        this.setData({
          userInfo: mockUser,
          avatarLoadFailed: false
        })
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        })
      }, 800)
    } else {
      wx.showToast({
        title: '已登录',
        icon: 'none',
        duration: 1500
      })
    }
  },

  /**
   * 添加宠物 - 跳转到 petinfo 页（来源 profile）
   */
  onAddPet() {
    wx.navigateTo({
      url: '/pages/petinfo/petinfo?from=profile',
      fail: (err) => {
        console.error('跳转添加宠物页失败：', err)
      }
    })
  },

  /**
   * 编辑宠物 - 跳转到 petinfo 页（携带 pet_id）
   */
  onEditPet(e) {
    const petId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/petinfo/petinfo?from=profile&pet_id=${petId}`,
      fail: (err) => {
        console.error('跳转编辑宠物页失败：', err)
      }
    })
  },

  /**
   * 删除宠物
   */
  onDeletePet(e) {
    const petId = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定删除该宠物档案吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' })
          api.del(`/pets/${petId}`).then(() => {
            wx.hideLoading()
            wx.showToast({ title: '删除成功', icon: 'success' })
            this.loadPets()
          }).catch(err => {
            wx.hideLoading()
            console.error('删除宠物失败：', err)
            wx.showToast({ title: '删除失败，请重试', icon: 'none' })
          })
        }
      }
    })
  },

  /**
   * 去订阅 - 弹出订阅选择弹窗
   */
  onTapSubscribe() {
    this.setData({
      showSubModal: true,
      selectedSub: 'monthly'
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
    const expireDate = new Date()
    expireDate.setMonth(expireDate.getMonth() + (selectedSub === 'monthly' ? 1 : 12))
    const pad = (n) => String(n).padStart(2, '0')
    const expireStr = `${expireDate.getFullYear()}-${pad(expireDate.getMonth() + 1)}-${pad(expireDate.getDate())}`

    // 保存订阅信息到缓存
    const subInfo = {
      isActive: true,
      planName: selectedSub === 'monthly' ? '月度会员' : '年度会员',
      expireDate: expireStr
    }
    wx.setStorageSync('subInfo', subInfo)
    this.setData({
      subInfo,
      showSubModal: false
    })

    wx.showToast({
      title: `已开通${planName}`,
      icon: 'success',
      duration: 2000
    })
  },

  /**
   * 点击免责声明
   */
  onTapDisclaimer() {
    wx.navigateTo({
      url: '/pages/disclaimer/disclaimer',
      fail: (err) => {
        console.error('跳转免责声明页失败：', err)
      }
    })
  },

  /**
   * 点击隐私政策
   */
  onTapPrivacy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy',
      fail: (err) => {
        console.error('跳转隐私政策页失败：', err)
      }
    })
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {},

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
  onShareAppMessage() {}
})
