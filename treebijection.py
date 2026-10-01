import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


class TreeNode:

  def __init__(self, name):
    self.name = name
    self.left = None
    self.right = None


class PTT:

  def __init__(self, n, page_index=0, step_index=None):
    plt.close('all')  # 清除 Matplotlib 快取，防止 Streamlit 記憶體洩漏

    self.n = int(n)
    self.paths = self._generate_dyck_paths(self.n)
    self.total_count = len(self.paths)

    # 接收 Streamlit 傳入的頁碼與步驟索引
    self.current_path_idx = max(0, min(page_index, self.total_count - 1))
    self.max_steps = 2 * self.n  # Dyck Path 長度為 2n
    self.frame_idx = (
        self.max_steps
        if step_index is None
        else max(0, min(step_index, self.max_steps))
    )

    self.is_running = False

    # 顏色規範
    self.color_left = '#0015ff'  # 藍色 (R) -> '('
    self.color_right = '#e74c3c'  # 紅色 (U) -> ')'
    self.node_real = '#34495e'
    self.node_null = '#ffffff'

    # 建立畫布
    self.fig = plt.figure(figsize=(18, 8.5))

    # 重新分配網格比例，並移除底部控制按鈕區空間
    gs = self.fig.add_gridspec(
        2, 5, hspace=0.35, wspace=0.25, bottom=0.06, top=0.88
    )

    self.ax_full_path = self.fig.add_subplot(gs[0, 0:2])
    self.ax_std_tree = self.fig.add_subplot(gs[0, 2:5])
    self.ax_ani_path = self.fig.add_subplot(gs[1, 0:2])
    self.ax_ani_tree = self.fig.add_subplot(gs[1, 2:5])

    self._setup_current_mapping()

  def _setup_current_mapping(self):
    path = self.paths[self.current_path_idx]
    tree = self._transform_dfs(path)
    self.G, self.pos, self.edge_order = self._precompute_tree_edges(tree)
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
    return paths

  def _transform_dfs(self, path):
    if not path:
      return None
    balance, match_idx = 0, -1
    for i, char in enumerate(path):
      balance += 1 if char == 'R' else -1
      if balance == 0:
        match_idx = i
        break
    root = TreeNode('Node')
    root.left = self._transform_dfs(path[1:match_idx])
    root.right = self._transform_dfs(path[match_idx + 1 :])
    return root

  def _precompute_tree_edges(self, tree_root):
    G = nx.DiGraph()
    pos = {}
    edge_order = []

    def count_elements(node):
      if not node:
        return 1
      return count_elements(node.left) + 1 + count_elements(node.right)

    def build(node, start_x=0, y=0, parent_nid=None, side=None):
      if not node:
        return None

      nid = id(node)
      G.add_node(nid, real=True)

      left_count = count_elements(node.left)
      curr_x = start_x + left_count
      pos[nid] = (curr_x, y)

      if node.left:
        cid_left = id(node.left)
        edge_order.append((nid, cid_left, True, 'left'))
        build(node.left, start_x, y - 1.2, nid, 'left')
      else:
        cid_left = f'null_{nid}_left'
        G.add_node(cid_left, real=False)
        pos[cid_left] = (start_x, y - 1.2)
        edge_order.append((nid, cid_left, False, 'left'))

      if node.right:
        cid_right = id(node.right)
        right_start_x = curr_x + 1
        edge_order.append((nid, cid_right, True, 'right'))
        build(node.right, right_start_x, y - 1.2, nid, 'right')
      else:
        cid_right = f'null_{nid}_right'
        G.add_node(cid_right, real=False)
        pos[cid_right] = (curr_x + 1, y - 1.2)
        edge_order.append((nid, cid_right, False, 'right'))

      return nid

    if tree_root:
      self.root_nid = id(tree_root)
      build(tree_root, start_x=0, y=0)
    else:
      self.root_nid = None

    return G, pos, edge_order

  def _update_display(self):
    for ax in [
        self.ax_full_path,
        self.ax_ani_path,
        self.ax_ani_tree,
        self.ax_std_tree,
    ]:
      ax.clear()

    path = self.paths[self.current_path_idx]
    display_path = path.replace('R', '(').replace('U', ')')

    self._draw_path_step(
        self.ax_full_path, path, len(path), show_nums=False, is_static=True
    )
    self.ax_full_path.set_title(
        f'1. Dyck Path : {display_path}',
        color='black',
        fontsize=11,
        fontweight='bold',
    )

    self._draw_path_step(
        self.ax_ani_path, path, self.frame_idx, show_nums=True, is_static=False
    )
    current_paren_progress = display_path[: self.frame_idx]
    self.ax_ani_path.set_title(
        f'2. Dyck Path (Step: {self.frame_idx})\n{current_paren_progress}',
        fontsize=11,
        fontweight='bold',
        color='black',
    )

    self._draw_tree_step(
        self.ax_std_tree, len(self.edge_order), is_mode='STANDARD_RESULT'
    )
    self.ax_std_tree.set_title(
        f'3. Standard Binary Tree ({self.n} real nodes)',
        fontsize=11,
        fontweight='bold',
    )

    self._draw_tree_step(self.ax_ani_tree, self.frame_idx, is_mode='ANIMATION')
    self.ax_ani_tree.set_title(
        f'4. Full Binary Tree (Step: {self.frame_idx})',
        fontsize=11,
        fontweight='bold',
    )

    status = 'PAUSED' if not self.is_running else 'PLAYING'
    catalan_num = (
        math.comb(2 * self.n, self.n) // (self.n + 1) if self.n >= 0 else 0
    )
    self.fig.suptitle(
        f'Catalan Bijection Mapping | Page'
        f' #{self.current_path_idx+1}/{catalan_num} ',
        fontsize=12,
        fontweight='bold',
        y=0.98,
    )
    self.fig.canvas.draw_idle()

  def _draw_path_step(self, ax, path, frame, show_nums=True, is_static=False):
    # 繪製貼合山脈外型的格線
    for h in range(self.n + 1):
      ax.plot([0, 2 * self.n], [h, h], color='gray', alpha=0.12, linestyle=':')
    for i in range(2 * self.n + 1):
      ax.plot([i, i], [0, self.n], color='gray', alpha=0.12, linestyle=':')
    # 繪製地平線基準線
    ax.plot([0, 2 * self.n], [0, 0], 'k-', alpha=0.4, lw=1.2)

    x, y = 0, 0
    step_midpoints = []

    for i in range(frame):
      move = path[i]
      old_x, old_y = x, y

      # R 向右上走，U 向右下走
      if move == 'R':
        x += 1
        y += 1
      else:
        x += 1
        y -= 1

      mid_x, mid_y = (old_x + x) / 2, (old_y + y) / 2
      step_midpoints.append((mid_x, mid_y))

      # 當走到下坡 U 時，拉出水平虛線連接左側對應的上坡 R 節點（水平對射關係）
      if not is_static and move == 'U':
        potential_stack = []
        for j in range(i):
          m = path[j]
          if m == 'R':
            potential_stack.append(j)
          else:
            potential_stack.pop()

        if potential_stack:
          matched_r_idx = potential_stack[-1]
          rx, ry = step_midpoints[matched_r_idx]
          ux, uy = mid_x, mid_y

          ax.annotate(
              '',
              xy=(ux, uy),
              xycoords='data',
              xytext=(rx, ry),
              textcoords='data',
              arrowprops=dict(
                  arrowstyle='-',
                  color='#000000',
                  linestyle='--',
                  alpha=0.4,
                  connectionstyle='arc3,rad=0.0',
                  lw=1.2,
              ),
              zorder=2,
          )

      curr_c = (
          '#000000'
          if is_static
          else (self.color_left if move == 'R' else self.color_right)
      )
      ax.plot(
          [old_x, x],
          [old_y, y],
          'o-',
          color=curr_c,
          lw=2.5 if is_static else 2.5,
          ms=3 if is_static else 6,
          zorder=3,
      )

      if show_nums and not is_static:
        ax.text(
            mid_x,
            mid_y + 0.5,
            str(i + 1),
            color='black',
            fontsize=7,
            weight='bold',
            ha='center',
            va='bottom',
            zorder=2,
        )

    # 精準控制邊界，消除空白，放大山脈主體
    ax.set_xlim(-0.5, 2 * self.n + 0.5)
    ax.set_ylim(-0.5, self.n + 0.5)
    ax.set_aspect('equal')  # 確保 45 度角不變形
    ax.axis('off')

  def _draw_tree_step(self, ax, frame, is_mode='ANIMATION'):
    ax.axis('off')
    for spine in ax.spines.values():
      spine.set_visible(False)

    # 背景淡淡的點（只有動態圖需要背景淡化效果，靜態圖不要）
    if is_mode != 'STANDARD_RESULT':
      all_nodes = list(self.G.nodes())
      if all_nodes:
        bg_alpha = 0.15
        nc_bg = [self.node_null for _ in all_nodes]
        ns_bg = [20 for _ in all_nodes]
        nx.draw_networkx_nodes(
            self.G,
            self.pos,
            nodelist=all_nodes,
            ax=ax,
            node_color=nc_bg,
            node_size=ns_bg,
            alpha=bg_alpha,
        )

    current_edges = self.edge_order[:frame]
    for i, (u, v, is_real, direction) in enumerate(current_edges):
      if is_mode == 'STANDARD_RESULT':
        if not is_real:
          continue
        color, style, width, alpha, arrows = (
            '#000000',
            'solid',
            1.0,
            1.0,
            False,
        )
      else:
        color = self.color_left if direction == 'left' else self.color_right
        style = 'solid' if is_real else (0, (4, 2))
        width = 1.5 if is_real else 1.8
        alpha = 1.0
        arrows = False

      nx.draw_networkx_edges(
          self.G,
          self.pos,
          edgelist=[(u, v)],
          ax=ax,
          edge_color=color,
          style=style,
          width=width,
          arrows=arrows,
          alpha=alpha,
      )

      if is_mode == 'ANIMATION':
        ux, uy = self.pos[u]
        vx, vy = self.pos[v]
        mx, my = (ux + vx) / 2, (uy + vy) / 2
        ax.text(
            mx,
            my + 0.18,
            str(i + 1),
            color='black',
            fontsize=7,
            weight='bold',
            ha='center',
            va='center',
            bbox=dict(
                facecolor='white',
                alpha=0.6,
                edgecolor='none',
                pad=1,
            ),
        )

    if is_mode == 'STANDARD_RESULT':
      active_nodes = [
          n for n, d in self.G.nodes(data=True) if d.get('real', False)
      ]
    else:
      active_nodes = {n for u, v, _, _ in current_edges for n in (u, v)}

    if active_nodes:
      nc_act = [
          self.node_real if self.G.nodes[n].get('real', True) else '#bdc3c7'
          for n in active_nodes
      ]

      # 調整點的大小，讓真實節點大一點 (20)，虛擬淡灰點小一點 (15) 形成視覺對比
      ns_act = [
          20 if self.G.nodes[n].get('real', True) else 15 for n in active_nodes
      ]

      nx.draw_networkx_nodes(
          self.G,
          self.pos,
          nodelist=list(active_nodes),
          ax=ax,
          node_color=nc_act,
          node_size=ns_act,
          alpha=1.0,
      )

    # 範圍修正邏輯
    x_values = [p[0] for p in self.pos.values()]
    y_values = [p[1] for p in self.pos.values()]
    if not x_values:
      return
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)

    pad_x = (x_max - x_min) * 0.05 if x_max != x_min else 1.0
    ax.set_xlim(x_min - pad_x - 0.5, x_max + pad_x + 0.5)
    ax.set_ylim(y_min - 0.8, y_max + 0.8)
    ax.set_aspect('equal')

