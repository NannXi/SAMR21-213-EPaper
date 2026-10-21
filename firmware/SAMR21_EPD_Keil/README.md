# SAMR21 2.13 寸墨水屏 Keil5 工程

LG Innotek ESL TAG2.13B Rev0.1 / ATSAMR21G18A / WF0213T50CZ16E41e，横向 212×104，黑白红三色。

MCU 固件由 C 和 ARM 汇编组成，使用 Keil ARMCC 5、CMSIS 和 Microchip 器件头文件。`Tools/*.py` 在电脑上负责 SWD 下载、备份、回读和调试命令。

![从实际 MCU 帧缓冲回读生成的预览](demo_preview.png)

## 当前状态

- 默认画面上半白底黑字 `Hello World`，下半红底白字 `2.13 inch e-Paper`，附芯片、电池、屏幕图标。上下各 52 像素。
- Keil uVision 实际编译 0 错误、0 警告；已实机烧录，完整 256 KiB 回读与预期一致，未写区域和辅助区保持一致。
- 原厂完整恢复已在这块板上实测成功。
- 用户确认最新版方向正常；**黑字折角偏浅、红底白字发泛仍存在**，全白清屏后未明显改善。原因待查，尚不能认定为屏幕老化。
- 可控边框已验证：`0x50=0x37` 加黑细边，`0x77` 恢复白边。外侧混色边缘在各次测试中未改变。

预览由 MCU 的 `g_framebuffer` 回读生成，展示像素布局；显示器上的红白对比度不代表实物墨水屏的反射效果。

## 编译与烧录

打开 `SAMR21_EPD.uvprojx`，选择 ARM Compiler 5，F7 编译。目标采用通用 Cortex-M0+，实际外设定义来自附带的 SAMR21 头文件。尚未配置 Keil 原生 FLM 下载及 Keil 内部在线调试，下载使用已实测的外部 SWD 工具。

命令行编译：

```powershell
.\build.ps1 -KeilRoot 'D:\12-keil5'
```

首次配置电脑端 Python 3.10+ 环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Tools\requirements.txt
.\flash.ps1 -Action flash
.\flash.ps1 -Action status
.\flash.ps1 -Action demo
```

其他动作：`white`、`black-border`、`white-border`、`pattern`、`red`、`recover`。测试动作等待应用空闲后，通过 RAM 命令邮箱触发。

`recover` 恢复本板的完整原厂备份，包含原厂配置和设备标识，不是其他硬件的通用固件。SHA-256：

```text
023efc81fb12f6bbfec844374120924c8c1e8597ea3e2884af3306df3d8639c8
```

默认使用本次实测 ST-Link 序列号，可通过环境变量 `EPD_PROBE_SERIAL` 选择其他探针。`flash.ps1` 优先使用工程内 `.venv`，也兼容本次工作目录的环境。

每次下载前双读备份完整 Flash，并保存辅助区；仅擦写所需的 256 字节行，每个 64 字节页写后校验，向量表所在行最后写入。随后校验完整 Flash 及辅助区。记录保存于 `Runs/`。

生成文件名沿用 `Objects/epd_white.axf/.bin/.hex`，当前内容是上图示例。`APP_STARTUP_COMMAND=6` 为此示例；上电刷新一次，随后等待命令。

## 源码与硬件

| 文件 | 用途 |
|---|---|
| `App/main.c` | SysTick、命令邮箱、错误及运行状态 |
| `App/graphics.c` | 三色帧缓冲、矩形、5×7 点阵字、图标和默认画面 |
| `Drivers/epd.c` | GPIO、软件 SPI 模式 3、BUSY 超时、初始化、传输和断电 |
| `Startup/` | ARMCC 启动汇编、OSC8M 8 MHz 配置 |
| `Device/` | Microchip SAMR21 DFP 2.1.155 头文件和 SVD |
| `CMSIS/` | ARM CMSIS 5.0.1 头文件和原许可证 |
| `Tools/` | 电脑端下载、回读、原厂恢复及依赖 |

图形坐标横向 `(0..211, 0..103)`，控制器坐标 `x=y`、`y=211-x`，对应用户确认的安装方向。两平面各 2756 字节，共 5512 字节 RAM。白色为 1/1，黑色为 0/1，红色为 0/0；没有灰度、抗锯齿或抖动处理。字库当前只包含示例需要的字符，新增文字时应补充 `font[]`。

CS=PA23，SDIO=PA24，SCLK=PA25，BUSY=PA27（低忙），电源使能=PA28，D/C=PB22，RESET=PB23。`0x40` 读取沿用原厂 PA24 双向 GPIO 流程，实读 `0x18`；它作为温度相关读数记录，不作为 IC 身份证据。

`g_status` 包含 magic、stage、error、ticks_ms、command、completed、last_epd_command、busy、busy_wait_ms、refresh_ms、temperature_raw、border、bytes_sent。命令：1 白屏、2 白屏黑边框、3 白屏白边框、4 图案、5 红屏、6 默认示例。主机从 AXF 自动定位 RAM 符号。

屏幕初始化参数来自原厂程序的静态分析和运行捕获，使用原有 OTP 波形，没有加载自定义 LUT 或调整升压电压。具体驱动 IC 尚未最终确认。同类参考：[GxEPD2_213c](https://github.com/ZinggJM/GxEPD2/blob/master/src/epd3c/GxEPD2_213c.cpp)，本项目未复制该库代码。

NFC 传图、无线通信和整机低功耗尚未实现。当前轻睡眠用于保持调试访问。Microchip 和 ARM 文件保留原版权声明；原厂二进制备份不属于本工程原创源码。
