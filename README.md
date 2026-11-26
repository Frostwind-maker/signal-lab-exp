# 信号与系统实验可视化

项目提供可离线打开的纯 HTML/JavaScript 实验站点，以及原有的 Python/Streamlit 实现。覆盖常见信号、FFT/傅里叶级数、STFT、采样与混叠、相位谱、窗函数、滤波和语音分析。

## 本机打开 HTML 版本

直接双击项目根目录的 `index.html`，即可在新版 Chrome、Edge 或 Firefox 中打开。界面、图表和数值运算所需文件均在仓库中，初次打开后无需安装 Python、npm 或联网。麦克风权限取决于浏览器的安全上下文；如果 `file://` 页面无法请求麦克风，可在项目目录运行：

```powershell
py -m http.server 8000
```

然后访问 <http://localhost:8000>。麦克风音频和导入的录音均在本机浏览器中处理，不会上传。

Plotly.js 本地副本位于 `assets/plotly.min.js`，遵循 MIT 许可，声明见 `assets/THIRD_PARTY_NOTICES.md`。

## 发布到 GitHub Pages（可选）

项目已推送到 [GitHub 仓库](https://github.com/Frostwind-maker/signal-lab-exp)。GitHub Actions 会在每次更新时检查并打包 HTML 文件，打包结果可在 Actions 运行页面的 Artifacts 下载。

若希望获得在线网页，可在仓库 **Settings → Pages → Build and deployment** 中选择 **Deploy from a branch**，设置分支为 `main`、目录为 `/(root)` 并保存。等待 GitHub 启用后，站点地址为：

<https://frostwind-maker.github.io/signal-lab-exp/>

如果选择 **GitHub Actions** 作为 Pages 来源，需先在设置中启用 Pages 并授权 Actions；当前发布令牌无法替仓库所有者修改这一设置。

## Python/Streamlit 版本

如需运行原有 Python 版本，请使用以下步骤。

## 运行环境

- Python 3.10 或更高版本
- Streamlit 1.50 或更高版本（Plotly 图表和浏览器录音控件）
- Plotly 5.24 或更高版本（浏览器端帧动画）
- 浏览器录音需要麦克风权限；语音模块同时支持 WAV 文件导入
- 实时麦克风分析使用运行应用的本机音频输入设备
- Windows PowerShell

## 安装和运行

```powershell
cd D:\python\exp_3
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

应用启动后，在左侧菜单切换实验模块。

完整的模块分区、代码入口和实验实现说明见[项目总文档](./项目总文档.md)。

## 项目结构

```text
app.py                         Streamlit 应用入口
signal_lab/
  ui.py                        页面导航
  core/                        与界面解耦的信号/分析算法
    signals.py                 常见信号生成
    spectrum.py                FFT、幅度谱、相位谱和窗函数
    fourier_series.py          傅里叶级数
    time_frequency.py          STFT
    sampling.py                采样与混叠
    filters.py                 滤波
    audio.py                   语音处理
  screens/                     独立实验页面
  visualization/               图表和动画组件
```

浏览器版入口是 `index.html`，功能逻辑位于 `app.js`，样式位于 `styles.css`。原 Python 版本保留在 `app.py` 和 `signal_lab/`：`core` 层负责纯数值计算，`screens` 组织 Streamlit 页面，`visualization` 负责原有图表。

## 当前状态

HTML 版本包含七个实验模块，使用本地 Plotly.js 绘图；时域动画固定横轴并推进信号函数，语音模块支持浏览器麦克风和本地音频文件。原有 Streamlit 版本仍可按上方步骤运行。页面不提供实验报告模板。

## 测试

```powershell
# 确保在运行应用的同一 Python 环境中先安装依赖
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

`tests\test_app_pages.py` 使用 Streamlit 自带的 `streamlit.testing.v1.AppTest`。
如果编辑器提示该导入无法解析，请在 VS Code 中选择已安装项目依赖的 Python 解释器；
不要用一个解释器安装依赖、再用另一个解释器运行测试。
