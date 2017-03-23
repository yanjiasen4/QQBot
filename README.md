
# 简介
这是一个课余时间写着玩的QQ机器人项目，基于酷Q框架，需要使用酷Q Pro（付费）的一些功能。  

# 环境
## 开发环境
* 酷Q Pro
* 酷Q Python接口 by [muxiaofei](http://git.oschina.net/muxiaofei/cq_python_sdk)
* Python2.7及相关lib（已包含在python接口包中）
* 可翻墙网络  
## 运行环境
* 酷Q Pro
* 可翻墙网络

# 功能
此机器人主要功能对群使用，尚无个人使用功能
1. 修仙：群员发言/连续发言/熬夜发言的将获得不同的经验奖励，并升至不同的仙人等级。指令  
`.xx`
2. 开车：根据输入指令以及参数，从**yande**或**danbooro**爬取图片（开车）。指令  
`!drive tag`
3. 语音：选择语音库中的一个语音文件发送，根据参数可以选择文件夹。语音文件为本地文件，防止在酷Q/data/record中。指令  
`!idol tag`
4. 记忆：记住键值对，并对你说的话做出自动回复。此功能可以用来当作群表情库、群黑历史库等，记住的关键字只能为文本，值可以是表情。关键字有屏蔽功能，在**ignore.json**中配置。指令  
`!learn key#value`
5. 忘记：忘记通过记忆指令学习的词条，可以设置权限，权限在**admin.json**中配置。指令  
`!forget key`
6. roll：测一测你的运气，指令  
`!roll max`
7. 排行榜： 查看群修仙榜，指令  
`!roll number`
8. 开车推荐：由于开车功能所使用的图库原因，tag要求为英语或日语罗马音，且比较严格，此指令可自动推荐5个tag给乘客。指令  
`!tag`
9. 添加屏蔽关键词：添加关键词到屏蔽列表，所有关键词使用拼音谐音检查。指令  
`!banword keyword`
10. 计算：计算一个数学式子/方程，现在支持四则运算以及乘方^、阶乘!、取余%、积分int{}、微分方程y'=xy+1等。指令  
`!calc exp`
11. 卡尔：体验dota2中祈求者切技能的快感，根据输入的参数(qwe)释放卡尔的技能，发送相应的语音（英文版）。指令  
`!invoke qqq`  
12. 窥屏检测：查看当前群内有谁在窥屏，通过QQ的Share类型消息实现（Share的图片链接需要被通过http访问一次），可以显示窥屏人员的IP和地址。指令  
`!spy`
# 卫星
- [ ] 帮助指令
- [ ] 重构一下代码，特别是读取配置部分，现在太乱，有些还是硬编码在代码中的。
- [ ] 更多的语音库
- [ ] 开车黄图鉴别（据说最近企鹅查的很严？）
- [ ] dota2战绩查询
- [ ] 学习功能扩展：回复自己
- [x] 谁在窥屏（服务器端已经做好）
- [ ] 支持更多种的计算式
# 代码
配置文件未上传，也许后面会整合为统一的一个`config.json`  
[github - QQBot](https://github.com/yanjiasen4/QQBot)
