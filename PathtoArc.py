import math
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


class DTA:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體溢位

    self.n = int(n)
    self.words = self.generate_all_dyck_words(self.n)
    self.total_count = len(self.words)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # 2n 步完成
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 色彩盤配置 (1~n 個元素/配對擁有獨特專屬顏色)
    self.colors = self.generate_rgb_palette(self.n)

    # 計算基礎點位
    self.linear_x = np.arange(2 * self.n)
    self.linear_y = np.zeros(2 * self.n)

    # 建立畫布與 2x2 佈局
    self.fig = plt.figure(figsize=(20, 8.5))
    gs = self.fig.add_gridspec(
        2, 2, wspace=0.15, hspace=0.35, bottom=0.06, top=0.88
    )

    # 四個子圖佈局
    self.ax_static_arc = self.fig.add_subplot(gs[0, 0])  # 上排左：Arc 靜態圖
    self.ax_static_dyck = self.fig.add_subplot(gs[0, 1])  # 上排右：Dyck 靜態圖
    self.ax_anim_arc = self.fig.add_subplot(gs[1, 0])  # 下排左：Arc 動態進度
    self.ax_anim_dyck = self.fig.add_subplot(gs[1, 1])  # 下排右：Dyck 動態進度

    self.update_display()

  def generate_rgb_palette(self, n):
    n = int(n)
    classic_colors = [
        '#FF3B30',
        '#34C759',
        '#007AFF',
        '#FFCC00',
        '#AF52DE',
        '#5AC8FA',
        '#FF9500',
    ]
    if n <= len(classic_colors):
      return classic_colors[:n]
    else:
      palette = []
      for i in range(n):
        hue = i / n
        rgb = mcolors.hsv_to_rgb((hue, 0.85, 0.90))
        palette.append(mcolors.to_hex(rgb))
      return palette

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

  def update_display(self):
    for ax in [
        self.ax_static_arc,
        self.ax_static_dyck,
        self.ax_anim_arc,
        self.ax_anim_dyck,
    ]:
      ax.clear()

    word = self.words[self.current_idx]
    current_view = word[: self.anim_step]

    bg_node_color = '#e0e0e0'
    orig_color = '#7f8c8d'

    # 計算括號配對關係與相對應的色彩 mapping
    color_mapping = {}
    stack = []
    pair_counter = 0
    for i, char in enumerate(word):
      if char == '(':
        color_mapping[i] = self.colors[pair_counter % self.n]
        stack.append(pair_counter)
        pair_counter += 1
      elif stack:
        p_idx = stack.pop()
        color_mapping[i] = self.colors[p_idx % self.n]

    # =================================================================
    # 1. 上排左側：Arc Diagram (靜態完整圖)
    # =================================================================
    self.ax_static_arc.set_title(
        '1. Non-crossing Arc Diagram', fontsize=12, fontweight='bold', pad=12
    )
    self.ax_static_arc.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax_static_arc.scatter(
        self.linear_x, self.linear_y, color=orig_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      self.ax_static_arc.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color='#34495e',
          fontweight='bold',
          fontsize=9,
      )

    orig_stack = []
    for i, char in enumerate(word):
      if char == '(':
        orig_stack.append(i)
      elif orig_stack:
        start_node = orig_stack.pop()
        center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
        radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
        theta = np.linspace(0, np.pi, 100)
        self.ax_static_arc.plot(
            center_x + radius * np.cos(theta),
            radius * np.sin(theta),
            color=color_mapping[start_node],
            lw=2,
            alpha=0.85,
            zorder=2,
        )
        self.ax_static_arc.scatter(
            [self.linear_x[start_node], self.linear_x[i]],
            [0, 0],
            color=color_mapping[start_node],
            s=40,
            zorder=5,
        )

    # =================================================================
    # 2. 上排右側：Dyck Path (靜態完整圖)
    # =================================================================
    self.ax_static_dyck.set_title(
        f'2. Dyck Path ({word})', fontsize=12, fontweight='bold', pad=12
    )
    for h in range(self.n + 1):
      self.ax_static_dyck.plot(
          [0, 2 * self.n], [h, h], color='gray', alpha=0.15, linestyle=':'
      )
    for i in range(2 * self.n + 1):
      self.ax_static_dyck.plot(
          [i, i], [0, self.n], color='gray', alpha=0.15, linestyle=':'
      )
    self.ax_static_dyck.plot([0, 2 * self.n], [0, 0], 'k-', alpha=0.3, lw=1.2)

    x, y = 0, 0
    path_coords = [(0, 0)]
    for char in word:
      x += 1
      y += 1 if char == '(' else -1
      path_coords.append((x, y))
    px, py = zip(*path_coords)
    self.ax_static_dyck.plot(
        px, py, 'o-', color='#34495e', lw=2.5, ms=5, zorder=3
    )

    # =================================================================
    # 3. 下排左側：Arc Diagram (動態進度)
    # =================================================================
    self.ax_anim_arc.set_title(
        f'3. Dynamic Arc Diagram (Step: {self.anim_step} / {2*self.n})',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    self.ax_anim_arc.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax_anim_arc.scatter(
        self.linear_x, self.linear_y, color=bg_node_color, s=40, zorder=3
    )
    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax_anim_arc.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color=color,
          fontweight='bold',
          fontsize=9,
      )

    anim_stack = []
    for i, char in enumerate(current_view):
      current_rgb = color_mapping[i]
      if char == '(':
        anim_stack.append(i)
        self.ax_anim_arc.scatter(
            self.linear_x[i],
            self.linear_y[i],
            color=current_rgb,
            s=80,
            edgecolors='white',
            zorder=4,
        )
      else:
        if len(anim_stack) > 0:
          start_node = anim_stack.pop()
          line_rgb = color_mapping[start_node]

          center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
          theta = np.linspace(0, np.pi, 100)
          self.ax_anim_arc.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=line_rgb,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )
          self.ax_anim_arc.scatter(
              [self.linear_x[start_node], self.linear_x[i]],
              [0, 0],
              color=line_rgb,
              s=50,
              zorder=5,
          )

    # =================================================================
    # 4. 下排右側：Dyck Path Progress (動態進度)
    # =================================================================
    step_str = current_view + '_' * (2 * self.n - self.anim_step)
    self.ax_anim_dyck.set_title(
        f'4. Dyck Path Progress {step_str}',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    for h in range(self.n + 1):
      self.ax_anim_dyck.plot(
          [0, 2 * self.n], [h, h], color='gray', alpha=0.15, linestyle=':'
      )
    for i in range(2 * self.n + 1):
      self.ax_anim_dyck.plot(
          [i, i], [0, self.n], color='gray', alpha=0.15, linestyle=':'
      )
    self.ax_anim_dyck.plot([0, 2 * self.n], [0, 0], 'k-', alpha=0.3, lw=1.2)

    cur_x, cur_y = 0, 0
    dyck_stack = []

    for i, char in enumerate(current_view):
      next_x = cur_x + 1
      next_y = cur_y + (1 if char == '(' else -1)
      seg_color = color_mapping[i]

      # 繪製當前步的 Dyck Path 實線段
      self.ax_anim_dyck.plot(
          [cur_x, next_x],
          [cur_y, next_y],
          'o-',
          color=seg_color,
          lw=3,
          ms=6,
          zorder=4,
      )

      # 顯示步驟數字
      mid_x = (cur_x + next_x) / 2.0
      mid_y = (cur_y + next_y) / 2.0
      self.ax_anim_dyck.text(
          mid_x,
          mid_y + 0.35,
          str(i + 1),
          color=seg_color,
          fontsize=8,
          fontweight='bold',
          ha='center',
          va='center',
          zorder=6,
          bbox=dict(
              boxstyle='circle,pad=0.25',
              facecolor='white',
              edgecolor=seg_color,
              linewidth=1.2,
          ),
      )

      if char == '(':
        dyck_stack.append((cur_x, cur_y, next_x, next_y))
      else:
        if dyck_stack:
          up_x1, up_y1, up_x2, up_y2 = dyck_stack.pop()

          mid_up_x, mid_up_y = (up_x1 + up_x2) / 2, (up_y1 + up_y2) / 2
          mid_down_x, mid_down_y = (cur_x + next_x) / 2, (cur_y + next_y) / 2

          self.ax_anim_dyck.plot(
              [mid_up_x, mid_down_x],
              [mid_up_y, mid_down_y],
              linestyle='--',
              color=seg_color,
              lw=2,
              alpha=0.85,
              zorder=2,
          )

      cur_x, cur_y = next_x, next_y

    # 設定邊界與比例
    max_h = (2 * self.n - 1) / 2
    for ax in [self.ax_static_arc, self.ax_anim_arc]:
      ax.axis('off')
      ax.set_xlim(-0.7, 2 * self.n - 0.3)
      ax.set_ylim(-0.8, max(max_h + 0.5, 2.0))
      ax.set_aspect('equal')

    for ax in [self.ax_static_dyck, self.ax_anim_dyck]:
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-0.5, self.n + 0.5)
      ax.set_aspect('equal')
      ax.axis('off')

    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        'Catalan Bijection Mapping  | Page'
        f' #{self.current_idx+1}/{catalan_num}\n',
        fontsize=13,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()

