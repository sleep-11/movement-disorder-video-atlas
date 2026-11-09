# 临床视频资料：症状学与脑血管 DSA

按章节序号浏览并播放视频的静态网页。使用浏览器原生播放器，支持手机、电脑、拖动进度和全屏。

网页地址：https://sleep-11.github.io/movement-disorder-video-atlas/

脑血管 DSA 独立页面：https://sleep-11.github.io/movement-disorder-video-atlas/dsa.html

“症状学”和“脑血管 DSA”为两个同级专题，在顶部导航切换。症状学保留97段视频及原章节；DSA页面独立呈现9段视频。

## 文件

- `index.html`、`styles.css`、`app.js`：页面与播放器。
- `library.js`：章节、视频标题、时长和媒体路径。
- `videos/`：适合网页播放的 MP4 副本。
- `scripts/prepare_videos.py`：从上一级文件夹的原始视频生成网页副本和目录。
- `dsa.html`、`dsa-library.js`、`dsa-videos/`：DSA独立页面、目录和视频副本。
- `scripts/prepare_dsa.py`：读取上一级 `脑血管dsa` 文件夹，生成无损重封装的网页视频与目录；原始文件不变。现有文件没有描述性名称，按文件名升序编号01–09，不代表临床分类或检查顺序。

页面初次打开不会请求视频内容，选择视频后才开始加载。目录保留原编号，包括编号间的空缺。无编号的视频列在补充视频中。

## 本地查看与更新

在此目录执行 `python -m http.server 8765 --bind 127.0.0.1`，然后打开 `http://127.0.0.1:8765`。

视频更新需要 Python、ffmpeg 和 ffprobe，运行 `python scripts/prepare_videos.py`。准备脚本不改动原始视频。检查网页后将更新推送到 `main` 分支，GitHub Pages 会重新发布。

更新DSA视频使用 `python scripts/prepare_dsa.py`。它独立生成DSA目录，不修改症状学目录。

## 托管

使用 GitHub Pages 免费网址。仓库与视频为公开内容。网站受平台容量、流量和可用性限制，不承诺所有网络均可访问。
