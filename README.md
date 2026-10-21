# SAMR21 2.13 inch e-Paper

LG Innotek ESL TAG2.13B 电子价签的硬件资料、原厂固件探测备份和 Keil5 C/ASM 示例工程。

![默认画面：实际 MCU 帧缓冲回读](firmware/SAMR21_EPD_Keil/demo_preview.png)

当前示例横向 212×104，上半白底黑字 **Hello World**，下半红底白字 **2.13 inch e-Paper**，带小芯片、电池和屏幕图标。每次上电刷新一次。

## 硬件资料入口

| 资源 | 这块板上已知道什么 | 完整介绍 |
|---|---|---|
| 整机与供电 | LG Innotek ESL TAG2.13B Rev0.1，REBE-TZ21B；原两节 CR2430 并联；当前 ST-Link 四线供电调试 | [板卡、损伤、供电与 SWD](docs/HARDWARE.md) |
| 主控 | ATSAMR21G18A，256 KiB Flash、32 KiB SRAM；原厂保护关闭，复位与编程已实测 | [芯片资源及 SERCOM 分工](docs/HARDWARE.md) |
| 屏幕 | WF0213T50CZ16E41e，104×212 / 横向 212×104；SPI 模式 3；引脚和原厂初始化已定位 | [引脚、双向读、命令、边框与偏淡现象](docs/HARDWARE.md) |
| NFC | NXP Type 2 / NTAG I²C 类行为，地址 0x55；UID 和块读已验证，精确型号和手机传图仍待研究 | [NFC 线圈、I²C 接线、容量及限制](docs/HARDWARE.md) |
| 2.4 GHz 无线 | SAMR21 片内 IEEE 802.15.4 射频与板载印刷天线；SERCOM4 内部连接已定位，协议未知 | [内部引脚和无线边界](docs/HARDWARE.md) |
| UART / 存储 / ADC | 115200 UART 代码、可选 SPI NOR 驱动和电源检测线索；各项实测边界分别记录 | [更多接口与未确认项](docs/HARDWARE.md) |
| 原厂固件 | 启动与应用地址、函数入口、原始图像格式、完整备份和实际恢复记录 | [固件与备份详解](docs/ORIGINAL_FIRMWARE.md) |
| 原始实物资料 | 22 张照片、原始说明和离线 DFP 包全部保留，逐项说明用途 | [全部照片与资料索引](docs/PHOTO_INDEX.md) |

硬件文档区分用户观察、静态分析、运行实测和仍未确认的内容。完整 FPC 针序、驱动 IC、NFC 精确料号、射频协议、外置 Flash 是否焊接和动态供电都没有用推测补成确定结论。

## 已验证与待排查

- 主控 ATSAMR21G18A，Cortex-M0+，256 KiB Flash、32 KiB SRAM。
- 屏幕 WF0213T50CZ16E41e，原生 104×212，横置 212×104，黑白红。具体驱动 IC 尚未最终确认。
- Keil ARMCC 5.06 u5 实际编译 0 错误、0 警告，实机烧录后完整 Flash 回读与预期一致，未写区和辅助区一致，约 15 秒完成刷新。
- 用户已确认新版方向正常。**黑字折角偏淡、红底白字发泛仍未解决**，全白清屏后仍存在；屏幕老化尚未确认。
- 原厂固件完整备份与恢复已实测。屏幕外侧混色边缘在白屏、红屏和边框设置实验中均未明显改变。
- NFC、无线和电池低功耗未在自制固件中实现。Keil 内部 FLM 下载与在线调试尚未配置，当前通过 ST-Link 和电脑端 Python 工具下载。

## 快速开始

进入 [Keil 工程](firmware/SAMR21_EPD_Keil/README.md)，打开 `SAMR21_EPD.uvprojx`，使用 ARM Compiler 5 编译。工程附带 CMSIS 和 SAMR21 器件头文件。

```powershell
cd firmware/SAMR21_EPD_Keil
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Tools/requirements.txt
.\flash.ps1 -Action flash
```

`Objects/epd_white.axf/.bin/.hex` 名称沿用最初白屏测试，内容已更新为当前示例。默认探针序列号对应本次实测硬件，可设置 `EPD_PROBE_SERIAL`。本仓库的原厂镜像含本板配置和标识，恢复前应核对硬件。

## 资料位置

| 路径 | 内容 |
|---|---|
| `firmware/SAMR21_EPD_Keil/` | C/ASM 源码、Keil 工程、预编译固件、下载恢复工具和验证记录 |
| `hardware/original_materials/` | 用户整理的原始照片、说明和 Microchip DFP 离线包，文件完整保留 |
| `docs/HARDWARE.md` | 整机、供电、主控、SWD、屏幕、NFC、无线、UART、可选存储、ADC 及全部接口边界 |
| `docs/PHOTO_INDEX.md` | 每张原始照片、说明和器件包的链接及用途 |
| `docs/ORIGINAL_FIRMWARE.md` | 原厂内存布局、函数入口、图像格式、备份文件和恢复验证详解 |
| `docs/DISPLAY_QUALITY.md` | 实物偏淡、方向修正及后续排查记录 |
| `docs/investigation_history/` | 分阶段硬件快照、原厂备份、反汇编、烧录与恢复记录 |
| `tools/investigation_history/` | 早期探测脚本，保留作过程参考 |
| `repository_manifest.json` | 入库文件长度及 SHA-256 |

早期资料中的“尚未烧录自制固件”等表述记录的是当时状态；当前状态以本页及工程 `validation_summary.json` 为准。早期脚本保留本机路径与地址，只供过程参考；日常下载请使用工程内 `flash.ps1`。线性反汇编包含把数据解释为指令的区域，不能当作可编译源码。

Microchip、ARM 文件保留各自版权及许可证。原始照片、第三方器件包和原厂二进制不因收录在本仓库而获得新的授权；本仓库不对这些材料追加统一开源许可证。
