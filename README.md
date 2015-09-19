# ultrA

## 数据模型

### Topic

* title: 标题  

	可修改（与 path 同步）

* category: 类别

* uri: 相对网络资源路径

* path: 本地资源路径

	与 category 和 title 同步

* create_time: 创建时间

* update_time: 修改时间

* photos: 图片 ObjectId 数组

* click_count: 点击次数

* rating: 评级

* status: 状态

	值域为：normal, deleted, removed

### Photo

* url: 绝对网络资源路径
	
* path: 本地资源路径

* pending: 待下载，True or False

* sha1: SHA-1 值

* blur: 是否为垃圾图片，True or False

* topic: 主题 ObjectId

### Blur
* sha1: SHA-1 值


## 主要功能
### 相似主题管理
分析所有主题，罗列两个相似主题，显示主题A【标题】、主题A【图片数】，主题B【标题】、主题B【图片数】，【相似度】

#### 相似主题分析算法
获取主题A所有图片的 SHA-1 值数组，与主题B求交集。随后标记 topic 的 relevant_scanned = True

relevant = 2*len(intersection(TA-IMAGE-SHA1-LIST, TB-IMAGE-SHA1-LIST)) / (len(TA-IMAGE-SHA1-LIST) + len(TB-IMAGE-SHA1-LIST))

#### 相似度计算时机
保存爬取到的主题时，遍历所有主题，计算相似度放入 relevant 集合，标记该 topic 的 relevant = True。

### 垃圾主题管理
标记垃圾图片，垃圾图片在主题中不显示，列表显示主题的【垃圾度】

#### 垃圾度计算时机
* 保存爬取到的主题时
* 标记垃圾图片时

### 删除主题
删除可以通过以下方式：

* deleted: 逻辑删除
* removed: 物理删除
