import math
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class TTC:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體溢位

    self.n = int(n)

    # 核心生成：利用二元樹邏輯生成路徑，並轉換為括號字串
    self.paths = self.generate_ordered_paths(self.n)
    self.words = [p.replace('R', '(').replace('U', ')') for p in self.paths]
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 核心彩虹色系
    self.colors = self.generate_rgb_palette(self.n)

    # 圓形座標系統設定
    angles = np.pi / 2 - np.linspace(0, 2 * np.pi, 2 * self.n, endpoint=False)
    self.circle_px, self.circle_py = np.cos(angles), np.sin(angles)

    # 建立畫布
    self.fig = plt.figure(figsize=(20, 8.5))

    # 劃分 2x2 網格
    # 上排：靜態圖 (1: Tree 靜態, 2: Chord 靜態)
    # 下排：動態圖 (3: Tree 動態, 4: Chord 動態)
    gs = self.fig.add_gridspec(
        2, 2, wspace=0.15, hspace=0.35, bottom=0.06, top=0.88
    )
    self.ax_static_tree = self.fig.add_subplot(gs[0, 0])
    self.ax_static_chord = self.fig.add_subplot(gs[0, 1])
    self.ax_anim_tree = self.fig.add_subplot(gs[1, 0])
    self.ax_anim_chord = self.fig.add_subplot(gs[1, 1])

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
    for ax in [
        self.ax_static_tree,
        self.ax_static_chord,
        self.ax_anim_tree,
        self.ax_anim_chord,
    ]:
      ax.clear()

    path = self.paths[self.current_idx]
    word = self.words[self.current_idx]
    tree = self.path_to_tree(path)
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}

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

    # =================================================================
    # 1. 上排左側：Binary Tree (靜態完整樹)
    # =================================================================
    self.ax_static_tree.set_title(
        '1. Standard Binary Tree', fontsize=12, fontweight='bold', pad=10
    )

    parent_positions = {tuple(e['p1']) for e in edges_list}
    leaf_positions = {tuple(n['pos']) for n in nodes_list} - parent_positions

    for j, e in enumerate(edges_list):
      if tuple(e['p2']) in leaf_positions:
        continue
      self.ax_static_tree.plot(
          [e['p1'][0], e['p2'][0]],
          [e['p1'][1], e['p2'][1]],
          color='#34495e',
          lw=2.5,
          zorder=1,
      )

    for n in nodes_list:
      if tuple(n['pos']) in leaf_positions:
        continue
      self.ax_static_tree.scatter(
          n['pos'][0],
          n['pos'][1],
          color='#34495e',
          s=n['size'],
          marker='o',
          zorder=5,
      )

    # =================================================================
    # 2. 上排右側：Circular Chord Diagram (靜態完整弦圖)
    # =================================================================
    self.ax_static_chord.set_aspect('equal')
    self.ax_static_chord.add_artist(
        plt.Circle((0, 0), 1, color='#f8f9fa', fill=True, zorder=1)
    )
    self.ax_static_chord.set_title(
        '2. Non-intersecting Chord', fontsize=12, fontweight='bold', pad=10
    )

    self.ax_static_chord.scatter(
        self.circle_px, self.circle_py, color='#7f8c8d', s=40, zorder=3
    )
    for i in range(2 * self.n):
      self.ax_static_chord.text(
          self.circle_px[i] * 1.25,
          self.circle_py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          color='#34495e',
          fontweight='bold',
          fontsize=9,
      )

    orig_stack = []
    for i, char in enumerate(word):
      if char == '(':
        orig_stack.append(i)
      else:
        if len(orig_stack) > 0:
          start_node = orig_stack.pop()
          self.ax_static_chord.plot(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color='#7f8c8d',
              lw=2,
              alpha=0.7,
              zorder=2,
          )
          self.ax_static_chord.scatter(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color='#7f8c8d',
              s=40,
              zorder=5,
          )

    # =================================================================
    # 3. 下排左側：Binary Tree (動態生成樹)
    # =================================================================
    self.ax_anim_tree.set_title(
        f'3. Full Binary Tree (Step: {self.anim_step} / {self.max_steps})',
        fontsize=12,
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
        self.ax_anim_tree.plot(
            [e['p1'][0], e['p2'][0]],
            [e['p1'][1], e['p2'][1]],
            color=color,
            lw=2.5,
            zorder=1,
        )

        x_mid = (e['p1'][0] + e['p2'][0]) / 2
        y_mid = (e['p1'][1] + e['p2'][1]) / 2
        self.ax_anim_tree.text(
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
        self.ax_anim_tree.scatter(
            n['pos'][0],
            n['pos'][1],
            color='black',
            s=n['size'],
            marker='o',
            alpha=1.0,
            zorder=5,
        )
      else:
        self.ax_anim_tree.scatter(
            n['pos'][0],
            n['pos'][1],
            color='black',
            s=n['size'],
            marker='o',
            alpha=0.0,
            zorder=5,
        )

    # =================================================================
    # 4. 下排右側：Circular Chord Diagram (動態進度 & 彩虹顏色連動)
    # =================================================================
    self.ax_anim_chord.set_aspect('equal')
    self.ax_anim_chord.add_artist(
        plt.Circle((0, 0), 1, color='#f8f9fa', fill=True, zorder=1)
    )
    self.ax_anim_chord.set_title(
        '4. Dynamic Non-intersecting Chord (Step:'
        f' {self.anim_step} / {self.max_steps})',
        fontsize=12,
        fontweight='bold',
        pad=10,
    )

    current_view = word[: self.anim_step]

    self.ax_anim_chord.scatter(
        self.circle_px, self.circle_py, color='#e0e0e0', s=40, zorder=3
    )
    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax_anim_chord.text(
          self.circle_px[i] * 1.25,
          self.circle_py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          color=color,
          fontweight='bold',
          fontsize=9,
      )

    chord_stack = []
    for i, char in enumerate(current_view):
      ball_color = step_colors[i]
      if char == '(':
        chord_stack.append(i)
        self.ax_anim_chord.scatter(
            self.circle_px[i],
            self.circle_py[i],
            color=ball_color,
            s=80,
            edgecolors='white',
            zorder=4,
        )
      else:
        if len(chord_stack) > 0:
          start_node = chord_stack.pop()
          line_color = step_colors[start_node]

          self.ax_anim_chord.plot(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=line_color,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )
          self.ax_anim_chord.scatter(
              [self.circle_px[start_node], self.circle_px[i]],
              [self.circle_py[start_node], self.circle_py[i]],
              color=line_color,
              s=50,
              zorder=5,
          )

    # =================================================================
    # 5. 邊界與比例設定
    # =================================================================
    for ax in [self.ax_static_tree, self.ax_anim_tree]:
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-1.2 * self.n - 0.5, 0.5)
      ax.set_aspect('equal')
      ax.axis('off')

    for ax in [self.ax_static_chord, self.ax_anim_chord]:
      ax.axis('off')
      ax.set_xlim(-1.4, 1.4)
      ax.set_ylim(-1.4, 1.4)

    self.fig.suptitle(
        'Catalan Bijection Mapping | '
        f' Page #{self.current_idx+1}/{self.total_count}\n',
        fontsize=13,
        fontweight='bold',
        y=0.98,
    )
    self.fig.canvas.draw_idle()


