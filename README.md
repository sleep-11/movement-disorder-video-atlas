# 运动障碍视频图谱

按章节序号浏览并播放视频的静态网页。使用浏览器原生播放器，支持手机、电脑、拖动进度和全屏。

网页地址：https://sleep-11.github.io/movement-disorder-video-atlas/

## 文件

- `index.html`、`styles.css`、`app.js`：页面与播放器。
- `library.js`：章节、视频标题、时长和媒体路径。
- `videos/`：适合网页播放的 MP4 副本。
- `scripts/prepare_videos.py`：从上一级文件夹的原始视频生成网页副本和目录。

页面初次打开不会请求视频内容，选择视频后才开始加载。目录保留原编号，包括编号间的空缺。无编号的视频列在补充视频中。

## 本地查看与更新

在此目录执行 `python -m http.server 8765 --bind 127.0.0.1`，然后打开 `http://127.0.0.1:8765`。

视频更新需要 Python、ffmpeg 和 ffprobe，运行 `python scripts/prepare_videos.py`。准备脚本不改动原始视频。检查网页后将更新推送到 `main` 分支，GitHub Pages 会重新发布。

## 托管

使用 GitHub Pages 免费网址。仓库与视频为公开内容。网站受平台容量、流量和可用性限制，不承诺所有网络均可访问。
