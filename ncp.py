import logging
import warnings

# 1. 基礎警報封鎖
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("matplotlib").setLevel(logging.ERROR)

import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np




class NCP:

  def __init__(self, n, page_index=0, step_index=None):
    # 避免 Streamlit 記憶體累積
    plt.close("all")

    self.n = max(1, int(n))
    self.combinations = sorted(self.generate_all_combinations())
    self.total_count = len(self.combinations)

    self.current_page = page_index % self.total_count
    self.max_steps = 2 * self.n  # 動畫總步數為 2n

    if step_index is None:
      self.step_index = 0
    else:
      self.step_index = max(0, min(step_index, self.max_steps))

    # 計算順時針排列頂點座標 (1在正上方)
    angles = -np.linspace(0, 2 * np.pi, self.n, endpoint=False) + np.pi / 2
    self.pts = {
        i + 1: (0.85 * np.cos(a), 0.85 * np.sin(a)) for i, a in enumerate(angles)
    }

    # 建立 4 宮格畫布
    self.fig = plt.figure(figsize=(16, 7.5))
    self.fig.patch.set_facecolor("white")

    self.ax_dyck_static = self.fig.add_axes([0.08, 0.58, 0.38, 0.32])
    self.ax_part_static = self.fig.add_axes([0.54, 0.58, 0.38, 0.32])
    self.ax_dyck_dynamic = self.fig.add_axes([0.08, 0.10, 0.38, 0.32])
    self.ax_part_dynamic = self.fig.add_axes([0.54, 0.10, 0.38, 0.32])

    # 計算當前頁面資料
    seq = self.combinations[self.current_page]
    self.step_data = self.get_step_data(seq)

    # 群組顏色分配
    self.group_colors = {}
    num_final_groups = len(self.final_groups)
    for idx, fg in enumerate(self.final_groups):
      fixed_color = mcolors.hsv_to_rgb(
          [idx / max(1, num_final_groups), 0.65, 0.9]
      )
      self.group_colors[frozenset(fg["nodes"])] = fixed_color

    # 執行繪製
    self.render()

  def generate_all_combinations(self):
    res = []

    def backtrack(s, open_n, close_n):
      if open_n == close_n == self.n:
        res.append(s)
        return
      if open_n < self.n:
        backtrack(s + "(", open_n + 1, close_n)
      if close_n < open_n:
        backtrack(s + ")", open_n, close_n + 1)

    backtrack("", 0, 0)
    return res

  def get_step_data(self, seq):
    steps = []
    stack = []
    groups = []
    curr_y = 0

    path_pts = [(0, 0)]
    steps.append({
        "type": "start",
        "char": "",
        "current_step_idx": -1,
        "path": list(path_pts),
        "groups": [],
    })

    for i, char in enumerate(seq):
      if char == "(":
        node_idx = len([c for c in seq[: i + 1] if c == "("])
        stack.append({"node": node_idx, "x": i, "y": curr_y})
        curr_y += 1
        path_pts.append((i + 1, curr_y))
        steps.append({
            "type": "move",
            "char": "(",
            "current_step_idx": i,
            "path": list(path_pts),
            "groups": [dict(g) for g in groups],
        })
      else:
        curr_y -= 1
        path_pts.append((i + 1, curr_y))
        start_info = stack.pop()

        closing_node = len([c for c in seq[: i + 1] if c == "("])

        pair = {
            "nodes": {start_info["node"], closing_node},
            "range": (start_info["x"], i),
            "level": start_info["y"] + 0.5,
        }
        found = False
        for g in groups:
          if not pair["nodes"].isdisjoint(g["nodes"]):
            g["nodes"].update(pair["nodes"])
            g["pairs"].append(pair)
            found = True
            break
        if not found:
          groups.append({"nodes": pair["nodes"], "pairs": [pair]})
        steps.append({
            "type": "pair",
            "char": ")",
            "current_step_idx": i,
            "path": list(path_pts),
            "groups": [dict(g) for g in groups],
        })

    self.final_groups = groups
    return steps

  def init_ax(self):
    self.ax_dyck_static.clear()
    self.ax_part_static.clear()
    self.ax_dyck_dynamic.clear()
    self.ax_part_dynamic.clear()

    # Dyck Path 坐標軸防縮放鎖定
    for ax in [self.ax_dyck_static, self.ax_dyck_dynamic]:
      ax.grid(True, linestyle="-", alpha=0.15)
      ax.set_xlim(-0.5, 2 * self.n + 0.5)
      ax.set_ylim(-0.2, self.n + 0.5)
      ax.set_autoscale_on(False)

    # Noncrossing Partition 坐標軸防縮放鎖定
    for ax in [self.ax_part_static, self.ax_part_dynamic]:
      ax.set_aspect("equal", adjustable="box")
      ax.set_axis_off()
      ax.set_xlim(-0.95, 0.95)
      ax.set_ylim(-1.20, 1.10)
      ax.set_autoscale_on(False)

      for j in range(1, self.n + 1):
        p1, p2 = self.pts[j], self.pts[j % self.n + 1]
        ax.plot(
            [p1[0], p2[0]],
            [p1[1], p2[1]],
            "--",
            color="#bdc3c7",
            lw=1,
            alpha=0.4,
        )

        if j == 1:
          ax.text(
              p1[0],
              p1[1] + 0.10,
              str(j),
              ha="center",
              va="bottom",
              fontsize=11,
          )
        elif self.n % 2 == 0 and j == (self.n // 2) + 1:
          ax.text(
              p1[0], p1[1] - 0.10, str(j), ha="center", va="top", fontsize=11
          )
        else:
          ax.text(
              p1[0] * 1.25,
              p1[1] * 1.25,
              str(j),
              ha="center",
              va="center",
              fontsize=11,
          )

  def draw_static_plots(self):
    seq = self.combinations[self.current_page]

    curr_y = 0
    static_path = [(0, 0)]
    for char in seq:
      curr_y = curr_y + 1 if char == "(" else curr_y - 1
      static_path.append((len(static_path), curr_y))
    self.full_static_path = static_path
    sx, sy = zip(*static_path)

    self.ax_dyck_static.plot(sx, sy, color="#2c3e50", lw=3, zorder=2)
    self.ax_dyck_static.scatter(sx, sy, color="#2c3e50", s=20, zorder=3)
    self.ax_dyck_static.set_title(
        f"1. Dyck Path {seq}", fontsize=12, fontweight="bold", pad=10
    )

    for node in range(1, self.n + 1):
      pt = self.pts[node]
      self.ax_part_static.add_patch(
          patches.Circle(
              pt,
              radius=0.04,
              facecolor="#7f8c8d",
              edgecolor="#7f8c8d",
              zorder=4,
          )
      )

    for fg in self.final_groups:
      sorted_nodes = sorted(list(fg["nodes"]))
      if len(fg["nodes"]) == 2:
        p1, p2 = self.pts[sorted_nodes[0]], self.pts[sorted_nodes[1]]
        self.ax_part_static.plot(
            [p1[0], p2[0]], [p1[1], p2[1]], color="#7f8c8d", lw=2, zorder=2
        )
      elif len(fg["nodes"]) > 2:
        for idx in range(len(sorted_nodes)):
          p1 = self.pts[sorted_nodes[idx]]
          p2 = self.pts[sorted_nodes[(idx + 1) % len(sorted_nodes)]]
          self.ax_part_static.plot(
              [p1[0], p2[0]], [p1[1], p2[1]], color="#7f8c8d", lw=2, zorder=2
          )

    self.ax_part_static.set_title(
        f"2. Non-crossing Partition ({self.n} vertices)",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )

  def render(self):
    frame = self.step_index
    self.init_ax()
    self.draw_static_plots()

    fx, fy = zip(*self.full_static_path)
    self.ax_dyck_dynamic.plot(
        fx, fy, color="#bdc3c7", lw=4, alpha=0.25, zorder=1
    )

    max_step_drawn = frame
    has_polygon_shaded = set()

    seq = self.combinations[self.current_page]

    up_step_info = {}
    left_idx = 0
    for i, char in enumerate(seq):
      if char == "(":
        left_idx += 1
        matched_color = "#95a5a6"
        matched_fg = None
        for fg_set, col in self.group_colors.items():
          if left_idx in fg_set:
            matched_color = col
            matched_fg = fg_set
            break
        up_step_info[left_idx] = {
            "start_x": i,
            "color": matched_color,
            "fg_set": matched_fg,
        }

    triggered_fg_sets = set()

    for fg_set, color in self.group_colors.items():
      group_pairs = []
      for fg in self.final_groups:
        if frozenset(fg["nodes"]) == fg_set:
          group_pairs = fg["pairs"]
          break

      for p in group_pairs:
        s, e = p["range"]
        label_num = len([c for c in seq[: s + 1] if c == "("])

        if s + 1 <= max_step_drawn:
          self.ax_dyck_dynamic.plot(
              [s, s + 1], [fy[s], fy[s + 1]], color=color, lw=4, zorder=3
          )

          if e + 1 > max_step_drawn:
            up_mx = (s + (s + 1)) / 2
            up_my = (fy[s] + fy[s + 1]) / 2
            self.ax_dyck_dynamic.text(
                up_mx - 0.25,
                up_my + 0.35,
                str(label_num),
                color=color,
                fontsize=13,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=20,
            )

        if e + 1 <= max_step_drawn:
          self.ax_dyck_dynamic.plot(
              [e, e + 1], [fy[e], fy[e + 1]], color=color, lw=4, zorder=3
          )
          self.ax_dyck_dynamic.hlines(
              p["level"],
              s + 0.5,
              e + 0.5,
              colors=color,
              linestyles="--",
              alpha=0.5,
              lw=1.5,
          )
          self.ax_dyck_dynamic.plot(
              [s + 0.5, e + 0.5],
              [p["level"], p["level"]],
              color="#e74c3c",
              linestyle=":",
              lw=1.2,
              alpha=0.6,
              zorder=4,
          )

          down_mx = (e + (e + 1)) / 2
          down_my = (fy[e] + fy[e + 1]) / 2
          self.ax_dyck_dynamic.text(
              down_mx + 0.25,
              down_my + 0.35,
              str(label_num),
              color=color,
              fontsize=13,
              fontweight="bold",
              ha="center",
              va="center",
              zorder=20,
          )

          triggered_fg_sets.add(fg_set)

    for fg_set in triggered_fg_sets:
      color = self.group_colors[fg_set]
      sorted_nodes = sorted(list(fg_set))
      if len(fg_set) >= 2:
        group_pts = np.array([self.pts[node] for node in sorted_nodes])
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
          self.ax_part_dynamic.add_patch(
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
          self.ax_part_dynamic.add_patch(
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
          node_color = "#95a5a6"
          for fg_set, col in self.group_colors.items():
            if node in fg_set:
              node_color = col
              break
          pt = self.pts[node]
          self.ax_part_dynamic.add_patch(
              patches.Circle(
                  pt,
                  radius=0.06,
                  facecolor=node_color,
                  alpha=0.35,
                  edgecolor=node_color,
                  linewidth=1.5,
                  zorder=4,
              )
          )

    px, py = zip(*self.full_static_path[: max_step_drawn + 1])
    self.ax_dyck_dynamic.scatter(px, py, color="#2c3e50", s=25, zorder=5)

    display_step = 0 if frame == 0 else frame

    self.fig.suptitle(
        "Catalan Bijection Mapping |"
        f"  Page #{self.current_page + 1}/{self.total_count}",
        fontsize=14,
        fontweight="bold",
        y=0.97,
    )
    curr_brackets = seq[:frame] + "_" * (self.max_steps - frame)
    self.ax_dyck_dynamic.set_title(
        f"3. Dynamic Dyck Path {curr_brackets} (Step: {display_step} / {self.max_steps})",
        loc="center",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )
    self.ax_part_dynamic.set_title(
        f"4. Dynamic Non-crossing Partition (Step: {display_step} / {self.max_steps})",
        loc="center",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )


# 相容別名設定
Noncrossing_Partition = NCP