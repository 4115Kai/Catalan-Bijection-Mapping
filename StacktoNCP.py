import math
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


class STNCP:

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

    # 色彩盤配置 (1~n 個元素擁有獨特專屬顏色，與 ChordtoStack 一致)
    self.colors = self.generate_rgb_palette(self.n)

    # NCP 環狀頂點座標設定 (1 在正上方，順時針排列)
    angles = np.pi / 2 - np.linspace(
        0, 2 * np.pi, self.n, endpoint=False
    )
    self.px = 0.85 * np.cos(angles)
    self.py = 0.85 * np.sin(angles)

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

    self.ax_full_stack = self.fig.add_subplot(
        gs[0, 0]
    )  # 左上：1. Stack Permutation Overview
    self.ax_static_ncp = self.fig.add_subplot(
        gs[0, 1]
    )  # 右上：2. Non-crossing Partition (靜態)
    self.ax_dyn_stack = self.fig.add_subplot(
        gs[1, 0]
    )  # 左下：3. Dynamic Stack Simulation
    self.ax_dyn_ncp = self.fig.add_subplot(
        gs[1, 1]
    )  # 右下：4. Dynamic Non-crossing Partition Progress

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

  def get_ncp_groups(self, word):
    stack = []
    groups = []
    for i, char in enumerate(word):
      if char == '(':
        node_idx = word[: i + 1].count('(')
        stack.append((node_idx, i))
      else:
        closing_node = word[: i + 1].count('(')
        if stack:
          start_node, start_i = stack.pop()
          pair_nodes = {start_node, closing_node}

          found = False
          for g in groups:
            if not g['nodes'].isdisjoint(pair_nodes):
              g['nodes'].update(pair_nodes)
              g['step_triggers'].append(i + 1)
              found = True
              break
          if not found:
            groups.append({'nodes': pair_nodes, 'step_triggers': [i + 1]})
    return groups

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
        if stack:
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
        if stack:
          pop_order.append(stack.pop())
    return pop_order

  def update_display(self):
    for ax in [
        self.ax_full_stack,
        self.ax_static_ncp,
        self.ax_dyn_stack,
        self.ax_dyn_ncp,
    ]:
      ax.clear()

    word = self.words[self.current_idx]
    current_view = word[: self.anim_step]

    ncp_groups = self.get_ncp_groups(word)
    step_ball_ids, step_colors = self.parse_word_metadata(word)
    full_permutation = self.get_full_permutation(word, step_ball_ids)

    # =================================================================
    # 1. [左上] Stack Permutation Overview
    # =================================================================
    self.ax_full_stack.set_title(
        '1. Stack Permutation Overview', fontsize=11, fontweight='bold'
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
    ball_size = max(60, 280 - (self.n - 4) * 12) if self.n > 4 else 280

    for i in range(self.n):
      cx = x_base + i * spacing_x
      ball_color = self.colors[i]
      self.ax_full_stack.scatter(
          cx, 0.70, color=ball_color, s=ball_size, zorder=3
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

    for i, ball_id in enumerate(full_permutation):
      cx = x_base + i * spacing_x
      ball_color = self.colors[ball_id - 1]
      self.ax_full_stack.scatter(
          cx,
          0.30,
          facecolors='white',
          edgecolors=ball_color,
          lw=2.0,
          s=ball_size * 0.9,
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
    # 2. [右上] Non-crossing Partition (靜態 NCP)
    # =================================================================
    self.ax_static_ncp.set_xlim(-1.3, 1.3)
    self.ax_static_ncp.set_ylim(-1.3, 1.3)
    self.ax_static_ncp.set_aspect('equal')
    self.ax_static_ncp.set_title(
        f'2. Non-crossing Partition ({self.n} Vertices)',
        fontsize=11,
        fontweight='bold',
    )

    # 外圍虛線多邊形
    polygon_x = np.append(self.px, self.px[0])
    polygon_y = np.append(self.py, self.py[0])
    self.ax_static_ncp.plot(
        polygon_x, polygon_y, linestyle='--', color='#bdc3c7', lw=1, zorder=1
    )

    # 繪製各個 NCP 群組 (區塊)
    for fg in ncp_groups:
      sorted_nodes = sorted(list(fg['nodes']))
      # 以群組中最小點號的色彩做為該群組代表色
      group_color = self.colors[sorted_nodes[0] - 1]

      if len(sorted_nodes) == 2:
        n1, n2 = sorted_nodes[0] - 1, sorted_nodes[1] - 1
        self.ax_static_ncp.plot(
            [self.px[n1], self.px[n2]],
            [self.py[n1], self.py[n2]],
            color=group_color,
            lw=2.5,
            zorder=2,
        )
      elif len(sorted_nodes) > 2:
        poly_x = [self.px[n - 1] for n in sorted_nodes]
        poly_y = [self.py[n - 1] for n in sorted_nodes]
        self.ax_static_ncp.fill(
            poly_x, poly_y, color=group_color, alpha=0.35, zorder=2
        )
        self.ax_static_ncp.plot(
            poly_x + [poly_x[0]],
            poly_y + [poly_y[0]],
            color=group_color,
            lw=2.0,
            zorder=2,
        )

    # 繪製頂點與標號 (每個點對應專屬色彩)
    for j in range(1, self.n + 1):
      idx = j - 1
      node_col = self.colors[idx]
      self.ax_static_ncp.scatter(
          self.px[idx], self.py[idx], color=node_col, s=80, zorder=3
      )
      self.ax_static_ncp.text(
          self.px[idx] * 1.25,
          self.py[idx] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=9,
          fontweight='bold',
      )

    self.ax_static_ncp.axis('off')

    # =================================================================
    # 3. [左下] Dynamic Stack Simulation
    # =================================================================
    self.ax_dyn_stack.set_title(
        f'3. Dynamic Stack Simulation (Step: {self.anim_step} /'
        f' {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )
    self.ax_dyn_stack.set_aspect('equal')

    step_str = current_view + '_' * (2 * self.n - self.anim_step)
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}
    self.ax_dyn_stack.text(
        0.5,
        2.4,
        f'',
        fontdict=font_prop,
        ha='center',
        va='center',
        color='#2c3e50',
    )

    ball_radius = (
        0.22 if self.n <= 4 else max(0.08, 0.22 - (self.n - 4) * 0.01)
    )
    x_spacing = ball_radius * 2.1
    tube_left = 0.4
    tube_height = ball_radius * 2 + 0.06
    tube_length = self.n * x_spacing + 0.15
    tube_right = tube_left + tube_length
    tube_y_center = 1.6

    # 繪製 U 型 Stack 管道
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

    curr_stack, curr_pop, curr_input = [], [], []
    last_action = 'Action: START'

    for i, char in enumerate(current_view):
      b_id = step_ball_ids.get(i, 1)
      if char == '(':
        curr_stack.append(b_id)
        curr_input.append(b_id)
        last_action = f'Step {i+1}: Push Ball {b_id}'
      else:
        if curr_stack:
          popped = curr_stack.pop()
          curr_pop.append(popped)
          last_action = f'Step {i+1}: Pop Ball {popped}'

    # 管道內的球
    for level, b_id in enumerate(curr_stack):
      cx = tube_left + ball_radius + 0.05 + level * x_spacing
      c = self.colors[b_id - 1]
      self.ax_dyn_stack.add_patch(
          plt.Circle((cx, tube_y_center), ball_radius, color=c, zorder=3)
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

    # 上方 Input 與下方 POP 序列
    input_y = tube_y_center + 0.65
    pop_y = tube_y_center - 0.65

    self.ax_dyn_stack.text(
        tube_left - 0.1,
        input_y,
        'Input Order:',
        fontsize=9,
        fontweight='bold',
        color='#34495e',
        va='center',
        ha='right',
    )
    self.ax_dyn_stack.text(
        tube_left - 0.1,
        pop_y,
        'POP Order:',
        fontsize=9,
        fontweight='bold',
        color='#e67e22',
        va='center',
        ha='right',
    )

    for i in range(self.n):
      bx = tube_left + ball_radius + 0.05 + (i * x_spacing)

      # Input 球
      if i < len(curr_input) and curr_input[i] not in curr_pop:
        b_id = curr_input[i]
        c = self.colors[b_id - 1]
        self.ax_dyn_stack.add_patch(
            plt.Circle(
                (bx, input_y),
                ball_radius * 0.7,
                color=c,
                zorder=3,
            )
        )
        self.ax_dyn_stack.text(
            bx,
            input_y,
            str(b_id),
            ha='center',
            va='center',
            color='white',
            fontweight='bold',
            fontsize=8,
            zorder=4,
        )
      else:
        self.ax_dyn_stack.add_patch(
            plt.Circle(
                (bx, input_y),
                ball_radius * 0.7,
                fill=False,
                edgecolor='#bdc3c7',
                linestyle='--',
                lw=1,
                zorder=3,
            )
        )

      # POP 球
      if i < len(curr_pop):
        p_id = curr_pop[i]
        c = self.colors[p_id - 1]
        self.ax_dyn_stack.add_patch(
            plt.Circle(
                (bx, pop_y),
                ball_radius * 0.8,
                fill=False,
                edgecolor=c,
                lw=2.0,
                zorder=3,
            )
        )
        self.ax_dyn_stack.text(
            bx,
            pop_y,
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
                (bx, pop_y),
                ball_radius * 0.8,
                fill=False,
                edgecolor='#e0e0e0',
                lw=1.0,
                zorder=3,
            )
        )

    # 動作文字
    self.ax_dyn_stack.text(
        (tube_left + tube_right) / 2,
        0.2,
        last_action,
        ha='center',
        va='center',
        fontsize=10,
        fontweight='bold',
        color='#e67e22',
    )

    self.ax_dyn_stack.set_xlim(-0.1, max(tube_right + 0.4, 3.5))
    self.ax_dyn_stack.set_ylim(0.0, 2.7)
    self.ax_dyn_stack.axis('off')

    # =================================================================
    # 4. [右下] Dynamic Non-crossing Partition Progress
    # =================================================================
    self.ax_dyn_ncp.set_xlim(-1.3, 1.3)
    self.ax_dyn_ncp.set_ylim(-1.3, 1.3)
    self.ax_dyn_ncp.set_aspect('equal')
    self.ax_dyn_ncp.set_title(
        f'4. Non-crossing Partition Progress (Step: {self.anim_step} /'
        f' {self.max_steps})',
        fontsize=11,
        fontweight='bold',
    )

    # 外圍虛線多邊形
    self.ax_dyn_ncp.plot(
        polygon_x, polygon_y, linestyle='--', color='#bdc3c7', lw=1, zorder=1
    )

    # 預設灰色底頂點
    for j in range(1, self.n + 1):
      idx = j - 1
      self.ax_dyn_ncp.scatter(
          self.px[idx],
          self.py[idx],
          color='#ecf0f1',
          edgecolors='#7f8c8d',
          s=80,
          zorder=2,
      )
      self.ax_dyn_ncp.text(
          self.px[idx] * 1.25,
          self.py[idx] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=9,
          fontweight='bold',
      )

    # 根據 anim_step 繪製活化的 NCP 群組
    for fg in ncp_groups:
      sorted_nodes = sorted(list(fg['nodes']))
      color = self.colors[sorted_nodes[0] - 1]

      if any(tr <= self.anim_step for tr in fg['step_triggers']):
        # 上色當前已觸發的點
        for node in sorted_nodes:
          idx = node - 1
          node_color = self.colors[idx]
          self.ax_dyn_ncp.scatter(
              self.px[idx], self.py[idx], color=node_color, s=95, zorder=4
          )

        # 若此 group 所有對應步驟都完成，畫線/面
        if max(fg['step_triggers']) <= self.anim_step:
          if len(sorted_nodes) == 2:
            n1, n2 = sorted_nodes[0] - 1, sorted_nodes[1] - 1
            self.ax_dyn_ncp.plot(
                [self.px[n1], self.px[n2]],
                [self.py[n1], self.py[n2]],
                color=color,
                lw=2.5,
                zorder=3,
            )
          elif len(sorted_nodes) > 2:
            poly_x = [self.px[n - 1] for n in sorted_nodes]
            poly_y = [self.py[n - 1] for n in sorted_nodes]
            self.ax_dyn_ncp.fill(
                poly_x, poly_y, color=color, alpha=0.35, zorder=3
            )
            self.ax_dyn_ncp.plot(
                poly_x + [poly_x[0]],
                poly_y + [poly_y[0]],
                color=color,
                lw=2.0,
                zorder=3,
            )

    self.ax_dyn_ncp.axis('off')

    # 總標題
    self.fig.suptitle(
        'Catalan Bijection Mapping'
        f' |  Page #{self.current_idx+1}/{self.total_count}\n',
        fontsize=13,
        fontweight='bold',
        y=0.96,
    )
    self.fig.canvas.draw_idle()


