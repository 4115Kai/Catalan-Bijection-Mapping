import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


class PTC:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除舊圖表快取，避免記憶體洩漏

    self.n = int(n)
    self.words = self.generate_all_dyck_words(self.n)
    self.total_count = len(self.words)

    # 綁定外部傳入的頁碼與步驟
    self.current_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # Dyck Word 的長度為 2n
    self.step_index = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    # 圓點座標預算
    angles = np.linspace(0, 2 * np.pi, 2 * self.n, endpoint=False) + np.pi / 2
    self.px, self.py = np.cos(angles), np.sin(angles)

    # 建立專用的繪圖畫布
    self.fig = plt.figure(figsize=(21, 7.75))

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

  def render(self):
    self.fig.clear()  # 完全重置畫布

    word = self.words[self.current_idx]
    n = self.n
    colors = [mcolors.hsv_to_rgb((i / n, 0.7, 0.9)) for i in range(n)]

    segment_colors = [None] * (2 * self.n)
    pair_info = {}
    stack_temp = []
    c_id = 0
    for i, char in enumerate(word):
      if char == '(':
        stack_temp.append((i, c_id))
        segment_colors[i] = colors[c_id]
        c_id += 1
      else:
        start_i, color_idx = stack_temp.pop()
        segment_colors[i] = colors[color_idx]
        pair_info[i] = start_i

    path_coords = [(0, 0)]
    curr_y = 0
    for i, char in enumerate(word):
      curr_y += 1 if char == '(' else -1
      path_coords.append((i + 1, curr_y))

    # =========================================================================
    # 【上面一排：靜態全黑展示】
    # =========================================================================

    # --- 1. [左上] 靜態完整 Dyck Path (全黑) ---
    ax_static_path = self.fig.add_subplot(2, 2, 1)
    ax_static_path.set_xlim(-0.5, 2 * n + 0.5)
    ax_static_path.set_ylim(-0.5, n + 0.5)
    ax_static_path.grid(True, alpha=0.1)
    ax_static_path.set_title('1. Dyck Path', fontsize=11, fontweight='bold')

    for i in range(2 * n):
      p1, p2 = path_coords[i], path_coords[i + 1]
      ax_static_path.plot(
          [p1[0], p2[0]], [p1[1], p2[1]], color='black', lw=3, zorder=3
      )

      # 靜態虛線對應 (灰色)
      if word[i] == ')' and i in pair_info:
        s_idx = pair_info[i]
        mx1, my1 = (
            path_coords[s_idx][0] + path_coords[s_idx + 1][0]
        ) / 2, (path_coords[s_idx][1] + path_coords[s_idx + 1][1]) / 2
        mx2, my2 = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax_static_path.plot(
            [mx1, mx2],
            [my1, my2],
            color='gray',
            ls='--',
            lw=1.5,
            alpha=0.7,
            zorder=2,
        )

    # --- 2. [右上] 靜態完整圓中弦 (全黑) ---
    ax_static_circle = self.fig.add_subplot(2, 2, 2)
    ax_static_circle.set_xlim(-1.3, 1.3)
    ax_static_circle.set_ylim(-1.3, 1.3)
    ax_static_circle.set_aspect('equal')
    ax_static_circle.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )
    ax_static_circle.set_title(
        '2. Non-Intersecting Chords', fontsize=11, fontweight='bold'
    )

    # 繪製完整的黑弦
    static_stack = []
    for i in range(2 * n):
      char = word[i]
      if char == '(':
        static_stack.append(i)
      else:
        s_node = static_stack.pop()
        ax_static_circle.plot(
            [self.px[s_node], self.px[i]],
            [self.py[s_node], self.py[i]],
            color='black',
            lw=3,
            zorder=2,
        )

    # 繪製端點
    for i in range(2 * n):
      ax_static_circle.scatter(
          self.px[i], self.py[i], color='black', s=40, zorder=3
      )
      ax_static_circle.text(
          self.px[i] * 1.25,
          self.py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          weight='normal',
      )
    ax_static_circle.axis('off')

    # =========================================================================
    # 【下面一排：動態彩色對應】
    # =========================================================================

    # --- 3. [左下] 動態 Dyck Path 繪製 ---
    ax_path = self.fig.add_subplot(2, 2, 3)
    ax_path.set_xlim(-0.5, 2 * n + 0.5)
    ax_path.set_ylim(-0.5, n + 0.5)
    ax_path.grid(True, alpha=0.1)

    is_finished = self.step_index == 2 * n

    for i in range(self.step_index):
      p1, p2 = path_coords[i], path_coords[i + 1]
      col = segment_colors[i]
      ax_path.plot([p1[0], p2[0]], [p1[1], p2[1]], color=col, lw=4, zorder=3)

      if not is_finished:
        if i == self.step_index - 1 and word[i] == ')' and i in pair_info:
          s_idx = pair_info[i]
          mx1, my1 = (
              path_coords[s_idx][0] + path_coords[s_idx + 1][0]
          ) / 2, (path_coords[s_idx][1] + path_coords[s_idx + 1][1]) / 2
          mx2, my2 = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
          ax_path.plot(
              [mx1, mx2],
              [my1, my2],
              color=col,
              ls='--',
              lw=2.5,
              alpha=1.0,
              zorder=4,
          )
      else:
        if word[i] == ')' and i in pair_info:
          s_idx = pair_info[i]
          mx1, my1 = (
              path_coords[s_idx][0] + path_coords[s_idx + 1][0]
          ) / 2, (path_coords[s_idx][1] + path_coords[s_idx + 1][1]) / 2
          mx2, my2 = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
          ax_path.plot(
              [mx1, mx2],
              [my1, my2],
              color=col,
              ls='--',
              lw=1.5,
              alpha=0.6,
              zorder=2,
          )

    if self.step_index > 0:
      ax_path.plot(
          path_coords[self.step_index][0],
          path_coords[self.step_index][1],
          'ro',
          ms=8,
          zorder=5,
      )

    ax_path.set_title(
        f"3. Colored Dyck Path :{word[:self.step_index].ljust(2*n, '_')}",
        fontsize=11,
        loc='left',
    )

    # --- 4. [右下] 動態 圓中弦 繪製 ---
    ax_circle = self.fig.add_subplot(2, 2, 4)
    ax_circle.set_xlim(-1.3, 1.3)
    ax_circle.set_ylim(-1.3, 1.3)
    ax_circle.set_aspect('equal')
    ax_circle.add_artist(
        plt.Circle(
            (0, 0), 1, facecolor='#f7f9f9', edgecolor='#555555', zorder=0
        )
    )

    stack = []
    node_colors = ['#bdc3c7'] * (2 * n)
    active_c_id = 0
    for i in range(self.step_index):
      char = word[i]
      if char == '(':
        stack.append((i, active_c_id))
        ax_circle.scatter(
            self.px[i],
            self.py[i],
            color='white',
            edgecolors=colors[active_c_id],
            s=120,
            lw=2,
            zorder=4,
        )
        active_c_id += 1
      else:
        s_node, c_idx = stack.pop()
        node_colors[s_node] = node_colors[i] = colors[c_idx]
        ax_circle.plot(
            [self.px[s_node], self.px[i]],
            [self.py[s_node], self.py[i]],
            color=colors[c_idx],
            lw=4,
            zorder=2,
        )

    for i in range(2 * n):
      active = i < self.step_index
      ax_circle.scatter(
          self.px[i],
          self.py[i],
          color=node_colors[i],
          s=80 if active else 30,
          zorder=3,
      )
      ax_circle.text(
          self.px[i] * 1.25,
          self.py[i] * 1.25,
          str(i + 1),
          ha='center',
          va='center',
          weight='bold' if active else 'normal',
      )

    ax_circle.axis('off')
    ax_circle.set_title('4. Colored Non-Intersecting Chord', fontsize=11)

    # --- 總標題 ---
    self.fig.suptitle(
        'Catalan Bijection Mapping  | Page #'
        f' {self.current_idx+1}/{self.total_count}',
        fontsize=15,
        fontweight='bold',
    )

    # 調整畫布邊界，填滿移除按鈕後的下方空間 (bottom 設為 0.08)
    self.fig.subplots_adjust(
        left=0.06, right=0.94, top=0.88, bottom=0.08, hspace=0.3, wspace=0.15
    )


