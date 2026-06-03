# VR身心脑协同训练系统 — 完整技术方案

## 项目背景

大连理工大学大学生创新训练项目：**"虚拟现实（VR）技术支持下的大学生身心脑协同训练系统开发"**

项目三大目标：
1. 选型传感器（身/心/脑），构建数据采集管道，将传感器数据转为AI可读格式
2. 搭建AI智能分析通道，将原始数据转为具体运动方式与强度指导
3. 输出文字说明，解释如何与VR头显结合

---

## 一、系统总体架构

```
                   方案一 (低成本 ~$80)              方案二 (高精度 ~$2,130)
                   ====================            ============================
                   Polar H10 (ECG/HRV)             Polar H10 + Empatica E4 + Muse S
                         |                          |          |          |
                         | BLE                      | BLE      | BLE      | BLE
                         v                          v          v          v
+----------------------------------------------------------------------------+
|                     数据采集层 Lab Streaming Layer (LSL)                   |
|                                                                            |
|   方案一: pyLSL Inlet (ECG→LSL) + VR追踪数据 (Unity→LSL)                   |
|   方案二: 上述 + BlueMuse (EEG→LSL) + E4 Streaming Server (GSR/PPG→LSL)   |
+------------------------------------|---------------------------------------+
                                     |
                                     v
+----------------------------------------------------------------------------+
|                      信号处理管道 (Python Backend)                         |
|                                                                            |
|   时间同步&缓冲区 -> 去噪&伪影去除 -> 特征提取 -> 标准化                   |
|   方案一: ~12维特征 (HRV为主 + VR行为指标)                                 |
|   方案二: ~30维特征 (+GSR情感 + EEG注意力/情绪 + 加速度运动质量)           |
+------------------------------------|---------------------------------------+
                                     |
                                     v
+----------------------------------------------------------------------------+
|                       AI分析引擎 (Python)                                  |
|                                                                            |
|   方案一: 规则引擎为主 + RF分类器辅助   (粗粒度：运动类型+强度)             |
|   方案二: RF分类器 + SVR回归 + 规则引擎 (细粒度：运动+情绪+注意力+恢复)    |
+------------------------------------|---------------------------------------+
                                     |
                       LSL + JSON over HTTP :5000
                                     |
                                     v
+----------------------------------------------------------------------------+
|                    VR渲染引擎 (Unity 2022 LTS + Meta Quest 3)              |
|                                                                            |
|   LSL4Unity接收器 -> 生物反馈HUD -> 运动场景管理 -> 环境自适应             |
+----------------------------------------------------------------------------+
                                     |
                                     v
+----------------------------------------------------------------------------+
|                     数据存储 (SQLite + JSON)                               |
+----------------------------------------------------------------------------+
```

---

## 二、目标一：传感器选型与数据采集方案

### 核心设计思路

"身心脑"三个维度的数据采集，并非每个维度都必须依赖独立硬件。关键策略是**一源多用**——同一个传感器的数据可以同时反映多个维度的状态。例如，心率变异性(HRV) 既是身体负荷指标（身），也是自主神经压力指标（心），还反映中枢-自主神经整合功能（脑）。这种思路在低成本方案中尤为关键。

以下两套方案，分别对应不同的精度追求和预算水平。

---

### 2.1 方案一：低成本稳定采集方案（总价约 ¥600 / $80）

#### 设计哲学

> **只用一颗传感器解决身心脑三维度。** 核心硬件极简，靠软件算法从单一高精度信号中挖掘多维度信息，辅以VR头显自带能力补充运动数据。低成本 ≠ 低质量——用科研级单传感器比用多个不可靠的廉价传感器更有价值。

#### 传感器清单

| 序号 | 设备 | 价格 | 采集指标 | 对应维度 |
|------|------|------|---------|---------|
| **1** | **Polar H10 胸带** | ~$80 (¥580) | 原始ECG波形(130Hz)、逐拍心率、RR间期序列 | **身** (直接) |
| **—** | *(VR头显自带)* | $0 (已拥有) | 头部6DoF位姿、手部23关节跟踪、手柄IMU加速度 | **身** (补充) |

**总计：~$80（约 ¥580-600），仅需购买一颗传感器。**

#### 为什么一颗传感器够用？—— "一源三用"策略

```
Polar H10 输出的 RR间期序列 (一串心跳间隔时间，单位ms)
        │
        ├──→ 身(Body)：HR区间、运动负荷、卡路里估算
        │    特征：mean_hr, max_hr, hr_zone
        │
        ├──→ 心(Mind)：自主神经压力、交感/副交感平衡、情绪唤醒
        │    特征：RMSSD(副交感指标), LF/HF(交感平衡), 
        │          Baevsky压力指数, 样本熵(复杂度)
        │    科学依据：RMSSD < 20ms 表示高压力状态；
        │           LF/HF > 3 表示交感神经占优(紧张/焦虑)
        │
        └──→ 脑(Brain)：中枢-自主神经整合功能
             特征：HRV样本熵(反映神经网络调控复杂度)
                   HRV总功率(反映整体神经调控能力)
             补充：VR内置认知测试(反应时、Stroop测验)
                   作为脑功能的行为学代理指标
```

#### VR头显自带的"免费传感器"

| VR能力 | 可提取指标 | 用途 |
|--------|-----------|------|
| 头部6DoF追踪 | 头部运动平滑度、姿势稳定性 | 评估运动控制质量 |
| 手部23关节追踪 (Quest 3) | 手部运动轨迹、关节角度、动作幅度 | 太极/伸展动作的完成度评分 |
| 手柄IMU (加速度计+陀螺仪) | 挥动速度、加速度峰值、动作频率 | 高强度训练中的运动强度量化 |
| VR内置认知任务 | 反应时间(ms)、正确率(%)、注意力持续时长 | 脑功能的**行为学代理指标** |

#### 低成本方案下的身心脑覆盖矩阵

| 维度 | 核心数据源 | 软件提取方法 | 处理库 | 稳定性 |
|------|-----------|-------------|--------|--------|
| **身-心率** | Polar H10 ECG | 直接读取 BPM | HeartPy | ★★★★★ 医疗级精度 |
| **身-心率变异性** | Polar H10 RR间期 | 时域(RMSSD,SDNN)+频域(LF,HF)+非线性(样本熵) | NeuroKit2 | ★★★★★ 科研金标准 |
| **身-运动量** | VR头显IMU/追踪 | 加速度幅值、位移量 | Unity内置/C# | ★★★★ 消费级够用 |
| **心-压力水平** | HRV(RMSSD)+Baevsky指数 | RMSSD<20ms=高压; Baevsky>150=紧张 | NeuroKit2 | ★★★★ 临床验证指标 |
| **心-情绪唤醒** | HRV(LF/HF比) | LF/HF>3=交感活跃(焦虑); <1=副交感(平静) | NeuroKit2 | ★★★★ 大量文献支持 |
| **心-放松程度** | HRV(SDNN趋势) | SDNN上升→放松; 下降→累积疲劳 | NeuroKit2 | ★★★★ 趋势判断可靠 |
| **脑-神经整合** | HRV(样本熵+总功率) | 熵值↑=神经网络灵活性↑ | NeuroKit2 | ★★★ 间接指标，可做趋势 |
| **脑-认知功能** | VR认知测试 | 反应时、Stroop正确率、N-back | Unity/C# | ★★★ 行为学代理 |

#### 低成本方案的优势与局限

**优势：**
- ✅ 成本极致压缩（~$80），几乎零门槛启动
- ✅ Polar H10 是经过 700+ 论文验证的科研级传感器，数据质量无可争议
- ✅ 单传感器意味着零时间同步问题、极少的数据丢包风险
- ✅ BLE连接极其稳定（400小时电池，20m范围），适合VR场景下的自由移动
- ✅ HRV是经过大量验证的多维生理指标，不是"凑合"而是科学上成立

**局限：**
- ⚠️ "脑"维度的直接神经测量缺失——HRV只能反映自主神经调控，不能测量皮层活动
- ⚠️ 缺少GSR皮肤电导——对于瞬间情绪波动的捕捉不如专用GSR传感器灵敏
- ⚠️ 缺少EEG——无法直接检测注意力波动、认知负荷变化
- ⚠️ AI推荐粒度较粗——能够区分"该休息/该运动/太紧张了"，但无法做精细的情绪分类

**适合场景：** 运动强度指导、压力管理训练、HR区间训练、呼吸训练引导、恢复状态评估

#### 方案一详细数据采集清单：传感器 → 原始数据 → 提取特征 → 生理/心理含义

##### 数据源 ①：Polar H10 ECG胸带

| 采集的原始数据 | 数据类型 | 采样率 | 提取的特征 | 特征含义 |
|-------------|---------|--------|----------|---------|
| **ECG波形** | 电压信号 (μV) | 130 Hz | — (作为原始参考信号保留) | 心电原始波形，用于后续R峰检测和质量校验 |
| **R-R间期序列** | 时间序列 (ms) | 逐拍 (~1Hz等效) | **mean_hr_bpm** (平均心率) | 当前运动负荷水平。安静=60-80，热身=90-110，有氧=120-150，高强度=150+ |
| | | | **sdnn_ms** (NN间期标准差) | 总体心率变异性。>50ms=健康自主调节，<30ms=自主神经功能受抑 |
| | | | **rmssd_ms** (相邻NN间期差值均方根) | **副交感神经(迷走神经)活性。** >40ms=放松/良好恢复，<20ms=高压/疲劳/恢复不足。这是方案一最重要的"心"维度指标 |
| | | | **pnn50_pct** (相邻间期差>50ms的百分比) | 与RMSSD高度相关，另一个副交感活性指标。>20%=良好 |
| | | | **lf_power_ms2** (低频功率 0.04-0.15Hz) | 反映交感+副交感混合调控。升高=压力反应/运动应激 |
| | | | **hf_power_ms2** (高频功率 0.15-0.4Hz) | 反映副交感(迷走)调控，与呼吸性窦性心律不齐(RSA)同步。升高=放松/深呼吸 |
| | | | **lf_hf_ratio** (LF/HF比值) | **交感-副交感平衡。** >3=交感占优(紧张/焦虑/运动应激)；<1=副交感占优(放松/冥想)；1-2=平衡 |
| | | | **sample_entropy** (样本熵) | **心率复杂度/神经网络调控灵活性。** 熵值越高=自主神经调控越灵活健康；熵值降低=系统僵化/累积疲劳/过度训练 |
| | | | **baevsky_stress_index** (Baevsky压力指数) | 综合压力评估。SI<50=放松；50-150=正常；150-500=中度压力；>500=高压力/过度疲劳 |

