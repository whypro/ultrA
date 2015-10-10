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

	值域为：normal, deleted, removed, refreshing

### Photo

* url: 绝对网络资源路径
	
* path: 本地资源路径

* pending: 待下载，True or False

* sha1: SHA-1 值

* blur: 是否为垃圾图片，True or False

* topic: 主题 ObjectId

### Blur
* sha1: SHA-1 值

### Similarity
* topics
* value

## 主要功能
### 相似主题管理
分析所有主题，罗列两个相似主题，显示主题A【标题】、主题A【图片数】，主题B【标题】、主题B【图片数】，【相似度】

#### 相似主题分析算法
获取主题A所有图片的 SHA-1 值数组，与主题B求交集。随后标记 topic 的 similarity_calculated = True

	similarity = 2*len(intersection(TA-IMAGE-SHA1-LIST, TB-IMAGE-SHA1-LIST)) / (len(TA-IMAGE-SHA1-LIST) + len(TB-IMAGE-SHA1-LIST))

#### 相似度计算时机
* 保存爬取到的主题时，遍历所有主题，计算相似度，如果 > 0 则放入 relevant 集合，并标记该 topic 的 similarity_calculated = True。
* 标记垃圾图片时，将所有与之相关的 topic 标记为 similarity_calculated = False
* 手动运行

### 垃圾主题管理
标记垃圾图片，垃圾图片在主题中不显示，列表显示主题的【纯净度】。

	purity = (len(topic['photos']) - len(blurs)) / len(topic['photos'])

<!--
#### 纯净度计算时机
* 保存爬取到的主题时
* 手动运行
* 标记垃圾图片时

当【纯净度】为 0 时，删除主题（removed）。
-->


### 删除主题
删除可以通过以下方式：

* type = hide, status -> hidden: 隐藏（标记）
	* 标记为已隐藏
	* 保留 photos 集合所对应的记录
	* 保留 topics 集合的 photos 字段
	* 保留文件

* type = delete, status -> deleted: 逻辑删除（保留文件）
	* 标记为已删除
	* 删除 photos 集合所对应的记录
	* 删除 topics 集合的 photos 字段
	* 保留文件
* type = remove, status -> removed: 物理删除（释放空间）
	* 标记为已移除
	* 删除 photos 集合所对应的记录
	* 清空 topics 集合的 photos 字段
	* 删除文件
* type = refresh, status -> refreshing: 刷新（如果需要重新爬取时可使用该方式）
	* 标记为正在刷新（优先爬取）
	* 删除 photos 集合所对应的记录
	* 清空 topics 集合的 photos 字段
* type = wipe, 完全删除
	* 删除 photos 集合中对应的记录
	* 删除 topics 集合中对应的记录

