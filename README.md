UI配置：

Start Recording: 开始录制

Stop Recording: 结束录制

Save Events：保存到文件（开始录制再结束录制后保存到文件夹里）

Select and Replay Events File: 直接执行一个文件


Load Config: 加载配置文件

加载完直接点击Play Playlist即可开始播放

Add File to Buffer：脚本加载到缓存区

Remove File from Buffer：脚本移除出缓存区

Number of Times to Play: 重复几次（默认一次，写数字后点击Submit to Playlist即可：缓存区文件*Number of Times to Play放大到最终结算区里）


Remove File from Playlist:脚本移除出结算区

Play Playlist:执行结算区脚本


config配置：

binding: (value1 = ?? value 2 = ??)

该配置文件所需加载的文件（和Add file to Buffer同理）

times: (value = ??)

（number of times to play同理）

value: (expected value1 = ?? expected value2 = ??)

(需要比对的结果）

allowed difference: (value = ??%)

(和value相关，脚本内不含复制的快捷键操作可以写0%)


注意事项：

在回放操作的每一次ctrl+c的操作是都会把复制缓存的内容和期望内容（expected value）进行一次对比

在回放操作时esc即可停止所有功能