##### 数据源 ②：VR头显自带能力（零成本）

| 采集的原始数据 | 数据类型 | 更新率 | 提取的特征 | 特征含义 |
|-------------|---------|--------|----------|---------|
| **头部6DoF位姿** (Quest 3 IMU+摄像头) | 位置(x,y,z)+旋转(pitch,yaw,roll) | ~90 Hz | **head_movement_smoothness** (头部运动平滑度/抖动指数) | 运动控制质量。平滑度下降=疲劳或注意力缺失 |
| | | | **posture_stability_index** (姿势稳定性) | 核心稳定性。稳定性下降=核心疲劳或分心 |
| **手部23关节位置** (Quest 3手部追踪) | 每只手23个关节3D坐标 | ~30 Hz | **hand_trajectory_length** (手部轨迹总长) | 运动幅度。配合太极/伸展训练的完成度评估 |
| | | | **joint_angle_range** (关键关节活动范围) | 关节灵活性和动作幅度 |
| | | | **movement_symmetry_LR** (左右手运动对称性) | 左右侧运动不对称可能提示代偿或注意力偏侧 |
| **手柄IMU** (加速度计+陀螺仪) | 加速度(m/s²) + 角速度(°/s) | ~100 Hz | **acc_peak_magnitude** (加速度峰值) | 运动爆发力。高强度训练中的出力水平 |
| | | | **movement_frequency** (动作频率) | 运动节奏。如拳击/击打训练中的出拳频率 |
| **VR认知测试数据** (内置于VR场景) | 用户行为响应 | 按测试触发 | **reaction_time_ms** (简单反应时) | **脑-认知处理速度。** 反应时延长=中枢疲劳或注意力下降 |
| | | | **stroop_interference_ms** (Stroop干扰效应) | **执行功能/抑制控制。** 干扰越大=前额叶执行资源越少 |
| | | | **nback_d_prime** (N-back d'敏感度) | **工作记忆容量。** d'下降=工作记忆负荷已满或认知疲劳 |
| | | | **sustained_attention_decay** (持续注意力衰减率) | 注意力维持能力。随时间衰减越快=认知耐力越低 |

**方案一特征汇总：约12维**
- Polar H10 → 9个HRV特征（身+心+脑代理）
- VR追踪 → 4个运动质量特征（身）
- VR认知测试 → 4个认知功能特征（脑代理）
- 加上HR当前值和HR区间 → 2个实时状态指标

---

### 2.2 方案二：高精度精细化采集方案（总价约 ¥15,000 / $2,130）

#### 设计哲学

> **多传感器融合，每个维度都有专用硬件直接测量。** 目标是获取足够精细和丰富的数据，使得AI能够给出高度**个性化**的运动指导——不只是"你该做有氧"，而是"你当前的前额叶Alpha不对称提示情绪偏负面，加上GSR显示交感神经轻度激活，建议做5分钟森林场景下的腹式呼吸，配合528Hz音频，目标将RMSSD从当前的28ms提升到35ms以上"。

#### 传感器清单

| 序号 | 设备 | 价格 | 采集指标 | 采样率 | 对应维度 |
|------|------|------|---------|--------|---------|
| **1** | **Polar H10** | ~$80 | 原始ECG(130Hz)、RR间期、逐拍HR | 130Hz(BLE) | **身** |
| **2** | **Empatica E4** | ~$1,700 | PPG血容脉冲(64Hz)、GSR皮肤电导(4Hz)、皮温(4Hz)、3轴加速度(32Hz) | 4-64Hz(BLE) | **身+心** |
| **3** | **Muse S** | ~$350 | EEG 4通道(AF7,AF8,TP9,TP10, 256Hz)、加速度计 | 256Hz(BLE) | **心+脑** |

**总计：~$2,130（约 ¥15,000）**

#### 方案二详细数据采集清单：传感器 → 原始数据 → 提取特征 → 生理/心理含义

##### 数据源 ①：Polar H10 ECG胸带（身-心脏）

| 采集的原始数据 | 提取的特征 | 特征含义 |
|-------------|----------|---------|
| ECG波形 (130Hz, μV) | *(原始参考信号，用于R峰检测)* | 心电活动原始波形 |
| R-R间期序列 | **mean_hr_bpm** | 运动负荷水平 |
| | **sdnn_ms** | 总体自主神经调节能力 |
| | **rmssd_ms** | 副交感/迷走神经活性 — "恢复状态指示器" |
| | **pnn50_pct** | 副交感活性(与RMSSD互补验证) |
| | **lf_power_ms2** | 交感+副交感混合调控(压力/运动响应) |
| | **hf_power_ms2** | 纯副交感调控(呼吸性窦性心律不齐) |
| | **lf_hf_ratio** | **交感-副交感天平** — 核心压力/放松指标 |
| | **sample_entropy** | 心率调控复杂度(系统灵活性/累积疲劳) |
| | **baevsky_stress_index** | 综合生理压力评分(0-500+) |

##### 数据源 ②：Empatica E4 腕带（身-自主神经+运动+循环）

| 采集的原始数据 | 采样率 | 提取的特征 | 特征含义 |
|-------------|--------|----------|---------|
| **GSR/EDA** (皮肤电导, μS) | 4 Hz | **gsr_tonic_level** (皮肤电导基础水平, SCL) | **交感神经基础激活度。** 持续升高=慢性压力/焦虑状态，降低=放松 |
| | | **gsr_phasic_peak_count** (皮肤电导反应峰频率, SCR/min) | **瞬时情绪唤醒事件频率。** 单位时间内SCR峰越多=经历的情绪波动越多。用于检测VR场景引发的情绪反应 |
| | | **gsr_phasic_amplitude_mean** (SCR平均幅度) | 单次情绪唤醒的强度。幅度越大=情绪反应越强烈 |
| | | **gsr_rise_time_mean** (SCR上升时间) | 情绪唤醒的速度。上升越快=反应越灵敏(或越紧张) |
| **BVP/PPG** (血容脉冲, 光电容积描记) | 64 Hz | **ppg_hr_bpm** (PPG心率, 与ECG交叉验证) | 光学心率，与Polar H10 ECG心率做交叉验证 |
| | | **ppg_amplitude** (脉搏波幅值) | 外周血管舒缩状态。幅值降低=外周血管收缩(压力反应)；幅值升高=血管舒张(放松) |
| | | **pulse_arrival_time_ms** (脉搏到达时间) | 结合ECG R峰可计算脉搏传导时间(PAT)，与血压变化相关 |
| **Skin Temperature** (皮温, °C) | 4 Hz | **temp_absolute** (绝对皮温) | 外周循环状态。运动后皮温升高=正常热量散发；持续低温=外周血管收缩(压力或寒冷) |
| | | **temp_trend_slope** (皮温变化趋势, °C/min) | 热调节速率。斜率大=快速升温(高强度运动)；斜率平=稳定状态 |
| | | **temp_hr_coupling** (皮温-心率耦合指数) | 热调节-心血管协调性。解耦可能提示热应激或脱水 |
| **3-Axis Accelerometer** (加速度, g) | 32 Hz | **acc_magnitude_mean** (加速度幅值均值) | **躯干整体运动量。** 比VR头显追踪更能反映全身运动强度(腕部佩戴) |
| | | **acc_magnitude_std** (加速度幅值标准差) | 运动模式变化程度。高值=动作多样，低值=单一重复动作 |
| | | **acc_entropy** (加速度熵) | 运动复杂度。配合太极等复杂动作训练时的丰富度评估 |

##### 数据源 ③：Muse S 脑电头带（心-情绪+注意力+放松+脑-认知）

| 采集的原始数据 | 采样率 | 提取的特征 | 特征含义 |
|-------------|--------|----------|---------|
| **EEG Ch1: AF7** (左前额) | 256 Hz | 5个频段功率: **Delta**(0.5-4Hz), **Theta**(4-8Hz), **Alpha**(8-13Hz), **Beta**(13-30Hz), **Gamma**(30-45Hz) | 左前额叶脑电活动。AF7通常与语言加工、正性情绪的左侧化有关 |
| **EEG Ch2: AF8** (右前额) | 256 Hz | 同上5个频段功率 | 右前额叶脑电活动。AF8通常与情绪处理、负性情绪的右侧化有关 |
| **EEG Ch3: TP9** (左颞顶) | 256 Hz | 同上5个频段功率 | 左颞顶叶。与听觉处理、语言理解有关 |
| **EEG Ch4: TP10** (右颞顶) | 256 Hz | 同上5个频段功率 | 右颞顶叶。与空间注意、多感觉整合有关 |
| **4通道综合** | — | **alpha_power_mean** (4通道Alpha均值) | **放松程度核心指标。** Alpha↑=放松/冥想/闭眼休息；Alpha↓=警觉/睁眼/认知活跃 |
| | | **beta_power_mean** (4通道Beta均值) | **活跃思维/认知加工。** Beta↑=专注思考/焦虑反射；Beta↓=放松/困倦 |
| | | **theta_power_mean** (4通道Theta均值) | **内省/冥想深度。** Theta↑=深度冥想/浅睡；配合Alpha可判断冥想质量 |
| | | **delta_power_mean** (4通道Delta均值) | 深度睡眠指标(清醒时Delta升高通常为伪影，可作为信号质量指标) |
| | | **gamma_power_mean** (4通道Gamma均值) | **高阶认知加工。** Gamma↑=知觉整合/专注/学习；与注意力高度相关 |
| | | **alpha_asymmetry_fp** = (AF8_alpha − AF7_alpha) / (AF8_alpha + AF7_alpha) | **情绪效价核心指标。** 正值(AF8>AF7)=右前额活跃→偏负面/回避情绪；负值(AF7>AF8)=左前额活跃→偏正面/趋近情绪。这是方案二最有价值的特征之一 |
| | | **theta_beta_ratio** = Theta功率/Beta功率 | **注意力量化指标。** TBR<1.5=注意力集中；1.5-2.5=正常波动；>2.5=注意力涣散/ADHD倾向/疲劳。方案二最核心的注意力特征 |
| | | **alpha_peak_frequency** (个体Alpha峰值频率, IAF) | 个体认知特征。IAF较高(>10.5Hz)=认知加工较快；IAF较低(<9.5Hz)=可能与疲劳或认知衰退相关 |
| | | **alpha_reactivity** (睁眼Alpha衰减率) | 睁眼时Alpha下降幅度。反映大脑对外界刺激的响应灵敏度 |
| **Muse Accelerometer** | 50 Hz | **head_motion_artifact_flag** | 头部运动幅度，用于标记EEG中可能被运动伪影污染的时段 |

##### 数据源 ④：VR头显自带（零成本，与方案一相同）

| 原始数据 | 提取特征 | 特征含义 |
|---------|---------|---------|
| 头部6DoF + 手部23关节 + 手柄IMU | head_movement_smoothness, posture_stability, hand_trajectory_length, joint_angle_range, movement_symmetry_LR, acc_peak_magnitude, movement_frequency | 运动质量控制(与方案一相同) |
| VR认知测试(Stroop/N-back/反应时) | reaction_time_ms, stroop_interference_ms, nback_d_prime, sustained_attention_decay | 认知功能行为学指标(与方案一相同) |

**方案二特征汇总：约31维**
- Polar H10 → 9个HRV特征（身+心）
- Empatica E4 → 4个GSR情感特征 + 3个PPG循环特征 + 3个皮温代谢特征 + 3个加速度运动特征 = 13个特征（身+心）
- Muse S → 4通道×5频段(20维原始)+5个综合脑电指标 + 4个注意力/情绪指标 = 约5个综合特征（心+脑）
- VR追踪+认知 → 8个特征（身+脑）
- 加上HR当前值和HR区间 → 2个实时状态指标

---

#### 为什么需要三颗传感器？—— 精度对比

| 测量需求 | 方案一(低成本) | 方案二(高精度) | 精度提升 |
|---------|-------------|-------------|---------|
| **心率** | Polar H10 ECG ✓ | Polar H10 ECG ✓ | → 持平（都用金标准） |
| **HRV分析** | Polar H10 RR间期 ✓ | Polar H10 RR间期 ✓ | → 持平 |
| **压力检测** | HRV间接推断（RMSSD↓=压力↑） | GSR直接测量（交感神经皮肤电导） | ↑ **大幅提升**：GSR是压力检测的金标准，秒级响应 |
| **情绪效价** | 无法直接测量 | EEG额叶Alpha不对称（正/负情绪） | ↑ **从无到有**：可以区分积极/消极情绪 |
| **注意力监测** | HRV粗略趋势 | EEG Theta/Beta比（注意力量化指标） | ↑ **大幅提升**：可以量化注意力水平 |
| **身体运动** | VR追踪（头部+手部） | E4加速度计（躯干）+ VR追踪 | ↑ 躯干运动数据补充 |
| **皮肤温度** | 无 | E4皮温（压力/循环/代谢指标） | ↑ **新增维度** |
| **脑功能** | VR行为测试代理 | EEG频段功率+额叶不对称+认知测试 | ↑ **多维交叉验证** |
| **情绪分类** | 无法实现 | EEG+GSR+HRV三模态融合 | ↑ **从无到有**：可实现基本的效价-唤醒度情绪映射 |

#### 多传感器融合的个性化指导能力

**方案一能做到的：**
> "你的HRV偏低(RMSSD=22ms)，心率偏高(95bpm)，建议降低运动强度，切换到呼吸训练。"

**方案二能做到的：**
> "你的GSR显示交感神经轻度激活(3.2μS)，额叶Alpha不对称提示情绪偏负面(AF8<AF7)，Theta/Beta比偏低提示注意力有所分散(1.4)，加上心率处于Zone 2偏高区间(85bpm)，综合分析：你当前处于'紧张但注意力不集中'的状态。建议先做5分钟海滩场景盒式呼吸(4-4-4-4)，目标将RMSSD从22ms恢复到35ms以上，同时通过额叶Alpha不对称的实时反馈来确认情绪改善。如果Alpha不对称指标在3分钟内未改善，自动切换为森林正念漫步。"

这就是精度差异带来的**个性化指导深度**的质变。

#### 高精度方案身心脑数据矩阵

| 维度 | 传感器 | 提取特征 | 特征数量 | AI可回答的问题 |
|------|--------|---------|---------|-------------|
| **身-心脏** | Polar H10 | HR, SDNN, RMSSD, pNN50, LF, HF, LF/HF, 样本熵, Baevsky指数 | 9维 | 运动负荷是否合适？需要恢复吗？ |
| **身-自主神经** | Empatica E4 | GSR基础水平, GSR反应峰值频率, GSR反应幅度 | 3维 | 交感神经是否过度激活？ |
| **身-运动** | E4 ACC + VR追踪 | 躯干加速度幅值, 头部运动平滑度, 手部轨迹 | 3维 | 动作质量如何？有代偿动作吗？ |
| **身-代谢/循环** | Empatica E4 | 皮温, 皮温变化率, PPG血容脉冲幅值 | 3维 | 外周循环是否正常？代谢状态？ |
| **心-注意力** | Muse S | Theta/Beta比, Alpha峰值频率 | 2维 | 注意力是否集中？是否疲劳？ |
| **心-情绪** | Muse S + E4 | 额叶Alpha不对称, GSR-EEG联合唤醒度 | 2维 | 情绪是积极还是消极？唤醒度高低？ |
| **心-放松** | Muse S | Alpha功率(AF7,AF8,TP9,TP10均值), Alpha/Theta比 | 2维 | 放松程度是否达标？ |
| **脑-认知** | Muse S | Gamma功率(30-45Hz), Theta相位同步 | 2维 | 认知加工是否活跃？ |
| **脑-执行功能** | VR Stroop测试 | 反应时, 正确率, 干扰效应 | 3维 | 执行功能状态如何？ |
| **脑-记忆** | VR N-back测试 | 反应时, d'敏感度 | 2维 | 工作记忆状态如何？ |

**总特征维度：** 30+ 维（方案一：约12维）

#### 高精度方案的优势与局限

**优势：**
- ✅ GSR提供秒级的情绪唤醒检测，比HRV快一个数量级
- ✅ EEG直接测量脑电活动，可以量化注意力、放松、情绪效价
- ✅ 三模态交叉验证大幅提升AI分类精度（从~75%提升到预计>90%）
- ✅ 支持情绪效价-唤醒度二维模型，可以做更精细的运动推荐
- ✅ 皮温数据可以检测运动中的热调节状态，防止过热
- ✅ 加速度计在躯干位置（E4腕部），比头显自带的头部追踪更能反映全身运动

**局限：**
- ⚠️ 三颗传感器需要同时管理BLE连接，增加技术复杂度
- ⚠️ Empatica E4价格较高（~$1,700），可能需要项目经费支持
- ⚠️ 三个设备的时间同步需要LSL统一管理（技术上可行但需要仔细测试）
- ⚠️ Muse S干电极信号质量受运动和出汗影响，需在VR运动场景中验证稳定性
- ⚠️ 仍然缺少直接的脑皮层氧合测量(fNIRS)，但EEG已可提供足够的脑功能代理指标

**适合场景：** 个性化运动处方、情绪自适应训练、注意力引导冥想、科研级数据采集

---

### 2.3 两套方案对比总览

| 对比维度 | 方案一：低成本 | 方案二：高精度 |
|---------|-------------|-------------|
| **硬件成本** | ~$80 (¥600) | ~$2,130 (¥15,000) |
| **传感器数量** | 1颗 + VR自带 | 3颗 + VR自带 |
| **身体指标** | HR, HRV, 运动量(粗) | HR, HRV, GSR, 皮温, 加速度, 运动量(精) |
| **心理指标** | HRV压力推断 | EEG注意力+情绪+GSR唤醒+HRV验证 |
| **脑指标** | HRV神经调控代理+VR行为测试 | EEG频段+额叶不对称+VR认知测试 |
| **AI输入特征数** | ~12维 | ~30维 |
| **情绪检测** | ❌ 不支持 | ✅ 效价-唤醒度二维模型 |
| **注意力量化** | ❌ 粗略趋势 | ✅ Theta/Beta比精确量化 |
| **个性化深度** | 运动类型+强度（粗粒度） | 运动类型+强度+情绪调节+注意力引导（细粒度） |
| **BLE连接数** | 1 | 3（需管理多连接） |
| **穿戴复杂度** | 胸带1件 | 胸带+腕带+头带共3件 |
| **VR运动兼容** | ✅ 极佳（仅胸带，不干扰） | ⚠️ 头带+Muse需在VR头显下佩戴 |
| **数据可靠性** | 极高（单金标准源） | 高（需管理3源同步） |
| **实施难度** | ★★☆ | ★★★★ |
| **推荐启动时机** | **立刻可以启动** | 方案一验证后，有经费时升级 |

---

### 2.4 实施建议

**推荐路径：先低成本验证，后追求精度。** 

1. **第一阶段（当前）：** 用方案一（Polar H10, ~$80）搭建完整的数据管道→AI分析→VR反馈闭环。验证整个技术链条跑通，积累初始标注数据。
2. **第二阶段（方案一验证后）：** 申请项目经费，购入Muse S (~$350) + Empatica E4 (~$1,700)，增加新的LSL流和特征提取模块，重新训练AI模型（特征维度从12→30），实现精细化个性化指导。
3. **第三阶段（如有实验室资源）：** 借用大连理工大学心理/神经科学实验室的fNIRS设备，在关键实验阶段采集脑氧合数据，为AI模型增加脑维度的金标准标签。

**关键原则：** 两套方案共享同一套软件架构（LSL管道、JSON Schema、AI框架）。从方案一切换到方案二是**增加传感器流**而非推倒重来，工程量约增加30%（新增streamer + 新增特征提取器 + 重训模型）。

### 2.5 统一数据格式设计 (AI可读JSON)

#### Schema A: 原始传感器采样 (raw_sensor_sample)

```json
{
  "sample_id": "uuid",
  "timestamp_unix_ms": 1717412400000,
  "domain": "body",
  "source": {
    "device_type": "PolarH10",
    "stream_type": "ECG",
    "sampling_rate_hz": 130
  },
  "channel_labels": ["ECG_Lead1"],
  "data": [0.823],
  "unit": "mV",
  "quality_flag": 0
}
```

#### Schema B: 时间窗特征 (epoch_features)

```json
{
  "epoch_id": "uuid",
  "window_start_unix_ms": 1717412400000,
  "window_duration_s": 10.0,
  "domain": "body",
  "features": {
    "hr": { "mean_bpm": 72.3, "std_bpm": 4.1, "min_bpm": 68, "max_bpm": 78 },
    "hrv": { "sdnn_ms": 45.2, "rmssd_ms": 32.7, "pnn50_pct": 18.5,
             "lf_power_ms2": 850.3, "hf_power_ms2": 420.1, "lf_hf_ratio": 2.02 },
    "stress_index_baevsky": 84.1,
    "recovery_score_0_100": 72.0
  }
}
```

#### Schema C: AI推荐输出 (ai_recommendation)

```json
{
  "recommendation_id": "uuid",
  "timestamp_unix_ms": 1717412415000,
  "session_id": "session_20240603_001",
  "current_state": {
    "hr_current_bpm": 85, "hr_zone": 2,
    "hrv_sdnn_ms": 45.2, "gsr_tonic_us": 3.2,
    "eeg_alpha_power_mean": 5.15, "eeg_theta_beta_ratio": 1.72,
    "attention_index": 65.0, "stress_index": 35.0
  },
  "recommendation": {
    "exercise_type": "breathing_exercise",
    "intensity_pct": 30,
    "duration_minutes": 5,
    "target_hr_zone": 1,
    "guidance_text_zh": "当前压力指数偏高，建议进行5分钟盒式呼吸练习",
    "vr_scene": "beach_sunset"
  },
  "confidence": 0.87
}
```

#### Schema D: 多模态融合训练数据 (merged_multimodal_epoch)

```json
{
  "epoch_id": "uuid",
  "window_duration_s": 10.0,
  "body": { "hr_bpm": 72.3, "hrv_sdnn_ms": 45.2, "gsr_tonic_us": 3.2 },
  "mind": { "eeg_alpha_power_avg": 5.15, "eeg_theta_beta_ratio": 1.72 },
  "brain": { "fnirs_hbo_um_l": null },
  "label": { "exercise_type": "breathing_exercise", "intensity_pct": 30 }
}
```

### 2.6 数据流技术栈

- **传输协议：** Lab Streaming Layer (LSL) — 科研领域事实标准，支持C/Python/C#/MATLAB，内置时间同步
- **BLE桥接：** bleak (Python BLE库) 用于Polar H10直连；BlueMuse/Mind Monitor 用于Muse EEG→LSL
- **LSL→VR桥接：** LSL4Unity (Unity C#插件)
- **HTTP API：** Flask (端口5000)，供VR端拉取AI推荐结果

---

## 三、目标二：AI智能分析通道（基于方案二高精度数据设计）

### 3.0 设计总览：六层分析架构

基于方案二采集的31维精细特征，AI分析不再是一个简单的「特征→分类→输出」流水线，而是一个**六层递进分析架构**。每一层回答一个不同层级的问题，层层叠加，最终生成高度个性化的运动指导。

```
                    方案二 31维特征输入
                           │
    ┌──────────────────────┼──────────────────────┐
    v                      v                      v
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Layer 1  │    │ Layer 2  │    │ Layer 3  │
│ 生理状态 │    │ 心理/情绪│    │ 认知状态 │
│ 评估     │    │ 状态评估 │    │ 评估     │
│          │    │          │    │          │
│ 输入:    │    │ 输入:    │    │ 输入:    │
│ HRV 9维  │    │ EEG 5维  │    │ EEG Gamma│
│ GSR 4维  │    │ GSR 4维  │    │ VR Stroop│
│ PPG 3维  │    │ HRV 2维  │    │ VR N-back│
│ Temp 3维 │    │          │    │          │
│ ACC 3维  │    │          │    │          │
│ VR运动7维│    │          │    │          │
│          │    │          │    │          │
│ 输出:    │    │ 输出:    │    │ 输出:    │
│ 运动负荷 │    │ 情绪效价 │    │ 处理速度 │
│ 自主神经 │    │ 唤醒度   │    │ 执行功能 │
│ 循环代谢 │    │ 注意力   │    │ 工作记忆 │
│ 运动质量 │    │ 放松深度 │    │ 认知耐力 │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
                     v
            ┌──────────────┐
            │   Layer 4    │
            │ 综合状态融合 │
            │              │
            │ 3层输出融合  │
            │ → 用户全局   │
            │   状态向量   │
            └──────┬───────┘
                   │
                   v
            ┌──────────────┐
            │   Layer 5    │
            │ 推荐决策引擎 │
            │              │
            │ ML模型 +     │
            │ 规则引擎 +   │
            │ 安全门       │
            └──────┬───────┘
                   │
                   v
            ┌──────────────┐
            │   Layer 6    │
            │ VR适配输出   │
            │              │
            │ 场景选择     │
            │ 音频匹配     │
            │ 视觉引导参数 │
            │ 实时反馈策略 │
            └──────────────┘
```

---

### 3.0B 两套方案的AI分析能力对比

同样的六层架构，方案一和方案二因为输入数据的维度和精度不同，AI能回答的问题和给出的指导存在质的差异。

#### 逐层能力对比

| 分析层 | 方案一（低成本 ~12维） | 方案二（高精度 ~31维） | 差距本质 |
|--------|---------------------|----------------------|---------|
| **Layer 1 生理状态** | | | |
| 运动负荷 | ✅ HR+HR区间判断 | ✅ HR+HR区间+HRV趋势交叉验证 | 方案二能区分"运动应激"和"情绪性心率升高" |
| 自主神经平衡 | ⚠️ 仅RMSSD+LF/HF | ✅ RMSSD+GSR tonic+GSR phasic+LF/HF+Baevsky五重交叉验证 | 方案一：知道"压力大了"；方案二：知道"压力大是因为交感激活还是副交感撤退" |
| 循环代谢 | ❌ 无皮温数据 | ✅ 皮温绝对值+变化率+心率耦合 | 方案一缺少热调节监测，无法预警热应激 |
| 运动质量 | ⚠️ 仅VR头部+手部追踪 | ✅ VR追踪+躯干加速度+运动熵+左右对称性 | 方案一：知道"动了"；方案二：知道"动得质量如何" |
| **Layer 2 心理/情绪** | | | |
| 压力检测 | ⚠️ HRV间接推断(RMSSD↓) | ✅ GSR直接测量(交感神经皮肤电导) | 方案一：间接指标，有滞后(HRV需60s窗口)；方案二：直接指标，秒级响应 |
| 情绪效价(正/负) | ❌ 无法检测 | ✅ EEG额叶Alpha不对称 | **方案一完全不具备此能力** |
| 情绪唤醒度(高/低) | ⚠️ LF/HF粗略趋势 | ✅ GSR+EEG联合量化 | 方案一：趋势判断(上升/下降)；方案二：精确定位到效价-唤醒度二维坐标 |
| 注意力量化 | ❌ 仅HRV极粗略趋势 | ✅ EEG Theta/Beta比精确量化 | **方案一完全不具备此能力** |
| 放松深度 | ⚠️ HRV RMSSD趋势 | ✅ EEG Alpha功率+Alpha/Theta比+RMSSD三方验证 | 方案一：知道"心率平稳了"；方案二：知道"进入了多深的冥想状态" |
| **Layer 3 认知状态** | | | |
| 处理速度 | ✅ VR反应时 | ✅ VR反应时+EEG IAF交叉验证 | 方案一可做行为学测量；方案二可区分"运动疲劳"vs"认知疲劳" |
| 执行功能 | ✅ VR Stroop测试 | ✅ VR Stroop+EEG Gamma | 方案一有行为学指标；方案二可检测前额叶加工活跃度 |
| 工作记忆 | ✅ VR N-back测试 | ✅ VR N-back+EEG Theta相位同步 | 方案一有行为学指标；方案二可区分"不认真"vs"真的记不住" |
| **Layer 4 融合** | | | |
| 身心同步性 | ❌ 不可评估 | ✅ body_mind_coupling | 方案二能检测"脑放松但身体紧张"这种解耦状态 |
| 心脑耦合 | ❌ 不可评估 | ✅ mind_brain_coupling | 方案二能检测"情绪唤醒但认知疲劳"的组合状态 |
| **Layer 5 决策** | | | |
| 运动类型决策 | ✅ 5类(依赖规则为主) | ✅ 6类(ML+情绪微调) | 方案一：规则驱动；方案二：数据驱动+情绪自适应 |
| 强度决策 | ⚠️ HR区间查表 | ✅ SVR回归+情绪/认知/运动质量6因子修正 | 方案一：标准公式；方案二：个性化调节 |
| **Layer 6 输出** | | | |
| 目标指标 | ⚠️ 仅HR区间 | ✅ RMSSD目标+GSR目标+Alpha不对称目标+Alpha功率目标 | 方案二可设定心理/情绪维度的训练目标 |
| 自适应触发 | ❌ 无 | ✅ 6种自适应条件+切换策略 | 方案二实现了真正的实时闭环自适应 |

#### 典型场景中的AI能力差距

**场景A：用户做呼吸训练时走神了**

| | 方案一 | 方案二 |
|------|--------|--------|
| 检测能力 | HR可能略微上升，但AI无法判断是"走神"还是"身体不适" | Theta/Beta比突然升高→AI立即知道注意力涣散 |
| AI响应 | 无特异性响应 | VR音频自动加入引导语音"把注意力带回呼吸"，呼吸环亮度增强 |

**场景B：用户在做中等强度有氧时情绪变差**

| | 方案一 | 方案二 |
|------|--------|--------|
| 检测能力 | HR上升—AI只知道"强度上去了" | 额叶Alpha不对称转向负效价+GSR phasic增加—AI知道"用户变得烦躁/抗拒" |
| AI响应 | 可能误判为"运动投入良好"继续维持强度 | 自动降低目标强度5%，切换到森林场景，音频降BPM |

**场景C：用户外表安静但内心焦虑**

| | 方案一 | 方案二 |
|------|--------|--------|
| 检测能力 | HR偏低+RMSSD正常→AI判断为"放松状态" | Alpha功率低+Beta功率高+GSR tonic高→AI识别出"外表安静但内在焦虑(高Beta焦虑反射)" |
| AI响应 | 误以为用户已在放松，可能建议进入下一阶段 | 继续维持呼吸训练，并加入528Hz音频层辅助放松 |

**场景D：用户认知疲劳但身体状态良好**

| | 方案一 | 方案二 |
|------|--------|--------|
| 检测能力 | HR正常+HRV正常→AI判断为"状态良好" | 认知测试反应时延长+IAF下降→AI识别出"中枢疲劳" |
| AI响应 | 可能推荐中等强度运动 | 推荐已熟练的轻度运动，避免学习新动作（认知负荷已满） |

#### 一句话总结差距

> **方案一回答："你现在该做什么运动、做多强。"**
> **方案二回答："你现在身心脑处于什么状态、为什么处于这个状态、该做什么运动来改善这个状态、运动过程中如何实时调整、如果效果不好怎么切换方案。"**

---

### 3.1 Layer 1：生理状态评估（身体层）

**输入：** HRV 9维 + GSR 4维 + PPG 3维 + 皮温 3维 + ACC 3维 + VR运动 7维 = **29维身体特征**

**输出：** 四个生理子维度评分（每个0-100）

#### 1A. 运动负荷评估 (Cardiac Load Score)

| 特征 | 权重倾向 | 评估逻辑 |
|------|---------|---------|
| `hr_current_bpm` vs `hr_max_estimated` | 核心指标 | %HRmax: <60%=低负荷 / 60-75%=中 / 75-85%=中高 / >85%=高 |
| `lf_hf_ratio` | 运动应激确认 | 与%HRmax交叉验证：HR高+LF/HF高=真实运动应激；HR高+LF/HF低=其他原因 |
| `sample_entropy` 趋势 | 累积负荷 | 熵值持续下降=累积疲劳信号，即使当前HR不高 |

**输出：** `cardiac_load_score` (0-100)
- 0-30: 休息/恢复状态
- 30-55: 轻度负荷（热身区）
- 55-75: 中等负荷（有氧区）
- 75-90: 中高负荷（无氧阈值区）
- 90-100: 极限负荷（需要减速）

#### 1B. 自主神经平衡评估 (Autonomic Balance Score)

| 特征 | 权重倾向 | 评估逻辑 |
|------|---------|---------|
| `rmssd_ms` | **核心指标** (权重0.3) | vs个人基线：>120%=副交感活跃(恢复良好)；80-120%=正常；50-80%=轻度压力；<50%=高压/疲劳 |
| `gsr_tonic_level` | **核心指标** (权重0.25) | vs个人基线：<2μS=放松；2-5μS=正常；5-10μS=轻度压力；>10μS=高压力 |
| `lf_hf_ratio` | 辅助验证 (权重0.2) | 与RMSSD+GSR交叉：三者方向一致=可信度高 |
| `gsr_phasic_peak_count` | 情绪波动频率 (权重0.15) | >5次/分=情绪波动频繁；<1次/分=情绪平稳 |
| `baevsky_stress_index` | 综合压力 (权重0.1) | SI<50=放松；50-150=正常；>150=压力 |

**输出：** `autonomic_balance_score` (0-100)
- 0-25: 副交感主导（深度放松/冥想状态）
- 25-50: 偏向放松（适合呼吸训练/轻度伸展）
- 50-75: 自主神经平衡（适合有氧运动）
- 75-100: 交感主导（压力/紧张/过度唤醒 → 不适合高强度训练）

#### 1C. 循环代谢评估 (Circulatory-Metabolic Score)

| 特征 | 权重倾向 | 评估逻辑 |
|------|---------|---------|
| `temp_absolute` | 基础循环 | 32-34°C=寒冷/外周收缩；34-36°C=正常；>36°C=运动产热/热应激 |
| `temp_trend_slope` | 热调节速率 | >0.5°C/min=快速升温(高强度运动)；<0=降温/恢复中 |
| `ppg_amplitude` | 外周血管状态 | 幅值降低=血管收缩(压力/寒冷)；幅值升高=血管舒张(运动后/放松) |
| `temp_hr_coupling` | 热-心血管协调 | 解耦=可能热应激或脱水风险 |

**输出：** `circulatory_score` (0-100)
- 低分=外周循环受限（建议热身/调高环境温度）
- 中分=循环正常
- 高分=运动产热充分（需注意散热和水合）

#### 1D. 运动质量评估 (Movement Quality Score)

| 特征 | 权重倾向 | 评估逻辑 |
|------|---------|---------|
| `acc_magnitude_mean` (E4腕部) | 躯干运动量 | 与VR头部追踪交叉对比，评估全身vs局部运动 |
| `acc_entropy` | 运动复杂度 | 高熵=动作多样(太极/舞蹈)；低熵=重复动作(跑步/骑行) |
| `head_movement_smoothness` | 运动控制 | 平滑度下降=疲劳或注意力下降的信号 |
| `movement_symmetry_LR` | 左右协调 | 不对称度>15%=可能存在代偿 |
| `hand_trajectory_length` / `joint_angle_range` | 动作幅度 | 与目标动作模板对比，计算完成度百分比 |

**输出：** `movement_quality_score` (0-100)
- 低分=动作质量差/代偿/协调下降 → 降低难度或纠正动作
- 高分=动作流畅标准 → 可提升难度

---

### 3.2 Layer 2：心理/情绪状态评估（心理层）

**输入：** EEG 5个综合指标 + GSR 4维 + HRV (RMSSD用于交叉验证)

**输出：** 情绪效价-唤醒度坐标 + 注意力评分 + 放松深度评分

#### 2A. 情绪效价-唤醒度模型 (Valence-Arousal Circumplex)

这是方案二AI最核心的能力——基于Russell的情绪环状模型，用生理数据实时定位用户的情绪坐标。

```
                    高唤醒 (High Arousal)
                         |
         紧张/焦虑       |       兴奋/激动
         (Tense)         |       (Excited)
                         |
   负效价 ←──────────────┼──────────────→ 正效价
   (Negative)            |            (Positive)
                         |
         悲伤/抑郁       |       放松/满足
         (Sad)           |       (Calm)
                         |
                    低唤醒 (Low Arousal)
```

**效价轴(X轴, -1到+1) 数据来源：**

| 特征 | 处理方式 | 生理含义 |
|------|---------|---------|
| `alpha_asymmetry_fp` = (AF8-AF7)/(AF8+AF7) | **直接映射为主** | 正值(AF8>AF7)→右前额活跃→偏负面/回避；负值(AF7>AF8)→左前额活跃→偏正面/趋近 |
| `gsr_phasic_amplitude_mean` | 辅助修正 | 高幅度SCR+正效价=兴奋；高幅度SCR+负效价=焦虑 |
| `theta_beta_ratio` | 辅助修正 | TBR极高(>3)+负效价=疲劳性负面情绪；TBR极高+正效价=冥想性平静 |

**唤醒轴(Y轴, 0到1) 数据来源：**

| 特征 | 处理方式 | 生理含义 |
|------|---------|---------|
| `gsr_tonic_level` | **直接映射为主** (归一化vs个人基线) | GSR升高=交感激活→高唤醒 |
| `gsr_phasic_peak_count` | 辅助 | SCR频率高=情绪波动多→高唤醒 |
| `lf_hf_ratio` | 交叉验证 | 与GSR同向=可信；反向=需进一步分析 |
| `beta_power_mean` | 辅助 | Beta升高+GSR升高=认知性高唤醒(思考/焦虑)；Beta正常+GSR升高=纯情绪性高唤醒 |

**情绪象限 → 运动建议映射：**

| 象限 | 情绪状态 | 推荐运动策略 | VR场景 |
|------|---------|-------------|--------|
| **高唤醒+负效价** (紧张/焦虑) | 压力大、紧张、烦躁 | **优先级最高：降低唤醒度+转向正效价。** 呼吸训练为主，目标降低GSR、提升Alpha不对称 | 海滩日落呼吸 / 森林正念漫步 |
| **高唤醒+正效价** (兴奋/激动) | 精力充沛、兴奋 | 最佳训练状态。高强度有氧/间歇训练，利用当下高能量 | 抽象空间高强度挑战 |
| **低唤醒+负效价** (悲伤/疲劳) | 情绪低落、疲惫 | **需要温和激活。** 轻度→中等强度过渡，用VR场景提升情绪，逐步增加唤醒度 | 森林正念→山湖太极→渐进加速 |
| **低唤醒+正效价** (放松/满足) | 平静、满足 | 适合精细动作训练、太极、瑜伽。保持当前状态，做品质高的运动 | 山湖太极 / 海滩轻度活动 |

#### 2B. 注意力量化评分 (Attention Score)

| 特征 | 处理方式 | 生理含义 |
|------|---------|---------|
| `theta_beta_ratio` | **核心指标** | <1.5=注意力集中；1.5-2.5=正常；2.5-3.5=注意力轻度涣散；>3.5=严重注意力缺陷/极度疲劳 |
| `alpha_peak_frequency` | 辅助 | IAF下降>1Hz(相对个人基线)=认知疲劳信号 |
| `gamma_power_mean` | 辅助 | Gamma↑=认知活跃/专注加工 |

**输出：** `attention_score` (0-100)
- 0-40: 注意力涣散 → 不适合需要高度专注的训练
- 40-60: 注意力正常波动 → 适合中等复杂度运动
- 60-100: 高度专注 → 适合需要精细控制的运动(太极/瑜伽)

#### 2C. 放松深度评分 (Relaxation Depth Score)

| 特征 | 处理方式 | 生理含义 |
|------|---------|---------|
| `alpha_power_mean` | **核心指标** | vs个人睁眼基线：>200%=深度冥想状态；150-200%=放松；100-150%=正常清醒；<100%=警觉/紧张 |
| `alpha_theta_ratio` | 冥想质量 | 高比值+高Alpha=优质放松；高比值+低Alpha=困倦而非放松 |
| `rmssd_ms` | 身体放松验证 | RMSSD升高+Alpha升高=身心同步放松(最优)；Alpha高+RMSSD低=脑放松但身体仍紧张 |

**输出：** `relaxation_depth_score` (0-100)

---

### 3.3 Layer 3：认知状态评估（脑层）

**输入：** VR Stroop测试 + VR N-back测试 + EEG Gamma/Theta

**输出：** 三个认知子维度评分

| 认知维度 | 核心指标 | 辅助指标 | 评估逻辑 |
|---------|---------|---------|---------|
| **处理速度** | `reaction_time_ms` (简单反应时) | `alpha_peak_frequency` (IAF较高=处理快) | RT<250ms=快；250-350=正常；>350=慢(中枢疲劳) |
| **执行功能** | `stroop_interference_ms` (Stroop干扰效应) | `gamma_power_mean` (Gamma高=执行加工活跃) | 干扰<50ms=执行功能强；50-120ms=正常；>120ms=执行功能减弱(前额叶疲劳) |
| **工作记忆** | `nback_d_prime` (N-back d') | `sustained_attention_decay` (注意力衰减率) | d'>2=优秀；1-2=正常；<1=工作记忆不足(认知负荷过高) |

**输出：** `cognitive_function_score` (0-100，三维度加权合成)
- 认知功能良好 → 适合需要学习新动作/复杂运动模式的训练
- 认知功能下降 → 建议做已掌握的热身运动，不宜学习新动作

---

### 3.4 Layer 4：综合状态融合

Layer 1-3各自输出了独立的评分。Layer 4的任务是将它们融合为一个**用户全局状态向量 (Global State Vector)**，作为Layer 5推荐引擎的输入。

#### 融合策略：可解释的规则化融合

不使用黑盒神经网络，而使用**可解释的规则化融合**：

```
全局状态向量 = {
    // 身体维度
    cardiac_load:          Layer1A.cardiac_load_score,
    autonomic_balance:     Layer1B.autonomic_balance_score,
    circulatory:           Layer1C.circulatory_score,
    movement_quality:      Layer1D.movement_quality_score,
    
    // 心理维度
    emotion_valence:       Layer2A.valence,           // -1 到 +1
    emotion_arousal:       Layer2A.arousal,           // 0 到 1
    emotion_quadrant:      Layer2A.quadrant,          // "HA-HV" / "HA-LV" / "LA-HV" / "LA-LV"
    attention:             Layer2B.attention_score,
    relaxation_depth:      Layer2C.relaxation_depth_score,
    
    // 脑维度
    cognitive:             Layer3.cognitive_function_score,
    
    // 关键交叉关系（捕捉多域相互作用）
    body_mind_coupling:    // 身体和心理是否同步？
        if |autonomic_balance - relaxation_depth| < 15: "身心同步"
        elif relaxation_depth > autonomic_balance: "脑放松>身体放松"
        else: "身体放松>脑放松",
    
    mind_brain_coupling:   // 情绪和认知是否匹配？
        if emotion_quadrant in ["HA-HV","HA-LV"] AND cognitive < 40: "情绪唤醒但认知疲劳"
        if emotion_quadrant in ["LA-LV"] AND cognitive < 40: "情绪低落+认知疲劳→需要激活"
    
    recovery_readiness:     // 综合恢复准备度
        weighted_score(rmssd_trend, gsr_tonic_trend, temp_trend, cognitive_trend)
}
```

---

### 3.5 Layer 5：推荐决策引擎

这是AI的核心决策层。不再使用单一的「一个分类器+一个回归器」模式，而是一个**多层决策系统**。

#### 5A. 运动类型决策：级联判断树 + RF分类器

第一级：安全规则过滤 → 第二级：生理边界判定 → 第三级：ML分类器 → 第四级：情绪/认知微调

```
决策流程：

STEP 0: 安全规则检查（最高优先级，不可被ML覆盖）
├── HR > 0.9 × HRmax? → "STOP_EXERCISE"（立即停止，启动恢复协议）
├── HRV_SDNN < 基线 × 0.5? → "RECOVERY_ONLY"（仅允许恢复类活动）
├── temp_trend_slope > 1.0°C/min 持续3分钟? → "COOLDOWN"（热应激预警）
└── 通过安全规则 → 进入STEP 1

STEP 1: 生理边界判定（确定性规则）
├── autonomic_balance > 75 (交感主导)? → 候选类型：{breathing, recovery, light_movement}
├── cardiac_load > 75 (高负荷)? → 候选类型：{recovery, breathing}
├── circulatory < 30 (循环不良)? → 候选类型：{light_movement (热身优先)}
├── movement_quality < 30 (动作质量差)? → 候选类型：{breathing, light_movement (降低难度)}
└── 无边界限制 → 候选类型：全部6类开放 → 进入STEP 2

STEP 2: RF分类器（统计模型，特征→运动类型概率分布）
输入：全局状态向量 (约20维)
输出：每种运动类型的概率
{
    rest:              0.05,
    breathing:          0.35,  ← 最高概率
    light_movement:     0.25,
    moderate_aerobic:   0.20,
    high_intensity:     0.03,
    recovery:           0.12
}
候选类型(概率>0.2) = {breathing, light_movement, moderate_aerobic}

STEP 3: 情绪/认知微调（在ML候选中做最终选择）
├── emotion_quadrant == "HA-HV" (紧张)? → 优先 breathing
├── emotion_quadrant == "HA-LV" (兴奋)? → 优先 high_intensity 或 moderate_aerobic
├── emotion_quadrant == "LA-HV" (疲劳)? → 优先 light_movement (温和激活)
├── emotion_quadrant == "LA-LV" (满足)? → 优先 light_movement 或 moderate_aerobic (保持状态)
├── attention_score < 30? → 排除 high_intensity（注意力不足时高风险）
├── cognitive_score < 30? → 优先 breathing 或 light_movement (已知动作)
└── 综合选择 → 最终运动类型
```

#### 5B. 强度决策：SVR回归 + 上下文修正

```
基础强度 = SVR_regressor.predict(全局状态向量)  // 输出0-100

上下文修正（乘法因子，每个0.8-1.2）：
├── 情绪负效价? → ×0.85 (负面情绪时稍微降低强度，避免挫败感)
├── 注意力分散(attention<30)? → ×0.8 (注意力低时不宜高强度)
├── 认知疲劳(cognitive<30)? → ×0.85 (认知疲劳时身体训练效果也打折)
├── 运动质量差(movement<30)? → ×0.7 (动作变形时强度不是重点，先校准)
├── 高唤醒+正效价(兴奋)? → ×1.15 (状态好时可以稍微push)
├── 恢复准备度(recovery<30)? → ×0.7 (身体还没准备好)
└── 最终强度 = clamp(base_intensity × Π factors, 5, 95)
```

#### 5C. VR场景与感官参数决策

根据运动类型+情绪状态，自动选择VR环境和感官参数：

| 运动类型 | 情绪象限 | VR场景 | 音频 | 核心视觉引导 | 环境色调 |
|---------|---------|--------|------|------------|---------|
| breathing | HA-HV (紧张) | 海滩日落 | 432Hz + 海浪 | 呼吸环缩放 + GSR实时水滴(目标:水滴排空) | 暖橙→深蓝过渡 |
| breathing | LA-HV (疲劳) | 森林正念小径 | 528Hz + 鸟鸣 | 呼吸环 + Alpha功率光晕 | 翠绿暖光 |
| light_movement | 任意 | 山湖太极 | 528Hz + 自然 | 虚拟化身 + 目标球 | 暖黄 |
| moderate_aerobic | LA-LV (平静) | 森林小径 | 节奏渐进(120BPM) | HR区间环 | 绿色→金色 |
| moderate_aerobic | HA-LV (兴奋) | 海滩 | 节奏渐进(135BPM) | HR区间环 + 得分 | 亮蓝+金色 |
| high_intensity | HA-LV (兴奋) | 抽象空间 | 140-160BPM | 目标+连击分数+HR | 霓虹 |
| recovery | 任意 | 海滩日落 | 432Hz | 呼吸环 + HR↓指示器 | 慢慢暗下来 |

#### 5D. 实时反馈策略

AI推荐不只是"开始前选择场景"，还包括**运动过程中的实时自适应调整**：

| 实时监测信号 | 触发条件 | 自适应动作 |
|------------|---------|-----------|
| `rmssd_ms` 趋势 | 连续2个epoch下降 >20% | VR教练: "放慢一点，注意呼吸节奏" + HR区间环闪烁提醒 |
| `gsr_phasic_peak_count` | 突然增加 >3个/分钟 | 环境音频自动降低BPM + 天空色温变暖 |
| `alpha_asymmetry_fp` | 持续负效价 >5分钟 | 自动切换场景到森林 + 音频切换为自然声 |
| `theta_beta_ratio` | 突然升高 >1.0 (注意力大跌) | 简化运动目标 + 视觉引导增强(更大的目标球) |
| `temp_trend_slope` | >0.5°C/min持续 | 虚拟风扇动画 + 提示补充水分 |
| `movement_symmetry_LR` | >20%不对称 | 高亮偏弱侧 + 引导均衡发力 |

---

### 3.6 Layer 6：AI推荐输出 (Schema C 完整版)

基于以上六层分析的最终输出格式：

```json
{
  "recommendation_id": "uuid",
  "timestamp_unix_ms": 1717412415000,
  "session_id": "session_20240603_001",
  
  "user_global_state": {
    "body": {
      "cardiac_load_score": 45,
      "cardiac_load_label": "轻度负荷",
      "autonomic_balance_score": 72,
      "autonomic_balance_label": "交感轻度主导",
      "circulatory_score": 55,
      "movement_quality_score": 68
    },
    "mind": {
      "emotion_valence": -0.25,
      "emotion_arousal": 0.65,
      "emotion_quadrant": "HA-HV",
      "emotion_label": "轻度紧张",
      "attention_score": 48,
      "attention_label": "正常偏低",
      "relaxation_depth_score": 28,
      "relaxation_label": "不够放松"
    },
    "brain": {
      "cognitive_function_score": 62,
      "processing_speed_ms": 280,
      "executive_function_label": "正常",
      "working_memory_label": "正常"
    },
    "cross_domain": {
      "body_mind_coupling": "身心不同步(脑紧张>身体紧张)",
      "recovery_readiness_pct": 55
    }
  },
  
  "recommendation": {
    "exercise_type": "breathing_exercise",
    "exercise_subtype": "box_breathing_4_4_4_4",
    "intensity_pct": 25,
    "duration_minutes": 8,
    "target_hr_zone": 1,
    "target_metrics": {
      "rmssd_target_ms": 35,
      "gsr_tonic_target_us": 2.0,
      "alpha_asymmetry_target": -0.10,
      "alpha_power_target_pct_increase": 80
    },
    "vr_scene": "beach_sunset",
    "vr_audio": "waves_432hz",
    "vr_visual_cue": "breathing_ring_with_gsr_droplet",
    "vr_coach_prompts": [
      "吸气...感受腹部的扩张 (4秒)",
      "屏息...让氧气充分交换 (4秒)",
      "缓慢呼气...让紧张随气息流走 (4秒)",
      "暂停...感受这一刻的平静 (4秒)"
    ],
    "expected_effect": "预计8分钟后GSR基础水平将降至2.0μS以下，Alpha不对称将趋向正值减少"
  },
  
  "adaptive_triggers": {
    "if_rmssd_not_improving_3min": "switch_to_forest_mindfulness",
    "if_alpha_asymmetry_worsening": "add_528hz_audio_layer",
    "if_gsr_dropping_below_2us": "transition_to_light_movement"
  },
  
  "confidence": {
    "exercise_type_confidence": 0.89,
    "intensity_confidence": 0.82,
    "emotion_quadrant_confidence": 0.78,
    "attention_confidence": 0.85
  },
  
  "model_version": "rf_classifier_v2.1+svr_v2.0+emotion_v1.0"
}
```

---

### 3.7 实时处理循环（修订版）

```
初始化：
    load_personal_baseline(user_id)  // 加载该用户的静息基线
    load_models()                     // 加载RF/SVR/情绪模型

主循环 (每2秒一个tick):
    // Step 1: 拉取所有LSL流的最新数据
    samples = pull_all_lsl_inlets(timeout=0.2s)
    
    // Step 2: 写入环形缓冲区
    for each stream in samples:
        ring_buffers[stream.name].push(stream.data)
    
    // Step 3: 检查各域epoch是否就绪
    epoch_ready = {
        body: ring_buffers["HRV"].duration >= 60s,
        gsr:  ring_buffers["GSR"].duration >= 30s,
        eeg:  ring_buffers["EEG"].duration >= 10s,
        temp: ring_buffers["Temp"].duration >= 30s,
        acc:  ring_buffers["ACC"].duration >= 10s
    }
    
    // Step 4: 各域特征提取（独立并行）
    features = {}
    if epoch_ready.body:
        features.hrv = extract_hrv_features(ring_buffers["HRV"])
    if epoch_ready.gsr:
        features.gsr = extract_gsr_features(ring_buffers["GSR"])
    if epoch_ready.eeg:
        features.eeg = extract_eeg_features(ring_buffers["EEG"])
    
    // Step 5: 每30秒(15个tick)运行一次完整AI分析
    if tick_count % 15 == 0 AND features 足够完整:
        physio_state = assess_physiological_state(features, user_baseline)
        mental_state = assess_mental_state(features, user_baseline)
        if vr_cognitive_data_fresh():
            cognitive_state = assess_cognitive_state(vr_cognitive_data)
        global_state = fuse_states(physio_state, mental_state, cognitive_state)
        recommendation = decision_engine.decide(global_state, user_baseline)
        push_to_lsl("AIRecommendation", serialize_schema_c(recommendation))
        http_post("localhost:5000/recommendation", recommendation)
    
    // Step 6: 安全关键指标每2秒检查一次
    if hr_current > 0.9 * hr_max:
        emergency_stop()
    if abnormally_high_gsr_jump():
        trigger_calming_protocol()
```

---

### 3.8 个性化基线校准

每个用户首次使用时的**5分钟静息基线采集协议**是AI精准分析的基础：

| 采集阶段 | 时长 | 采集内容 | 建立基线 |
|---------|------|---------|---------|
| 静坐睁眼 | 2min | HR, HRV, GSR, EEG | 清醒静息基线 |
| 静坐闭眼 | 2min | HR, HRV, GSR, EEG | Alpha功率基线(闭眼Alpha应为最高) |
| 简单反应时测试 | 1min | VR反应时 | 认知速度基线 |

所有后续特征都**相对于个人基线进行z-score标准化**，而非使用绝对阈值。这确保AI推荐是个性化的。

---

### 3.9 AI管道技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| ECG/HRV处理 | NeuroKit2 0.2+ | R峰检测、HRV时域/频域/非线性特征 |
| EDA/GSR处理 | NeuroKit2 (cvxEDA) | 皮肤电导tonic/phasic分解、SCR峰值检测 |
| EEG处理 | MNE-Python 1.6+ | ICA去伪影、Welch PSD、频段功率提取 |
| 分类器 | scikit-learn RandomForest | 运动类型多分类 |
| 回归器 | scikit-learn SVR (RBF核) | 运动强度回归 |
| 情绪模型 | scikit-learn LogisticRegression | 情绪象限分类（4分类） |
| 注意力模型 | scikit-learn Ridge | 注意力量化回归 |
| 模型序列化 | joblib | .pkl模型持久化 |
| 特征存储 | pandas | 特征DataFrame管理 |
| 后端API | Flask + flask-cors | HTTP服务 |
| 数据存储 | SQLite (时间序列) + JSON (会话摘要) | 本地记录 |
| 实时流 | pylsl 1.16+ | LSL输入/输出 |

---

### 3.10 两套方案决策差异（直白版）

用一个真实的例子说明最终AI给出的指导有什么不同。

**同一个用户，同一时刻的生理状态：**
心率85bpm，微微出汗，呼吸稍快。

**方案一（低成本）看到的数据：**
> 心率85，属于Zone 2，RMSSD=28ms偏低，LF/HF=3.2偏高。
> → "心率有点快，压力指标偏高。建议做5分钟呼吸训练放松一下，心率降到Zone 1就行。"

**方案二（高精度）看到的数据：**
> 心率85(Zone 2)，RMSSD=28ms偏低，GSR tonic=4.8μS偏高，LF/HF=3.2偏高，Alpha不对称=+0.18(偏负面)，Theta/Beta比=1.3(注意力还行)，皮温=35.2°C正常，加速度幅值=0.12g运动量不大。
> → "你心率虽然不快但身体处于轻度紧张状态——交感神经偏活跃、情绪偏负面。不过注意力还算集中，身体温度正常，不是疲劳导致的。建议先做8分钟海滩场景盒式呼吸，目标是让RMSSD回到35ms以上、皮肤电导降到2.0μS以下。呼吸时注意看着面前的蓝色光环，它会随着你的呼气慢慢缩小，同时你的压力水滴图标也会逐渐排空。如果3分钟后额叶Alpha不对称还没改善，系统会自动帮你切换到森林正念漫步。"

**三句话总结差异：**

- **方案一看的是"数"——** 心率高了就降心率，压力高了就做呼吸。判断依据是两个趋势值，推荐内容是运动类型和强度。
- **方案二看的是"人"——** 心率为什么高？是运动累的还是紧张？情绪是积极的还是消极的？注意力还在不在？身体热不热？把这些串在一起，才知道用户真正需要什么。判断依据是六个维度交叉验证，推荐内容包含运动+情绪调节+注意力引导+环境适配+实时调整策略。
- **简单说：** 方案一像体温计，告诉你烧到多少度；方案二像医生，告诉你为什么发烧、该吃什么药、吃了没效怎么办。

---

## 四、目标三：VR头显结合方案

### 4.1 VR头显选择

**主推：Meta Quest 3 (~$500)**

- 内向外追踪、手势识别、BLE能力
- 两种运行模式：
  - **PC Link模式：** Quest作为显示器，所有处理在PC端，LSL直接在PC运行
  - **独立模式：** APK侧载到Quest，通过WiFi接收PC端的HTTP API数据

**备选：HTC Vive** — PC直连更简单，USB-C可接传感器

### 4.2 VR应用架构 (Unity)

```
Unity场景层级:
├── VRManager (单例)
│   ├── LSLReceiver (LSL4Unity) — 拉取AI推荐流 + 原始HR流
│   ├── BiofeedbackHUD
│   │   ├── HeartRateDisplay — 心率数字 + 区间颜色环
│   │   ├── BrainWaveViz — EEG五个频段柱状图
│   │   ├── StressGauge — GSR压力仪表盘
│   │   └── BreathingGuide — 呼吸引导动画球
│   ├── ExerciseSceneManager — 运动场景切换
│   └── EnvironmentController
│       ├── SkyboxChanger — 天空色温随压力变化
│       ├── AudioManager — 背景音频频率随HR区间变化
│       └── ParticleSystem — Alpha波高时萤火虫粒子
└── SessionLogger — 本地CSV+同步到PC
```

### 4.3 生物反馈可视化设计

| 反馈元素 | 显示内容 | 视觉设计 | 数据源 |
|---------|---------|---------|--------|
| HR区间环 | 脚部/腕部彩色环 | 蓝(Zone1)→绿(2)→黄(3)→橙(4)→红(5) | Polar H10实时HR |
| 心跳脉冲 | 实时心率跳动 | 与RR间期同步缩放的光球 | Polar H10 ECG |
| 脑波柱 | 5频段功率 | Delta/Theta/Alpha/Beta/Gamma柱状图 | Muse EEG |
| 压力计 | GSR唤醒度 | 水滴填充/排空，满=高压力 | Empatica E4 GSR |
| 呼吸引导 | 吸气/呼气提示 | 4s扩-4s持-4s缩-4s持 | AI推荐 |

### 4.4 环境自适应

| 环境参数 | 触发条件 | 效果 |
|---------|---------|------|
| 天空色温 | 压力指数 | 暖日落(平静) ↔ 冷灰色(压力) |
| 背景音频频率 | HR区间 | 432Hz(休息) → 528Hz(活跃) |
| 粒子密度 | EEG Alpha功率 | 放松时萤火虫增加 |
| 光照强度 | 注意力指数 | 注意力高时亮度增加 |
| 虚拟教练语音 | AI推荐 | "慢下来" / "继续保持" / "做得很好" |

### 4.5 四类VR运动场景

1. **海滩日落 — 呼吸训练：** 天空随呼吸节奏变换色调，海浪动画同步，432Hz背景音
2. **山湖 — 太极引导：** 虚拟化身演示动作，目标球出现在手部位置，528Hz环境音
3. **森林小径 — 正念漫步：** 程序化森林，音频引导感官注意，EEG Alpha化为手中光晕
4. **抽象空间 — 高强度挑战：** 霓虹网格，目标快速出现需要击打，音乐节奏随心率加速

### 4.6 网络拓扑

```
[PC: Python AI后端]  <--WiFi-->  [Meta Quest 3: Unity App]
     |                                  |
     | LSL流 (局域网)                    | LSL4Unity 拉取
     |                                  |
     +-- HTTP :5000/recommendation -->--+
```

LSL在同一WiFi子网下可跨设备工作。PC Link模式下，LSL完全在PC端运行，Quest仅作显示。

---

## 五、技术栈总览

```
层次              技术                           理由
──────────────────────────────────────────────────────────
传感器桥接        Python 3.10+ bleak pyLSL        生物信号处理最佳生态
信号处理          NeuroKit2 HeartPy MNE-Python    一站式ECG/HRV/EEG/EDA
AI/ML            scikit-learn (RF+SVR) joblib     小数据友好，可解释
后端服务          Flask + flask-cors sqlite3       轻量HTTP API
VR前端           Unity 2022 LTS LSL4Unity          VR工具链最成熟
                  Meta XR SDK / OpenXR
开发工具          Git VS Code Jupyter conda
```

### Python依赖 (requirements.txt)

```
numpy scipy pandas neurokit2 heartpy mne mne-nirs
pylsl scikit-learn joblib xgboost flask flask-cors
bleak pyyaml tqdm
```

---

## 六、实施阶段计划

### Phase 0: 环境搭建 (第1-2周)
- Python conda环境 + requirements.txt
- Unity 2022 LTS项目创建 + LSL4Unity导入
- Polar H10/Muse S BLE配对验证
- LSL流验证 (LabRecorder录制60秒测试)

### Phase 1: 数据采集管道 (第3-6周)
- polar_h10_streamer.py — BLE→LSL ECG流
- muse_streamer.py — Mind Monitor→LSL EEG流
- lsl_manager.py — 多流管理
- ring_buffer.py — 环形缓冲区
- json_schema.py — 四类JSON Schema序列化
- **交付：** `python main.py --sensors` 即可见两个LSL流

### Phase 2: 信号处理管道 (第7-10周)
- body_processor.py — ECG/HRV特征提取(NeuroKit2)
- mind_processor.py — EEG频段功率(Welch PSD)+去伪影(ICA)
- epoch_merger.py — 多模态时间对齐+Schema D输出
- **交付：** `python main.py --process` 输出epoch级特征向量

### Phase 3: AI管道开发 (第11-14周)
- 基准数据收集协议(5-10人×6段)
- train.py — RF分类器+SVR回归器训练
- inference.py — 实时推理模块
- rule_engine.py — 安全规则引擎
- server.py — Flask API (推荐拉取+会话管理)
- **交付：** `python main.py --full` 输出AI推荐到LSL+HTTP

### Phase 4: VR应用开发 (第15-18周)
- LSL4Unity集成 + VRBiofeedbackManager.cs
- BiofeedbackHUD (HR环+脑波柱+压力计+呼吸引导)
- 4个运动场景 (海滩/山湖/森林/抽象空间)
- EnvironmentController.cs (自适应环境)
- Quest APK构建与侧载测试
- **交付：** Quest端APK，端到端生物反馈闭环

### Phase 5: 集成测试与验证 (第19-20+周)
- 端到端延迟测量 (目标HR<500ms, AI推荐<2s)
- 10人试点研究 (20分钟/人)
- 模型精炼 (试点数据扩增训练集)
- 文档编写 (用户手册+开发者指南+研究报告)

### 目录结构

```
vr-body-mind-brain/
├── python_backend/
│   ├── sensors/        # polar_h10_streamer.py, muse_streamer.py
│   ├── processing/     # body_processor.py, mind_processor.py, epoch_merger.py
│   ├── ai/             # train.py, inference.py, rule_engine.py
│   ├── api/            # server.py
│   ├── utils/          # lsl_manager.py, json_schema.py
│   ├── config/         # settings.yaml
│   └── tests/
├── unity_vr/
│   └── Assets/
│       ├── Scripts/    # VRBiofeedbackManager.cs, EnvironmentController.cs
│       ├── Scenes/     # BeachSunset, MountainLake, ForestPath, AbstractSpace
│       └── Prefabs/    # HUD元素, 运动引导预制件
├── docs/               # architecture.md, sensor_setup_guide.md
├── data/               # raw_recordings/, labeled_epochs/, models/
└── README.md
```

---

## 七、关键架构决策

1. **LSL作为数据骨干：** 避免自定义网络协议，内置时间同步，神经生理学科研标准。两套方案共用同一条数据管道架构。
2. **Python后端 + Unity前端：** 生物信号处理Python生态最佳，VR工具链Unity最成熟。
3. **基于时间窗而非逐样本处理：** HRV和EEG PSD都需要数据窗口(10秒epoch)。
4. **四Schema JSON设计：** 原始采样/epoch特征/AI推荐/融合训练数据 各司其职。
5. **规则引擎作为安全层：** ML模型是统计性的，规则引擎强制执行生理安全约束。
6. **一源多用策略：** 单传感器通过软件挖掘多维信息（如HRV同时反映身、心、脑），这是低成本方案成立的核心逻辑。
7. **渐进式传感器升级：** 方案一($80)先跑通全链条，方案二($2,130)增加传感器流和特征维度，不推倒重建。
8. **PC端AI + Quest端渲染：** 重计算在PC，Quest专注渲染和交互。
