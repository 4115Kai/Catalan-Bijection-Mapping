import math
import matplotlib.pyplot as plt
import numpy as np


class ATC:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)
    self.words = self.generate_all_dyck_words(self.n)
    self.total_count = len(self.words)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n + 1  # 總步數為頂點掃描完畢
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False

    # --- 計算圖形基礎位置 ---
    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, 2 * self.n, endpoint=False)
    self.circle_px, self.circle_py = np.cos(angles), np.sin(angles)

    self.linear_x = np.arange(2 * self.n)
    self.linear_y = np.zeros(2 * self.n)

    # 建立大型畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 劃分 2x2 的網格 (調整邊界以利網格呈現)
    gs = self.fig.add_gridspec(
        2, 2, wspace=0.15, hspace=0.35, bottom=0.06, top=0.88
    )
    self.ax1 = self.fig.add_subplot(gs[0, 0])
    self.ax2 = self.fig.add_subplot(gs[0, 1])
    self.ax3 = self.fig.add_subplot(gs[1, 0])
    self.ax4 = self.fig.add_subplot(gs[1, 1])

    # 首次繪製
    self.update_display()

  def generate_all_dyck_words(self, n):
    words = []

    def backtrack(s, o, c):
      if len(s) == 2 * n:
        words.append(s)
        return
      if o < n:
        backtrack(s + '(', o + 1, c)
      if c < o:
        backtrack(s + ')', o, c + 1)

    backtrack('', 0, 0)
    return sorted(words)

  def get_rgb_color(self, val, max_val):
    return plt.cm.rainbow(val / max_val)

  def update_display(self):
    # 清空繪圖軸線避免重疊殘留
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    word = self.words[self.current_idx]
    current_view = word[: self.anim_step]
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}

    bg_node_color = '#e0e0e0'
    orig_color = '#7f8c8d'
    max_color_idx = max(2 * self.n - 1, 1)

    # =================================================================
    # 1. 圓形不相交弦視圖 (RGB 動態進度)
    # =================================================================
    self.ax3.set_aspect('equal')
    self.ax3.add_artist(
        plt.Circle((0, 0), 1, color='#f8f9fa', fill=True, zorder=1)
    )
    self.ax3.set_title(
        f'3. Non-Intersecting Chord (Step: {self.anim_step}) ',
        fontsize=11,
        fontweight='bold',
        pad=12,
    )

    title_step_detail = ''
    self.ax3.text(
        -0.1,
        1.2,
        title_step_detail,
        fontdict=font_prop,
        ha='left',
        va='top',
        transform=self.ax3.transAxes,
        color='#2c3e50',
    )

    self.ax3.scatter(
        self.circle_px, self.circle_py, color=bg_node_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax3.text(
          self.circle_px[i] * 1.25,
          self.circle_py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          color=color,
          fontweight='bold',
          fontsize=9,
      )

    # =================================================================
    # 2. 直線拉直視圖 (RGB 動態進度)
    # =================================================================
    self.ax4.set_title(
        f'4. Non-Crossing Arc Diagram (Step: {self.anim_step})', fontsize=11, fontweight='bold', pad=12
    )
    self.ax4.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax4.scatter(
        self.linear_x, self.linear_y, color=bg_node_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax4.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color=color,
          fontweight='bold',
          fontsize=9,
      )

    # 執行上排動態堆疊配對
    stack = []
    for i, char in enumerate(current_view):
      current_rgb = self.get_rgb_color(i, max_color_idx)
      if char == '(':
        stack.append(i)
        self.ax3.scatter(
            self.circle_px[i],
            self.circle_py[i],
            color=current_rgb,
            s=80,
            edgecolors='white',
            zorder=4,
        )
        self.ax4.scatter(
            self.linear_x[i],
            self.linear_y[i],
            color=current_rgb,
            s=80,
            edgecolors='white',
            zorder=4,
        )
      else:
        if len(stack) > 0:
          start_node = stack.pop()
          line_rgb = self.get_rgb_color(start_node, max_color_idx)

          self.ax3.plot(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=line_rgb,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )

          center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
          theta = np.linspace(0, np.pi, 100)
          self.ax4.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=line_rgb,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )

          self.ax3.scatter(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=line_rgb,
              s=50,
              zorder=5,
          )
          self.ax4.scatter(
              [self.linear_x[start_node], self.linear_x[i]],
              [0, 0],
              color=line_rgb,
              s=50,
              zorder=5,
          )

    # =================================================================
    # 3. 圓形不相交弦視圖 (完整參考)
    # =================================================================
    self.ax1.set_aspect('equal')
    self.ax1.add_artist(
        plt.Circle((0, 0), 1, color='#f8f9fa', fill=True, zorder=1)
    )
    self.ax1.set_title(
        '1. Non-Intersecting Chord ', fontsize=11, fontweight='bold', pad=12
    )
    self.ax1.text(
        -0.1,
        1.2,
        '',
        fontdict=font_prop,
        ha='left',
        va='top',
        transform=self.ax1.transAxes,
        color='#7f8c8d',
    )

    self.ax1.scatter(
        self.circle_px, self.circle_py, color=orig_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      self.ax1.text(
          self.circle_px[i] * 1.25,
          self.circle_py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          color='#34495e',
          fontweight='bold',
          fontsize=9,
      )

    # =================================================================
    # 4. 直線拉直視圖 (完整參考)
    # =================================================================
    self.ax2.set_title(
        '2. Non-Crossing Arc Diagram ', fontsize=11, fontweight='bold', pad=12
    )
    self.ax2.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax2.scatter(
        self.linear_x, self.linear_y, color=orig_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      self.ax2.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color='#34495e',
          fontweight='bold',
          fontsize=9,
      )

    # 繪製下排完整靜態原圖
    orig_stack = []
    for i, char in enumerate(word):
      if char == '(':
        orig_stack.append(i)
      else:
        if len(orig_stack) > 0:
          start_node = orig_stack.pop()
          self.ax1.plot(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=orig_color,
              lw=2,
              alpha=0.7,
              zorder=2,
          )

          center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
          theta = np.linspace(0, np.pi, 100)
          self.ax2.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=orig_color,
              lw=2,
              alpha=0.7,
              zorder=2,
          )

          self.ax1.scatter(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=orig_color,
              s=40,
              zorder=5,
          )
          self.ax2.scatter(
              [self.linear_x[start_node], self.linear_x[i]],
              [0, 0],
              color=orig_color,
              s=40,
              zorder=5,
          )

    # --- 四格範圍、刻度關閉與邊界收斂設定 ---
    for ax in [self.ax1, self.ax3]:
      ax.axis('off')
      ax.set_xlim(-1.4, 1.4)
      ax.set_ylim(-1.4, 1.4)

    max_h = (2 * self.n - 1) / 2
    for ax in [self.ax2, self.ax4]:
      ax.axis('off')
      ax.set_xlim(-0.7, 2 * self.n - 0.3)
      ax.set_ylim(-0.8, max(max_h + 0.5, 2.0))
      ax.set_aspect('equal')

    # 總體主標題
    self.fig.suptitle(
        'Catalan Bijection Mapping  | '
        f' Page #{self.current_idx+1}/{self.total_count}\n',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()


