import math
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


class TTNCP:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止記憶體洩漏

    self.n = int(n)

    # 核心生成：利用二元樹邏輯生成戴克路徑，並轉換為括號字串
    self.paths = self.generate_ordered_paths(self.n)
    self.words = [p.replace('R', '(').replace('U', ')') for p in self.paths]
    self.total_count = len(self.paths)

    # 接收傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # 2n 步完成
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 色彩盤配置 (1~n 個元素擁有獨特專屬顏色)
    self.colors = self.generate_rgb_palette(self.n)

    # 頂點圓形排列座標 (Noncrossing Partition 用)
    angles = -np.linspace(0, 2 * np.pi, self.n, endpoint=False) + np.pi / 2
    self.pts = {
        i + 1: (0.85 * np.cos(a), 0.85 * np.sin(a))
        for i, a in enumerate(angles)
    }

    # 建立畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 重新分配網格比例
    gs = self.fig.add_gridspec(
        2, 4, wspace=0.25, hspace=0.35, bottom=0.06, top=0.88
    )

    # 四個子圖佈局
    self.ax1 = self.fig.add_subplot(gs[0, 0:2])  # 1. 完整二元樹 (左上)
    self.ax2 = self.fig.add_subplot(gs[0, 2:4])  # 2. 完整 NCP (右上)
    self.ax3 = self.fig.add_subplot(gs[1, 0:2])  # 3. 動態建樹過程 (左下)
    self.ax4 = self.fig.add_subplot(gs[1, 2:4])  # 4. 動態 NCP 進度 (右下)

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

  def get_ncp_groups(self, word):
    stack = []
    groups = []
    for i, char in enumerate(word):
      if char == '(':
        node_idx = len([c for c in word[: i + 1] if c == '('])
        stack.append({'node': node_idx, 'x': i})
      else:
        closing_node = len([c for c in word[: i + 1] if c == '('])
        start_info = stack.pop()
        pair_nodes = {start_info['node'], closing_node}

        found = False
        for g in groups:
          if not pair_nodes.isdisjoint(g['nodes']):
            g['nodes'].update(pair_nodes)
            g['step_triggers'].append(i + 1)
            found = True
            break
        if not found:
          groups.append({'nodes': pair_nodes, 'step_triggers': [i + 1]})
    return groups

  def parse_word_metadata(self, word):
    step_ball_ids, step_colors = {}, {}
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

      nodes_list.append({
          'pos': (curr_x, curr_y),
          'facecolor': 'black',
          'edgecolor': 'black',
          'size': 50,
          'marker': 'o',
          'is_null': False,
      })

      # 左子樹邊界
      if curr_node['left']:
        left_left_count = self._count_elements(curr_node['left']['left'])
        next_x_l = curr_start_x + left_left_count
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_l, curr_y - dy),
            'is_right': False,
            'is_null': False,
        })
        collect_recursive(curr_node['left'], curr_start_x, curr_y - dy)
      else:
        next_x_l = curr_start_x
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_l, curr_y - dy),
            'is_right': False,
            'is_null': True,
        })
        nodes_list.append({
            'pos': (next_x_l, curr_y - dy),
            'facecolor': 'black',
            'edgecolor': 'black',
            'size': 20,
            'marker': 'o',
            'is_null': True,
        })

      # 右子樹邊界
      if curr_node['right']:
        right_start_x = curr_x + 1
        right_left_count = self._count_elements(curr_node['right']['left'])
        next_x_r = right_start_x + right_left_count
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_r, curr_y - dy),
            'is_right': True,
            'is_null': False,
        })
        collect_recursive(curr_node['right'], right_start_x, curr_y - dy)
      else:
        next_x_r = curr_x + 1
        edges_list.append({
            'p1': (curr_x, curr_y),
            'p2': (next_x_r, curr_y - dy),
            'is_right': True,
            'is_null': True,
        })
        nodes_list.append({
            'pos': (next_x_r, curr_y - dy),
            'facecolor': 'black',
            'edgecolor': 'black',
            'size': 20,
            'marker': 'o',
            'is_null': True,
        })

    collect_recursive(node, start_x, y)

  def update_display(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    word = self.words[self.current_idx]
    tree = self.path_to_tree(path)

    ncp_groups = self.get_ncp_groups(word)
    step_ball_ids, step_colors = self.parse_word_metadata(word)

    nodes_list, edges_list = [], []
    self._collect_tree_elements(
        tree,
        start_x=0,
        y=0,
        dy=1.2,
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
            facecolors='black',
            edgecolors='black',
            s=50,
            zorder=5,
        )

    # =================================================================
    # 2. Static Noncrossing Partition (右上)
    # =================================================================
    self.ax2.set_title(
        f'2. Non-crossing Partition ({self.n} Vertices) ',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )
    self.ax2.set_aspect('equal')
    self.ax2.axis('off')

    for j in range(1, self.n + 1):
      p1, p2 = self.pts[j], self.pts[j % self.n + 1]
      self.ax2.plot(
          [p1[0], p2[0]], [p1[1], p2[1]], '--', color='#bdc3c7', lw=1, alpha=0.5
      )
      node_col = self.colors[j - 1]
      self.ax2.add_patch(
          patches.Circle(
              self.pts[j],
              radius=0.04,
              facecolor=node_col,
              edgecolor=node_col,
              zorder=4,
          )
      )
      self.ax2.text(
          self.pts[j][0] * 1.25,
          self.pts[j][1] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=11,
          fontweight='bold',
      )

    for fg in ncp_groups:
      sorted_nodes = sorted(list(fg['nodes']))
      group_color = self.colors[sorted_nodes[0] - 1]

      if len(sorted_nodes) == 2:
        p1, p2 = self.pts[sorted_nodes[0]], self.pts[sorted_nodes[1]]
        self.ax2.plot(
            [p1[0], p2[0]], [p1[1], p2[1]], color=group_color, lw=2.5, zorder=2
        )
      elif len(sorted_nodes) > 2:
        group_pts = np.array([self.pts[node] for node in sorted_nodes])
        self.ax2.add_patch(
            patches.Polygon(
                group_pts,
                closed=True,
                facecolor=group_color,
                alpha=0.35,
                zorder=2,
            )
        )
        for idx in range(len(sorted_nodes)):
          p1 = self.pts[sorted_nodes[idx]]
          p2 = self.pts[sorted_nodes[(idx + 1) % len(sorted_nodes)]]
          self.ax2.plot(
              [p1[0], p2[0]], [p1[1], p2[1]], color=group_color, lw=2, zorder=3
          )

    # =================================================================
    # 3. Dynamic Binary Tree (左下)
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
      ball_id = step_ball_ids.get(j, 1)
      target_color = step_colors.get(j, self.colors[0])

      if self.anim_step > j:
        self.ax3.plot(
            [e['p1'][0], e['p2'][0]],
            [e['p1'][1], e['p2'][1]],
            color=target_color,
            lw=2.5,
            zorder=1,
        )

        x_mid = (e['p1'][0] + e['p2'][0]) / 2
        y_mid = (e['p1'][1] + e['p2'][1]) / 2

        if e['is_right']:
          badge_bg = 'white'
          badge_border = target_color
          text_col = target_color
        else:
          badge_bg = target_color
          badge_border = target_color
          text_col = 'white'

        bbox_props = dict(
            facecolor=badge_bg,
            edgecolor=badge_border,
            boxstyle='circle,pad=0.18',
            linewidth=1.5,
        )
        self.ax3.text(
            x_mid,
            y_mid,
            str(ball_id),
            color=text_col,
            fontsize=8,
            fontweight='bold',
            ha='center',
            va='center',
            bbox=bbox_props,
            zorder=10,
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
            s=n['size'],
            zorder=5,
        )

    # =================================================================
    # 4. Dynamic Noncrossing Partition (右下)
    # =================================================================
    self.ax4.set_title(
        f'4. Dynamic Non-crossing Partition (Step: {self.anim_step} /'
        f' {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=10,
    )
    self.ax4.set_aspect('equal')
    self.ax4.axis('off')

    for j in range(1, self.n + 1):
      p1, p2 = self.pts[j], self.pts[j % self.n + 1]
      self.ax4.plot(
          [p1[0], p2[0]], [p1[1], p2[1]], '--', color='#bdc3c7', lw=1, alpha=0.5
      )
      self.ax4.add_patch(
          patches.Circle(
              self.pts[j],
              radius=0.04,
              facecolor='#ecf0f1',
              edgecolor='#7f8c8d',
              zorder=4,
          )
      )
      self.ax4.text(
          self.pts[j][0] * 1.25,
          self.pts[j][1] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=11,
          fontweight='bold',
      )

    for fg in ncp_groups:
      sorted_nodes = sorted(list(fg['nodes']))
      color = self.colors[sorted_nodes[0] - 1]

      if any(tr <= self.anim_step for tr in fg['step_triggers']):
        for node in sorted_nodes:
          node_col = self.colors[node - 1]
          self.ax4.add_patch(
              patches.Circle(
                  self.pts[node],
                  radius=0.05,
                  facecolor=node_col,
                  edgecolor=node_col,
                  zorder=5,
              )
          )

        if max(fg['step_triggers']) <= self.anim_step:
          group_pts = np.array([self.pts[node] for node in sorted_nodes])
          if len(sorted_nodes) == 2:
            dist = np.linalg.norm(group_pts[0] - group_pts[1])
            angle = np.degrees(
                np.arctan2(
                    group_pts[1][1] - group_pts[0][1],
                    group_pts[1][0] - group_pts[0][0],
                )
            )
            self.ax4.add_patch(
                patches.Ellipse(
                    np.mean(group_pts, axis=0),
                    dist + 0.1,
                    0.08,
                    angle=angle,
                    facecolor=color,
                    alpha=0.35,
                )
            )
          elif len(sorted_nodes) > 2:
            self.ax4.add_patch(
                patches.Polygon(
                    group_pts, closed=True, facecolor=color, alpha=0.35
                )
            )

    # =================================================================
    # 5. 視覺範圍設定與更新
    # =================================================================
    for ax in [self.ax1, self.ax3]:
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-1.2 * self.n - 0.5, 0.5)
      ax.set_aspect('equal')
      ax.axis('off')

    for ax in [self.ax2, self.ax4]:
      ax.set_xlim(-1.1, 1.1)
      ax.set_ylim(-1.1, 1.1)

    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        'Catalan Bijection Mapping'
        f'  | Page #{self.current_idx+1}/{catalan_num}',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )

    self.fig.canvas.draw_idle()
