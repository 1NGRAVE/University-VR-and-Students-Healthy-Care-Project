"""Generate figures for the VR Body-Mind-Brain paper."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc, Wedge, Circle, Rectangle
import numpy as np
import os

output_dir = 'docs/paper_figures'
os.makedirs(output_dir, exist_ok=True)

plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# Figure 1: System Architecture Overview
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor('#FAFBFC')

# Title
ax.text(8, 9.5, 'VR身心脑协同训练系统总体架构', ha='center', va='center',
        fontsize=18, fontweight='bold', color='#1a1a2e')

# Box drawing helper
def draw_box(ax, x, y, w, h, text, color, text_color='white', fontsize=10, bold=False):
    rect = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.15",
                          facecolor=color, edgecolor='#333', linewidth=1.5, alpha=0.92)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=text_color, fontweight='bold' if bold else 'normal')
    return rect

# Sensor Layer
ax.text(8, 8.85, '数据采集层 (Sensing Layer)', ha='center', va='center',
        fontsize=13, fontweight='bold', color='#2d3436')
draw_box(ax, 3, 7.6, 5.2, 1.5,
         '方案一 (低成本 ~$80)\nPolar H10 ECG/HRV + VR内置追踪',
         '#0984e3', 'white', 9)
draw_box(ax, 12, 7.6, 5.5, 1.5,
         '方案二 (高精度 ~$2,130)\nPolar H10 + Muse S EEG + Empatica E4',
         '#6c5ce7', 'white', 9)

# Arrow sensor -> LSL
ax.annotate('', xy=(8, 6.5), xytext=(8, 7.0),
            arrowprops=dict(arrowstyle='->', color='#333', lw=2.5))

# LSL Layer
draw_box(ax, 8, 6.05, 13, 1.1,
         '数据传输层: Lab Streaming Layer (LSL) — 多设备时间同步 · 实时流传输',
         '#00b894', 'white', 10, True)

# Arrow LSL -> Processing
ax.annotate('', xy=(8, 5.1), xytext=(8, 5.55),
            arrowprops=dict(arrowstyle='->', color='#333', lw=2.5))

# Signal Processing
draw_box(ax, 8, 4.65, 13, 1.1,
         '信号处理层: NeuroKit2 (ECG/HRV/EDA) · MNE-Python (EEG) · HeartPy',
         '#e17055', 'white', 10, True)

# Arrow Processing -> AI
ax.annotate('', xy=(8, 3.7), xytext=(8, 4.15),
            arrowprops=dict(arrowstyle='->', color='#333', lw=2.5))

# AI Engine
ai_layers = [
    ('L1 生理状态评估', '#fd79a8'),
    ('L2 心理情绪评估', '#e84393'),
    ('L3 认知状态评估', '#d63031'),
    ('L4 综合状态融合', '#e17055'),
    ('L5 推荐决策引擎', '#fdcb6e'),
    ('L6 VR适配输出', '#00b894'),
]
for i, (label, color) in enumerate(ai_layers):
    x_pos = 1.5 + i * 2.3
    draw_box(ax, x_pos, 3.1, 2.1, 0.7, label, color, 'white', 8)

ax.text(8, 3.65, 'AI分析引擎 (6层递进式可解释管道)', ha='center', va='center',
        fontsize=12, fontweight='bold', color='#2d3436')

# Arrow AI -> VR
ax.annotate('', xy=(8, 2.3), xytext=(8, 2.75),
            arrowprops=dict(arrowstyle='->', color='#333', lw=2.5))

# VR Layer
draw_box(ax, 8, 1.7, 13, 1.3,
         'VR渲染层: Unity 2022 LTS + Meta Quest 3\n'
         '四类运动场景 · 实时生物反馈HUD · 环境自适应渲染',
         '#2d3436', 'white', 10, True)

# Data flow arrows on sides
for y_pos, label in [(7.6, 'LSL\nStream'), (4.65, 'JSON\nHTTP'), (1.7, 'LSL+HTTP')]:
    ax.annotate('', xy=(15.5, y_pos-0.3), xytext=(15.5, y_pos+0.3),
                arrowprops=dict(arrowstyle='->', color='#636e72', lw=1.5))

# Legend
legend_text = (
    '硬件: Meta Quest 3 VR头显 + 多模态生理传感器\n'
    '软件: Python 3.10+ (后端) · Unity 2022 LTS (前端)\n'
    '数据协议: LSL (实时流) · JSON/HTTP (AI推荐) · SQLite (存储)'
)
ax.text(8, 0.35, legend_text, ha='center', va='center', fontsize=9,
        color='#636e72', style='italic')

plt.tight_layout()
fig.savefig(f'{output_dir}/fig1_system_architecture.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('Figure 1 saved.')

# ============================================================
# Figure 2: AI Pipeline Detail
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(18, 11))
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis('off')
ax.set_facecolor('#FAFBFC')

ax.text(9, 10.6, '六层递进式AI分析管道', ha='center', va='center',
        fontsize=18, fontweight='bold', color='#1a1a2e')

layers_data = [
    {
        'num': 'L1', 'name': '生理状态评估\nPhysiological State',
        'y': 9.0, 'color': '#0984e3',
        'input': 'ECG·HRV (9维)\nVR运动追踪 (4维)\nPPG·TEMP·ACC (方案二)',
        'output': '心脏负荷评分\n自主神经平衡\n循环代谢指数\n运动质量评分',
        'method': 'HRV时域/频域/非线性\nNeuroKit2 + HeartPy\n规则加权评分'
    },
    {
        'num': 'L2', 'name': '心理情绪评估\nPsychological-Emotional',
        'y': 7.0, 'color': '#6c5ce7',
        'input': 'EEG 5频段功率 (方案二)\nGSR tonic/phasic (方案二)\nHRV RMSSD+LF/HF',
        'output': '效价-唤醒度坐标\n注意力评分(0-100)\n放松深度评分(0-100)',
        'method': 'Russell环状模型映射\n额叶Alpha不对称→效价\nGSR→唤醒度'
    },
    {
        'num': 'L3', 'name': '认知状态评估\nCognitive State',
        'y': 5.0, 'color': '#e17055',
        'input': 'VR Stroop测试\nVR N-back测试\n简单反应时\nEEG Gamma/Theta',
        'output': '处理速度评分\n执行功能评分\n工作记忆评分',
        'method': 'Stroop干扰效应\nN-back d\'敏感度\n反应时归一化'
    },
    {
        'num': 'L4', 'name': '综合状态融合\nIntegrative Fusion',
        'y': 3.0, 'color': '#00b894',
        'input': 'L1-L3 所有输出',
        'output': '全局状态向量\n身心耦合度\n脑身耦合度\n恢复准备度',
        'method': '可解释规则融合\n跨域耦合计算\n趋势加权综合'
    },
]

for layer in layers_data:
    y = layer['y']
    c = layer['color']

    # Layer number circle
    circle = Circle((1.0, y), 0.35, facecolor=c, edgecolor='#333', linewidth=2, zorder=3)
    ax.add_patch(circle)
    ax.text(1.0, y, layer['num'], ha='center', va='center', fontsize=14,
            fontweight='bold', color='white', zorder=4)

    # Layer name
    ax.text(2.2, y+0.15, layer['name'], ha='left', va='center', fontsize=11,
            fontweight='bold', color='#2d3436')

    # Input box
    rect_in = FancyBboxPatch((4.5, y-0.4), 3.5, 0.8, boxstyle="round,pad=0.1",
                             facecolor='#dfe6e9', edgecolor='#b2bec3', linewidth=1)
    ax.add_patch(rect_in)
    ax.text(6.25, y, layer['input'], ha='center', va='center', fontsize=7.5, color='#2d3436')

    # Arrow in -> process
    ax.annotate('', xy=(8.5, y), xytext=(8.0, y),
                arrowprops=dict(arrowstyle='->', color=c, lw=2))

    # Process box
    rect_proc = FancyBboxPatch((8.5, y-0.4), 3.5, 0.8, boxstyle="round,pad=0.1",
                               facecolor=c, edgecolor='#333', linewidth=1.5, alpha=0.15)
    ax.add_patch(rect_proc)
    ax.text(10.25, y, layer['method'], ha='center', va='center', fontsize=7.5,
            color='#2d3436', fontweight='bold')

    # Arrow process -> output
    ax.annotate('', xy=(12.5, y), xytext=(12.0, y),
                arrowprops=dict(arrowstyle='->', color=c, lw=2))

    # Output box
    rect_out = FancyBboxPatch((12.5, y-0.4), 3.5, 0.8, boxstyle="round,pad=0.1",
                              facecolor='#ffeaa7', edgecolor='#fdcb6e', linewidth=1)
    ax.add_patch(rect_out)
    ax.text(14.25, y, layer['output'], ha='center', va='center', fontsize=7.5, color='#2d3436')

# L5 & L6 are special - side by side at bottom
y_l5 = 1.5
# L5
circle5 = Circle((1.0, y_l5), 0.35, facecolor='#fdcb6e', edgecolor='#333', linewidth=2, zorder=3)
ax.add_patch(circle5)
ax.text(1.0, y_l5, 'L5', ha='center', va='center', fontsize=14,
        fontweight='bold', color='#2d3436', zorder=4)
ax.text(2.2, y_l5+0.15, '推荐决策引擎\nDecision Engine', ha='left', va='center',
        fontsize=11, fontweight='bold', color='#2d3436')

draw_box_v2 = lambda ax, x, y, w, h, text, c, tc='#2d3436', fs=7.5: (
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.1",
                 facecolor=c, edgecolor='#333', linewidth=1.5)),
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, color=tc, fontweight='bold')
)

draw_box_v2(ax, 7.5, y_l5, 7, 0.9,
            '安全规则门控 → 生理边界过滤 → RF运动分类 → SVR强度回归 → 上下文微调',
            '#ffeaa7', '#2d3436', 8)

# L6
y_l6 = 0.4
circle6 = Circle((1.0, y_l6), 0.35, facecolor='#00b894', edgecolor='#333', linewidth=2, zorder=3)
ax.add_patch(circle6)
ax.text(1.0, y_l6, 'L6', ha='center', va='center', fontsize=14,
        fontweight='bold', color='white', zorder=4)
ax.text(2.2, y_l6+0.15, 'VR适配输出\nVR Adaptation', ha='left', va='center',
        fontsize=11, fontweight='bold', color='#2d3436')

draw_box_v2(ax, 7.5, y_l6, 7, 0.9,
            '运动场景选择 → 音频频率匹配 → 视觉引导强度 → 环境参数自适应',
            '#55efc4', '#2d3436', 8)

# Down arrows between L4→L5 and L5→L6
ax.annotate('', xy=(1, 2.2), xytext=(1, 2.8),
            arrowprops=dict(arrowstyle='->', color='#636e72', lw=2))
ax.annotate('', xy=(1, 0.8), xytext=(1, 1.3),
            arrowprops=dict(arrowstyle='->', color='#636e72', lw=2))

# Global state vector label
ax.text(5.5, 2.5, '全局状态向量\nGlobal State Vector', ha='center', va='center',
        fontsize=8, color='#636e72', style='italic')

plt.tight_layout()
fig.savefig(f'{output_dir}/fig2_ai_pipeline.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('Figure 2 saved.')

# ============================================================
# Figure 3: Russell's Circumplex Model with Bio-signal Mapping
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(11, 10))
ax.set_xlim(-1.3, 1.3)
ax.set_ylim(-0.2, 1.2)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor('#FAFBFC')

ax.text(0, 1.12, "Russell's情绪环状模型与生理信号映射", ha='center', va='center',
        fontsize=16, fontweight='bold', color='#1a1a2e')

# Background quadrants with soft colors
quadrants = [
    ((-1.2, 0.5), 0.7, 0.5, '#ff7675', '高唤醒-负效价\nHA-HV\n紧张/焦虑'),
    ((0.5, 0.5), 0.7, 0.5, '#fdcb6e', '高唤醒-正效价\nHA-LV\n兴奋/激动'),
    ((-1.2, 0), 0.7, 0.5, '#81ecec', '低唤醒-负效价\nLA-HV\n悲伤/疲劳'),
    ((0.5, 0), 0.7, 0.5, '#55efc4', '低唤醒-正效价\nLA-LV\n放松/满足'),
]
for (x, y), w, h, color, label in quadrants:
    rect = Rectangle((x, y), w, h, facecolor=color, edgecolor='#ddd', linewidth=1, alpha=0.3)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=8, color='#2d3436', alpha=0.7)

# Axes
ax.axhline(y=0.5, color='#636e72', linewidth=2, linestyle='-', zorder=2)
ax.axvline(x=0, color='#636e72', linewidth=2, linestyle='-', zorder=2)

# Axis labels
ax.text(1.25, 0.48, '正效价\nPositive Valence', ha='center', va='top', fontsize=10, fontweight='bold', color='#0984e3')
ax.text(-1.25, 0.48, '负效价\nNegative Valence', ha='center', va='top', fontsize=10, fontweight='bold', color='#d63031')
ax.text(0.02, 1.05, '高唤醒 High Arousal', ha='left', va='center', fontsize=10, fontweight='bold', color='#e17055')
ax.text(0.02, -0.05, '低唤醒 Low Arousal', ha='left', va='center', fontsize=10, fontweight='bold', color='#00b894')

# Bio-signal mapping annotations
annotations = [
    (0.6, 0.85, 'GSR↑ + Beta↑\nLF/HF > 3', '#d63031', '兴奋/焦虑'),
    (-0.6, 0.85, 'GSR↑ + LF/HF > 3\nRMSSD < 20ms', '#d63031', '紧张/高压'),
    (0.6, 0.15, 'Alpha↑ + RMSSD↑\nTBR < 1.5', '#0984e3', '专注/满足'),
    (-0.6, 0.15, 'Alpha↑ + GSR↓\nLF/HF < 1', '#636e72', '冥想/放松'),
]
for x, y, text, color, label in annotations:
    ax.annotate(text, xy=(x*0.85, y*0.85), xytext=(x, y),
                fontsize=7, ha='center', va='center', color=color,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=color, alpha=0.85),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2))

# Center: bio-signal legend
ax.text(0, 0.5, '效价轴(X):\nEEG额叶Alpha不对称\n(AF8-AF7)/(AF8+AF7)',
        ha='center', va='center', fontsize=7, color='#636e72',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='#b2bec3', alpha=0.9))
ax.text(0, 0.45, '唤醒轴(Y):\nGSR皮肤电导\n+ LF/HF交叉验证',
        ha='center', va='top', fontsize=7, color='#636e72')

# VR scene recommendations
scene_annotations = [
    (-0.6, 0.65, '[海滩] 呼吸训练\n432Hz + 海浪', '#ff7675'),
    (0.6, 0.65, '[挑战] 抽象空间高强度\n140-160BPM', '#fdcb6e'),
    (-0.6, 0.3, '[森林] 正念漫步\n528Hz + 鸟鸣', '#81ecec'),
    (0.6, 0.3, '[山湖] 太极引导\n528Hz + 自然', '#55efc4'),
]
for x, y, text, color in scene_annotations:
    ax.text(x, y, text, ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=color, alpha=0.9, linewidth=1.5), color=color)

plt.tight_layout()
fig.savefig(f'{output_dir}/fig3_emotion_model.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('Figure 3 saved.')

# ============================================================
# Figure 4: Hardware Comparison Table (will be embedded as text in paper)
# Figure generated as a separate visualization
# ============================================================
fig, ax = plt.subplots(1, 1, figsize=(16, 5))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5)
ax.axis('off')

ax.text(8, 4.7, 'VR运动场景设计与生物反馈映射', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#1a1a2e')

# Scene cards
scenes = [
    ('海滩日落\nBreathing', '呼吸训练', '432Hz + 海浪', 'HR色环\n呼吸光球\nGSR水滴', '#ff7675', '暖橙→深蓝\n(随压力过渡)'),
    ('山湖\nTai Chi', '太极引导', '528Hz + 自然', '虚拟化身\n目标球\n关节指示', '#fdcb6e', '暖黄\n(稳定光)'),
    ('森林小径\nMindful Walk', '正念漫步', '528Hz + 鸟鸣', 'Alpha光晕\n步频指示\n心率环', '#55efc4', '翠绿暖光\n(粒子密度)'),
    ('抽象空间\nHigh Intensity', '高强度挑战', '140-160BPM', '连击分数\nHR区间\n目标环', '#0984e3', '霓虹\n(随HR加速)'),
]

for i, (name, type_, audio, viz, color, env) in enumerate(scenes):
    x = 1.5 + i * 3.5
    rect = FancyBboxPatch((x-1.5, 0.3), 3.0, 4.1, boxstyle="round,pad=0.2",
                          facecolor='white', edgecolor=color, linewidth=2.5)
    ax.add_patch(rect)
    # Header bar
    header = FancyBboxPatch((x-1.5, 3.8), 3.0, 0.6, boxstyle="round,pad=0.02",
                            facecolor=color, edgecolor='none')
    ax.add_patch(header)
    ax.text(x, 4.1, name, ha='center', va='center', fontsize=12,
            fontweight='bold', color='white')
    ax.text(x, 3.1, f'类型: {type_}', ha='center', va='center', fontsize=9, color='#2d3436')
    ax.text(x, 2.5, f'音频: {audio}', ha='center', va='center', fontsize=8, color='#636e72')
    ax.text(x, 1.9, f'生物反馈:\n{viz}', ha='center', va='center', fontsize=7.5, color='#2d3436')
    ax.text(x, 0.8, f'环境: {env}', ha='center', va='center', fontsize=7.5, color='#636e72')

plt.tight_layout()
fig.savefig(f'{output_dir}/fig4_vr_scenes.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print('Figure 4 saved.')

print(f'\nAll figures saved to {output_dir}/')
print('Files:')
for f in sorted(os.listdir(output_dir)):
    print(f'  {f}')
