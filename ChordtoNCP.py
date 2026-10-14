
import math

import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np




class CtoNCP:

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

    # 計算 圓周不相交弦 (Chord) 的基礎位置 (2n 個節點) - 頂點 1 設於正上方 (pi/2)
    angles_chord = np.pi / 2 - np.linspace(
        0, 2 * np.pi, 2 * self.n, endpoint=False
    )
    self.chord_pts = {
        i: (0.85 * np.cos(a), 0.85 * np.sin(a))
        for i, a in enumerate(angles_chord)
    }

    # 計算 NCP 圖的基礎位置 (n 個節點) - 頂點 1 設於正上方 (pi/2)
    angles_ncp = np.pi / 2 - np.linspace(
        0, 2 * np.pi, self.n, endpoint=False
    )
    self.ncp_pts = {
        i + 1: (0.85 * np.cos(a), 0.85 * np.sin(a))
        for i, a in enumerate(angles_ncp)
    }

    # 建立大型畫布
    self.fig = plt.figure(figsize=(21, 8.5))

    # 劃分 2x2 網格
    gs = self.fig.add_gridspec(
        2, 2, wspace=0.15, hspace=0.35, bottom=0.06, top=0.88
    )
    self.ax_chord_static = self.fig.add_subplot(gs[0, 0])
    self.ax_ncp_static = self.fig.add_subplot(gs[0, 1])
    self.ax_chord_dynamic = self.fig.add_subplot(gs[1, 0])
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
    self.vertex_to_color = {}
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
        self.vertex_to_color[p['linear_pair'][0]] = color
        self.vertex_to_color[p['linear_pair'][1]] = color

    # --- 繪製左上：圓周不相交弦 (靜態參考) ---
    self.ax_chord_static.clear()
    self.ax_chord_static.set_aspect('equal')
    self.ax_chord_static.set_axis_off()
    self.ax_chord_static.set_xlim(-1.1, 1.1)
    self.ax_chord_static.set_ylim(-1.1, 1.1)
    self.ax_chord_static.set_title(
        f'1. Non-crossing Chord Diagram ({2 * self.n} vertices)',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )

    # 補上：圓周線條 (Circle boundary)
    self.ax_chord_static.add_patch(
        patches.Circle(
            (0, 0),
            radius=0.85,
            fill=False,
            color='#bdc3c7',
            lw=1.5,
            linestyle='--',
            alpha=0.6,
            zorder=1,
        )
    )

    for i in range(2 * self.n):
      p = self.chord_pts[i]
      self.ax_chord_static.text(
          p[0] * 1.22,
          p[1] * 1.22,
          str(i + 1),
          ha='center',
          va='center',
          color='#34495e',
          fontweight='bold',
          fontsize=9,
      )
      self.ax_chord_static.add_patch(
          patches.Circle(
              p,
              radius=0.03,
              facecolor='#7f8c8d',
              edgecolor='#7f8c8d',
              zorder=4,
          )
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
        p1, p2 = self.chord_pts[start_x], self.chord_pts[i]

        self.ax_chord_static.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            color='#7f8c8d',
            lw=2,
            alpha=0.7,
            zorder=2,
        )

        lbl = self.linear_pair_labels.get((start_x, i), start_node_id)
        mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        self.ax_chord_static.text(
            mid_x,
            mid_y,
            str(lbl),
            ha='center',
            va='center',
            color='#e74c3c',
            fontsize=8,
            fontweight='bold',
            bbox=dict(
                boxstyle='circle,pad=0.15', fc='white', ec='none', alpha=0.7
            ),
        )

    # --- 繪製右上：NCP 靜態圖 ---
    self.ax_ncp_static.clear()
    self.ax_ncp_static.set_aspect('equal')
    self.ax_ncp_static.set_axis_off()
    self.ax_ncp_static.set_xlim(-1.1, 1.1)
    self.ax_ncp_static.set_ylim(-1.1, 1.1)
    self.ax_ncp_static.set_title(
        f'2. Non-crossing Partition ({self.n} vertices)',
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
    # 左下：圓周不相交弦 (動態進度與頂點上色)
    # -------------------------------------------------------------
    self.ax_chord_dynamic.clear()
    self.ax_chord_dynamic.set_aspect('equal')
    self.ax_chord_dynamic.set_axis_off()
    self.ax_chord_dynamic.set_xlim(-1.1, 1.1)
    self.ax_chord_dynamic.set_ylim(-1.1, 1.1)
    self.ax_chord_dynamic.set_title(
        f'3. Dynamic Non-crossing Chord Diagram (Step: {self.anim_step})',
        fontsize=12,
        fontweight='bold',
        pad=12,
    )

    # 補上：圓周線條 (Circle boundary)
    self.ax_chord_dynamic.add_patch(
        patches.Circle(
            (0, 0),
            radius=0.85,
            fill=False,
            color='#bdc3c7',
            lw=1.5,
            linestyle='--',
            alpha=0.6,
            zorder=1,
        )
    )

    for i in range(2 * self.n):
      p = self.chord_pts[i]
      if i < self.anim_step:
        v_color = self.vertex_to_color.get(i, '#3498db')
        self.ax_chord_dynamic.add_patch(
            patches.Circle(
                p,
                radius=0.04,
                facecolor=v_color,
                edgecolor=v_color,
                zorder=5,
            )
        )
        txt_color = '#34495e'
      else:
        self.ax_chord_dynamic.add_patch(
            patches.Circle(
                p,
                radius=0.03,
                facecolor='#e0e0e0',
                edgecolor='#bdc3c7',
                zorder=3,
            )
        )
        txt_color = '#bdc3c7'

      self.ax_chord_dynamic.text(
          p[0] * 1.22,
          p[1] * 1.22,
          str(i + 1),
          ha='center',
          va='center',
          color=txt_color,
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
          p1, p2 = self.chord_pts[start_x], self.chord_pts[i]

          self.ax_chord_dynamic.plot(
              [p1[0], p2[0]],
              [p1[1], p2[1]],
              color=line_color,
              lw=2.5,
              alpha=0.9,
              zorder=2,
          )

          lbl = self.linear_pair_labels.get((start_x, i), start_node_id)
          mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
          self.ax_chord_dynamic.text(
              mid_x,
              mid_y,
              str(lbl),
              ha='center',
              va='center',
              color='#e74c3c',
              fontsize=8,
              fontweight='bold',
              bbox=dict(
                  boxstyle='circle,pad=0.15',
                  fc='white',
                  ec='none',
                  alpha=0.8,
              ),
          )

    # -------------------------------------------------------------
    # 右下：NCP 動態圖 (頂點同步帶有顏色)
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

    # 計算當前動態步驟中，NCP 頂點所對應的顏色
    active_ncp_colors = {}
    for i in range(min(self.anim_step, 2 * self.n)):
      node = len([c for c in self.word[: i + 1] if c == '('])
      v_color = self.vertex_to_color.get(i, '#3498db')
      active_ncp_colors[node] = v_color

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

      # 若該 NCP 頂點已在動態步驟中被活化，則上對應顏色；否則保持預設淡灰色
      if node in active_ncp_colors:
        self.ax_ncp_dynamic.add_patch(
            patches.Circle(
                self.ncp_pts[node],
                radius=0.05,
                facecolor=active_ncp_colors[node],
                edgecolor=active_ncp_colors[node],
                zorder=5,
            )
        )
      else:
        self.ax_ncp_dynamic.add_patch(
            patches.Circle(
                self.ncp_pts[node], radius=0.03, facecolor='#bdc3c7', zorder=3
            )
        )

    self.fig.suptitle(
        'Catalan Bijection Mapping  | '
        f' Path #{self.current_idx+1}/{self.total_count}\n',
        fontsize=15,
        fontweight='bold',
        y=0.98,
    )
    self.fig.canvas.draw_idle()