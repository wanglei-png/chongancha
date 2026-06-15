// pages/petinfo/petinfo.js
const api = require('../../utils/api')
const { reportPageView } = require('../../utils/analytics')


// 品种数据：猫/狗 → 分类 → 具体品种
const BREED_DATA = {
  '猫': {
    '常见家猫': ['中华田园猫', '英国短毛猫', '美国短毛猫', '布偶猫', '暹罗猫', '波斯猫', '缅因猫', '苏格兰折耳猫', '金吉拉', '无毛猫'],
    '稀有品种': ['孟加拉豹猫', '阿比西尼亚猫', '俄罗斯蓝猫', '挪威森林猫', '德文卷毛猫', '斯芬克斯猫', '伯曼猫', '土耳其梵猫']
  },
  '狗': {
    '小型犬': ['泰迪/贵宾', '比熊犬', '博美犬', '吉娃娃', '约克夏', '马尔济斯', '蝴蝶犬', '西施犬'],
    '中型犬': ['柯基犬', '柴犬', '哈士奇', '边牧', '萨摩耶', '法斗', '英斗', '松狮犬'],
    '大型犬': ['金毛', '拉布拉多', '德牧', '阿拉斯加', '秋田犬', '杜宾犬', '罗威纳', '圣伯纳'],
    '超大型犬': ['大丹犬', '藏獒', '纽芬兰犬', '爱尔兰猎狼犬']
  }
}

// 常见品种快捷列表（按物种）
const QUICK_BREEDS = {
  '猫': ['中华田园猫', '英国短毛猫', '布偶猫', '暹罗猫', '缅因猫'],
  '狗': ['泰迪/贵宾', '柯基犬', '柴犬', '金毛', '哈士奇']
}

