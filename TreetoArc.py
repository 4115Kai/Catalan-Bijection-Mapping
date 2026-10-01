import math
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class TTA:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)

    # 核心生成：利用二元樹邏輯生成戴克路徑，並轉換為括號字串
    self.paths = self.generate_ordered_paths(self.n)
    self.words = [p.replace('R', '(').replace('U', ')') for p in self.paths]
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # 2n 步完成
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False

    # 弧線與邊使用的核心彩虹色系
    self.colors = self.generate_rgb_palette(self.n)

    # 弧線圖基本座標軸設定
    self.linear_x = np.arange(2 * self.n)
    self.linear_y = np.zeros(2 * self.n)

    # 建立畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 重新分配網格比例，並移除底部控制按鈕區空間
    gs = self.fig.add_gridspec(
        2, 4, wspace=0.25, hspace=0.35, bottom=0.06, top=0.88
    )

    # 四個子圖佈局
    self.ax1 = self.fig.add_subplot(gs[0, 0:2])  # 1. 完整二元樹 (左上)
    self.ax2 = self.fig.add_subplot(gs[0, 2:4])  # 2. 完整弧線圖 (右上)
    self.ax3 = self.fig.add_subplot(gs[1, 0:2])  # 3. 動態建樹過程 (左下)
    self.ax4 = self.fig.add_subplot(gs[1, 2:4])  # 4. 動態弧線進度 (右下)

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

      # 實節點：黑色，大小 50
      nodes_list.append({'pos': (curr_x, curr_y), 'size': 50})

      if curr_node['left']:
        left_left_count = self._count_elements(curr_node['left']['left'])
        next_x_l = curr_start_x + left_left_count
        edges_list.append(
            {'p1': (curr_x, curr_y), 'p2': (next_x_l, curr_y - dy)}
        )
        collect_recursive(curr_node['left'], curr_start_x, curr_y - dy)
      else:
        next_x_l = curr_start_x
        edges_list.append(
            {'p1': (curr_x, curr_y), 'p2': (next_x_l, curr_y - dy)}
        )
        # 虛擬葉節點：黑色圓形，大小 40
        nodes_list.append({'pos': (next_x_l, curr_y - dy), 'size': 40})

      if curr_node['right']:
        right_start_x = curr_x + 1
        right_left_count = self._count_elements(curr_node['right']['left'])
        next_x_r = right_start_x + right_left_count
        edges_list.append(
            {'p1': (curr_x, curr_y), 'p2': (next_x_r, curr_y - dy)}
        )
        collect_recursive(curr_node['right'], right_start_x, curr_y - dy)
      else:
        next_x_r = curr_x + 1
        edges_list.append(
            {'p1': (curr_x, curr_y), 'p2': (next_x_r, curr_y - dy)}
        )
        nodes_list.append({'pos': (next_x_r, curr_y - dy), 'size': 40})

    collect_recursive(node, start_x, y)

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

  def update_display(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    word = self.words[self.current_idx]
    tree = self.path_to_tree(path)
    step_ball_ids, step_colors = self.parse_word_metadata(word)

    # 收集二元樹幾何資訊
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

    # 基礎動態參數計算
    scatter_size = max(10, 40 - (self.n - 4) * 1.5) if self.n > 4 else 40
    axis_font_size = max(6, int(9 - (self.n - 4) * 0.2)) if self.n > 4 else 9

    # =================================================================
    # 1. Standard Binary Tree (左上)
    # =================================================================
    self.ax1.set_title(
        '1. Standard Binary Tree ', fontsize=11, fontweight='bold', pad=10
    )

    parent_positions = {tuple(e['p1']) for e in edges_list}
    leaf_positions = {tuple(n['pos']) for n in nodes_list} - parent_positions

    for j, e in enumerate(edges_list):
      if tuple(e['p2']) in leaf_positions:
        continue
      self.ax1.plot(
          [e['p1'][0], e['p2'][0]],
          [e['p1'][1], e['p2'][1]],
          color='black',
          lw=2.5,
          zorder=1,
      )

    for n in nodes_list:
      if tuple(n['pos']) in leaf_positions:
        continue
      self.ax1.scatter(
          n['pos'][0],
          n['pos'][1],
          color='black',
          s=n['size'],
          marker='o',
          zorder=5,
      )

    # =================================================================
    # 2. Complete Arc Diagram (右上)
    # =================================================================
    self.ax2.set_title(
        '2. Non-crossing Arc Diagram ', fontsize=11, fontweight='bold', pad=10
    )
    self.ax2.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
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
          fontsize=axis_font_size,
      )
    self.ax2.scatter(
        self.linear_x,
        self.linear_y,
        color='#7f8c8d',
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
          self.ax2.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color='black',
              lw=2.2,
              alpha=0.7,
              zorder=2,
          )

    # =================================================================
    # 3. Dynamic Tree Construction (左下)
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
        self.ax3.text(
            x_mid,
            y_mid,
            str(j + 1),
            color='white',
            fontsize=8,
            fontweight='bold',
            ha='center',
            va='center',
            bbox=dict(
                facecolor=color,
                edgecolor='none',
                boxstyle='circle,pad=0.15',
                alpha=1.0,
            ),
            zorder=10,
        )

        active_points.add(tuple(e['p1']))
        active_points.add(tuple(e['p2']))

    for n in nodes_list:
      if tuple(n['pos']) in active_points:
        self.ax3.scatter(
            n['pos'][0],
            n['pos'][1],
            color='black',
            s=n['size'],
            marker='o',
            alpha=1.0,
            zorder=5,
        )
      else:
        self.ax3.scatter(
            n['pos'][0],
            n['pos'][1],
            color='black',
            s=n['size'],
            marker='o',
            alpha=0.00,
            zorder=5,
        )

    # =================================================================
    # 4. Dynamic Arc Diagram Progress (右下)
    # =================================================================
    self.ax4.set_title(
        f'4. Non-crossing Arc Diagram (Step: {self.anim_step} /'
        f' {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )
    self.ax4.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )

    self.ax4.scatter(
        self.linear_x,
        self.linear_y,
        color='#bdc3c7',
        s=scatter_size,
        zorder=3,
    )

    current_view = word[: self.anim_step]
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
          fontsize=axis_font_size,
      )

    arc_stack = []
    for i, char in enumerate(current_view):
      ball_color = step_colors[i]
      ball_id = step_ball_ids[i]
      if char == '(':
        arc_stack.append((i, ball_id))
        self.ax4.scatter(
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

          self.ax4.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=ball_color,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )
          self.ax4.scatter(
              self.linear_x[start_node],
              [0],
              color=ball_color,
              s=scatter_size * 1.2,
              zorder=5,
          )
          self.ax4.scatter(
              self.linear_x[i],
              [0],
              facecolors='white',
              edgecolors=ball_color,
              lw=2,
              s=scatter_size * 1.5,
              zorder=5,
          )

    # =================================================================
    # 5. 畫布大小自適應與更新
    # =================================================================
    for ax in [self.ax1, self.ax3]:
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-1.2 * self.n - 0.5, 0.5)
      ax.set_aspect('equal')
      ax.axis('off')

    max_h = (2 * self.n - 1) / 2
    for ax in [self.ax2, self.ax4]:
      ax.axis('off')
      ax.set_xlim(-0.7, 2 * self.n - 0.3)
      ax.set_ylim(-1.35, max(max_h + 0.5, 2.0))
      ax.set_aspect('equal')

    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        f'Catalan Bijection Mapping '
        f'  | Page #{self.current_idx+1}/{catalan_num}',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()


