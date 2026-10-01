import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class TriToNCP:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除舊圖表快取，避免 Streamlit 記憶體洩漏

    self.n = int(n)
    self.n_v = self.n + 2  # (n+2)-邊形

    # 生成所有 Catalan 結構
    self.paths = self.generate_ordered_paths(self.n)
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = self.n
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False
    self.timer = None

    # 多邊形與 NCP 圓形頂點座標
    self.verts = self._generate_verts(self.n_v)
    self.ncp_verts = self._generate_verts(self.n)

    # 色彩調色盤
    self.palette = self.generate_rgb_palette(self.n)

    # 建立寬螢幕畫布
    self.fig = plt.figure(figsize=(16, 8.0))

    # 劃分 2x4 網格佈局 (調整 top=0.86 與 hspace=0.45 留出適當間距)
    gs = self.fig.add_gridspec(
        5, 4, wspace=0.25, hspace=0.45, bottom=0.06, top=0.86
    )
    self.ax1 = self.fig.add_subplot(gs[0:2, 0:2])  # 1. 靜態剖分圖 (無編號)
    self.ax2 = self.fig.add_subplot(gs[0:2, 2:4])  # 2. 靜態 NCP 圖 (無編號)
    self.ax3 = self.fig.add_subplot(gs[2:5, 0:2])  # 3. 動態剖分過程 (含 Left/Right rem)
    self.ax4 = self.fig.add_subplot(gs[2:5, 2:4])  # 4. 動態 NCP 建構過程

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
    return [
        mcolors.to_hex(mcolors.hsv_to_rgb((i / n, 0.85, 0.90))) for i in range(n)
    ]

  def _generate_verts(self, count):
    v = {}
    angle_step = 2 * np.pi / count
    offset = np.pi / 2 - angle_step / 2
    for i in range(1, count + 1):
      angle = offset - (i - 1) * angle_step
      v[i] = np.array([np.cos(angle), np.sin(angle)])
    return v

  def generate_ordered_paths(self, n):
    paths = []

    def backtrack(u, d, path):
      if len(path) == 2 * n:
        paths.append(path)
        return
      if u < n:
        backtrack(u + 1, d, path + 'U')
      if d < u:
        backtrack(u, d + 1, path + 'D')

    backtrack(0, 0, '')
    return sorted(paths, key=lambda p: [0 if c == 'U' else 1 for c in p])

  def path_to_tree(self, path):
    if not path:
      return None
    balance, split_idx = 0, -1
    for i, char in enumerate(path):
      balance += 1 if char == 'U' else -1
      if balance == 0:
        split_idx = i
        break
    return {
        'left': self.path_to_tree(path[1:split_idx]),
        'right': self.path_to_tree(path[split_idx + 1 :]),
        'left_nodes': split_idx // 2,
        'right_nodes': (len(path) - split_idx - 1) // 2,
    }

  def build_triangles(self, node, L, R, current_id=1):
    if not node:
      return []
    k = L + node['right_nodes'] + 1
    p1, p2, p3 = self.verts[L], self.verts[k], self.verts[R]
    my_tri = {
        'id': current_id,
        'verts': (L, k, R),
        'centroid': (p1 + p2 + p3) / 3.0,
        'left_rem': R - k - 1,
        'right_rem': k - L - 1,
        'node_ref': node,
    }
    left_tris = self.build_triangles(node['left'], k, R, current_id + 1)
    right_tris = self.build_triangles(
        node['right'], L, k, current_id + 1 + len(left_tris)
    )
    return [my_tri] + left_tris + right_tris

  def extract_ncp_blocks(self, node):
    """核心雙射：依據二元樹左子鏈提取不相交分割 (NCP) 區塊"""
    if not node:
      return []
    curr_id = node.get('id', 1)

    left_blocks = self.extract_ncp_blocks(node['left'])
    right_blocks = self.extract_ncp_blocks(node['right'])

    if left_blocks:
      my_block = [curr_id] + left_blocks[0]
      other_left = left_blocks[1:]
    else:
      my_block = [curr_id]
      other_left = []

    return [my_block] + other_left + right_blocks

  def assign_ids_to_tree(self, node, current_id=1):
    if not node:
      return current_id
    node['id'] = current_id
    next_id = self.assign_ids_to_tree(node['left'], current_id + 1)
    return self.assign_ids_to_tree(node['right'], next_id)

  def reset_animation(self):
    self.anim_step = 0
    self.is_playing = False
    if self.timer:
      self.timer.stop()
    self.update_display()

  # --- 繪圖輔助函式 ---
  def draw_polygon_base(self, ax, show_labels=True):
    for i in range(1, self.n_v + 1):
      next_i = i + 1 if i < self.n_v else 1
      p1, p2 = self.verts[i], self.verts[next_i]
      ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='black', lw=1.8, zorder=5)
      if show_labels:
        ax.text(
            p1[0] * 1.12,
            p1[1] * 1.12,
            f'${{{i}}}$',
            ha='center',
            va='center',
            fontweight='bold',
            fontsize=10,
            zorder=5,
        )

  def draw_single_triangle(
      self, ax, tri, color, is_active=False, fill=True, show_label=True
  ):
    L, k, R = tri['verts']
    p1, p2, p3 = self.verts[L], self.verts[k], self.verts[R]
    if fill:
      poly = plt.Polygon(
          [p1, p2, p3],
          facecolor=color,
          alpha=0.55 if is_active else 0.35,
          zorder=2,
      )
      ax.add_patch(poly)

    # 只畫內部對角線
    for u, v in [(L, k), (k, R), (L, R)]:
      u_m, v_m = min(u, v), max(u, v)
      if not (u_m + 1 == v_m or (u_m == 1 and v_m == self.n_v)):
        pu, pv = self.verts[u], self.verts[v]
        ax.plot(
            [pu[0], pv[0]],
            [pu[1], pv[1]],
            color=color,
            lw=2.5 if is_active else 1.5,
            zorder=3,
        )

    if show_label:
      cx, cy = tri['centroid']
      ax.text(
          cx,
          cy,
          str(tri['id']),
          color='white' if fill else color,
          fontsize=9,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              facecolor=color if fill else 'white',
              boxstyle='circle,pad=0.15',
              alpha=0.95,
          ),
          zorder=6,
      )

  def draw_ncp_base(self, ax, show_labels=True, color_vertices=True):
    """繪製 NCP 圓形底圖 (頂點顏色對應三角形色彩)"""
    circle = plt.Circle(
        (0, 0),
        1.0,
        color='#e0e0e0',
        fill=False,
        linestyle='--',
        lw=1.5,
        zorder=1,
    )
    ax.add_patch(circle)
    for i in range(1, self.n + 1):
      p = self.ncp_verts[i]
      v_color = self.palette[i - 1] if color_vertices else '#2c3e50'
      ax.scatter(p[0], p[1], color=v_color, s=55, zorder=5)
      if show_labels:
        ax.text(
            p[0] * 1.15,
            p[1] * 1.15,
            str(i),
            ha='center',
            va='center',
            fontweight='bold',
            fontsize=11,
            zorder=6,
        )

  def draw_ncp_block(self, ax, block, color, is_active=False):
    """在 NCP 圓形點位上繪製子集 Block"""
    pts = [self.ncp_verts[elem] for elem in sorted(block)]

    if len(pts) == 1:
      ax.scatter(
          pts[0][0], pts[0][1], color=color, s=120 if is_active else 80, zorder=7
      )
    elif len(pts) == 2:
      ax.plot(
          [pts[0][0], pts[1][0]],
          [pts[0][1], pts[1][1]],
          color=color,
          lw=3.5 if is_active else 2.2,
          zorder=4,
      )
    else:
      poly = plt.Polygon(
          pts,
          facecolor=color,
          alpha=0.45 if is_active else 0.25,
          edgecolor=color,
          lw=3.0 if is_active else 1.8,
          zorder=3,
      )
      ax.add_patch(poly)

  def update_display(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    tree = self.path_to_tree(path)
    self.assign_ids_to_tree(tree, 1)

    triangles = self.build_triangles(tree, 1, self.n_v)
    ncp_blocks = self.extract_ncp_blocks(tree)
    status_str = 'PLAYING' if self.is_playing else 'PAUSED'

    # 1. 靜態剖分圖 (無編號)
    self.ax1.set_title(
        f'1. {self.n_v}-gon Triangulation', fontsize=11, fontweight='bold', pad=8
    )
    self.draw_polygon_base(self.ax1, show_labels=False)
    for tri in triangles:
      self.draw_single_triangle(
          self.ax1, tri, color='black', fill=False, show_label=False
      )

    # 2. 靜態 NCP 圖 (頂點色彩與三角形對齊)
    self.ax2.set_title(
        f'2. Non-Crossing Partition',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_ncp_base(self.ax2, show_labels=False, color_vertices=True)
    for block in ncp_blocks:
      block_color = self.palette[block[0] - 1]
      self.draw_ncp_block(self.ax2, block, color=block_color)

    # 3. 動態剖分圖 (含編號與 Left/Right rem 提示)
    self.ax3.set_title(
        '3. Draw Triangulation Progress (Step:'
        f' {self.anim_step} / {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_polygon_base(self.ax3, show_labels=True)

    active_info_str = ''
    for idx in range(min(self.anim_step, len(triangles))):
      tri = triangles[idx]
      is_curr = idx == self.anim_step - 1
      self.draw_single_triangle(
          self.ax3,
          tri,
          color=self.palette[tri['id'] - 1],
          is_active=is_curr,
          fill=True,
          show_label=True,
      )

      if is_curr:
        L, k, R = tri['verts']
        active_info_str = (
            rf"Tri #{tri['id']}: ($\Delta x_{{{L}}} x_{{{k}}} x_{{{R}}}$)  | "
            f" Left rem: {tri['left_rem']} tris  |  Right rem:"
            f" {tri['right_rem']} tris"
        )

    self.ax3.text(
        0,
        -1.35,
        active_info_str,
        ha='center',
        va='center',
        color='#8e44ad',
        fontweight='bold',
        fontsize=9.5,
    )

    # 4. 動態 NCP 建構過程 (頂點彩色呈現)
    self.ax4.set_title(
        '4. Dynamic Non-crossing Partition',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_ncp_base(self.ax4, show_labels=True, color_vertices=True)

    active_ids = set(range(1, self.anim_step + 1))
    for block in ncp_blocks:
      visible_sub_block = [elem for elem in block if elem in active_ids]
      if visible_sub_block:
        is_curr = self.anim_step in visible_sub_block
        block_color = self.palette[block[0] - 1]
        self.draw_ncp_block(
            self.ax4, visible_sub_block, color=block_color, is_active=is_curr
        )

    # 調整畫布視角
    for ax in [self.ax1, self.ax3]:
      ax.set_aspect('equal')
      ax.axis('off')
      ax.set_xlim(-1.3, 1.3)
      ax.set_ylim(-1.45, 1.3)

    for ax in [self.ax2, self.ax4]:
      ax.set_aspect('equal')
      ax.axis('off')
      ax.set_xlim(-1.3, 1.3)
      ax.set_ylim(-1.3, 1.3)

    self.fig.suptitle(
        'Catalan Bijection Mapping '
        f' | Page #{self.current_idx+1}/{self.total_count}',
        fontsize=12,
        fontweight='bold',
        y=0.96,
    )
    self.fig.canvas.draw_idle()


