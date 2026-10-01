import math
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class TTS:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)

    # 1. 核心生成：利用「二元樹檔案」的邏輯生成戴克路徑，並將其轉換成「堆疊檔案」的括號字串
    self.paths = self.generate_ordered_paths(self.n)
    self.words = [p.replace('R', '(').replace('U', ')') for p in self.paths]
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # 剛好 2n 步完成全部操作與畫出整棵樹的邊
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False

    # 核心色彩（堆疊與對應球號使用）
    self.colors = self.generate_rgb_palette(self.n)

    # 建立畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 劃分 2x2 網格，調整邊界
    gs = self.fig.add_gridspec(
        2, 2, hspace=0.35, wspace=0.25, bottom=0.06, top=0.88
    )

    # 四個子圖的佈局
    self.ax1 = self.fig.add_subplot(gs[0, 0])  # 1. 完整二元樹 (左上)
    self.ax2 = self.fig.add_subplot(gs[0, 1])  # 2. 完整堆疊排列 (右上)
    self.ax3 = self.fig.add_subplot(gs[1, 0])  # 3. 動態建樹過程與球號對應 (左下)
    self.ax4 = self.fig.add_subplot(gs[1, 1])  # 4. 動態堆疊進度 (右下)

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

  def generate_ordered_paths(self, n):
    paths = []

    def backtrack(x, y, path):
      if len(path) == 2 * n:
        paths.append(path)
        return
      if x < n:
        backtrack(x + 1, y, path + 'R')
      if y < x:
        backtrack(x, y + 1, path + 'U')

    backtrack(0, 0, '')
    return sorted(paths)

  def path_to_tree(self, path):
    if not path:
      return None
    balance, split_idx = 0, -1
    for i, char in enumerate(path):
      balance += 1 if char == 'R' else -1
      if balance == 0:
        split_idx = i
        break
    return {
        'left': self.path_to_tree(path[1:split_idx]),
        'right': self.path_to_tree(path[split_idx + 1 :]),
        'left_nodes': split_idx // 2,
        'right_nodes': (len(path) - split_idx - 1) // 2,
    }

  def _count_elements(self, node):
    if not node:
      return 1
    return (
        self._count_elements(node['left'])
        + 1
        + self._count_elements(node['right'])
    )

  def _collect_tree_elements(
      self, node, start_x, y, dy, nodes_list, edges_list
  ):
    if not node:
      return

    def collect_recursive(curr_node, curr_start_x, curr_y):
      if not curr_node:
        return

      left_count = self._count_elements(curr_node['left'])
      curr_x = curr_start_x + left_count

      # 真實內部節點：一律為「大實心黑圓」
      nodes_list.append({
          'pos': (curr_x, curr_y),
          'facecolor': 'black',
          'edgecolor': 'black',
          'size': 50,
          'marker': 'o',
          'is_null': False,
      })

      # 往左邊界
      if curr_node['left']:
        left_left_count = self._count_elements(curr_node['left']['left'])
        next_x_l = curr_start_x + left_left_count
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_l, curr_y - dy),
            'color': '#0015ff',
            'is_right': False,
            'is_null': False,
        })
        collect_recursive(curr_node['left'], curr_start_x, curr_y - dy)
      else:
        next_x_l = curr_start_x
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_l, curr_y - dy),
            'color': '#bdc3c7',
            'is_right': False,
            'is_null': True,  # 指向空節點的邊
        })
        # 左側空節點：小實心黑圓
        nodes_list.append({
            'pos': (next_x_l, curr_y - dy),
            'facecolor': 'black',
            'edgecolor': 'black',
            'size': 20,
            'marker': 'o',
            'is_null': True,
        })

      # 往右邊界
      if curr_node['right']:
        right_start_x = curr_x + 1
        right_left_count = self._count_elements(curr_node['right']['left'])
        next_x_r = right_start_x + right_left_count
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_r, curr_y - dy),
            'color': '#e74c3c',
            'is_right': True,
            'is_null': False,
        })
        collect_recursive(curr_node['right'], right_start_x, curr_y - dy)
      else:
        next_x_r = curr_x + 1
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_r, curr_y - dy),
            'color': '#bdc3c7',
            'is_right': True,
            'is_null': True,  # 指向空節點的邊
        })
        # 右側空節點：小實心黑圓
        nodes_list.append({
            'pos': (next_x_r, curr_y - dy),
            'facecolor': 'black',
            'edgecolor': 'black',
            'size': 20,
            'marker': 'o',
            'is_null': True,
        })

    collect_recursive(node, start_x, y)

  def _draw_edge_label(self, ax, x_mid, y_mid, ball_id, color, is_right):
    """僅於動態圖（ax3）繪製邊上的球號數字標籤"""
    if not is_right:
      ax.text(
          x_mid,
          y_mid,
          str(ball_id),
          color='white',
          fontsize=8,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              facecolor=color,
              edgecolor=color,
              boxstyle='circle,pad=0.18',
              alpha=1.0,
          ),
          zorder=10,
      )
    else:
      ax.text(
          x_mid,
          y_mid,
          str(ball_id),
          color=color,
          fontsize=8,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              facecolor='white',
              edgecolor=color,
              boxstyle='circle,pad=0.18',
              linewidth=1.5,
              alpha=1.0,
          ),
          zorder=10,
      )

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

    path = self.paths[self.current_idx]
    word = self.words[self.current_idx]
    tree = self.path_to_tree(path)
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}
    step_ball_ids, step_colors = self.parse_word_metadata(word)

    # 收集樹幾何結構
    nodes_list, edges_list = [], []
    tree_dy = 1.2
    self._collect_tree_elements(
        tree,
        start_x=0,
        y=0,
        dy=tree_dy,
        nodes_list=nodes_list,
        edges_list=edges_list,
    )

    # =================================================================
    # 1. Standard Binary Tree (左上)
    # =================================================================
    self.ax1.set_title(
        '1. Standard Binary Tree ', fontsize=11, fontweight='bold', pad=10
    )

    for e in edges_list:
      if not e.get('is_null', False):
        self.ax1.plot(
            [e['p1'][0], e['p2'][0]],
            [e['p1'][1], e['p2'][1]],
            color='black',
            lw=2.0,
            zorder=1,
        )

    for n in nodes_list:
      if not n.get('is_null', False):
        self.ax1.scatter(
            n['pos'][0],
            n['pos'][1],
            facecolors=n['facecolor'],
            edgecolors=n['edgecolor'],
            linewidths=1.5,
            s=n['size'],
            marker='o',
            zorder=5,
        )

    # =================================================================
    # 2. Stack Permutation (右上)
    # =================================================================
    self.ax2.set_title(
        '2. Stack Permutation ', fontsize=11, fontweight='bold', pad=10
    )
    self.ax2.text(
        0.02,
        0.65,
        'Input Order:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
    )
    self.ax2.text(
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
    ax2_ball_size = max(60, 280 - (self.n - 4) * 12) if self.n > 4 else 280
    ax2_font_size = max(6, 9 - (self.n - 4) // 3)

    for i in range(self.n):
      cx = x_base + i * spacing_x
      ball_color = self.colors[i]
      self.ax2.scatter(
          cx, 0.65, color=ball_color, s=ax2_ball_size, zorder=3
      )
      self.ax2.text(
          cx,
          0.65,
          str(i + 1),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=ax2_font_size,
          zorder=4,
      )
      self.ax2.text(
          cx,
          0.45,
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
      self.ax2.scatter(
          cx,
          0.25,
          facecolors='white',
          edgecolors=ball_color,
          lw=2.0,
          s=ax2_ball_size * 0.9,
          zorder=3,
      )
      self.ax2.text(
          cx,
          0.25,
          str(ball_id),
          ha='center',
          va='center',
          color=ball_color,
          fontweight='bold',
          fontsize=ax2_font_size,
          zorder=4,
      )

    # =================================================================
    # 3. Step-by-Step Tree Construction (左下)
    # =================================================================
    self.ax3.set_title(
        f'3. Full Binary Tree (Step: {self.anim_step} / {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )

    active_points = set()
    root_x = self._count_elements(tree['left']) if tree else 0
    if self.anim_step >= 1:
      active_points.add((root_x, 0))

    for j, e in enumerate(edges_list):
      ball_id = step_ball_ids[j]
      color = self.colors[ball_id - 1]
      if self.anim_step > j:
        self.ax3.plot(
            [e['p1'][0], e['p2'][0]],
            [e['p1'][1], e['p2'][1]],
            color=color,
            lw=2.5,
            zorder=1,
        )

        x_mid = (e['p1'][0] + e['p2'][0]) / 2
        y_mid = (e['p1'][1] + e['p2'][1]) / 2
        self._draw_edge_label(
            self.ax3, x_mid, y_mid, ball_id, color, e['is_right']
        )

        active_points.add(tuple(e['p1']))
        active_points.add(tuple(e['p2']))

    for n in nodes_list:
      if tuple(n['pos']) in active_points:
        self.ax3.scatter(
            n['pos'][0],
            n['pos'][1],
            facecolors=n['facecolor'],
            edgecolors=n['edgecolor'],
            linewidths=1.5,
            s=n['size'],
            marker='o',
            alpha=1.0,
            zorder=5,
        )

    # =================================================================
    # 4. Step-by-Step Stack Simulation (右下)
    # =================================================================
    self.ax4.set_title(
        f'4. Dynamic Stack Permutation (Step: {self.anim_step} /'
        f' {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )
    self.ax4.set_aspect('equal')

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

    self.ax4.plot(
        [tube_right, tube_left, tube_left, tube_right],
        [top_wall, top_wall, bottom_wall, bottom_wall],
        color='#4f5d73',
        lw=3,
        zorder=2,
    )

    current_view = word[: self.anim_step]
    title_step_detail = f""
    self.ax4.text(
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
        last_action = f'Now Step: Push Ball {ball_id}'
      else:
        if len(curr_stack) > 0:
          popped = curr_stack.pop()
          current_pop_order.append(popped)
          last_action = f'Now Step: Pop Ball {popped}'

    for level, ball_id in enumerate(curr_stack):
      c = self.colors[ball_id - 1]
      x_center = tube_left + ball_radius + 0.05 + level * x_spacing
      self.ax4.add_patch(
          plt.Circle(
              (x_center, tube_y_center), ball_radius, color=c, zorder=3
          )
      )
      self.ax4.text(
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

    input_y = tube_y_center + 0.65
    text_x_pos = tube_left - 0.1
    self.ax4.text(
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
        self.ax4.add_patch(
            plt.Circle((ball_x, input_y), input_ball_radius, color=c, zorder=3)
        )
        self.ax4.text(
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
        self.ax4.add_patch(
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

    self.ax4.text(
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
    self.ax4.text(
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
        self.ax4.add_patch(
            plt.Circle(
                (ball_x, pop_base_y),
                pop_ball_radius,
                fill=False,
                edgecolor=c,
                lw=2.5,
                zorder=3,
            )
        )
        self.ax4.text(
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
        self.ax4.add_patch(
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
    # 5. 畫布大小自適應調整與統一刷新
    # =================================================================
    for ax in [self.ax1, self.ax3]:
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-1.2 * self.n - 0.5, 0.5)
      ax.set_aspect('equal')
      ax.axis('off')

    self.ax2.set_xlim(0, 1.0)
    self.ax2.set_ylim(0, 1.0)
    self.ax2.axis('off')

    max_pop_x = tube_left + pop_ball_radius + 0.1 + (self.n * pop_spacing)
    self.ax4.set_xlim(-0.1, max(tube_right + 0.4, max_pop_x, 3.5))
    self.ax4.set_ylim(-0.4, tube_y_center + 1.4)
    self.ax4.axis('off')

    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        f'Catalan Bijection Mapping  | '
        f' Page #{self.current_idx+1}/{catalan_num}',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()

