# SCU 自动打卡
## 需要操作:
1. fork仓库
2. 在setting-screts-actions中添加三个属性:SCU_USERNAME,SCU_PASSWORD,TOKEN
  * SCU_USERNAME: 学号
  * SCU_PASSWORD: 微服务密码(可以去 http://ua.scu.edu.cn/ 验证一下)
  * TOKEN: 在个人账户的Settings - Developer settings - Personal access tokens 中创建新token: 需要的scope为repo
4. 去forked repository - Actions 中打开自动运行功能:
  * Enable autorun
  * Enable keepalive

## 说明
1. 每天的自动打卡大概在凌晨的2点左右, 打卡内容会延续上一次的打卡内容; 需要变更打卡内容时, 请在凌晨手打打卡一次.
2. 所有的属性 - SCU_USERNAME,SCU_PASSWORD,TOKEN 对仓库管理者外的人隐藏
3. 本仓库只为方便学生每天重复打卡, 一切后果由学生自己承担.
