# PTA 比赛滚榜工具生成器



一款自动爬取PTA编程比赛提交记录，并生成ICPC官方滚榜工具兼容XML的解决方案


1. 启动工具之后， 会让你强制配置cookie信息(在pta界面按f12点击应用程序找到cookie一栏并复制下来即可)<br>
![img_3.png](images/img_3.png)<br>
   (1) 保存配置 选择保存地址，会将你的cookie信息保存为json格式<br>
    ![img_2.png](images/img_1.png)<br>
   (2) 加载配置，选择保存的json格式的cookie，即可快捷完成配置
2. 加载cookie信息之后，点击刷新列表(若报错，可能是cookie信息过期，需要重新手动获取)，然后点击想要生成榜单的那场比赛再点击生成xml，即可得到resolver能识别的xml文件<br>
    ![img_1.png](images/img_2.png)

