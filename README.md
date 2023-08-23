操作录制脚本比对工具的开发文档
1.	项目背景
为了更方便重复比对输入以及一些繁琐的功能的重复实现而开发出的一款非源码识别的自动化UI工具，以方便开发测试人员对于产品验证的体验

2.	方案选择
尝试过目前开源的github脚本录制工具和selenium（通过html进行操作录制）的工具，发现都不是很好修改和适配成为一款更偏向于开发人员的测试工具，从而尝试使用python的pynput库和tkinterUI制作了一款更灵活，方便增加功能的工具

3.	目录结构、文件、代码模块说明
源文件main.py，通过跑main.py创建config, report, script和test一共4个文件夹config里面需要手动创建一个config.txt来配置全局文件，report里面则是跑完脚本后会自动生成的报告，script里面保存了所有脚本文件，test里面则是包含了测试期望值和脚本对应关系的配置。

project-root/
├── config/            # 全局配置文件夹
│   └── config.txt    # 手动创建的配置文件
├── report/           # 脚本运行后的报告文件夹
├── script/           # 所有脚本文件存储位置
├── test/             # 测试期望值和脚本对应关系的配置
└── main.py       # 主入口文件

main.py: 主程序的入口点，用于初始化和运行整个项目
config/config.txt: 用于存储全局配置信息。

Input Handler: 通过使用pynput库处理用户的输入。
UI Module: 使用tkinter构建的用户界面部分。
Script Manager: 负责管理和执行存储在script/文件夹中的脚本文件。

4.	代码注释详见代码内部
