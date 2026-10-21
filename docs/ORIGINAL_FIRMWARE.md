# 原厂固件、图像与备份介绍

更新日期：2026-10-21。以下地址只对应本仓库保存的原厂镜像，不能作为其他固件版本或当前自制程序的固定地址。地址表使用清除 Thumb 最低位后的指令地址；函数指针通常带最低位 1。

## 1. Flash 与内存布局

| 地址 / 区间 | 发现 | 证据边界 |
|---|---|---|
| `0x00000000..0x00000BFF` | 原厂启动区 | 启动向量和代码分析 |
| `0x00000000` | 启动向量，初始 SP=`0x20002060`，Reset=`0x00000AA0` | 镜像解析与直接复位停机 |
| `0x00000C00` | 应用向量，初始 SP=`0x20004D88`，Reset=`0x000118BC` | 镜像解析 |
| `0x0001194C` / `0x00011974` | main / 主循环 | 调用关系和运行观察 |
| 至约 `0x00014443` | 程序和只读数据 | 静态估计，不是完整链接 map |
| `0x00014444..0x0001453B` | 初始化数据的 Flash 载入区 | 启动代码分析 |
| `0x00019C00..0x0001B32F` | 已还原的 5936 字节条码与红图标 | 数据解码与原图对照 |
| `0x00030C00..0x00034FFF` 附近 | `LG01` 标记及其他图像样式数据 | 尚未全部解码 |
| `0x0003F800..0x0003F8FF` | 原厂参数区域 | 运行前后比较；完整字段定义未知 |
| `0x20000000..0x20007FFF` | SRAM 地址范围 | 已保存完整 32 KiB 快照 |

空白 `FF` 区域不能直接认定为可自由覆盖：原厂可能将它作为图像库、升级或预留空间。当前自制固件从地址 0 启动，其 Scatter 预留应用范围为 `0..0x17FFF`；下载脚本实际只擦写当前镜像所需的行，并校验其余 Flash 未改变。这与原厂应用从 `0xC00` 启动的布局不同。

## 2. 关键函数入口

| 功能 | 原厂地址 |
|---|---|
| 屏幕对象创建 | `0x00000D6C` |
| 屏幕初始化 | `0x00001A64` |
| 屏幕命令 / 数据 | `0x000014BC` / `0x00001508` |
| 屏幕刷新 | `0x00001820` |
| GPIO 双向屏幕读事务 | `0x00001830` |
| 屏幕 SERCOM3 SPI 初始化 | `0x000052B8` |
| 原厂图像色彩转换 | `0x00007144` |
| NFC 初始化 | `0x00004594` |
| NFC 块读 / 块写 | `0x000044B8` / `0x000044D4` |
| NFC 底层 I²C 读 | `0x0000421C` |
| UART 初始化 | `0x00005774` |
| 可选 SPI NOR 初始化 / 读数据 | `0x00005104` / `0x000097D4` |
| GPIO 写 / 输入读 | `0x00004000` / `0x00004054` |

这些入口可用于理解原厂调用关系；块写入口存在不表示本轮额外调用了 NFC 写入。早期断点捕获仅使用硬件断点，没有把 Python 程序下载到 MCU，也没有向原厂 RAM 注入执行代码。

## 3. 已还原的屏幕图像

![原厂资源解码：条码与红色图标](investigation_history/original_screen_recovered_4x.png)

这是 Flash 数据解码结果，不是实物拍照，也不是重新绘制的示意图。

| 格式 | 值 |
|---|---|
| Flash 起点 | `0x19C00` |
| 长度 | 5936 字节 |
| 存储尺寸 | 104×212 |
| 像素 | 2 bpp，每字节 4 像素，高位先出 |
| 行跨度 | 28 字节：26 字节有效像素，加 2 字节填充 |
| 原厂颜色编码 | 0 黑、1 黑、2 红、3 白 |
| LUT 位置 | RAM `0x20000036`、`0x20000042`，与 `0x7144` 转换函数对应 |
| 历史预览 | 原存储坐标逆时针 90° 得到横向 212×104 |

原厂 2 bpp 存储的 5936 字节包含行填充；它不同于当前直接传输的两个 1 bpp 平面共 5512 字节。当前示例又根据用户确认的外壳方向旋转了 180°，不能把历史解码预览方向直接当作实物安装方向。

原数据：[original_screen_resource_2bpp.bin](investigation_history/original_screen_resource_2bpp.bin)。预览：[原尺寸](investigation_history/original_screen_recovered_212x104.png) / [4 倍整数放大](investigation_history/original_screen_recovered_4x.png)。其他布局和可能的字库未全部解码；没有把数据区误反汇编出来的字符串当成已识别字库。

## 4. 启动捕获与设备标识

