import math
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class CTP:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體溢位

    self.n = int(n)
    self.n_v = self.n + 2  # 多邊形頂點數
    self.words = self.generate_all_dyck_words(self.n)
    self.paths = self.generate_ordered_paths(self.n)
    self.total_count = len(self.words)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_page = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n
    self.step_index = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 圓點座標預算 (Chord 用) - 逆時針排列
    angles = np.linspace(0, 2 * np.pi, 2 * self.n, endpoint=False) * (
        -1
    ) + np.pi / 2
    self.px, self.py = np.cos(angles), np.sin(angles)

    # 多邊形頂點座標 (Triangulation 用)
    self.verts = self._generate_verts()

    # 建立畫布
    self.fig = plt.figure(figsize=(21, 8.5))

    self.render()

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
    return words

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

  def _generate_verts(self):
    v = {}
    angle_step = 2 * np.pi / self.n_v
    offset = np.pi / 2 - angle_step / 2
    for i in range(1, self.n_v + 1):
      angle = offset - (i - 1) * angle_step
      v[i] = np.array([np.cos(angle), np.sin(angle)])
    return v

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

  def _collect_dual_elements(
      self,
      node,
      L,
      R,
      colors_pool,
      nodes_list,
      interleaved_edges,
      leaf_nodes_map,
  ):
    if not node:
      return
    color_idx_iter = iter(range(len(colors_pool)))
    step_counter = 1

    def collect_recursive(curr_node, curr_L, curr_R):
      nonlocal step_counter
      if not curr_node:
        return
      k = curr_L + curr_node['right_nodes'] + 1
      centroid = (
          self.verts[curr_L] + self.verts[k] + self.verts[curr_R]
      ) / 3

      try:
        c_idx = next(color_idx_iter)
        node_color = colors_pool[c_idx % len(colors_pool)]
      except StopIteration:
        node_color = '#ca0fec'

      nodes_list.append(
          {'pos': centroid, 'color': node_color, 'size': 30, 'marker': 'o'}
      )

      if curr_node['left']:
        child = curr_node['left']
        nk = k + child['right_nodes'] + 1
        nc = (self.verts[k] + self.verts[nk] + self.verts[curr_R]) / 3
        mid_p = (centroid + nc) / 2
        interleaved_edges.append({
            'p1': centroid,
            'p2': nc,
            'mid': mid_p,
            'color': node_color,
            'is_leaf': False,
            'step': step_counter,
        })
        step_counter += 1
        collect_recursive(curr_node['left'], k, curr_R)
      else:
        edge_mid = (self.verts[k] + self.verts[curr_R]) / 2
        mid_p = (centroid + edge_mid) / 2
        interleaved_edges.append({
            'p1': centroid,
            'p2': edge_mid,
            'mid': mid_p,
            'color': node_color,
            'is_leaf': True,
            'step': step_counter,
        })
        leaf_nodes_map[len(interleaved_edges) - 1] = {
            'pos': edge_mid,
            'color': node_color,
            'size': 20,
            'marker': 's',
        }
        step_counter += 1

      if curr_node['right']:
        child = curr_node['right']
        nk = curr_L + child['right_nodes'] + 1
        nc = (self.verts[curr_L] + self.verts[nk] + self.verts[k]) / 3
        mid_p = (centroid + nc) / 2
        interleaved_edges.append({
            'p1': centroid,
            'p2': nc,
            'mid': mid_p,
            'color': node_color,
            'is_leaf': False,
            'step': step_counter,
        })
        step_counter += 1
        collect_recursive(curr_node['right'], curr_L, k)
      else:
        edge_mid = (self.verts[curr_L] + self.verts[k]) / 2
        mid_p = (centroid + edge_mid) / 2
        interleaved_edges.append({
            'p1': centroid,
            'p2': edge_mid,
            'mid': mid_p,
            'color': node_color,
            'is_leaf': True,
            'step': step_counter,
        })
        leaf_nodes_map[len(interleaved_edges) - 1] = {
            'pos': edge_mid,
            'color': node_color,
            'size': 20,
            'marker': 's',
        }
        step_counter += 1

    collect_recursive(node, L, R)

  def draw_polygon_base(self, ax):
    for i in range(1, self.n_v + 1):
      next_i = i + 1 if i < self.n_v else 1
      p1, p2 = self.verts[i], self.verts[next_i]
      is_base = (i == self.n_v and next_i == 1) or (
          i == 1 and next_i == self.n_v
      )

      c, lw = ('#FF00FF' if is_base else 'black', 2.5 if is_base else 1.5)

      ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=lw)
      ax.text(
          p1[0] * 1.2,
          p1[1] * 1.2,
          str(i),
          ha='center',
          va='center',
          fontweight='bold',
          fontsize=9,
      )

  def draw_chords(self, ax, node, L, R, alpha=0.3):
    if not node:
      return
    k = L + node['right_nodes'] + 1
    for target in [L, R]:
      if abs(k - target) > 1 and not (
          min(k, target) == 1 and max(k, target) == self.n_v
      ):
        ax.plot(
            [self.verts[target][0], self.verts[k][0]],
            [self.verts[target][1], self.verts[k][1]],
            'k--',
            lw=1.2,
            alpha=alpha,
        )
    self.draw_chords(ax, node['right'], L, k, alpha)
    self.draw_chords(ax, node['left'], k, R, alpha)

  def render(self):
    self.fig.clf()  # 清空畫布

    word = self.words[self.current_page]
    path_str = self.paths[self.current_page]
    tree = self.path_to_tree(path_str)
    n = self.n

    colors = [mcolors.hsv_to_rgb((i / n, 0.7, 0.9)) for i in range(n)]

    # =========================================================================
    # 1. [左上] 靜態完整圓中弦 (Chord 靜態圖)
    # =========================================================================
    ax1 = self.fig.add_subplot(2, 2, 1)
    ax1.set_xlim(-1.3, 1.3)
    ax1.set_ylim(-1.3, 1.3)
    ax1.set_aspect('equal')
    ax1.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )
    ax1.set_title('1. Non-intersecting Chord', fontsize=11, fontweight='bold')

    static_stack = []
    for i in range(2 * n):
      char = word[i]
      if char == '(':
        static_stack.append(i)
      else:
        s_node = static_stack.pop()
        ax1.plot(
            [self.px[s_node], self.px[i]],
            [self.py[s_node], self.py[i]],
            color='black',
            lw=2.5,
            zorder=2,
        )

    for i in range(2 * n):
      ax1.scatter(self.px[i], self.py[i], color='black', s=35, zorder=3)
      ax1.text(
          self.px[i] * 1.2,
          self.py[i] * 1.2,
          str(i + 1),
          ha='center',
          va='center',
          fontsize=8,
      )
    ax1.axis('off')

    # =========================================================================
    # 2. [右上] 靜態三角形剖分 (Triangulation 靜態圖)
    # =========================================================================
    ax2 = self.fig.add_subplot(2, 2, 2)
    ax2.set_xlim(-1.4, 1.4)
    ax2.set_ylim(-1.4, 1.4)
    ax2.set_aspect('equal')
    ax2.axis('off')
    self.draw_polygon_base(ax2)
    self.draw_chords(ax2, tree, 1, self.n_v, alpha=0.4)
    ax2.set_title(
        f'2. {self.n_v}-gon Polygon Triangulation',
        fontsize=11,
        fontweight='bold',
    )

    # =========================================================================
    # 3. [左下] 動態圓中弦過程 (Chord 動態圖)
    # =========================================================================
    ax3 = self.fig.add_subplot(2, 2, 3)
    ax3.set_xlim(-1.3, 1.3)
    ax3.set_ylim(-1.3, 1.3)
    ax3.set_aspect('equal')
    ax3.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )

    stack = []
    node_colors = ['#bdc3c7'] * (2 * n)
    active_c_id = 0
    curr_step_chord = min(self.step_index, 2 * n)

    for i in range(curr_step_chord):
      char = word[i]
      if char == '(':
        stack.append((i, active_c_id))
        ax3.scatter(
            self.px[i],
            self.py[i],
            color='white',
            edgecolors=colors[active_c_id],
            s=100,
            lw=2,
            zorder=4,
        )
        active_c_id += 1
      else:
        if stack:
          s_node, c_idx = stack.pop()
          node_colors[s_node] = node_colors[i] = colors[c_idx]
          ax3.plot(
              [self.px[s_node], self.px[i]],
              [self.py[s_node], self.py[i]],
              color=colors[c_idx],
              lw=3.5,
              zorder=2,
          )

    for i in range(2 * n):
      active = i < curr_step_chord
      ax3.scatter(
          self.px[i],
          self.py[i],
          color=node_colors[i],
          s=70 if active else 25,
          zorder=3,
      )
      ax3.text(
          self.px[i] * 1.2,
          self.py[i] * 1.2,
          str(i + 1),
          ha='center',
          va='center',
          fontsize=8,
      )

    ax3.axis('off')
    ax3.set_title(
        f'3. Dynamic Non-intersecting Chord (Step:{curr_step_chord}/{2*n})',
        fontsize=11,
        fontweight='bold',
    )

    # =========================================================================
    # 4. [右下] 動態三角形剖分與對偶過程
    # =========================================================================
    ax4 = self.fig.add_subplot(2, 2, 4)
    ax4.set_xlim(-1.4, 1.4)
    ax4.set_ylim(-1.4, 1.4)
    ax4.set_aspect('equal')
    ax4.axis('off')

    self.draw_polygon_base(ax4)
    self.draw_chords(ax4, tree, 1, self.n_v, alpha=0.1)

    nodes_ax4, interleaved_edges, leaf_nodes_map = [], [], {}
    self._collect_dual_elements(
        tree,
        1,
        self.n_v,
        colors,
        nodes_ax4,
        interleaved_edges,
        leaf_nodes_map,
    )

    total_edges = len(interleaved_edges)
    progress_ratio = curr_step_chord / (2 * n) if (2 * n) > 0 else 0
    current_edge_count = int(round(progress_ratio * total_edges))

    # 1. 節點全部預先畫好
    for node_item in nodes_ax4:
      ax4.scatter(
          node_item['pos'][0],
          node_item['pos'][1],
          color=node_item['color'],
          s=node_item['size'],
          marker=node_item['marker'],
          zorder=5,
      )

    # 2. 畫線段並在旁邊標上編號
    for idx in range(current_edge_count):
      e = interleaved_edges[idx]
      ax4.plot(
          [e['p1'][0], e['p2'][0]],
          [e['p1'][1], e['p2'][1]],
          color=e['color'],
          lw=2,
          zorder=4,
      )

      ax4.text(
          e['mid'][0],
          e['mid'][1],
          str(e['step']),
          color='black',
          fontsize=9,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              boxstyle='circle,pad=0.2',
              facecolor='white',
              alpha=0.9,
              edgecolor=e['color'],
              lw=1.5,
          ),
          zorder=6,
      )

      if e['is_leaf'] and idx in leaf_nodes_map:
        ln = leaf_nodes_map[idx]
        ax4.scatter(
            ln['pos'][0],
            ln['pos'][1],
            color=ln['color'],
            s=ln['size'],
            marker=ln['marker'],
            zorder=5,
        )

    ax4.set_title(
        f'4. Draw Dual Progress (Step:{current_edge_count}/{total_edges})',
        fontsize=11,
        fontweight='bold',
    )

    # --- 總標題 ---
    self.fig.suptitle(
        'Catalan Bijection Mapping | Page'
        f' #{self.current_page+1}/{self.total_count}\n',
        fontsize=14,
        fontweight='bold',
        y=0.96,
    )

    self.fig.subplots_adjust(
        left=0.05, right=0.95, top=0.88, bottom=0.06, hspace=0.25, wspace=0.1
    )
    self.fig.canvas.draw_idle()

