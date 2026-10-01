import io
import time
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Catalan Bijection Visualizer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 1. Catalan 結構列表與 21 組雙射模組對照表 (PAIRS_MAP)
# ==============================================================================
# 格式：(結構 A, 結構 B): ("模組檔名", "類別名稱", "步數類型(n或2n)")
# 💡 提示：輸入組合不分前後順序，自動比對。你與組員可以將 21 組全部填入此處！

PAIRS_MAP = {
    ("Polygon Triangulation", "Dyck Path"): (
        "PathtoPoly2",
        "PTP2",
        "2n",
    ),
    ("Dyck Path", "Non-intersecting Chord"): (
        "chord",
        "PTC",
        "2n",
    ),
    ("Binary Tree", "Dyck Path"): (
        "treebijection",
        "PTT",
        "2n",
    ),
    ("Polygon Triangulation", "Binary Tree"): (
        "triangulationDFS",
        "DualPolyDFS",
        "2n",
    ),
    ("Polygon Triangulation", "Stack Permutation"): (
        "PolytoStack",
        "PTS",
        "2n",
    ),
    ("Binary Tree", "Stack Permutation"): (
        "TreetoStack",
        "TTS",
        "2n",
    ),
    ("Non-crossing Arc Diagram", "Non-intersecting Chord"): (
        "arctochord",
        "ATC",
        "2n",
    ),
    ("Polygon Triangulation", "Non-crossing Partition"): (
        "PolytoNCP",
        "TriToNCP",
        "2n",
    ),
    ("Binary Tree", "Non-crossing Arc Diagram"): (
        "TreetoArc",
        "TTA",
        "2n",
    ),
    ("Dyck Path", "Non-crossing Partition"): (
            "ncp",
            "NCP",
            "2n",
    ),
    ("Non-crossing Arc Diagram", "Stack Permutation"): (
            "stack",
            "Stack",
            "2n",
    ),
    ("Non-crossing Partition", "Non-intersecting Chord"): (
            "ChordtoNCP",
            "CtoNCP",
            "2n",
    ),
    ("Polygon Triangulation", "Non-intersecting Chord"): (
                "ChordtoPoly",
                "CTP",
                "2n",
    ),
    ("Stack Permutation", "Non-intersecting Chord"): (
                    "ChordtoStack",
                    "CTS",
                    "2n",
    ),
    ("Non-crossing Arc Diagram", "Non-crossing Partition"): (
                        "ArctoNCP",
                        "AtNCP",
                        "2n",
        ), 
    ("Polygon Triangulation", "Non-crossing Arc Diagram"): (
                            "ArctoPoly",
                            "ATP",
                            "2n",
            ), 
    ("Dyck Path", "Stack Permutation"): (
                    "PathtoStack",
                    "DTS",
                    "2n",
        ),
    ("Non-crossing Partition", "Stack Permutation"): (
                        "StacktoNCP",
                        "STNCP",
                        "2n",
            ),
    ("Binary Tree", "Non-intersecting Chord"): (
                        "TreetoChord",
                        "TTC",
                        "2n",
        ),
    ("Binary Tree", "Non-crossing Partition"): (
                            "TreetoNCP",
                            "TTNCP",
                            "2n",
            ),
    ("Dyck Path", "Non-crossing Arc Diagram"): (
                        "PathtoArc",
                        "DTA",
                        "2n",
            ),
  }

# 提取所有可選的結構名稱列表
ALL_STRUCTURES = sorted(
    list(
        set(
            [s for pair in PAIRS_MAP.keys() for s in pair]
            + [
                "Dyck Path",
                "Binary Tree",
                "Non-intersecting Chord",
                "Non-crossing Arc Diagram",
                "Stack Permutation",
                "Polygon Triangulation",
                "Non-crossing Partition",
            ]
        )
    )
)


def find_mapping(struct_a, struct_b):
  """自動比對 (A, B) 或 (B, A) 的雙射對應模組"""
  if (struct_a, struct_b) in PAIRS_MAP:
    return PAIRS_MAP[(struct_a, struct_b)]
  if (struct_b, struct_a) in PAIRS_MAP:
    return PAIRS_MAP[(struct_b, struct_a)]
  return None


