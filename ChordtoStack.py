import math
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class CTS:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體溢位

    self.n = int(n)
    self.words = self.generate_all_dyck_words(self.n)
    self.total_count = len(self.words)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 圓形節點座標設定 (順時鐘排列：起點從頂部開始往右/順時鐘)
    angles = np.pi / 2 - np.linspace(
        0, 2 * np.pi, 2 * self.n, endpoint=False
    )
    self.px, self.py = np.cos(angles), np.sin(angles)

    # 色彩盤配置
    self.colors = self.generate_rgb_palette(self.n)

    # 建立大畫布與 2x2 佈局
    self.fig = plt.figure(figsize=(21, 8.5))
    gs = self.fig.add_gridspec(
        2,
        2,
        width_ratios=[1, 1],
        height_ratios=[1, 1],
        wspace=0.15,
        hspace=0.25,
        bottom=0.06,
        top=0.88,
    )

    self.ax_static_circle = self.fig.add_subplot(
        gs[0, 0]
    )  # 左上：靜態完整圓中弦 (全實心)
    self.ax_full_stack = self.fig.add_subplot(
        gs[0, 1]
    )  # 右上：完整堆疊原圖 (靜態)
    self.ax_dyn_circle = self.fig.add_subplot(
        gs[1, 0]
    )  # 左下：動態彩色圓中弦動畫
    self.ax_dyn_stack = self.fig.add_subplot(
        gs[1, 1]
    )  # 右下：動態 Stack 堆疊進出

    self.update_display()

  def generate_rgb_palette(self, n):
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
      return [
          mcolors.to_hex(mcolors.hsv_to_rgb((i / n, 0.85, 0.90)))
          for i in range(n)
      ]

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

  def parse_word_metadata(self, word):
    step_ball_ids = {}
    step_colors = {}
    stack = []
    push_counter = 0
    for i, char in enumerate(word):
      if char == '(':
        push_counter += 1
        stack.append((i, push_counter))
        step_ball_ids[i] = push_counter
        step_colors[i] = self.colors[push_counter - 1]
      else:
        if len(stack) > 0:
          start_i, ball_id = stack.pop()
          step_ball_ids[i] = ball_id
          step_colors[i] = self.colors[ball_id - 1]
    return step_ball_ids, step_colors

  def get_full_permutation(self, word, step_ball_ids):
    stack = []
    pop_order = []
    for i, char in enumerate(word):
      ball_id = step_ball_ids.get(i, 1)
      if char == '(':
        stack.append(ball_id)
      else:
        if len(stack) > 0:
          pop_order.append(stack.pop())
    return pop_order

  def update_display(self):
    for ax in [
        self.ax_static_circle,
        self.ax_full_stack,
        self.ax_dyn_circle,
        self.ax_dyn_stack,
    ]:
      ax.clear()

    word = self.words[self.current_idx]
    current_view = word[: self.anim_step]
    step_ball_ids, step_colors = self.parse_word_metadata(word)

    # =================================================================
    # 1. [左上] 靜態完整圓中弦 (全實心點、順時鐘編號)
    # =================================================================
    self.ax_static_circle.set_xlim(-1.3, 1.3)
    self.ax_static_circle.set_ylim(-1.3, 1.3)
    self.ax_static_circle.set_aspect('equal')
    self.ax_static_circle.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )
    self.ax_static_circle.set_title(
        '1. Non-intersecting Chord', fontsize=11, fontweight='bold'
    )

    static_stack = []
    for i in range(2 * self.n):
      if word[i] == '(':
        static_stack.append(i)
      else:
        if static_stack:
          s_node = static_stack.pop()
          self.ax_static_circle.plot(
              [self.px[s_node], self.px[i]],
              [self.py[s_node], self.py[i]],
              color='black',
              lw=2.5,
              zorder=2,
          )

    for i in range(2 * self.n):
      self.ax_static_circle.scatter(
          self.px[i], self.py[i], color='black', s=45, zorder=3
      )
      self.ax_static_circle.text(
          self.px[i] * 1.25,
          self.py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          fontsize=9,
      )
    self.ax_static_circle.axis('off')

    # =================================================================
    # 2. [右上] 完整堆疊原圖 (靜態 Stack Permutation)
    # =================================================================
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}
    self.ax_full_stack.set_title(
        '2. Stack Permutation', fontsize=11, fontweight='bold', pad=10
    )
    self.ax_full_stack.text(
        -0.1,
        1.05,
        f'',
        fontdict=font_prop,
        ha='left',
        va='top',
        transform=self.ax_full_stack.transAxes,
        color='#7f8c8d',
    )
    self.ax_full_stack.text(
        0.02,
        0.70,
        'Input Order:',
        fontsize=10,
        fontweight='bold',
        color='#34495e',
        va='center',
    )
    self.ax_full_stack.text(
        0.02,
        0.30,
        'Permutation:',
        fontsize=10,
        fontweight='bold',
        color='#34495e',
        va='center',
    )

    x_base = 0.28
    spacing_x = 0.65 / max(self.n, 1)
    ax3_ball_size = (
        max(60, 280 - (self.n - 4) * 12) if self.n > 4 else 280
    )

    for i in range(self.n):
      cx = x_base + i * spacing_x
      ball_color = self.colors[i]
      self.ax_full_stack.scatter(
          cx, 0.70, color=ball_color, s=ax3_ball_size, zorder=3
      )
      self.ax_full_stack.text(
          cx,
          0.70,
          str(i + 1),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=9,
          zorder=4,
      )
      self.ax_full_stack.text(
          cx,
          0.50,
          '↓',
          ha='center',
          va='center',
          color='#bdc3c7',
          fontsize=10,
      )

    full_permutation = self.get_full_permutation(word, step_ball_ids)
    for i, ball_id in enumerate(full_permutation):
      cx = x_base + i * spacing_x
      ball_color = self.colors[ball_id - 1]
      self.ax_full_stack.scatter(
          cx,
          0.30,
          facecolors='white',
          edgecolors=ball_color,
          lw=2.0,
          s=ax3_ball_size * 0.9,
          zorder=3,
      )
      self.ax_full_stack.text(
          cx,
          0.30,
          str(ball_id),
          ha='center',
          va='center',
          color=ball_color,
          fontweight='bold',
          fontsize=9,
          zorder=4,
      )

    self.ax_full_stack.set_xlim(0, 1.0)
    self.ax_full_stack.set_ylim(0, 1.0)
    self.ax_full_stack.axis('off')

    # =================================================================
    # 3. [左下] 動態彩色圓中弦動畫 (邊畫邊上色、弦中間以實心邊線空心圓標號)
    # =================================================================
    self.ax_dyn_circle.set_xlim(-1.3, 1.3)
    self.ax_dyn_circle.set_ylim(-1.3, 1.3)
    self.ax_dyn_circle.set_aspect('equal')
    self.ax_dyn_circle.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )
    self.ax_dyn_circle.set_title(
        f'3. Dynamic Non-intersecting Chord (Step:{self.anim_step}/{2*self.n})',
        fontsize=11,
        fontweight='bold',
    )

    # 先畫出全部所有的灰色底點與數字標籤
    for i in range(2 * self.n):
      self.ax_dyn_circle.scatter(
          self.px[i], self.py[i], color='#bdc3c7', s=45, zorder=2
      )
      self.ax_dyn_circle.text(
          self.px[i] * 1.25,
          self.py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          fontsize=9,
      )

    colored_nodes = set()
    dyn_circle_stack = []
    for i in range(self.anim_step):
      char = word[i]
      ball_id = step_ball_ids.get(i)
      c = step_colors.get(i, '#333333')

      if char == '(':
        # 左端點 (PUSH)：實心上色
        dyn_circle_stack.append((i, ball_id))
        colored_nodes.add(i)
        self.ax_dyn_circle.scatter(
            self.px[i], self.py[i], color=c, s=55, zorder=4
        )
      else:
        # 右端點 (POP)：畫弦、圓形實心邊線空心標號、右端點空心
        if len(dyn_circle_stack) > 0:
          s_node, s_ball_id = dyn_circle_stack.pop()
          sc = self.colors[s_ball_id - 1]

          # 畫彩色弦
          self.ax_dyn_circle.plot(
              [self.px[s_node], self.px[i]],
              [self.py[s_node], self.py[i]],
              color=sc,
              lw=3.5,
              zorder=3,
          )

          # 弦中點位置：繪製實心邊線、內部填白的圓形標號
          mid_x = (self.px[s_node] + self.px[i]) / 2.0
          mid_y = (self.py[s_node] + self.py[i]) / 2.0

          self.ax_dyn_circle.scatter(
              mid_x,
              mid_y,
              facecolors='white',
              edgecolors=sc,
              lw=2.0,
              s=220,
              zorder=5,
          )
          self.ax_dyn_circle.text(
              mid_x,
              mid_y,
              str(s_ball_id),
              ha='center',
              va='center',
              fontsize=9,
              fontweight='bold',
              color=sc,
              zorder=6,
          )

          # 起點實心
          colored_nodes.add(s_node)
          self.ax_dyn_circle.scatter(
              self.px[s_node], self.py[s_node], color=sc, s=55, zorder=4
          )

          # 終點空心
          colored_nodes.add(i)
          self.ax_dyn_circle.scatter(
              self.px[i],
              self.py[i],
              facecolors='white',
              edgecolors=sc,
              lw=2,
              s=60,
              zorder=4,
          )

    self.ax_dyn_circle.axis('off')

    # =================================================================
    # 4. [右下] 動態 Stack 堆疊進出動畫
    # =================================================================
    self.ax_dyn_stack.set_title(
        '4. Dynamic Stack Permutation', fontsize=11, fontweight='bold', pad=10
    )
    self.ax_dyn_stack.set_aspect('equal')

    ball_radius = (
        0.22 if self.n <= 4 else max(0.08, 0.22 - (self.n - 4) * 0.01)
    )
    x_spacing = ball_radius * 2.1
    tube_left = 0.4
    tube_height = ball_radius * 2 + 0.06
    tube_length = self.n * x_spacing + 0.15
    tube_right = tube_left + tube_length
    tube_y_center = 1.8

    self.ax_dyn_stack.plot(
        [tube_right, tube_left, tube_left, tube_right],
        [
            tube_y_center + tube_height / 2,
            tube_y_center + tube_height / 2,
            tube_y_center - tube_height / 2,
            tube_y_center - tube_height / 2,
        ],
        color='#4f5d73',
        lw=3,
        zorder=2,
    )

    curr_stack, current_pop_order = [], []
    last_action = 'START'
    for i, char in enumerate(current_view):
      b_id = step_ball_ids[i]
      if char == '(':
        curr_stack.append(b_id)
        last_action = f'Step {i+1}: PUSH 球 {b_id}'
      else:
        if len(curr_stack) > 0:
          current_pop_order.append(curr_stack.pop())
          last_action = f'Step {i+1}: POP'

    for level, b_id in enumerate(curr_stack):
      cx = tube_left + ball_radius + 0.05 + level * x_spacing
      self.ax_dyn_stack.add_patch(
          plt.Circle(
              (cx, tube_y_center),
              ball_radius,
              color=self.colors[b_id - 1],
              zorder=3,
          )
      )
      self.ax_dyn_stack.text(
          cx,
          tube_y_center,
          str(b_id),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=9,
          zorder=4,
      )

    self.ax_dyn_stack.text(
        (tube_left + tube_right) / 2,
        tube_y_center - 0.85,
        last_action,
        ha='center',
        va='center',
        fontsize=10,
        fontweight='bold',
        color='#e67e22',
    )

    pop_base_y = tube_y_center - 1.55
    self.ax_dyn_stack.text(
        tube_left - 0.1,
        pop_base_y,
        'POP order:',
        fontsize=10,
        fontweight='bold',
        color='#e67e22',
        va='center',
        ha='right',
    )
    for i in range(self.n):
      bx = tube_left + ball_radius + 0.05 + (i * x_spacing)
      if i < len(current_pop_order):
        p_id = current_pop_order[i]
        c = self.colors[p_id - 1]
        self.ax_dyn_stack.add_patch(
            plt.Circle(
                (bx, pop_base_y),
                ball_radius * 0.9,
                fill=False,
                edgecolor=c,
                lw=2.5,
                zorder=3,
            )
        )
        self.ax_dyn_stack.text(
            bx,
            pop_base_y,
            str(p_id),
            ha='center',
            va='center',
            color=c,
            fontweight='bold',
            fontsize=9,
            zorder=4,
        )
      else:
        self.ax_dyn_stack.add_patch(
            plt.Circle(
                (bx, pop_base_y),
                ball_radius * 0.9,
                fill=False,
                edgecolor='#e0e0e0',
                lw=1.5,
                zorder=3,
            )
        )

    self.ax_dyn_stack.set_xlim(-0.1, max(tube_right + 0.4, 3.5))
    self.ax_dyn_stack.set_ylim(-0.4, tube_y_center + 1.4)
    self.ax_dyn_stack.axis('off')

    # 總標題
    self.fig.suptitle(
        'Catalan Bijection Mapping  |  Page'
        f' #{self.current_idx+1}/{self.total_count}\n',
        fontsize=13,
        fontweight='bold',
        y=0.96,
    )
    self.fig.canvas.draw_idle()

