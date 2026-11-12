# 信号与系统实验：傅里叶变换动画可视化

基于 Python 和 Streamlit 的模块化实验项目，覆盖常见信号、FFT/傅里叶级数、STFT、采样与混叠，以及相位谱、窗函数、滤波和语音分析拓展。

## 运行环境

- Python 3.10 或更高版本
- Streamlit 1.50 或更高版本（动画 fragment 和浏览器录音控件）
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

页面层负责参数交互和实验流程；`core` 层负责纯数值计算；`visualization` 层负责图表与动画。后续实现时尽量保持层间依赖单向：页面调用算法和绘图组件，算法不依赖 Streamlit。

## 当前状态

时域/频域动画固定横轴并推进信号函数本身；页面不再提供实验报告模板。其余实验页面已接入对应的数值算法和交互控件。语音模块支持本机麦克风连续频谱刷新，以及浏览器录音/WAV 上传后的分帧回放；WAV 支持 8/16/24/32 位 PCM。离开语音页面会停止本机麦克风采集。

## 测试

```powershell
# 确保在运行应用的同一 Python 环境中先安装依赖
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

`tests\test_app_pages.py` 使用 Streamlit 自带的 `streamlit.testing.v1.AppTest`。
如果编辑器提示该导入无法解析，请在 VS Code 中选择已安装项目依赖的 Python 解释器；
不要用一个解释器安装依赖、再用另一个解释器运行测试。