Page({

  /**
   * 页面的初始数据
   */
  data: {
    // 从症状页传入的参数
    symptom_id: '',
    symptom_name: '',
    emoji: '',

    // 编辑模式（旧：从个人中心通过本地缓存编辑）
    editMode: false,
    editIndex: -1,

    // 来源页面：'symptom'（症状选择进入）或 'profile'（个人中心进入）
    fromPage: 'symptom',
    // 编辑模式时使用（从个人中心通过 API 编辑）
    petId: null,
    // 按钮文字
    buttonText: '确认并生成指引',

    // 宠物名称
    petName: '',

    // 品种 - 三级联动
    speciesList: ['猫', '狗'],
    speciesIndex: -1,
    breedCategoryList: [],
    breedCategoryIndex: -1,
    breedList: [],
    breedIndex: -1,
    quickBreeds: [],
    quickBreedIndex: -1,

    // 年龄
    ageStageList: ['幼年', '成年', '老年'],
    ageStageIndex: -1,
    ageDetail: '',

    // 体重
    weight: '',
    weightUnit: 'kg'
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    reportPageView('petinfo')

    // 接收从症状页传来的参数
    if (options.symptom_id) {
      this.setData({ symptom_id: decodeURIComponent(options.symptom_id) })
    }
    if (options.symptom_name) {
      this.setData({ symptom_name: decodeURIComponent(options.symptom_name) })
    }
    if (options.emoji) {
      this.setData({ emoji: decodeURIComponent(options.emoji) })
    }

    // 来源页面
    const from = options.from || 'symptom'
    const petId = options.pet_id || null

    // 按钮文字
    let buttonText = '确认并生成指引'
    if (from === 'profile') {
      buttonText = petId ? '保存修改' : '保存宠物档案'
    }

    this.setData({
      fromPage: from,
      petId: petId,
      buttonText: buttonText,
    })

    // 编辑模式：从个人中心传入（旧方式，通过本地缓存）
    if (options.edit !== undefined) {
      const editIndex = parseInt(options.edit)
      this.setData({
        editMode: true,
        editIndex: editIndex,
        fromPage: 'profile',
        buttonText: '保存修改',
      })

      // 预填宠物信息
      if (options.petInfo) {
        try {
          const pet = JSON.parse(decodeURIComponent(options.petInfo))
          this.fillPetInfo(pet)
        } catch (e) {
          console.error('解析宠物信息失败：', e)
        }
      }
    }

    // 编辑模式：通过 API 加载宠物数据
    if (petId) {
      this.loadPetDetail(petId)
    }
  },

  /**
   * 通过 API 加载宠物详情
   */
  loadPetDetail(petId) {
    api.get(`/pets/${petId}`).then(res => {
      const data = {}

      // 宠物名称
      if (res.name) data.petName = res.name

      // 品种
      if (res.species) {
        const speciesMap = { 'cat': '猫', 'dog': '狗' }
        const species = speciesMap[res.species] || res.species
        const speciesIndex = this.data.speciesList.indexOf(species)
        if (speciesIndex > -1) {
          data.speciesIndex = speciesIndex
          const categories = Object.keys(BREED_DATA[species] || {})
          data.breedCategoryList = categories
          data.quickBreeds = QUICK_BREEDS[species] || []

          if (res.breed) {
            for (let i = 0; i < categories.length; i++) {
              const breeds = BREED_DATA[species][categories[i]]
              const bi = breeds.indexOf(res.breed)
              if (bi > -1) {
                data.breedCategoryIndex = i
                data.breedList = breeds
                data.breedIndex = bi
                break
              }
            }
          }
        }
      }

      // 年龄
      if (res.age_type) {
        const ageMap = { 'baby': '幼年', 'adult': '成年', 'senior': '老年' }
        const ageStage = ageMap[res.age_type] || res.age_type
        const ageStageIndex = this.data.ageStageList.indexOf(ageStage)
        if (ageStageIndex > -1) data.ageStageIndex = ageStageIndex
      }
      if (res.age_months) {
        data.ageDetail = String(res.age_months)
      }

      // 体重
      if (res.weight) {
        data.weight = String(res.weight)
      }
      if (res.weight_unit) {
        data.weightUnit = res.weight_unit
      }

      this.setData(data)
    }).catch(err => {
      console.error('加载宠物详情失败：', err)
      wx.showToast({
        title: '加载宠物信息失败',
        icon: 'none',
      })
    })
  },

  /**
   * 预填宠物信息到表单（编辑模式 - 旧方式）
   */
  fillPetInfo(pet) {
    const data = {}

    // 品种
    if (pet.species) {
      const speciesIndex = this.data.speciesList.indexOf(pet.species)
      if (speciesIndex > -1) {
        data.speciesIndex = speciesIndex
        const categories = Object.keys(BREED_DATA[pet.species] || {})
        data.breedCategoryList = categories
        data.quickBreeds = QUICK_BREEDS[pet.species] || []

        if (pet.breed) {
          // 查找品种对应的分类和索引
          for (let i = 0; i < categories.length; i++) {
            const breeds = BREED_DATA[pet.species][categories[i]]
            const bi = breeds.indexOf(pet.breed)
            if (bi > -1) {
              data.breedCategoryIndex = i
              data.breedList = breeds
              data.breedIndex = bi
              break
            }
          }
        }
      }
    }

    // 年龄
    if (pet.ageStage) {
      const ageStageIndex = this.data.ageStageList.indexOf(pet.ageStage)
      if (ageStageIndex > -1) {
        data.ageStageIndex = ageStageIndex
      }
    }
    if (pet.ageDetail) {
      data.ageDetail = pet.ageDetail
    }

    // 体重
    if (pet.weight) {
      // 尝试分离数字和单位
      const match = pet.weight.match(/^([\d.]+)(kg|斤)?$/)
      if (match) {
        data.weight = match[1]
        if (match[2]) data.weightUnit = match[2]
      } else {
        data.weight = pet.weight
      }
    }

    this.setData(data)
  },

  /**
   * 选择物种（猫/狗）
   */
  onSpeciesChange(e) {
    const index = parseInt(e.detail.value)
    const species = this.data.speciesList[index]
    const categories = Object.keys(BREED_DATA[species] || {})

    this.setData({
      speciesIndex: index,
      breedCategoryList: categories,
      breedCategoryIndex: -1,
      breedList: [],
      breedIndex: -1,
      quickBreeds: QUICK_BREEDS[species] || [],
      quickBreedIndex: -1
    })
  },

  /**
   * 选择品种分类
   */
  onBreedCategoryChange(e) {
    const index = parseInt(e.detail.value)
    const species = this.data.speciesList[this.data.speciesIndex]
    const category = this.data.breedCategoryList[index]
    const breeds = BREED_DATA[species][category] || []

    this.setData({
      breedCategoryIndex: index,
      breedList: breeds,
      breedIndex: -1,
      quickBreedIndex: -1
    })
  },

  /**
   * 选择具体品种
   */
  onBreedChange(e) {
    const index = parseInt(e.detail.value)
    this.setData({
      breedIndex: index,
      quickBreedIndex: -1
    })
  },

  /**
   * 快捷选择常见品种
   */
  onQuickBreed(e) {
    const { index } = e.currentTarget.dataset
    const breedName = this.data.quickBreeds[index]

    // 查找该品种对应的分类和索引
    const species = this.data.speciesList[this.data.speciesIndex]
    const categories = Object.keys(BREED_DATA[species])

    let foundCategoryIndex = -1
    let foundBreedIndex = -1

    for (let i = 0; i < categories.length; i++) {
      const breeds = BREED_DATA[species][categories[i]]
      const bi = breeds.indexOf(breedName)
      if (bi > -1) {
        foundCategoryIndex = i
        foundBreedIndex = bi
        break
      }
    }

    if (foundCategoryIndex > -1 && foundBreedIndex > -1) {
      this.setData({
        breedCategoryIndex: foundCategoryIndex,
        breedList: BREED_DATA[species][categories[foundCategoryIndex]],
        breedIndex: foundBreedIndex,
        quickBreedIndex: index
      })
    }
  },

  /**
   * 选择年龄段
   */
  onAgeStageChange(e) {
    const index = parseInt(e.detail.value)
    this.setData({ ageStageIndex: index })
  },

  /**
   * 输入具体年龄
   */
  onAgeDetailInput(e) {
    this.setData({ ageDetail: e.detail.value })
  },

  /**
   * 输入宠物名称
   */
  onPetNameInput(e) {
    this.setData({ petName: e.detail.value })
  },

  /**
   * 输入体重
   */
  onWeightInput(e) {
    this.setData({ weight: e.detail.value })
  },

  /**
   * 切换体重单位
   */
  onWeightUnitChange(e) {
    const { unit } = e.currentTarget.dataset
    this.setData({ weightUnit: unit })
  },

  /**
   * 组装宠物信息
   */
  buildPetInfo() {
    const { petName, speciesIndex, speciesList, breedIndex, breedList, ageStageIndex, ageStageList, ageDetail, weight, weightUnit } = this.data

    const info = {}
    if (petName) info.petName = petName
    if (speciesIndex > -1) info.species = speciesList[speciesIndex]
    if (breedIndex > -1) info.breed = breedList[breedIndex]
    if (ageStageIndex > -1) info.ageStage = ageStageList[ageStageIndex]
    if (ageDetail) info.ageDetail = ageDetail
    if (weight) info.weight = weight + weightUnit

    return info
  },

  /**
   * 跳转到结果页
   */
  goToResult(petInfo) {
    const { symptom_id, symptom_name, emoji } = this.data
    const params = []
    if (symptom_id) params.push(`symptom_id=${encodeURIComponent(symptom_id)}`)
    if (symptom_name) params.push(`symptom_name=${encodeURIComponent(symptom_name)}`)
    if (emoji) params.push(`emoji=${encodeURIComponent(emoji)}`)
    if (petInfo && Object.keys(petInfo).length > 0) {
      params.push(`petInfo=${encodeURIComponent(JSON.stringify(petInfo))}`)
    }

    wx.navigateTo({
      url: `/pages/result/result?${params.join('&')}`,
      fail: (err) => {
        console.error('跳转结果页失败：', err)
        wx.showToast({
          title: '页面加载失败',
          icon: 'none'
        })
      }
    })
  },

  /**
   * 跳过，直接看指引
   */
  onSkip() {
    this.goToResult(null)
  },

  /**
   * 提交按钮 - 根据来源页面执行不同操作
   */
  onSubmit() {
    if (this.data.fromPage === 'profile') {
      this.savePetProfile()
    } else {
      this.onConfirm()
    }
  },

  /**
   * 保存宠物档案到后端 API
   */
  savePetProfile() {
    const { petName, speciesIndex, speciesList, breedIndex, breedList, ageStageIndex, ageStageList, ageDetail, weight, weightUnit, petId } = this.data

    // 验证必填字段
    if (speciesIndex === -1) {
      wx.showToast({ title: '请选择宠物品种', icon: 'none' })
      return
    }
    if (breedIndex === -1) {
      wx.showToast({ title: '请选择具体品种', icon: 'none' })
      return
    }

    // 映射中文品种为后端枚举值
    const speciesMap = { '猫': 'cat', '狗': 'dog' }
    const ageMap = { '幼年': 'baby', '成年': 'adult', '老年': 'senior' }

    const petData = {
      name: petName || '宠物',
      species: speciesMap[speciesList[speciesIndex]] || speciesList[speciesIndex],
      breed: breedList[breedIndex],
      age_type: ageMap[ageStageList[ageStageIndex]] || 'adult',
      age_months: ageDetail ? parseInt(ageDetail) : null,
      weight: weight ? parseFloat(weight) : null,
      weight_unit: weightUnit || 'kg',
    }

    const apiCall = petId
      ? api.put(`/pets/${petId}`, petData)
      : api.post('/pets', petData)

    wx.showLoading({ title: '保存中...' })

    apiCall.then(() => {
      wx.hideLoading()
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    }).catch(err => {
      wx.hideLoading()
      console.error('保存宠物档案失败：', err)
      wx.showToast({ title: '保存失败，请重试', icon: 'none' })
    })
  },

  /**
   * 确认并生成指引 / 保存宠物档案（旧方式）
   */
  onConfirm() {
    const petInfo = this.buildPetInfo()
    const { editMode, editIndex } = this.data

    if (editMode) {
      // 编辑模式：保存到 petList 并返回个人中心
      let petList = wx.getStorageSync('petList') || []
      if (editIndex > -1 && editIndex < petList.length) {
        petList[editIndex] = petInfo
      } else {
        petList.push(petInfo)
      }
      wx.setStorageSync('petList', petList)
      wx.showToast({
        title: '保存成功',
        icon: 'success',
        duration: 1500
      })
      setTimeout(() => {
        wx.navigateBack({ delta: 1 })
      }, 1500)
    } else {
      // 正常模式：跳转到结果页
      this.goToResult(petInfo)
    }
  },
})
