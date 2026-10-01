import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class PTP2:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除舊圖表快取，避免 Streamlit 記憶體洩漏

    self.n = int(n)
    self.n_v = self.n + 2  # (n+2)-邊形

    # 生成所有 Dyck Path 及其雙射樹結構
    self.paths = self.generate_ordered_paths(self.n)
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))

    # 接收 Streamlit 傳入的動畫步驟 index
    self.max_steps = 2 * self.n
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False
    self.timer = None

    # 多邊形頂點座標生成
    self.verts = self._generate_verts()

    # 色彩調色盤
    self.palette = self.generate_rgb_palette(self.n)

    # 建立寬螢幕畫布
    self.fig = plt.figure(figsize=(16, 8.0))

    # 劃分網格佈局（調整 top=0.86 與 hspace=0.45 預留足夠頂部與垂直間距）
    gs = self.fig.add_gridspec(
        5, 4, wspace=0.25, hspace=0.45, bottom=0.06, top=0.86
    )

    self.ax1 = self.fig.add_subplot(gs[0:2, 0:2])  # 1. 靜態多邊形
    self.ax2 = self.fig.add_subplot(gs[0:2, 2:4])  # 2. 靜態山脈 Dyck Path
    self.ax3 = self.fig.add_subplot(gs[2:5, 0:2])  # 3. 動態剖分過程
    self.ax4 = self.fig.add_subplot(gs[2:5, 2:4])  # 4. 動態山脈生成過程

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

  def _generate_verts(self):
    """生成正 (n+2)-邊形頂點座標"""
    v = {}
    angle_step = 2 * np.pi / self.n_v
    offset = np.pi / 2 - angle_step / 2
    for i in range(1, self.n_v + 1):
      angle = offset - (i - 1) * angle_step
      v[i] = np.array([np.cos(angle), np.sin(angle)])
    return v

  def is_internal(self, u, v):
    """判斷 (u, v) 是否為內部對角線（非多邊形外框邊）"""
    u_m, v_m = min(u, v), max(u, v)
    if u_m + 1 == v_m:
      return False
    if u_m == 1 and v_m == self.n_v:
      return False
    return True

  def generate_ordered_paths(self, n):
    """生成長度 2n 的 Dyck Path (U/D)"""
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
    """將 Dyck Path 轉換為二元樹"""
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

  def build_triangles_and_pairs(
      self, node, L, R, offset=0, current_id=1, parent_id=None
  ):
    """精確映射 Dyck Path 步驟索引至多邊形三角形 (含 push/pop 步號與 parent_id)"""
    if not node:
      return []

    n1 = node['left_nodes']
    n2 = node['right_nodes']

    k = L + n2 + 1
    my_push_step = offset
    my_pop_step = offset + 1 + 2 * n1

    p1, p2, p3 = self.verts[L], self.verts[k], self.verts[R]
    centroid = (p1 + p2 + p3) / 3.0

    my_tri = {
        'id': current_id,
        'parent_id': parent_id,
        'verts': (L, k, R),
        'centroid': centroid,
        'right_rem': k - L - 1,
        'left_rem': R - k - 1,
        'push_step': my_push_step,
        'pop_step': my_pop_step,
    }

    # 左側區域
    left_tris = self.build_triangles_and_pairs(
        node['left'],
        k,
        R,
        offset=offset + 1,
        current_id=current_id + 1,
        parent_id=current_id,
    )

    # 右側區域
    right_tris = self.build_triangles_and_pairs(
        node['right'],
        L,
        k,
        offset=offset + 2 * n1 + 2,
        current_id=current_id + 1 + n1,
        parent_id=current_id,
    )

    return [my_tri] + left_tris + right_tris

  def build_mountain_path_segments(self, path, triangles):
    """建立每一步 (0 ~ 2n-1) 的山脈斜線段與對應三角形 ID 的對照表"""
    step_tri_map = {}
    for tri in triangles:
      step_tri_map[tri['push_step']] = tri
      step_tri_map[tri['pop_step']] = tri

    segments = []
    curr_x, curr_y = 0, 0
    for i, char in enumerate(path):
      if char == 'U':
        next_x, next_y = curr_x + 1, curr_y + 1
      else:
        next_x, next_y = curr_x + 1, curr_y - 1

      tri = step_tri_map[i]
      segments.append({
          'step_idx': i,
          'char': char,
          'p1': (curr_x, curr_y),
          'p2': (next_x, next_y),
          'tri_id': tri['id'],
          'color': self.palette[tri['id'] - 1],
      })
      curr_x, curr_y = next_x, next_y

    return segments

  def reset_animation(self):
    self.anim_step = 0
    self.is_playing = False
    if self.timer:
      self.timer.stop()
    self.update_display()

  def draw_polygon_base(self, ax):
    """繪製多邊形外框與頂點名稱 x_1 ~ x_{n+2} (置頂 zorder=5)"""
    for i in range(1, self.n_v + 1):
      next_i = i + 1 if i < self.n_v else 1
      p1, p2 = self.verts[i], self.verts[next_i]
      is_base = (i == self.n_v and next_i == 1) or (
          i == 1 and next_i == self.n_v
      )
      c, lw = ('#ca0fec', 2.2) if is_base else ('black', 1.8)
      ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=lw, zorder=5)
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
    """繪製三角形：面與線分離，只對內部對角線繪製彩線"""
    L, k, R = tri['verts']
    p1, p2, p3 = self.verts[L], self.verts[k], self.verts[R]
    cx, cy = tri['centroid']

    if fill:
      poly = plt.Polygon(
          [p1, p2, p3],
          facecolor=color,
          alpha=0.55 if is_active else 0.35,
          edgecolor='none',
          zorder=2,
      )
      ax.add_patch(poly)

    edges = [(L, k), (k, R), (L, R)]
    lw = 2.5 if is_active else 1.5
    ls = '-' if (fill or is_active) else ':'

    for u, v in edges:
      if self.is_internal(u, v):
        pu, pv = self.verts[u], self.verts[v]
        ax.plot(
            [pu[0], pv[0]],
            [pu[1], pv[1]],
            color=color,
            lw=lw,
            linestyle=ls,
            zorder=3,
        )

    if show_label:
      bg_color = color if fill else 'white'
      text_color = 'white' if fill else color
      ax.text(
          cx,
          cy,
          str(tri['id']),
          color=text_color,
          fontsize=8.5,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              facecolor=bg_color,
              edgecolor=color if not fill else 'none',
              boxstyle='circle,pad=0.15',
              lw=1.0,
              alpha=0.95,
          ),
          zorder=6,
      )

  def draw_mountain_base(self, ax):
    """繪製山脈 Dyck Path 的完整基底網格與地平線"""
    ax.set_aspect('equal', adjustable='box')

    for x in range(2 * self.n + 1):
      ax.plot(
          [x, x], [0, self.n], color='#e0e0e0', linestyle='--', lw=1.0, zorder=1
      )
    for y in range(self.n + 1):
      c = '#2c3e50' if y == 0 else '#e0e0e0'
      lw = 2.0 if y == 0 else 1.0
      ls = '-' if y == 0 else '--'
      ax.plot([0, 2 * self.n], [y, y], color=c, linestyle=ls, lw=lw, zorder=1)

    x_min, x_max = -0.5, 2 * self.n + 0.5
    y_min, y_max = -0.8, self.n + 1.2
    ax.scatter(
        [x_min, x_max, x_min, x_max],
        [y_min, y_min, y_max, y_max],
        alpha=0,
        zorder=0,
    )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_autoscale_on(False)

  def draw_mountain_segment(self, ax, seg, is_active=False, show_label=True):
    """單步繪製山脈 Dyck Path 的一條斜線段 (Up 或 Down)"""
    (x1, y1), (x2, y2) = seg['p1'], seg['p2']
    color = seg['color']

    ax.plot(
        [x1, x2], [y1, y2], color=color, lw=3.5 if is_active else 2.2, zorder=4
    )
    ax.scatter(
        [x1, x2], [y1, y2], color=color, s=20 if is_active else 12, zorder=5
    )

    if show_label:
      mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
      offset_y = 0.25

      is_down = y2 < y1
      if is_down:
        text_color = color
        box_face = 'white'
        box_edge = color
        line_width = 1.2
      else:
        text_color = 'white'
        box_face = color
        box_edge = 'none'
        line_width = 1.0

      ax.text(
          mid_x,
          mid_y + offset_y,
          str(seg['tri_id']),
          color=text_color,
          fontsize=8,
          fontweight='bold',
          ha='center',
          va='center',
          bbox=dict(
              facecolor=box_face,
              edgecolor=box_edge,
              linewidth=line_width,
              boxstyle='circle,pad=0.15',
              alpha=0.95,
          ),
          zorder=6,
      )

  def update_display(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    tree = self.path_to_tree(path)
    status_str = 'PLAYING' if self.is_playing else 'PAUSED'

    triangles = self.build_triangles_and_pairs(tree, 1, self.n_v)
    mountain_segs = self.build_mountain_path_segments(path, triangles)

    # 1. Static Polygon Triangulation
    self.ax1.set_title(
        f'1. {self.n_v} edges Polygon Triangulation',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_polygon_base(self.ax1)
    for tri in triangles:
      self.draw_single_triangle(
          self.ax1, tri, color='black', fill=False, show_label=False
      )

    # 2. Static Mountain Dyck Path
    self.ax2.set_title(
        f'2. Dyck Path ({path})', fontsize=11, fontweight='bold', pad=8
    )
    self.draw_mountain_base(self.ax2)
    for seg in mountain_segs:
      (x1, y1), (x2, y2) = seg['p1'], seg['p2']
      self.ax2.plot([x1, x2], [y1, y2], color='black', lw=2.0, zorder=4)
      self.ax2.scatter([x1, x2], [y1, y2], color='black', s=12, zorder=5)

    # 3. Dynamic Polygon Triangulation
    self.ax3.set_title(
        '3. Draw Triangulation Progress (Step:'
        f' {self.anim_step} / {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_polygon_base(self.ax3)

    for tri in triangles:
      L, k, R = tri['verts']
      for u, v in [(L, k), (k, R), (L, R)]:
        if self.is_internal(u, v):
          pu, pv = self.verts[u], self.verts[v]
          self.ax3.plot(
              [pu[0], pv[0]],
              [pu[1], pv[1]],
              color='#999999',
              lw=1.2,
              linestyle='--',
              zorder=1,
          )

    curr_stack_state = []
    for i in range(self.anim_step):
      c = path[i]
      tri_id = mountain_segs[i]['tri_id']
      if c == 'U':
        curr_stack_state.append(tri_id)
      else:
        if curr_stack_state:
          curr_stack_state.pop()

    active_info_str = ''
    if self.anim_step > 0:
      curr_idx = self.anim_step - 1
      curr_char = path[curr_idx]

      for tri in triangles:
        p_step = tri['push_step']
        d_step = tri['pop_step']
        color = self.palette[tri['id'] - 1]

        if curr_idx >= d_step:
          is_active = curr_idx == d_step
          self.draw_single_triangle(
              self.ax3,
              tri,
              color=color,
              is_active=is_active,
              fill=False,
              show_label=True,
          )
        elif curr_idx >= p_step:
          is_active = curr_idx == p_step
          self.draw_single_triangle(
              self.ax3,
              tri,
              color=color,
              is_active=is_active,
              fill=True,
              show_label=True,
          )

        if curr_idx == p_step or curr_idx == d_step:
          L, k, R = tri['verts']
          l_size = tri['left_rem']
          r_size = tri['right_rem']

          if curr_char == 'U':
            desc = f'Left rems: {l_size} tris | Right rems: {r_size} tris'
          else:
            if r_size > 0:
              desc = f'Left rems: 0 -> Go to the right side ({r_size} tris)'
            else:
              if len(curr_stack_state) > 0:
                back_target = curr_stack_state[-1]
                desc = f'Left & Right rems: 0 -> Back to Tri #{back_target}'
              else:
                desc = 'Left & Right rems: 0 -> Triangulation Complete!'

          active_info_str = (
              rf' Now: Tri #{tri["id"]} ($\Delta x_{{{L}}} x_{{{k}}}'
              rf' x_{{{R}}}$)  |  {desc}'
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

    # 4. Dynamic Mountain Dyck Path Progress
    self.ax4.set_title(
        f'4. Draw Dyck Path (Step: {self.anim_step} / {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_mountain_base(self.ax4)

    for idx in range(min(self.anim_step, len(mountain_segs))):
      seg = mountain_segs[idx]
      is_current = idx == self.anim_step - 1
      self.draw_mountain_segment(
          self.ax4, seg, is_active=is_current, show_label=True
      )

    for ax in [self.ax1, self.ax3]:
      ax.set_aspect('equal')
      ax.axis('off')
      ax.set_xlim(-1.35, 1.35)
      ax.set_ylim(-1.45, 1.25)

    for ax in [self.ax2, self.ax4]:
      ax.set_aspect('equal', adjustable='box')
      ax.axis('off')
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-0.8, self.n + 1.2)
      ax.set_autoscale_on(False)

    # 將 suptitle 放在 y=0.96，搭配 top=0.86 可以完美錯開子圖標題
    self.fig.suptitle(
        'Catalan Bijection Mapping'
        f' | Page #{self.current_idx+1}/{self.total_count}',
        fontsize=12,
        fontweight='bold',
        y=0.96,
    )

    self.fig.canvas.draw_idle()

