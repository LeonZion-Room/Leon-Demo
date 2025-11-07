# 背景
- 我是一个 Python 程序员

# 具体需求
- 希望能完成一个 草药图片的分类系统
- 基于 CPU 训练，希望包括 训练推理 | 根据我给出的 path.txt 了解这个文件夹下的数据集和文件情况(只包括必要部分的文件路径)



# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/
- 

---
- 现在 草药分类部分的人工智能代码工作已经完成
- 我希望你基于 streamlit 实现一个简单的网页功能，希望包括
  - 上传图片功能
  - 显示图片功能
  - 显示分类结果功能
  - 上传压缩包，自动解压压缩包，显示压缩包内的图片，点击图片可以查看图片详情，包括 图片路径 | 图片分类结果
  - 希望基于 streamlit help 等组件实现必要的备注和说明

---

使用指南（Windows11 + PowerShell）

1) 初始化虚拟环境与安装依赖（已在本项目中执行过，若需复现）

```
py -m venv .venv
.venv\Scripts\pip install --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/
.venv\Scripts\pip install torch torchvision timm pillow numpy pandas streamlit tqdm -i https://mirrors.aliyun.com/pypi/simple/
```

2) 数据集概要查看（从 `path.txt` 自动解析必要路径）

```
.venv\Scripts\python main.py list --path-txt path.txt
```

3) 训练（CPU，轻量化，默认冻结骨干网络，仅训练分类头）

```
.venv\Scripts\python main.py train --path-txt path.txt --epochs 5 --batch-size 32 --img-size 224 --lr 1e-3 --model-name mobilenetv3_small_100 --val-ratio 0.1 --out-dir models
```

生成的最佳模型保存在 `models\best.pth`，类别文本在 `models\classes.txt`。

4) 推理（对 `Chinese Medicine/infer` 文件夹内图片全部推理并导出 CSV）

```
.venv\Scripts\python main.py infer --path-txt path.txt --checkpoint models\best.pth --out-csv infer_results.csv
```

5) 启动网页（Streamlit）

```
.venv\Scripts\python main.py web
```

网页功能包括：上传单张图片查看分类结果；上传 zip 自动解压并展示图片，点击查看详情（路径与分类结果）；侧边栏可设置模型路径，帮助区提供说明与示例。