# 接线、编译、烧录与恢复

适用于已记录的 LG Innotek ESL TAG2.13B Rev0.1 / ATSAMR21G18A。本页操作针对本仓库显示示例；手机上传见[NFC 仓库](https://github.com/NannXi/SAMR21-213-NFC)。

## 准备

- Windows、Keil5 与 ARM Compiler 5；本机已验证 ARMCC 5.06 u5 build 528。
- ST-Link，已安装 Windows 驱动；Python 3.10+。
- 已验证供电点的 3.3 V、GND、PA31 SWDIO、PA30 SWCLK。[SWD 照片与端口表](HARDWARE.md)用于辨认位置。

原厂电池为两节 CR2430 并联。BAT_IN 不是已验证的 5 V 输入。核对电源接法，避免把多个电源输出直接并接；不要把封装脚号当成排线针序。

## 构建

在仓库根目录：

```powershell
cd firmware/SAMR21_EPD_Keil
.\build.ps1 -KeilRoot 'D:\12-keil5'
```

将 KeilRoot 换成自己的安装目录；也可在 Keil 打开 `SAMR21_EPD.uvprojx`，选择 ARM Compiler 5 后 F7。工程附带 CMSIS 与器件头文件，输出位于 `Objects/epd_white.axf/.bin/.hex`。

## 配置下载环境

仍在工程目录：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Tools/requirements.txt
$env:EPD_PROBE_SERIAL = '你的ST-Link序列号'
.\flash.ps1 -Action flash
```

工具先双读备份完整 Flash 和辅助区，按 256 字节行擦写、64 字节页写入，向量表最后写，最后核对 256 KiB 全量 Flash 与辅助区。记录写入 `Runs/`。不使用整片擦除或自动解锁。

固件镜像从地址 0 启动；不能按原厂应用的 0xC00 入口直接偏移下载。Keil 原生 FLM/在线调试未配置，当前已验证的是外部 SWD 工具路径。

## 查看状态与测试图

等待上电刷新停止（本板约 15 秒）后：

```powershell
.\flash.ps1 -Action status
.\flash.ps1 -Action demo
```

| Action | 作用 |
|---|---|
| status | 读取本工程 g_status；使用匹配 AXF 定位符号 |
| white / red / pattern | 触发白屏、红屏或测试图刷新 |
| black-border / white-border | 白画面配黑/白细边框 |
| demo | 默认 Hello World 双区画面 |
| recover | 写回本板完整原厂镜像，替换当前自制固件 |

显示动作会改变实物画面；status 也会连接调试器，不能代替完全无干扰的运行观察。若板上运行 NFC 固件，使用 NFC 仓库匹配的 AXF 与工具，不要套用本例程的 RAM 符号。

## 原厂恢复

```powershell
.\flash.ps1 -Action recover
```

恢复镜像包含本块板配置与标识；不是同型号设备的通用镜像。原厂镜像 SHA-256：

```text
023efc81fb12f6bbfec844374120924c8c1e8597ea3e2884af3306df3d8639c8
```

恢复前保留自己的最新备份与本次 Runs 目录；恢复会替换当前程序。原厂运行后可能更新 0x3F890，不能将运行后的哈希变化直接认定为烧录错误。

## 常见问题

| 现象 | 排查 |
|---|---|
| 找不到 ST-Link | 检查驱动、共地、供电、序列号，以及是否被其他调试器占用 |
| Keil 编译器找不到 | 安装 ARM Compiler 5 并核对 KeilRoot；工程不是 STM32 标准库模板 |
| 连接后不启动 | 工具已包含 CRSTEXT 释放与复位停机流程；查看最新 Runs/result.json，不先尝试擦除或解锁 |
| 刷新正常但颜色淡 | 属于已知现象，见[显示质量](DISPLAY_QUALITY.md)，亮度参数不等于屏幕驱动电压 |
| 想用手机传图 | 安装[NFC 仓库](https://github.com/NannXi/SAMR21-213-NFC)配套固件与 APK |

提交故障时附固件哈希、工具版本、接线供电方式及 Runs 中的错误信息。完整 Flash/UID/序列号可能含本板信息，公开前自行检查。
