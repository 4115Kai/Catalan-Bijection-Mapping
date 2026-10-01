import math
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


class DTS:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體溢位

    self.n = int(n)

    # 1. 生成所有長度為 2n 的 Dyck Path (R: 上坡/Push, U: 下坡/Pop)
    self.paths = self._generate_dyck_paths(self.n)
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_path_idx = max(0, min(page_index, self.total_count - 1))
    self.max_frames = 2 * self.n
    self.frame_idx = (
        self.max_frames
        if step_index is None
        else max(0, min(step_index, self.max_frames))
    )

    # 為 1 ~ n 號球生成專屬獨立色彩調色盤
    self.ball_colors = self._generate_rgb_palette(self.n)

    # 建立 21 x 7.75 畫布
    self.fig = plt.figure(figsize=(20, 8.5))

    # 劃分 2x2 網格佈局 (左邊 Path，右邊 Stack)
    gs = self.fig.add_gridspec(
        2, 2, hspace=0.35, wspace=0.25, bottom=0.06, top=0.88
    )

    self.ax_full_path = self.fig.add_subplot(gs[0, 0])  # 1. 靜態完整 Dyck Path
    self.ax_std_stack = self.fig.add_subplot(
        gs[0, 1]
    )  # 2. 靜態最終 Stack 輸出排列
    self.ax_ani_path = self.fig.add_subplot(gs[1, 0])  # 3. 動態 Dyck Path 走查進度
    self.ax_ani_stack = self.fig.add_subplot(
        gs[1, 1]
    )  # 4. 動態 Stack 管道操作過程

    self._update_display()

  def _generate_dyck_paths(self, n):
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

  def _generate_rgb_palette(self, n):
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
    palette = []
    for i in range(n):
      hue = i / n
      rgb = mcolors.hsv_to_rgb((hue, 0.85, 0.90))
      palette.append(mcolors.to_hex(rgb))
    return palette

  def _parse_path_to_stack_events(self, path):
    """解析 Dyck Path (R/U)，對應出每一步操作的球號與顏色"""
    step_ball_ids = {}
    stack = []
    push_counter = 0

    for i, char in enumerate(path):
      if char == 'R':  # Push '('
        push_counter += 1
        ball_id = push_counter
        stack.append(ball_id)
        step_ball_ids[i] = ball_id
      else:  # Pop ')'
        if stack:
          popped_ball = stack.pop()
          step_ball_ids[i] = popped_ball
    return step_ball_ids

  def _get_final_permutation(self, path, step_ball_ids):
    """計算整個 Dyck Path 執行結束後的最終 Pop 輸出序號"""
    stack = []
    pop_order = []
    for i, char in enumerate(path):
      ball_id = step_ball_ids[i]
      if char == 'R':
        stack.append(ball_id)
      else:
        if stack:
          pop_order.append(stack.pop())
    return pop_order

  def _draw_path_step(
      self, ax, path, frame, step_ball_ids, show_nums=True, is_static=False
  ):
    # 繪製背景格線
    for h in range(self.n + 1):
      ax.plot([0, 2 * self.n], [h, h], color='gray', alpha=0.12, linestyle=':')
    for i in range(2 * self.n + 1):
      ax.plot([i, i], [0, self.n], color='gray', alpha=0.12, linestyle=':')
    ax.plot([0, 2 * self.n], [0, 0], 'k-', alpha=0.4, lw=1.2)

    x, y = 0, 0
    step_midpoints = []

    for i in range(frame):
      move = path[i]
      ball_id = step_ball_ids[i]
      step_color = self.ball_colors[ball_id - 1]

      old_x, old_y = x, y

      if move == 'R':  # Push
        x += 1
        y += 1
      else:  # Pop
        x += 1
        y -= 1

      mid_x, mid_y = (old_x + x) / 2, (old_y + y) / 2
      step_midpoints.append((mid_x, mid_y))

      # Pop 時畫出與對應 Push 節點對齊的水平對射虛線
      if not is_static and move == 'U':
        potential_stack = []
        for j in range(i):
          if path[j] == 'R':
            potential_stack.append(j)
          else:
            potential_stack.pop()

        if potential_stack:
          matched_r_idx = potential_stack[-1]
          rx, ry = step_midpoints[matched_r_idx]
          ax.annotate(
              '',
              xy=(mid_x, mid_y),
              xytext=(rx, ry),
              arrowprops=dict(
                  arrowstyle='-',
                  color=step_color,
                  linestyle='--',
                  alpha=0.6,
                  lw=1.5,
              ),
              zorder=2,
          )

      curr_c = '#000000' if is_static else step_color

      # 繪製折線段與結點
      ax.plot(
          [old_x, x],
          [old_y, y],
          'o-',
          color=curr_c,
          lw=2.5,
          ms=6 if not is_static else 3,
          zorder=3,
      )

      # 顯示步驟數字
      if show_nums and not is_static:
        is_up = path[i] == 'R'
        bg_color = curr_c if is_up else 'white'
        txt_color = 'white' if is_up else curr_c

        ax.text(
            mid_x,
            mid_y + 0.35,
            f'{ball_id}',
            color=txt_color,
            fontsize=8,
            weight='bold',
            ha='center',
            va='center',
            zorder=6,
            bbox=dict(
                boxstyle='circle,pad=0.25',
                facecolor=bg_color,
                edgecolor=curr_c,
                linewidth=1.2,
            ),
        )

    ax.set_xlim(-0.5, 2 * self.n + 0.5)
    ax.set_ylim(-0.5, self.n + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')

  def _draw_stack_dynamic(self, ax, path, frame, step_ball_ids):
    ax.set_aspect('equal')
    ax.axis('off')

    # 根據 n 動態計算球體大小與管道尺寸
    ball_radius = (
        max(0.08, 0.25 - (self.n - 4) * 0.012) if self.n > 4 else 0.25
    )
    x_spacing = ball_radius * 2.2
    tube_left = max(0.5, 0.2 + (self.n * 0.1))
    tube_length = self.n * x_spacing + 0.2
    tube_right = tube_left + tube_length

    # 垂直座標軸規劃
    tube_y_center = 2.0
    top_wall = tube_y_center + (ball_radius + 0.05)
    bottom_wall = tube_y_center - (ball_radius + 0.05)
    ball_font_size = (
        max(6, int(11 - (self.n - 4) * 0.35)) if self.n > 4 else 10
    )

    # 1. 繪製 Stack 管道外框
    ax.plot(
        [tube_right, tube_left, tube_left, tube_right],
        [top_wall, top_wall, bottom_wall, bottom_wall],
        color='#4f5d73',
        lw=3,
        zorder=2,
    )

    # 2. 頂部顯示即時括號字串
    current_view = path[:frame]
    display_brackets = current_view.replace('R', '(').replace('U', ')')
    bracket_str = f"{display_brackets + '_' * (2 * self.n - frame)}"
    ax.text(
        (tube_left + tube_right) / 2,
        top_wall + 0.4,
        bracket_str,
        fontdict={'family': 'monospace', 'fontsize': 11, 'fontweight': 'bold'},
        ha='center',
        va='bottom',
        color='#2c3e50',
    )

    # 3. 模擬當前 Stack 狀態與動態訊息
    curr_stack = []
    current_pop_order = []
    last_action = 'Ready'
    last_action_color = '#7f8c8d'

    for i in range(frame):
      char = path[i]
      ball_id = step_ball_ids[i]
      c = self.ball_colors[ball_id - 1]

      if char == 'R':  # Push
        curr_stack.append(ball_id)
        last_action = f'Step {i+1}: Push Ball {ball_id}'
        last_action_color = c
      else:  # Pop
        if curr_stack:
          popped = curr_stack.pop()
          current_pop_order.append(popped)
          last_action = f'Step {i+1}: Pop Ball {popped}'
          last_action_color = c

    # 4. 繪製 Stack 管道內部球體
    for level, ball_id in enumerate(curr_stack):
      c = self.ball_colors[ball_id - 1]
      x_center = tube_left + ball_radius + 0.08 + level * x_spacing
      ax.add_patch(
          plt.Circle((x_center, tube_y_center), ball_radius, color=c, zorder=3)
      )
      ax.text(
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

    # 5. 調整動態步驟文字的位置
    action_y_pos = bottom_wall - 0.45
    ax.text(
        (tube_left + tube_right) / 2,
        action_y_pos,
        last_action,
        ha='center',
        va='top',
        fontsize=11,
        fontweight='bold',
        color=last_action_color,
    )

    # 6. 繪製 POP 輸出隊列
    pop_base_y = action_y_pos - 0.65
    ax.text(
        tube_left - 0.1,
        pop_base_y,
        'POP order:',
        fontsize=10,
        fontweight='bold',
        color='#e67e22',
        va='center',
        ha='right',
    )

    pop_ball_radius = (
        0.20 if self.n <= 7 else max(0.09, 0.20 - (self.n - 7) * 0.008)
    )
    pop_spacing = pop_ball_radius * 2.3

    for i in range(self.n):
      ball_x = tube_left + pop_ball_radius + 0.05 + (i * pop_spacing)
      if i < len(current_pop_order):
        p_id = current_pop_order[i]
        c = self.ball_colors[p_id - 1]
        ax.add_patch(
            plt.Circle(
                (ball_x, pop_base_y),
                pop_ball_radius,
                fill=False,
                edgecolor=c,
                lw=2.5,
                zorder=3,
            )
        )
        ax.text(
            ball_x,
            pop_base_y,
            str(p_id),
            ha='center',
            va='center',
            color=c,
            fontweight='bold',
            fontsize=ball_font_size,
            zorder=4,
        )
      else:
        ax.add_patch(
            plt.Circle(
                (ball_x, pop_base_y),
                pop_ball_radius,
                fill=False,
                edgecolor='#e0e0e0',
                lw=1.5,
                zorder=3,
            )
        )

    # 設定視圖範圍
    max_pop_x = tube_left + pop_ball_radius + 0.1 + (self.n * pop_spacing)
    ax.set_xlim(-0.2, max(tube_right + 0.5, max_pop_x, 3.5))
    ax.set_ylim(pop_base_y - 0.5, top_wall + 0.8)

  def _update_display(self):
    for ax in [
        self.ax_full_path,
        self.ax_std_stack,
        self.ax_ani_path,
        self.ax_ani_stack,
    ]:
      ax.clear()

    path = self.paths[self.current_path_idx]
    display_path = path.replace('R', '(').replace('U', ')')
    step_ball_ids = self._parse_path_to_stack_events(path)

    # 1. 靜態完整 Dyck Path
    self._draw_path_step(
        self.ax_full_path,
        path,
        len(path),
        step_ball_ids,
        show_nums=False,
        is_static=True,
    )
    self.ax_full_path.set_title(
        f'1. Dyck Path : {display_path}', fontsize=11, fontweight='bold'
    )

    # 2. 靜態最終 Stack 序列結果
    self.ax_std_stack.set_title(
        '2. Stack Permutation', fontsize=11, fontweight='bold'
    )
    self.ax_std_stack.axis('off')
    self.ax_std_stack.text(
        0.05,
        0.65,
        'Input Order:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
    )
    self.ax_std_stack.text(
        0.05,
        0.25,
        'Permutation:',
        fontsize=11,
        fontweight='bold',
        color='#34495e',
        va='center',
    )

    x_base = 0.32
    spacing_x = 0.12 if self.n <= 4 else 0.60 / self.n
    ball_size = max(60, 280 - (self.n - 4) * 12) if self.n > 4 else 280

    for i in range(self.n):
      cx = x_base + i * spacing_x
      c = self.ball_colors[i]
      self.ax_std_stack.scatter(cx, 0.65, color=c, s=ball_size, zorder=3)
      self.ax_std_stack.text(
          cx,
          0.65,
          str(i + 1),
          ha='center',
          va='center',
          color='white',
          fontweight='bold',
          fontsize=9,
      )
      self.ax_std_stack.text(
          cx, 0.45, '↓', ha='center', va='center', color='#bdc3c7', fontsize=10
      )

    final_pop = self._get_final_permutation(path, step_ball_ids)
    for i, ball_id in enumerate(final_pop):
      cx = x_base + i * spacing_x
      c = self.ball_colors[ball_id - 1]
      self.ax_std_stack.scatter(
          cx,
          0.25,
          facecolors='white',
          edgecolors=c,
          lw=2.0,
          s=ball_size * 0.9,
          zorder=3,
      )
      self.ax_std_stack.text(
          cx,
          0.25,
          str(ball_id),
          ha='center',
          va='center',
          color=c,
          fontweight='bold',
          fontsize=9,
      )
    self.ax_std_stack.set_xlim(0, 1.0)
    self.ax_std_stack.set_ylim(0, 1.0)

    # 3. 動態 Dyck Path
    self._draw_path_step(
        self.ax_ani_path,
        path,
        self.frame_idx,
        step_ball_ids,
        show_nums=True,
        is_static=False,
    )
    self.ax_ani_path.set_title(
        '3. Dyck Path Progress (Step:'
        f' {self.frame_idx}/{self.max_frames})',
        fontsize=11,
        fontweight='bold',
    )

    # 4. 動態 Stack 操作
    self._draw_stack_dynamic(
        self.ax_ani_stack, path, self.frame_idx, step_ball_ids
    )
    self.ax_ani_stack.set_title(
        '4. Dynamic Stack Permutation (Step:'
        f' {self.frame_idx}/{self.max_frames})',
        fontsize=11,
        fontweight='bold',
    )

    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        'Catalan Bijection Mapping | Page'
        f' #{self.current_path_idx+1}/{catalan_num}',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )
    self.fig.canvas.draw_idle()

