import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


class Stack:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)
    self.words = self.generate_all_dyck_words(self.n)
    self.total_count = len(self.words)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # Push/Pop 共 2n 步
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False

    # 直線坐標設定
    self.linear_x = np.arange(2 * self.n)
    self.linear_y = np.zeros(2 * self.n)

    # 核心色彩
    self.colors = self.generate_rgb_palette(self.n)

    # 建立畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 劃分 2x2 網格：高度比例對調為 [0.7, 1.3] 確保下方動態視窗有足夠高度
    gs = self.fig.add_gridspec(
        2,
        2,
        width_ratios=[1, 1],
        height_ratios=[0.7, 1.3],
        wspace=0.18,
        hspace=0.38,
        bottom=0.06,
        top=0.88,
    )

    self.ax3 = self.fig.add_subplot(gs[0, 0])  # 1. 完整排列 (左上)
    self.ax4 = self.fig.add_subplot(gs[0, 1])  # 2. 完整弧線 (右上)
    self.ax1 = self.fig.add_subplot(gs[1, 0])  # 3. 動態堆疊 (左下)
    self.ax2 = self.fig.add_subplot(gs[1, 1])  # 4. 動態弧線 (右下)

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

  def parse_word_metadata(self, word):
    step_ball_ids = {}
    step_colors = {}
    stack = []
    push_counter = 0
    for i, char in enumerate(word):
      if char == '(':
        push_counter += 1
        ball_id = push_counter
        stack.append((i, ball_id))
        step_ball_ids[i] = ball_id
        step_colors[i] = self.colors[ball_id - 1]
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
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    word = self.words[self.current_idx]
    current_view = word[: self.anim_step]
    status_str = 'PLAYING' if self.is_playing else 'PAUSED'
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}
    orig_color = '#7f8c8d'

    step_ball_ids, step_colors = self.parse_word_metadata(word)

    # =================================================================
    # 1. Stack Permutation (左上：完整排列原圖)
    # =================================================================
    self.ax3.set_title(
        '1. Stack Permutation ', fontsize=12, fontweight='bold', pad=10
    )
    self.ax3.text(
        -0.1,
        1.05,
        f'',
        fontdict=font_prop,
        ha='left',
        va='top',
        transform=self.ax3.transAxes,
        color='#7f8c8d',
    )
    self.ax3.text(
        0.02,
        0.70,
        'Input Order:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
    )
    self.ax3.text(
        0.02,
        0.25,
        'Permutation:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
    )

    x_base = 0.28
    spacing_x = 0.12 if self.n <= 4 else 0.65 / self.n
    ax3_ball_size = max(60, 280 - (self.n - 4) * 12) if self.n > 4 else 280
    ax3_font_size = max(6, 9 - (self.n - 4) // 3)

    for i in range(self.n):
      cx = x_base + i * spacing_x
      ball_color = self.colors[i]
      self.ax3.scatter(cx, 0.70, color=ball_color, s=ax3_ball_size, zorder=3)
      self.ax3.text(
          cx,
          0.70,
          str(i + 1),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=ax3_font_size,
          zorder=4,
      )
      self.ax3.text(
          cx, 0.48, '↓', ha='center', va='center', color='#bdc3c7', fontsize=10
      )

    full_permutation = self.get_full_permutation(word, step_ball_ids)
    for i, ball_id in enumerate(full_permutation):
      cx = x_base + i * spacing_x
      ball_color = self.colors[ball_id - 1]
      self.ax3.scatter(
          cx,
          0.25,
          facecolors='white',
          edgecolors=ball_color,
          lw=2.0,
          s=ax3_ball_size * 0.9,
          zorder=3,
      )
      self.ax3.text(
          cx,
          0.25,
          str(ball_id),
          ha='center',
          va='center',
          color=ball_color,
          fontweight='bold',
          fontsize=ax3_font_size,
          zorder=4,
      )

    # =================================================================
    # 2. Arc Diagram (右上：完整弧線原圖)
    # =================================================================
    self.ax4.set_title(
        '2. Non-crossing Arc Diagram ', fontsize=12, fontweight='bold', pad=10
    )
    self.ax4.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )

    axis_font_size = max(6, int(9 - (self.n - 4) * 0.2)) if self.n > 4 else 9
    for i in range(2 * self.n):
      self.ax4.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color='#34495e',
          fontweight='bold',
          fontsize=axis_font_size,
      )

    scatter_size = max(10, 40 - (self.n - 4) * 1.5) if self.n > 4 else 40
    self.ax4.scatter(
        self.linear_x,
        self.linear_y,
        color=orig_color,
        s=scatter_size,
        edgecolors='white',
        zorder=5,
    )

    orig_stack = []
    for i, char in enumerate(word):
      if char == '(':
        orig_stack.append(i)
      else:
        if len(orig_stack) > 0:
          start_node = orig_stack.pop()
          center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
          theta = np.linspace(0, np.pi, 100)
          self.ax4.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=orig_color,
              lw=2.2,
              alpha=0.6,
              zorder=2,
          )

    # =================================================================
    # 3. Stack Permutation Step (左下：動態橫向堆疊進度)
    # =================================================================
    self.ax1.set_title(
        f'3. Stack Permutation (step : {self.anim_step} )',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    self.ax1.set_aspect('equal')

    # 基礎幾何縮放
    ball_radius = (
        max(0.08, 0.25 - (self.n - 4) * 0.012) if self.n > 4 else 0.25
    )
    x_spacing = ball_radius * 2.1
    tube_left = max(0.3, 0.15 + (self.n * 0.11))

    tube_height = ball_radius * 2 + 0.06
    tube_length = self.n * x_spacing + 0.15
    tube_right = tube_left + tube_length
    tube_y_center = 1.8

    top_wall = tube_y_center + (tube_height / 2)
    bottom_wall = tube_y_center - (tube_height / 2)

    ball_font_size = (
        max(6, int(11 - (self.n - 4) * 0.35)) if self.n > 4 else 10
    )

    # 繪製橫向 U 型管
    self.ax1.plot(
        [tube_right, tube_left, tube_left, tube_right],
        [top_wall, top_wall, bottom_wall, bottom_wall],
        color='#4f5d73',
        lw=3,
        zorder=2,
    )

    # 頂部狀態文字
    title_step_detail = f""
    self.ax1.text(
        (tube_left + tube_right) / 2,
        tube_y_center + 1.2,
        title_step_detail,
        fontdict=font_prop,
        ha='center',
        va='top',
        color='#2c3e50',
    )

    curr_stack = []
    current_pop_order = []
    current_input_order = []
    last_action = 'START'

    for i, char in enumerate(current_view):
      ball_id = step_ball_ids[i]
      if char == '(':
        curr_stack.append(ball_id)
        current_input_order.append(ball_id)
        last_action = f'Now Step: Push ball {ball_id}'
      else:
        if len(curr_stack) > 0:
          popped = curr_stack.pop()
          current_pop_order.append(popped)
          last_action = f'Now Step: Pop ball {popped}'

    # 繪製堆疊內部的球
    for level, ball_id in enumerate(curr_stack):
      c = self.colors[ball_id - 1]
      x_center = tube_left + ball_radius + 0.05 + level * x_spacing
      self.ax1.add_patch(
          plt.Circle((x_center, tube_y_center), ball_radius, color=c, zorder=3)
      )
      self.ax1.text(
          x_center,
          tube_y_center,
          str(ball_id),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=ball_font_size,
          zorder=4,
      )

    # 動態 Input order 繪製區
    input_y = tube_y_center + 0.65
    text_x_pos = tube_left - 0.1
    self.ax1.text(
        text_x_pos,
        input_y,
        'Input order:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
        ha='right',
    )

    input_ball_radius = ball_radius * 0.7
    input_spacing = input_ball_radius * 2.3

    for i in range(self.n):
      ball_x = tube_left + input_ball_radius + 0.05 + (i * input_spacing)
      if i < len(current_input_order):
        b_id = current_input_order[i]
        if b_id in current_pop_order:
          continue
        c = self.colors[b_id - 1]
        self.ax1.add_patch(
            plt.Circle((ball_x, input_y), input_ball_radius, color=c, zorder=3)
        )
        self.ax1.text(
            ball_x,
            input_y,
            str(b_id),
            ha='center',
            va='center',
            color='white',
            fontweight='bold',
            fontsize=max(5, ball_font_size - 1),
            zorder=4,
        )
      else:
        self.ax1.add_patch(
            plt.Circle(
                (ball_x, input_y),
                input_ball_radius,
                fill=False,
                edgecolor='#bdc3c7',
                linestyle='--',
                lw=1.2,
                zorder=3,
            )
        )

    # 下方 Action 狀態與 POP order 繪製區
    self.ax1.text(
        (tube_left + tube_right) / 2,
        tube_y_center - 0.85,
        last_action,
        ha='center',
        va='center',
        fontsize=11,
        fontweight='bold',
        color='#e67e22',
    )

    pop_base_y = tube_y_center - 1.55
    self.ax1.text(
        text_x_pos,
        pop_base_y,
        'POP order:',
        fontsize=12,
        fontweight='bold',
        color='#e67e22',
        va='center',
        ha='right',
    )

    pop_ball_radius = (
        0.22 if self.n <= 7 else max(0.10, 0.22 - (self.n - 7) * 0.009)
    )
    pop_spacing = pop_ball_radius * 2.3
    pop_font_size = (
        max(7, int(12 - (self.n - 7) * 0.35)) if self.n > 7 else 11
    )

    for i in range(self.n):
      ball_x = tube_left + pop_ball_radius + 0.05 + (i * pop_spacing)
      if i < len(current_pop_order):
        p_id = current_pop_order[i]
        c = self.colors[p_id - 1]
        self.ax1.add_patch(
            plt.Circle(
                (ball_x, pop_base_y),
                pop_ball_radius,
                fill=False,
                edgecolor=c,
                lw=2.5,
                zorder=3,
            )
        )
        self.ax1.text(
            ball_x,
            pop_base_y,
            str(p_id),
            ha='center',
            va='center',
            color=c,
            fontweight='bold',
            fontsize=pop_font_size,
            zorder=4,
        )
      else:
        self.ax1.add_patch(
            plt.Circle(
                (ball_x, pop_base_y),
                pop_ball_radius,
                fill=False,
                edgecolor='#e0e0e0',
                lw=1.5,
                zorder=3,
            )
        )

    # =================================================================
    # 4. Arc Diagram Step (右下：直線動態進度)
    # =================================================================
    self.ax2.set_title(
        f'4. Non-crossing Arc Diagram (step : {self.anim_step} )',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    self.ax2.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )

    self.ax2.scatter(
        self.linear_x, self.linear_y, color='#bdc3c7', s=scatter_size, zorder=3
    )

    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax2.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color=color,
          fontweight='bold',
          fontsize=axis_font_size,
      )
      if i < self.anim_step:
        arrow_str = '(' if word[i] == '(' else ')'
        ball_color = step_colors[i]
        self.ax2.text(
            self.linear_x[i],
            -0.65,
            arrow_str,
            ha='center',
            va='top',
            color=ball_color,
            fontweight='bold',
            fontsize=axis_font_size + 3,
        )

    arc_stack = []
    for i, char in enumerate(current_view):
      ball_color = step_colors[i]
      ball_id = step_ball_ids[i]
      if char == '(':
        arc_stack.append((i, ball_id))
        self.ax2.scatter(
            self.linear_x[i],
            self.linear_y[i],
            color=ball_color,
            s=scatter_size * 2,
            edgecolors='white',
            zorder=4,
        )
      else:
        if len(arc_stack) > 0:
          start_node, origin_ball_id = arc_stack.pop()
          center_x = (self.linear_x[start_node] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_node]) / 2
          theta = np.linspace(0, np.pi, 100)

          # 繪製弧線
          self.ax2.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=ball_color,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )
          # 起點實心球
          self.ax2.scatter(
              self.linear_x[start_node],
              [0],
              color=ball_color,
              s=scatter_size * 1.2,
              zorder=5,
          )
          # 終點空心球
          self.ax2.scatter(
              self.linear_x[i],
              [0],
              facecolors='white',
              edgecolors=ball_color,
              lw=2,
              s=scatter_size * 1.5,
              zorder=5,
          )

          # 終點空心球下方繪製球號
          self.ax2.text(
              self.linear_x[i],
              -1.15,
              str(origin_ball_id),
              ha='center',
              va='top',
              color='black',
              fontweight='normal',
              fontsize=axis_font_size + 2,
              zorder=6,
          )

    # 限界與自我適應畫布調整
    max_pop_x = tube_left + pop_ball_radius + 0.1 + (self.n * pop_spacing)
    self.ax1.set_xlim(-0.1, max(tube_right + 0.4, max_pop_x, 3.5))
    self.ax1.set_ylim(-0.4, tube_y_center + 1.4)
    self.ax1.axis('off')

    self.ax3.set_xlim(0, 1.0)
    self.ax3.set_ylim(0, 1.0)
    self.ax3.axis('off')

    max_h = (2 * self.n - 1) / 2
    for ax in [self.ax2, self.ax4]:
      ax.axis('off')
      ax.set_xlim(-0.7, 2 * self.n - 0.3)
      ax.set_ylim(-1.35, max(max_h + 0.5, 2.0))
      ax.set_aspect('equal')

    self.fig.suptitle(
        'Catalan Bijection Mapping  |  Page'
        f' #{self.current_idx+1}/{self.total_count} ({status_str})\n',
        fontsize=13,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()