原厂一次成功启动捕获包括屏幕对象型号配置 1、NFC 块 0 成功读取、NDEF 初始化结束，以及屏幕命令 `06 → 04 → 00 → 61 → 50 → 10 → 13 → 12`。温度相关 `0x40` 事务走独立 GPIO 函数，未经过同一个命令断点。

NFC UID 为 `04 16 9A 6A 1E 44 80`；EUI-64 / NDEF MAC 文本为 `FCC23DFFFED0E342`，RAM `0x20000228` 中以小端保存。它们是本块板的实际标识，不是所有同型号板的固定值。原厂检测 NFC 的标志位曾在 `0x2000011A` 观察为 1；屏幕 `0x40` 读回结果曾保存于 `0x20002A2A`。

详细过程在 [original_boot_trace.json](investigation_history/original_boot_trace.json)。采集在发送刷新命令处结束断点观察后让原程序继续运行，未以逐字节停机方式抓全部图像数据，也未用外部逻辑分析仪记录总线。

## 5. 备份文件与校验

| 文件 | 用途 |
|---|---|
| `original_flash_256KiB_read1.bin` / `original_flash_256KiB_read2.bin` | 两次初始完整 Flash 读取，逐字节一致 |
| `original_flash_postdebug_256KiB.bin` | 原厂运行探测后的完整 Flash，用于区分参数变化 |
| `original_sram_snapshot_32KiB.bin` / `original_sram_after_trace_32KiB.bin` | 两个阶段的 SRAM 快照 |
| `original_user_row_256B.bin` / `original_user_row_64B.bin` | 用户行备份与其较短读取版本 |
| `original_aux1_256B.bin` / `original_aux3_256B.bin` | 辅助区域备份 |
| `original_cal_8B.bin` / `original_calibration_16B.bin` | 不同长度的校准区域读取 |
| `postdebug_user_row_256B.bin` / `postdebug_aux1_256B.bin` / `postdebug_aux3_256B.bin` | 探测后的辅助区比较 |
| `hardware_snapshot.json` / `hardware_snapshot_running.json` | 初始状态和释放运行后的寄存器；采样阶段不同 |
| `original_firmware_linear_disassembly.asm` | 静态定位辅助，含数据误作指令的内容，不是可编译源码 |
| `backup_manifest.json` / `flash_manifest.json` | 历史分阶段文件清单与哈希 |

以上文件位于 [investigation_history](investigation_history/)。原始完整 Flash 哈希：

```text
023efc81fb12f6bbfec844374120924c8c1e8597ea3e2884af3306df3d8639c8
```

原厂运行前后比较时，程序及初始化数据一致；仅 `0x3F890` 由 `0x1E` 变为 `0x22`。它属于原厂参数区，精确含义未确认，不能直接标为启动次数。辅助区前后读取一致。原厂恢复后再次运行也可能更新该参数，因此固定哈希对应的是初始镜像和烧录后尚未运行的全片校验状态。

## 6. 已完成的编程验证

先在 `0x19C00` 图像行实际擦除、确认 256 字节全 FF，再按 64 字节页写回并校验；随后实际恢复全部 395 个含数据行，启动向量所在行最后写入。全片 1024 行中，其余 629 行原本全 FF，与备份一致，没有重复擦除。

完整 262144 字节回读与原厂镜像逐字节相同；用户行、AUX1、AUX3、校准字节保持一致。复位后命中原厂 main 并观察屏幕刷新命令，用户确认“看到了刷新”。完整恢复测试约 37.3 秒，见[该次 result.json](investigation_history/flash_restore_original/result.json)。

当前自制示例已完成另一次实际下载：镜像 2464 字节、擦写 10 行、完整 Flash 回读通过、未写区域和辅助区保持一致，刷新约 14.98 秒。其 SHA-256：

```text
099e805566d78b11d03a7fd6dbaadf6968f8bb146bc8c6415487e3c0ee07c325
```

以上不代表每种未来故障或“任意损坏状态恢复”的组合都已重测；历史原厂恢复实测和当前自制固件实测分别有独立记录。下载工具仅对普通 Flash 操作，没有整片 DSU 擦除、熔丝改写、锁位修改或 ST-Link 固件升级。

## 7. 现在如何使用

当前工程是 MCU 上的 **Keil C/ARM 汇编程序**；电脑端 Python 只负责 ST-Link 控制和文件校验。当前例程从 AXF 符号定位 `g_status` 和帧缓冲，不沿用上表原厂 RAM 地址。

编译、下载和恢复统一参阅 [Keil 工程说明](../firmware/SAMR21_EPD_Keil/README.md)，日常入口为 `flash.ps1`；原厂恢复使用 `-Action recover`。早期调查脚本保留原始路径和地址，供回溯过程，不作为搬移后已逐项复测的工具。
