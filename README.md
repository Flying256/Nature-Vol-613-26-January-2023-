# Nature 613 复现仓库

本仓库用于复现 **Nature 613, 26 January 2023** 论文：

> Burés, Larrosa, *Organic reaction mechanism classification using machine learning*

仓库内容以 **Nature 613** 为唯一范围，包含复现脚本、评估工具、结果图、复现报告，以及官方资源下载说明。  
**Science 378** 的复现内容没有放进这个仓库。

## 仓库内容

- `src/`：评估与资源管理相关的可复用代码。
- `scripts/`：官方资源下载说明、解包、预测、评估、训练保护入口、报告生成等脚本。
- `manifests/official_resources.yml`：官方资源的 DOI、Figshare 页面、直链、文件名、大小和校验信息。
- `artifacts/evaluation/`：官方预训练模型评估得到的小型 CSV 汇总和混淆矩阵。
- `outputs/report_assets/`：复现报告使用的图表和小型结果文件。
- `outputs/Nature613_复现报告_按参考格式重排.docx`：中文复现报告。

## 不直接随仓库分发的内容

以下内容刻意没有提交到 git：

- 官方 `AI_model_and_files.zip`
- 官方 `M1_M20_train_val_test_set.zip`
- 官方解压后的大体积数据和测试集
- 官方 `.h5` 权重
- 本地完整训练日志
- 本地虚拟环境
- 本次重训得到的 `M1_20_model.keras`

这样做的原因是：

- 官方大资源应从原 DOI / Figshare 获取，而不是从本仓库二次分发。
- 重训权重适合作为单独 Release 资产，不进入 git 历史。

## Release

本次本机 GPU 重训得到的权重已经作为 Release 资产上传：

- Release 页面：  
  [Nature 613 retrained model weights](https://github.com/Flying256/Nature-Vol-613-26-January-2023-/releases/tag/nature613-retrained-2026-06-03)
- 权重直链：  
  [M1_20_model.keras](https://github.com/Flying256/Nature-Vol-613-26-January-2023-/releases/download/nature613-retrained-2026-06-03/M1_20_model.keras)

权重文件信息：

- 文件名：`M1_20_model.keras`
- 大小：`6,970,602 bytes`
- 对应 tag：`nature613-retrained-2026-06-03`

## 官方资源获取

官方资源请从原始 DOI / Figshare 获取：

- Trained AI model and associated files：`10.48420/16965271`
- Training, validation and test set for M1-M20：`10.48420/16965292`

仓库里已经保留了下载说明和 manifest。先查看说明：

```powershell
python scripts/download_or_explain.py
```

如果想尝试命令行直接下载：

```powershell
python scripts/download_or_explain.py --attempt
```

如果自动下载失败，就按脚本输出的信息去浏览器打开原页面，手动下载后放到：

```text
official/AI_model_and_files.zip
official/M1_M20_train_val_test_set.zip
```

然后解包：

```powershell
python scripts/unpack_official_archives.py
```

## 复现结果摘要

本地完整训练结果如下：

- 最终停止 epoch：`1931`
- early stopping 恢复权重：`epoch 1631`
- 最佳验证准确率：`0.8193`
- 最佳验证损失：`0.4544`
- 本次测试分支：`standard_tp20_noise1`
- 本次重训 Top-1：`0.892090`
- 本次重训 Top-3：`0.995580`
- 本次重训 99% grouped accuracy：`0.998390`

同一 `standard_tp20_noise1` 分支下，官方预训练模型在本仓库里的复核结果为：

- 官方 Top-1：`0.891460`
- 官方 Top-3：`0.995430`
- 官方 99% grouped accuracy：`0.998350`

本地复现记录中，与论文核心标准分支对应的是 `tp6_noise0`，官方预训练模型在该分支上的结果为：

- Top-1：`0.926390`
- Top-3：`1.000000`
- 99% grouped accuracy：`0.999620`

不同测试分支不能直接硬比，所以 README 和报告里都把“同分支比较”和“论文核心分支比较”分开写了。

## 使用 Release 权重评估

下载上面的 `M1_20_model.keras` 后，将它放在仓库根目录。

在官方测试资源下载并解包完成后，可以这样评估重训权重：

```powershell
python scripts/predict_test_set.py `
  --model M1_20_model.keras `
  --data-dir official/test_subset `
  --output-probabilities outputs/report_assets/retrained_test_probabilities.npy `
  --output-labels outputs/report_assets/retrained_test_labels.npy
```

然后重新生成评估图和汇总：

```powershell
python scripts/make_repro_eval_assets.py
```

## 训练方式

训练入口做了保护，避免误触发长时间 GPU 任务。明确允许训练后再执行：

```powershell
$env:NATURE613_ALLOW_TRAINING = "1"
python scripts/train_entrypoint.py --train-script official/AI_model_and_files/train.py
```

本地 WSL 实际训练使用的是：

```powershell
wsl.exe --% -d Ubuntu-24.04 -- bash -lc "cd /mnt/d/复现/nature613_repro; . .venv-wsl-tf/bin/activate; export NATURE613_ALLOW_TRAINING=1; python -u official/AI_model_and_files/train.py"
```

## 说明

这个仓库只放 Nature 613 复现内容。  
Science 378 相关内容已明确排除，不会上传到这里。
