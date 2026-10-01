import logging
import warnings

# 1. 基礎警報封鎖
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("matplotlib").setLevel(logging.ERROR)

import matplotlib.pyplot as plt
import numpy as np




class DualPolyDFS:

  def __init__(self, n, page_index=0, step_index=None):
    # 防止 Streamlit 記憶體累積
    plt.close("all")

    self.n = max(1, int(n))
    self.n_v = self.n + 2
    self.paths = self.generate_ordered_paths(self.n)
    self.total_count = len(self.paths)
    self.current_idx = page_index % self.total_count
    self.verts = self._generate_verts()

    # 預先計算當前二元樹與雙重元素以確定總步驟數 max_steps
    path = self.paths[self.current_idx]
    tree = self.path_to_tree(path)
    tree_dy = 1.2

    nodes_ax3, edges_ax3 = [], []
    self._collect_dual_elements(tree, 1, self.n_v, nodes_ax3, edges_ax3)

    nodes_ax4, edges_ax4 = [], []
    self._collect_tree_elements(
        tree,
        start_x=0,
        y=0,
        dy=tree_dy,
        nodes_list=nodes_ax4,
        edges_list=edges_ax4,
    )

    # 精確步驟數：0 為初始狀態，1 ~ max_steps 依序繪製邊與節點
    self.max_steps = max(len(edges_ax3), len(edges_ax4))

    if step_index is None:
      self.step_index = 0
    else:
      self.step_index = max(0, min(step_index, self.max_steps))

    # 建立 4 宮格畫布
    self.fig = plt.figure(figsize=(16, 7.5))
    self.fig.patch.set_facecolor("white")

    gs = self.fig.add_gridspec(2, 2, hspace=0.35, wspace=0.25)
    self.ax1 = self.fig.add_subplot(gs[0, 0:1])
    self.ax2 = self.fig.add_subplot(gs[0, 1:2])
    self.ax3 = self.fig.add_subplot(gs[1, 0:1])
    self.ax4 = self.fig.add_subplot(gs[1, 1:2])

    self.render()

  def _generate_verts(self):
    v = {}
    angle_step = 2 * np.pi / self.n_v
    offset = np.pi / 2 - angle_step / 2
    for i in range(1, self.n_v + 1):
      angle = offset - (i - 1) * angle_step
      v[i] = np.array([np.cos(angle), np.sin(angle)])
    return v

  def generate_ordered_paths(self, n):
    paths = []

    def backtrack(x, y, path):
      if len(path) == 2 * n:
        paths.append(path)
        return
      if x < n:
        backtrack(x + 1, y, path + "R")
      if y < x:
        backtrack(x, y + 1, path + "U")

    backtrack(0, 0, "")
    return sorted(paths)

  def path_to_tree(self, path):
    if not path:
      return None
    balance, split_idx = 0, -1
    for i, char in enumerate(path):
      balance += 1 if char == "R" else -1
      if balance == 0:
        split_idx = i
        break
    return {
        "left": self.path_to_tree(path[1:split_idx]),
        "right": self.path_to_tree(path[split_idx + 1 :]),
        "left_nodes": split_idx // 2,
        "right_nodes": (len(path) - split_idx - 1) // 2,
    }

  def _collect_dual_elements(self, node, L, R, nodes_list, edges_list):
    if not node:
      return

    def collect_recursive(curr_node, curr_L, curr_R):
      if not curr_node:
        return
      k = curr_L + curr_node["right_nodes"] + 1
      centroid = (self.verts[curr_L] + self.verts[k] + self.verts[curr_R]) / 3
      nodes_list.append(
          {"pos": centroid, "color": "#ca0fec", "size": 35, "marker": "o"}
      )

      if curr_node["left"]:
        child = curr_node["left"]
        nk = k + child["right_nodes"] + 1
        nc = (self.verts[k] + self.verts[nk] + self.verts[curr_R]) / 3
        edges_list.append({"p1": centroid, "p2": nc, "color": "#0015ff"})
        collect_recursive(curr_node["left"], k, curr_R)
      else:
        edge_mid = (self.verts[k] + self.verts[curr_R]) / 2
        edges_list.append(
            {"p1": centroid, "p2": edge_mid, "color": "#32CD32"}
        )
        nodes_list.append(
            {"pos": edge_mid, "color": "#32CD32", "size": 25, "marker": "s"}
        )

      if curr_node["right"]:
        child = curr_node["right"]
        nk = curr_L + child["right_nodes"] + 1
        nc = (self.verts[curr_L] + self.verts[nk] + self.verts[k]) / 3
        edges_list.append({"p1": centroid, "p2": nc, "color": "#e74c3c"})
        collect_recursive(curr_node["right"], curr_L, k)
      else:
        edge_mid = (self.verts[curr_L] + self.verts[k]) / 2
        edges_list.append(
            {"p1": centroid, "p2": edge_mid, "color": "#32CD32"}
        )
        nodes_list.append(
            {"pos": edge_mid, "color": "#32CD32", "size": 25, "marker": "s"}
        )

    collect_recursive(node, L, R)

  def _count_elements(self, node):
    if not node:
      return 1
    return (
        self._count_elements(node["left"])
        + 1
        + self._count_elements(node["right"])
    )

  def _collect_tree_elements(
      self, node, start_x, y, dy, nodes_list, edges_list
  ):
    if not node:
      return

    def collect_recursive(curr_node, curr_start_x, curr_y):
      if not curr_node:
        return

      left_count = self._count_elements(curr_node["left"])
      curr_x = curr_start_x + left_count

      nodes_list.append(
          {"pos": (curr_x, curr_y), "color": "#ca0fec", "size": 35, "marker": "o"}
      )

      if curr_node["left"]:
        left_left_count = self._count_elements(curr_node["left"]["left"])
        next_x_l = curr_start_x + left_left_count
        edges_list.append({
            "p1": (curr_x, curr_y),
            "p2": (next_x_l, curr_y - dy),
            "color": "#0015ff",
        })
        collect_recursive(curr_node["left"], curr_start_x, curr_y - dy)
      else:
        next_x_l = curr_start_x
        edges_list.append({
            "p1": (curr_x, curr_y),
            "p2": (next_x_l, curr_y - dy),
            "color": "#32CD32",
        })
        nodes_list.append({
            "pos": (next_x_l, curr_y - dy),
            "color": "#32CD32",
            "size": 25,
            "marker": "s",
        })

      if curr_node["right"]:
        right_start_x = curr_x + 1
        right_left_count = self._count_elements(curr_node["right"]["left"])
        next_x_r = right_start_x + right_left_count
        edges_list.append({
            "p1": (curr_x, curr_y),
            "p2": (next_x_r, curr_y - dy),
            "color": "#e74c3c",
        })
        collect_recursive(curr_node["right"], right_start_x, curr_y - dy)
      else:
        next_x_r = curr_x + 1
        edges_list.append({
            "p1": (curr_x, curr_y),
            "p2": (next_x_r, curr_y - dy),
            "color": "#32CD32",
        })
        nodes_list.append({
            "pos": (next_x_r, curr_y - dy),
            "color": "#32CD32",
            "size": 25,
            "marker": "s",
        })

    collect_recursive(node, start_x, y)

  def draw_standard_tree_static(self, ax, node, start_x, y, dy=1.2):
    if not node:
      return

    left_count = self._count_elements(node["left"])
    curr_x = start_x + left_count

    if node["left"]:
      left_left_count = self._count_elements(node["left"]["left"])
      next_x_l = start_x + left_left_count
      ax.plot([curr_x, next_x_l], [y, y - dy], color="black", lw=1.5)
      self.draw_standard_tree_static(ax, node["left"], start_x, y - dy, dy)

    if node["right"]:
      right_start_x = curr_x + 1
      right_left_count = self._count_elements(node["right"]["left"])
      next_x_r = right_start_x + right_left_count
      ax.plot([curr_x, next_x_r], [y, y - dy], color="black", lw=1.5)
      self.draw_standard_tree_static(ax, node["right"], right_start_x, y - dy, dy)

    if y == 0:
      ax.scatter(
          curr_x,
          y,
          facecolors="none",
          edgecolors="black",
          s=160,
          marker="o",
          lw=1.5,
          zorder=6,
      )
      ax.scatter(curr_x, y, color="black", s=40, marker="o", zorder=6)
    else:
      ax.scatter(curr_x, y, color="black", s=60, zorder=5)

  def draw_polygon_base(self, ax):
    for i in range(1, self.n_v + 1):
      next_i = i + 1 if i < self.n_v else 1
      p1, p2 = self.verts[i], self.verts[next_i]
      is_base = (i == self.n_v and next_i == 1) or (
          i == 1 and next_i == self.n_v
      )
      c, lw = ("#FF00FF", 2.5) if is_base else ("black", 1.5)
      ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=lw)
      ax.text(
          p1[0] * 1.22,
          p1[1] * 1.22,
          str(i),
          ha="center",
          va="center",
          fontweight="bold",
          fontsize=11,
      )

  def draw_chords(self, ax, node, L, R, alpha=0.3):
    if not node:
      return
    k = L + node["right_nodes"] + 1
    for target in [L, R]:
      if abs(k - target) > 1 and not (
          min(k, target) == 1 and max(k, target) == self.n_v
      ):
        ax.plot(
            [self.verts[target][0], self.verts[k][0]],
            [self.verts[target][1], self.verts[k][1]],
            "k--",
            lw=1.2,
            alpha=alpha,
        )
    self.draw_chords(ax, node["right"], L, k, alpha)
    self.draw_chords(ax, node["left"], k, R, alpha)

  def render(self):
    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
      ax.clear()

    path = self.paths[self.current_idx]
    tree = self.path_to_tree(path)
    tree_dy = 1.2

    # --- 1. 左上角：剖分多邊形 ---
    self.draw_polygon_base(self.ax1)
    self.draw_chords(self.ax1, tree, 1, self.n_v)
    self.ax1.set_title(
        f"1. {self.n_v} edges Polygon Triangulation",
        fontweight="bold",
        pad=10,
    )

    # --- 2. 右上角：標準二元樹 ---
    self.draw_standard_tree_static(self.ax2, tree, start_x=0, y=0, dy=tree_dy)
    self.ax2.set_title(
        f"2. Standard Binary Tree (with {self.n} real nodes)",
        fontweight="bold",
        pad=10,
    )

    # --- 3. 左下角：雙重過程多邊形 ---
    self.draw_polygon_base(self.ax3)
    self.draw_chords(self.ax3, tree, 1, self.n_v, alpha=0.1)

    k_root = 1 + tree["right_nodes"] + 1
    root_centroid = (
        self.verts[1] + self.verts[k_root] + self.verts[self.n_v]
    ) / 3

    nodes_ax3, edges_ax3 = [], []
    self._collect_dual_elements(tree, 1, self.n_v, nodes_ax3, edges_ax3)

    active_pts_ax3 = {tuple(np.round(root_centroid, 4))}

    # 修正步驟判斷邏輯 (j < step_index)
    for j, e in enumerate(edges_ax3):
      if j < self.step_index:
        self.ax3.plot(
            [e["p1"][0], e["p2"][0]],
            [e["p1"][1], e["p2"][1]],
            color=e["color"],
            lw=2.5,
        )
        active_pts_ax3.add(tuple(np.round(e["p1"], 4)))
        active_pts_ax3.add(tuple(np.round(e["p2"], 4)))

    for n in nodes_ax3:
      pt = tuple(np.round(n["pos"], 4))
      if pt in active_pts_ax3:
        if np.allclose(n["pos"], root_centroid):
          self.ax3.scatter(
              n["pos"][0],
              n["pos"][1],
              facecolors="none",
              edgecolors=n["color"],
              s=140,
              marker="o",
              lw=1.8,
              zorder=6,
          )
          self.ax3.scatter(
              n["pos"][0], n["pos"][1], color=n["color"], s=35, marker="o", zorder=6
          )
        else:
          self.ax3.scatter(
              n["pos"][0],
              n["pos"][1],
              color=n["color"],
              s=n["size"],
              marker=n["marker"],
              zorder=5,
          )
      else:
        self.ax3.scatter(
            n["pos"][0],
            n["pos"][1],
            color="#e0e0e0",
            s=n["size"],
            marker=n["marker"],
            alpha=0.3,
            zorder=4,
        )

    # --- 4. 右下角：完整二元樹步驟繪製 ---
    root_x = self._count_elements(tree["left"]) if tree else 0
    root_tree_pt = (round(float(root_x), 4), 0.0)

    nodes_ax4, edges_ax4 = [], []
    self._collect_tree_elements(
        tree,
        start_x=0,
        y=0,
        dy=tree_dy,
        nodes_list=nodes_ax4,
        edges_list=edges_ax4,
    )

    active_pts_ax4 = {root_tree_pt}

    # 修正步驟判斷邏輯 (j < step_index)
    for j, e in enumerate(edges_ax4):
      if j < self.step_index:
        self.ax4.plot(
            [e["p1"][0], e["p2"][0]],
            [e["p1"][1], e["p2"][1]],
            color=e["color"],
            lw=2.5,
        )
        active_pts_ax4.add((round(e["p1"][0], 4), round(e["p1"][1], 4)))
        active_pts_ax4.add((round(e["p2"][0], 4), round(e["p2"][1], 4)))

    for n in nodes_ax4:
      pt = (round(n["pos"][0], 4), round(n["pos"][1], 4))
      if pt in active_pts_ax4:
        if pt == root_tree_pt:
          self.ax4.scatter(
              n["pos"][0],
              n["pos"][1],
              facecolors="none",
              edgecolors=n["color"],
              s=140,
              marker="o",
              lw=1.8,
              zorder=6,
          )
          self.ax4.scatter(
              n["pos"][0], n["pos"][1], color=n["color"], s=35, marker="o", zorder=6
          )
        else:
          self.ax4.scatter(
              n["pos"][0],
              n["pos"][1],
              color=n["color"],
              s=n["size"],
              marker=n["marker"],
              zorder=5,
          )
      else:
        self.ax4.scatter(
            n["pos"][0],
            n["pos"][1],
            color="#e0e0e0",
            s=n["size"],
            marker=n["marker"],
            alpha=0.25,
            zorder=4,
        )

    # 主標題
    self.fig.suptitle(
        "Catalan Bijection Mapping |"
        f"  Page #{self.current_idx + 1}/{self.total_count}",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    self.ax3.set_title(
        f"3. Draw Dual Process (Step: {self.step_index}/{self.max_steps})",
        fontweight="bold",
        pad=10,
    )
    self.ax4.set_title(
        f"4. Full Binary Tree (Step: {self.step_index}/{self.max_steps})",
        fontweight="bold",
        pad=10,
    )

    # 🛠️ 座標範圍精確設定 (防止裁切與拉伸)
    for ax in [self.ax1, self.ax3]:
      ax.set_aspect("equal", adjustable="datalim")
      ax.set_xlim(-1.5, 1.5)
      ax.set_ylim(-1.5, 1.5)
      ax.axis("off")

    tree_x_max = max(2 * self.n, 1)
    tree_y_min = -(self.n + 1) * tree_dy
    for ax in [self.ax2, self.ax4]:
      ax.set_xlim(-0.8, tree_x_max + 0.8)
      ax.set_ylim(tree_y_min - 0.5, 0.8)
      ax.axis("off")

    self.fig.tight_layout(rect=[0, 0, 1, 0.96])

