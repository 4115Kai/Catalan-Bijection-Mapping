import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


class PTS:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)
    self.n_v = self.n + 2  # (n+2)-邊形

    # 1. 生成所有 Dyck Path 及其雙射括號字串 (U -> '(', D -> ')')
    self.paths = self.generate_ordered_paths(self.n)
    self.words = [p.replace('U', '(').replace('D', ')') for p in self.paths]
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # Stack Push/Pop 共 2n 步
    self.anim_step = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_playing = False
    self.timer = None

    # 多邊形頂點座標生成
    self.verts = self._generate_verts()

    # 核心色彩調色盤 (球號與三角形一對一對應)
    self.colors = self.generate_rgb_palette(self.n)

    # 建立寬螢幕畫布
    self.fig = plt.figure(figsize=(16, 8.0))

    # 劃分 2x2 網格佈局 (調整 top=0.88 與 hspace=0.35 避免標題重疊)
    gs = self.fig.add_gridspec(
        2, 2, hspace=0.35, wspace=0.25, bottom=0.06, top=0.88
    )

    self.ax1 = self.fig.add_subplot(gs[0, 0])  # 1. 靜態多邊形 (純黑線條無數字)
    self.ax2 = self.fig.add_subplot(gs[0, 1])  # 2. 靜態堆疊排列 (右上)
    self.ax3 = self.fig.add_subplot(gs[1, 0])  # 3. 動態剖分過程 (左下)
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

  def _generate_verts(self):
    """生成正 (n+2)-邊形頂點座標"""
    v = {}
    angle_step = 2 * np.pi / self.n_v
    offset = np.pi / 2 - angle_step / 2
    for i in range(1, self.n_v + 1):
      angle = offset - (i - 1) * angle_step
      v[i] = np.array([np.cos(angle), np.sin(angle)])
    return v

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
    """將 Dyck Path 轉換為二元樹結構"""
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

  def is_internal(self, u, v):
    """判斷 (u, v) 是否為內部對角線（非多邊形外框邊）"""
    u_m, v_m = min(u, v), max(u, v)
    if u_m + 1 == v_m:
      return False
    if u_m == 1 and v_m == self.n_v:
      return False
    return True

  def build_triangles_and_pairs(
      self, node, L, R, offset=0, current_id=1, parent_id=None
  ):
    """精確映射 Dyck Path 步驟索引至多邊形三角形 (含 parent_id 追蹤)"""
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

  def parse_word_metadata(self, word):
    """解析堆疊步驟與球號顏色對應"""
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
    """計算最終的堆疊 Pop 輸出排列"""
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

  # --- 繪圖輔助函式 ---
  def draw_polygon_base(self, ax):
    """繪製多邊形外框與頂點標籤"""
    for i in range(1, self.n_v + 1):
      next_i = i + 1 if i < self.n_v else 1
      p1, p2 = self.verts[i], self.verts[next_i]
      is_base = (i == self.n_v and next_i == 1) or (
          i == 1 and next_i == self.n_v
      )
      c, lw = ('#ca0fec', 2.5) if is_base else ('black', 2.0)
      ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=lw, zorder=5)
      ax.text(
          p1[0] * 1.11,
          p1[1] * 1.11,
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

  def update_display(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    word = self.words[self.current_idx]
    tree = self.path_to_tree(path)
    status_str = 'PLAYING' if self.is_playing else 'PAUSED'
    font_prop = {'family': 'monospace', 'fontsize': 10, 'fontweight': 'bold'}
    step_ball_ids, step_colors = self.parse_word_metadata(word)
    triangles = self.build_triangles_and_pairs(tree, 1, self.n_v)

    # 1. Static Polygon Triangulation
    self.ax1.set_title(
        f'1. {self.n_v} edges Polygon Triangulation ',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_polygon_base(self.ax1)
    for tri in triangles:
      p1, p2, p3 = (
          self.verts[tri['verts'][0]],
          self.verts[tri['verts'][1]],
          self.verts[tri['verts'][2]],
      )
      poly = plt.Polygon(
          [p1, p2, p3], facecolor='none', edgecolor='black', lw=1.5, zorder=2
      )
      self.ax1.add_patch(poly)

    # 2. Static Stack Permutation
    self.ax2.set_title(
        '2. Stack Permutation ', fontsize=12, fontweight='bold', pad=8
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
          cx, 0.45, '↓', ha='center', va='center', color='#bdc3c7', fontsize=10
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

    # 3. Dynamic Polygon Triangulation Progress
    self.ax3.set_title(
        '3. Draw Triangulation Progress (Step:'
        f' {self.anim_step} / {self.max_steps})',
        fontsize=11,
        fontweight='bold',
        pad=8,
    )
    self.draw_polygon_base(self.ax3)

    for tri in triangles:
      p1, p2, p3 = (
          self.verts[tri['verts'][0]],
          self.verts[tri['verts'][1]],
          self.verts[tri['verts'][2]],
      )
      poly = plt.Polygon(
          [p1, p2, p3],
          facecolor='none',
          edgecolor='#e0e0e0',
          lw=1.2,
          ls='--',
          zorder=1,
      )
      self.ax3.add_patch(poly)

    curr_stack_state = []
    for i in range(self.anim_step):
      c = word[i]
      b_id = step_ball_ids[i]
      if c == '(':
        curr_stack_state.append(b_id)
      else:
        if curr_stack_state:
          curr_stack_state.pop()

    active_info_str = ''
    if self.anim_step > 0:
      curr_idx = self.anim_step - 1
      curr_char = word[curr_idx]

      for tri in triangles:
        p_step = tri['push_step']
        d_step = tri['pop_step']
        color = self.colors[tri['id'] - 1]

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

          if curr_char == '(':
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
              f"Now: Tri #{tri['id']} ($\Delta x_{{{L}}} x_{{{k}}} x_{{{R}}}$)"
              f'  |  {desc}'
          )

    self.ax3.text(
        0,
        -1.25,
        active_info_str,
        ha='center',
        va='center',
        color='#8e44ad',
        fontweight='bold',
        fontsize=9.5,
    )

    # 4. Dynamic Stack Permutation Progress
    self.ax4.set_title(
        '4. Dynamic Stack Permutation (Step:'
        f' {self.anim_step} / {self.max_steps})',
        fontsize=12,
        fontweight='bold',
        pad=8,
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
          plt.Circle((x_center, tube_y_center), ball_radius, color=c, zorder=3)
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

    # 5. 畫布視角對齊
    for ax in [self.ax1, self.ax3]:
      ax.set_aspect('equal')
      ax.axis('off')
      ax.set_xlim(-1.3, 1.3)
      ax.set_ylim(-1.35, 1.3)

    self.ax2.set_xlim(0, 1.0)
    self.ax2.set_ylim(0, 1.0)
    self.ax2.axis('off')

    max_pop_x = tube_left + pop_ball_radius + 0.1 + (self.n * pop_spacing)
    self.ax4.set_xlim(-0.1, max(tube_right + 0.4, max_pop_x, 3.5))
    self.ax4.set_ylim(-0.4, tube_y_center + 1.4)
    self.ax4.axis('off')

    self.fig.suptitle(
        'Catalan Bijection Mapping '
        f' |  Page #{self.current_idx+1}/{self.total_count}',
        fontsize=12,
        fontweight='bold',
        y=0.96,
    )
    self.fig.canvas.draw_idle()

