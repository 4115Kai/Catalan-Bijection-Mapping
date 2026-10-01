import logging
import math
import warnings
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

# 基礎警報封鎖
warnings.filterwarnings(
    'ignore', category=UserWarning, module='matplotlib'
)
warnings.filterwarnings('ignore', category=DeprecationWarning)
logging.getLogger('matplotlib').setLevel(logging.ERROR)



class AtNCP:

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

    # 計算 直線拉直視圖 (Linear) 的基礎位置 (2n 個節點)
    self.linear_x = np.arange(2 * self.n)
    self.linear_y = np.zeros(2 * self.n)

    # 計算 NCP 圖的基礎位置 (n 個節點) - 確保頂點 1 永遠在正上方 (pi/2)
    angles_ncp = np.pi / 2 - np.linspace(
        0, 2 * np.pi, self.n, endpoint=False
    )
    self.ncp_pts = {
        i + 1: (0.85 * np.cos(a), 0.85 * np.sin(a))
        for i, a in enumerate(angles_ncp)
    }

    # 建立大型畫布
    self.fig = plt.figure(figsize=(21, 8.5))

    # 劃分 2x2 網格 (調整邊界以利呈現)
    gs = self.fig.add_gridspec(
        2, 2, wspace=0.15, hspace=0.35, bottom=0.06, top=0.88
    )
    self.ax_linear_static = self.fig.add_subplot(gs[0, 0])
    self.ax_ncp_static = self.fig.add_subplot(gs[0, 1])
    self.ax_linear_dynamic = self.fig.add_subplot(gs[1, 0])
    self.ax_ncp_dynamic = self.fig.add_subplot(gs[1, 1])

    self._prepare_data_and_static()
    self.update_dynamic_display()

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

  def _prepare_data_and_static(self):
    self.word = self.words[self.current_idx]

    self.final_groups = []
    self.pair_to_group_color = {}
    self.linear_pair_labels = {}
    stack = []
    temp_stack_for_pairs = []

    open_node_counter = 0

    for i, char in enumerate(self.word):
      if char == '(':
        open_node_counter += 1
        node_idx = open_node_counter
        stack.append({'node': node_idx, 'x': i})
        temp_stack_for_pairs.append(i)
      else:
        start_info = stack.pop()
        start_x = temp_stack_for_pairs.pop()

        actual_closing_node = len(
            [c for c in self.word[: i + 1] if c == '(']
        )
        pair_nodes = {start_info['node'], actual_closing_node}
        pair = {
            'nodes': pair_nodes,
            'range': (start_info['x'], i),
            'linear_pair': (start_x, i),
        }

        self.linear_pair_labels[(start_x, i)] = start_info['node']

        found = False
        for g in self.final_groups:
          if not pair['nodes'].isdisjoint(g['nodes']):
            g['nodes'].update(pair['nodes'])
            g['pairs'].append(pair)
            found = True
            break
        if not found:
          self.final_groups.append({'nodes': pair['nodes'], 'pairs': [pair]})

    self.group_colors = {}
    for idx, fg in enumerate(self.final_groups):
      color = mcolors.hsv_to_rgb(
          [idx / max(1, len(self.final_groups)), 0.65, 0.9]
      )
      self.group_colors[frozenset(fg['nodes'])] = color
      for p in fg['pairs']:
        self.pair_to_group_color[p['linear_pair']] = color

    # --- 繪製左上：直線拉直視圖 (靜態參考) ---
    self.ax_linear_static.clear()
    self.ax_linear_static.set_title(
        '1. Non-crossing Arc Diagram',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    self.ax_linear_static.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax_linear_static.scatter(
        self.linear_x, self.linear_y, color='#7f8c8d', s=40, zorder=3
    )
    for i in range(2 * self.n):
      self.ax_linear_static.text(
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
    temp_orig_indices = []
    open_counter_static = 0
    for i, char in enumerate(self.word):
      if char == '(':
        open_counter_static += 1
        orig_stack.append(open_counter_static)
        temp_orig_indices.append(i)
      elif orig_stack:
        start_node_id = orig_stack.pop()
        start_x = temp_orig_indices.pop()
        center_x = (self.linear_x[start_x] + self.linear_x[i]) / 2
        radius = (self.linear_x[i] - self.linear_x[start_x]) / 2
        theta = np.linspace(0, np.pi, 100)

        self.ax_linear_static.plot(
            center_x + radius * np.cos(theta),
            radius * np.sin(theta),
            color='#7f8c8d',
            lw=2,
            alpha=0.7,
            zorder=2,
        )
        self.ax_linear_static.scatter(
            [self.linear_x[start_x], self.linear_x[i]],
            [0, 0],
            color='#7f8c8d',
            s=40,
            zorder=5,
        )

        lbl = self.linear_pair_labels.get((start_x, i), start_node_id)
        self.ax_linear_static.text(
            center_x,
            radius + 0.12,
            str(lbl),
            ha='center',
            va='bottom',
            color='#e74c3c',
            fontsize=9,
            fontweight='bold',
        )

    max_h = (2 * self.n - 1) / 2
    self.ax_linear_static.axis('off')
    self.ax_linear_static.set_xlim(-0.7, 2 * self.n - 0.3)
    self.ax_linear_static.set_ylim(-0.8, max(max_h + 0.5, 2.0))
    self.ax_linear_static.set_aspect('equal')

    # --- 繪製右上：NCP 靜態圖 ---
    self.ax_ncp_static.clear()
    self.ax_ncp_static.set_aspect('equal')
    self.ax_ncp_static.set_axis_off()
    self.ax_ncp_static.set_xlim(-1.1, 1.1)
    self.ax_ncp_static.set_ylim(-1.1, 1.1)
    self.ax_ncp_static.set_title(
        f'2. Noncrossing Partition {self.n} vertices',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )

    for j in range(1, self.n + 1):
      p1, p2 = self.ncp_pts[j], self.ncp_pts[j % self.n + 1]
      self.ax_ncp_static.plot(
          [p1[0], p2[0]], [p1[1], p2[1]], '--', color='#bdc3c7', lw=1, alpha=0.4
      )
      self.ax_ncp_static.text(
          p1[0] * 1.25,
          p1[1] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=11,
      )
      self.ax_ncp_static.add_patch(
          patches.Circle(
              p1,
              radius=0.04,
              facecolor='#7f8c8d',
              edgecolor='#7f8c8d',
              zorder=4,
          )
      )

    for fg in self.final_groups:
      sorted_nodes = sorted(list(fg['nodes']))
      if len(fg['nodes']) == 2:
        p1, p2 = self.ncp_pts[sorted_nodes[0]], self.ncp_pts[sorted_nodes[1]]
        self.ax_ncp_static.plot(
            [p1[0], p2[0]], [p1[1], p2[1]], color='#7f8c8d', lw=2, zorder=2
        )
      elif len(fg['nodes']) > 2:
        for idx in range(len(sorted_nodes)):
          p1 = self.ncp_pts[sorted_nodes[idx]]
          p2 = self.ncp_pts[sorted_nodes[(idx + 1) % len(sorted_nodes)]]
          self.ax_ncp_static.plot(
              [p1[0], p2[0]], [p1[1], p2[1]], color='#7f8c8d', lw=2, zorder=2
          )

  def update_dynamic_display(self):
    current_view = self.word[: self.anim_step]

    # -------------------------------------------------------------
    # 左下：直線拉直視圖 (動態進度)
    # -------------------------------------------------------------
    self.ax_linear_dynamic.clear()
    self.ax_linear_dynamic.set_title(
        f'3. Dynamic Non-crossing Arc Diagram (Step: {self.anim_step})',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )
    self.ax_linear_dynamic.plot(
        [-0.5, 2 * self.n - 0.5], [0, 0], color='#ddd', lw=1.5, zorder=1
    )
    self.ax_linear_dynamic.scatter(
        self.linear_x, self.linear_y, color='#e0e0e0', s=40, zorder=3
    )

    for i in range(2 * self.n):
      color = '#34495e' if i < self.anim_step else '#bdc3c7'
      self.ax_linear_dynamic.text(
          self.linear_x[i],
          -0.3,
          str(i + 1),
          ha='center',
          va='top',
          color=color,
          fontweight='bold',
          fontsize=9,
      )

    stack = []
    temp_stack_indices = []
    open_counter_dyn = 0
    for i, char in enumerate(current_view):
      if char == '(':
        open_counter_dyn += 1
        stack.append(open_counter_dyn)
        temp_stack_indices.append(i)
      else:
        if stack:
          start_node_id = stack.pop()
          start_x = temp_stack_indices.pop()

          line_color = self.pair_to_group_color.get((start_x, i), '#3498db')

          center_x = (self.linear_x[start_x] + self.linear_x[i]) / 2
          radius = (self.linear_x[i] - self.linear_x[start_x]) / 2
          theta = np.linspace(0, np.pi, 100)

          self.ax_linear_dynamic.plot(
              center_x + radius * np.cos(theta),
              radius * np.sin(theta),
              color=line_color,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )
          self.ax_linear_dynamic.scatter(
              [self.linear_x[start_x], self.linear_x[i]],
              [0, 0],
              color=line_color,
              s=50,
              zorder=5,
          )

          lbl = self.linear_pair_labels.get((start_x, i), start_node_id)
          self.ax_linear_dynamic.text(
              center_x,
              radius + 0.12,
              str(lbl),
              ha='center',
              va='bottom',
              color='#e74c3c',
              fontsize=9,
              fontweight='bold',
          )

    max_h = (2 * self.n - 1) / 2
    self.ax_linear_dynamic.axis('off')
    self.ax_linear_dynamic.set_xlim(-0.7, 2 * self.n - 0.3)
    self.ax_linear_dynamic.set_ylim(-0.8, max(max_h + 0.5, 2.0))
    self.ax_linear_dynamic.set_aspect('equal')

    # -------------------------------------------------------------
    # 右下：NCP 動態圖
    # -------------------------------------------------------------
    self.ax_ncp_dynamic.clear()
    self.ax_ncp_dynamic.set_aspect('equal')
    self.ax_ncp_dynamic.set_axis_off()
    self.ax_ncp_dynamic.set_xlim(-1.1, 1.1)
    self.ax_ncp_dynamic.set_ylim(-1.1, 1.1)
    self.ax_ncp_dynamic.set_title(
        f'4. Dynamic Non-crossing Partition (Step: {self.anim_step})',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )

    for j in range(1, self.n + 1):
      p1, p2 = self.ncp_pts[j], self.ncp_pts[j % self.n + 1]
      self.ax_ncp_dynamic.plot(
          [p1[0], p2[0]], [p1[1], p2[1]], '--', color='#bdc3c7', lw=1, alpha=0.4
      )
      self.ax_ncp_dynamic.text(
          p1[0] * 1.25,
          p1[1] * 1.25,
          str(j),
          ha='center',
          va='center',
          fontsize=11,
      )

    triggered_fg_sets = set()
    for fg_set, color in self.group_colors.items():
      for fg in self.final_groups:
        if frozenset(fg['nodes']) == fg_set:
          for p in fg['pairs']:
            s, e = p['range']
            if e + 1 <= self.anim_step:
              triggered_fg_sets.add(fg_set)

    has_polygon_shaded = set()
    for fg_set in triggered_fg_sets:
      color = self.group_colors[fg_set]
      sorted_nodes = sorted(list(fg_set))
      if len(fg_set) >= 2:
        group_pts = np.array([self.ncp_pts[node] for node in sorted_nodes])
        shrink_pts = group_pts * 0.95
        has_polygon_shaded.update(fg_set)

        if len(fg_set) == 2:
          dist = np.linalg.norm(shrink_pts[0] - shrink_pts[1])
          angle = np.degrees(
              np.arctan2(
                  shrink_pts[1][1] - shrink_pts[0][1],
                  shrink_pts[1][0] - shrink_pts[0][0],
              )
          )
          self.ax_ncp_dynamic.add_patch(
              patches.Ellipse(
                  np.mean(shrink_pts, axis=0),
                  dist + 0.12,
                  0.10,
                  angle=angle,
                  facecolor=color,
                  alpha=0.25,
              )
          )
        else:
          self.ax_ncp_dynamic.add_patch(
              patches.Polygon(
                  shrink_pts, closed=True, facecolor=color, alpha=0.25
              )
          )

    for node in range(1, self.n + 1):
      if node not in has_polygon_shaded:
        node_closed = False
        for fg_set in triggered_fg_sets:
          if node in fg_set:
            node_closed = True
        if node_closed:
          node_color = '#95a5a6'
          for fg_set, col in self.group_colors.items():
            if node in fg_set:
              node_color = col
              break
          self.ax_ncp_dynamic.add_patch(
              patches.Circle(
                  self.ncp_pts[node],
                  radius=0.06,
                  facecolor=node_color,
                  alpha=0.35,
                  edgecolor=node_color,
                  linewidth=1.5,
                  zorder=4,
              )
          )

      self.ax_ncp_dynamic.add_patch(
          patches.Circle(
              self.ncp_pts[node], radius=0.03, facecolor='#bdc3c7', zorder=3
          )
      )

    self.fig.suptitle(
        'Catalan Bijection Mapping  | '
        f' Page #{self.current_idx+1}/{self.total_count}\n',
        fontsize=15,
        fontweight='bold',
        y=0.98,
    )
    self.fig.canvas.draw_idle()