# ==============================================================================
# 2. Session State 狀態初始化
# ==============================================================================
if "app_mode" not in st.session_state:
  st.session_state.app_mode = "select"  # 頁面模式：'select' (首頁) 或 'view' (圖表頁)
if "playing" not in st.session_state:
  st.session_state.playing = False
if "step_idx" not in st.session_state:
  st.session_state.step_idx = 0
if "page_idx" not in st.session_state:
  st.session_state.page_idx = 0


# ==============================================================================
# 3. 主頁面：結構選擇與參數設定頁 (app_mode == 'select')
# ==============================================================================
# ==============================================================================
# 3. 主頁面：結構選擇與參數設定頁 (app_mode == 'select')
# ==============================================================================
if st.session_state.app_mode == "select":
  st.title("Catalan Bijection")
  st.markdown("請選擇您想要探索的**兩個 Catalan 結構**與**規模大小 (n)**:")
  st.markdown("---")

  # 選擇卡片區域
  col1, col2, col3 = st.columns([3, 3, 2])

  with col1:
    st.subheader("First Structure")
    struct_a = st.selectbox(
        "選擇第一個結構：",
        ALL_STRUCTURES,
        index=0,
        key="sel_a",
        label_visibility="collapsed",
    )

  with col2:
    st.subheader("Second Structure")

    # 1. 動態過濾：排除已在第一個選單中被選取的 struct_a
    options_b = [s for s in ALL_STRUCTURES if s != struct_a]

    # 2. 安全檢查：如果目前 sel_b 的紀錄剛好與選中的 struct_a 重疊，自動調整為 options_b 的第一個選項
    if "sel_b" in st.session_state and st.session_state.sel_b not in options_b:
      st.session_state.sel_b = options_b[0]

    struct_b = st.selectbox(
        "選擇第二個結構：",
        options_b,
        key="sel_b",
        label_visibility="collapsed",
    )

  with col3:
    st.subheader("Enter n")
    n_val = st.number_input(
        "輸入大小 n:",
        min_value=1,
        max_value=15,
        value=3,
        step=1,
        key="sel_n",
        label_visibility="collapsed",
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # 檢查該組合是否存在
  mapping_info = find_mapping(struct_a, struct_b)

  if mapping_info:
    st.success(f"已選擇：**{struct_a}** ↔ **{struct_b}**, n={n_val}")
    if st.button(
        "Go to show the bijection", type="primary", use_container_width=True
    ):
      st.session_state.selected_a = struct_a
      st.session_state.selected_b = struct_b
      st.session_state.selected_n = n_val
      st.session_state.current_mapping = mapping_info
      st.session_state.app_mode = "view"
      st.session_state.step_idx = 0
      st.session_state.page_idx = 0
      st.session_state.playing = False
      st.rerun()
  else:
    st.warning("⚠️ 尚不支援此結構組合的雙射解讀，請切換其他組合！")


# ==============================================================================
# 4. 視覺化頁面：4 張圖展示與控制列 (app_mode == 'view')
# ==============================================================================
elif st.session_state.app_mode == "view":

  struct_a = st.session_state.selected_a
  struct_b = st.session_state.selected_b
  n_val = st.session_state.selected_n
  mod_name, class_name, step_type = st.session_state.current_mapping

  # 頂部導覽列
  top_col1, top_col2 = st.columns([3.5, 6.5])
  with top_col1:
    if st.button("Back to home page"):
      st.session_state.app_mode = "select"
      st.session_state.playing = False
      st.rerun()

  with top_col2:
    st.subheader(f"{struct_a} ↔ {struct_b} (n = {n_val})")

  try:
    # 動態載入類別
    module = __import__(mod_name)
    cls = getattr(module, class_name)

    temp_obj = cls(n_val)
    total_paths = temp_obj.total_count
    max_step_val = (2 * n_val) if step_type == "2n" else n_val

    # 邊界校正
    st.session_state.page_idx = min(st.session_state.page_idx, total_paths - 1)
    st.session_state.step_idx = min(st.session_state.step_idx, max_step_val)

    # 實體化畫布物件
    obj = cls(
        n_val,
        page_index=st.session_state.page_idx,
        step_index=st.session_state.step_idx,
    )

    # ─── 【不跳動的核心渲染機制：Memory Buffer + Fixed Image】 ───
    buf = io.BytesIO()
    obj.fig.savefig(
        buf,
        format="png",
        dpi=100,
        bbox_inches=None,
        facecolor=obj.fig.get_facecolor(),
    )
    st.image(buf, use_container_width=True)
    plt.close(obj.fig)

    # ─── 【底部控制面板 (1:1 佈局)】 ───
    st.markdown("---")
    ctrl_left, ctrl_mid, ctrl_right = st.columns([1.5, 5, 3.5])

    # 【左側：Speed Control 速度控制】
    with ctrl_left:
      st.caption("Speed Control")
      speed_option = st.radio(
          "Speed",
          ["Slow", "Normal", "Fast"],
          index=1,
          horizontal=True,
          label_visibility="collapsed",
      )
      speed_map = {"Slow": 1.2, "Normal": 0.6, "Fast": 0.25}
      current_speed = speed_map[speed_option]

    # 【中央：Step Playback 步驟播放】
    with ctrl_mid:
      st.caption("Step Control")

      # 1. 利用左右留白 [1, 3, 1] 把按鈕集中在中間（比例可依需求調整，如 [1, 2, 1] 會更緊）
      _, btn_box, _ = st.columns([0.5, 3, 0.5])

      with btn_box:
        # 2. 設定 gap="small" 縮小欄位間距
        b_reset, b_prev, b_play, b_next = st.columns(4, gap="small")

        # 3. 按鈕加上 use_container_width=True 讓按鈕寬度齊平且整齊
        if b_reset.button("Reset", use_container_width=True):
          st.session_state.step_idx = 0
          st.session_state.playing = False
          st.rerun()

        if b_prev.button("Previous Step", use_container_width=True):
          st.session_state.step_idx = max(0, st.session_state.step_idx - 1)
          st.session_state.playing = False
          st.rerun()

        play_label = "Pause" if st.session_state.playing else "Play"
        if b_play.button(play_label, use_container_width=True):
          if st.session_state.playing:
            st.session_state.playing = False
          else:
            if st.session_state.step_idx >= max_step_val:
              st.session_state.step_idx = 0
            st.session_state.playing = True
          st.rerun()

        if b_next.button("Next Step", use_container_width=True):
          st.session_state.step_idx = min(
              max_step_val, st.session_state.step_idx + 1
          )
          st.session_state.playing = False
          st.rerun()

    # 【右側：Page Control 頁碼切換】
    with ctrl_right:
      st.caption("Page Control")
      p_prev, p_box, p_next = st.columns([1.5, 2, 1.5])

      if p_prev.button("Previous Page"):
        if st.session_state.page_idx > 0:
          st.session_state.page_idx -= 1
          st.session_state.step_idx = 0
          st.session_state.playing = False
          st.rerun()

      with p_box:
        page_input = st.number_input(
            "Page Jump",
            min_value=1,
            max_value=total_paths,
            value=st.session_state.page_idx + 1,
            label_visibility="collapsed",
        )
        if page_input - 1 != st.session_state.page_idx:
          st.session_state.page_idx = page_input - 1
          st.session_state.step_idx = 0
          st.session_state.playing = False
          st.rerun()

      if p_next.button("Next Page"):
        if st.session_state.page_idx < total_paths - 1:
          st.session_state.page_idx += 1
          st.session_state.step_idx = 0
          st.session_state.playing = False
          st.rerun()

    # ─── 【動畫連續播放觸發邏輯】 ───
    if st.session_state.playing:
      if st.session_state.step_idx < max_step_val:
        time.sleep(current_speed)
        st.session_state.step_idx += 1
        st.rerun()
      else:
        st.session_state.playing = False
        st.rerun()

  except Exception as e:
    st.error(f"載入或繪製模組 `{mod_name}.py` 時發生錯誤：")
    st.code(str(e))