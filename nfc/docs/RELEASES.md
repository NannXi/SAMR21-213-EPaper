# Android 发布包与兼容

Android v0.1.4 汇总此前全部应用更新，配套板端固件 v0.1.2；本板用户已确认 v0.1.2 手机上传成功。

## 下载

- [Android v0.1.4 APK](https://github.com/NannXi/SAMR21-213-EPaper/releases/download/v0.1.4/epaper-nfc-v0.1.4-debug.apk)：包含此前全部应用迭代的汇总版。
- 板端固件源代码位于 [`../firmware/`](../firmware/)；配套 v0.1.2 BIN/HEX 随 v0.1.4 Release 提供。

## 哈希与签名

| APK | SHA-256 |
|---|---|
| v0.1.4 APK | `b7cddf0c448169515f5a34b47203571f9801a6b088642ec52b2b9cb93513fb9d` |

APK 使用开发签名。证书 SHA-256：

```text
b798b530ff90aa9e5ab52a83fb5f4613b01988647c206fec0d625a4bc57d848b
```

Release 标记为预发布；目前只有一块目标设备和一次旧版手机端成功反馈，多机兼容、掉电恢复与长期稳定性仍待验证。Release 只放 APK 和配套固件文件，不上传硬件照片和原始资料。
