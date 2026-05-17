
from __future__ import annotations
import queue
import tkinter as tk
from typing import Optional
import os

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Please install customtkinter:  pip install customtkinter")

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from modules.simulation_engine import BankSimulation, SCENARIO_LABELS
from modules.exporter import export_csv, export_xlsx

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG      = "#0F1117"
PANEL   = "#1A1D27"
CARD    = "#22263A"
GREEN   = "#1DB954"
DGREEN  = "#1A5E38"
TEXT    = "#FFFFFF"
SUBTEXT = "#8892A4"
RED     = "#FF6B6B"
ORANGE  = "#FFA94D"
BLUE    = "#74B9FF"

SC_COLORS = {1: "#FF6B6B", 2: "#FFA94D", 3: "#74B9FF", 4: "#1DB954"}
KPI_COLORS = {"Exec Time": "#4A90D9", "Avg Wait": "#4A90D9", "Memory": "#4A90D9", "Throughput": "#4A90D9"}
COUNTER_COLORS = {"free": "#1DB954", "busy": "#FF6B6B"}
CUSTOMER_DOT = "#FFFFFF"


class SimulationCanvas(ctk.CTkFrame):
    COUNTER_W = 100
    COUNTER_H = 64
    DOT_R     = 6
    DOT_GAP   = 4
    PAD_X     = 50
    PAD_Y     = 40

    def __init__(self, parent, num_counters: int = 3, **kwargs):
        super().__init__(parent, fg_color=PANEL, corner_radius=12, **kwargs)
        self.num_counters = num_counters
        self._queue_data:     dict[int, list] = {i+1: [] for i in range(num_counters)}
        self._counter_status: dict[int, str]  = {i+1: "free" for i in range(num_counters)}
        self._counter_labels: dict[int, str]  = {i+1: "" for i in range(num_counters)}

        self.canvas = tk.Canvas(self, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def reset(self, num_counters: int) -> None:
        self.num_counters    = num_counters
        self._queue_data     = {i+1: [] for i in range(num_counters)}
        self._counter_status = {i+1: "free" for i in range(num_counters)}
        self._counter_labels = {i+1: "" for i in range(num_counters)}
        self.redraw()

    def update_counter(self, counter_id: int, status: str, label: str = "") -> None:
        self._counter_status[counter_id] = status
        self._counter_labels[counter_id] = label
        self.redraw()

    def update_all_queues(self, queue_list: list) -> None:
        n = self.num_counters
        buckets: dict[int, list] = {i+1: [] for i in range(n)}
        for idx, c in enumerate(queue_list):
            buckets[(idx % n) + 1].append(c)
        self._queue_data = buckets
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        n   = self.num_counters
        gap = (w - 2 * self.PAD_X) / n

        for i in range(n):
            cid    = i + 1
            cx     = int(self.PAD_X + gap * i + gap / 2)
            cy     = self.PAD_Y + self.COUNTER_H // 2
            status = self._counter_status.get(cid, "free")
            color  = COUNTER_COLORS[status]
            lbl    = self._counter_labels.get(cid, "")

            x0 = cx - self.COUNTER_W // 2
            y0 = cy - self.COUNTER_H // 2
            x1 = cx + self.COUNTER_W // 2
            y1 = cy + self.COUNTER_H // 2

            self.canvas.create_rectangle(x0, y0, x1, y1,
                fill=color, outline=TEXT, width=1.5)
            self.canvas.create_text(cx, cy - 12,
                text=f"Counter {cid}", fill=TEXT, font=("Helvetica", 9, "bold"))
            self.canvas.create_text(cx, cy + 6,
                text=status.upper(), fill=BG, font=("Helvetica", 8, "bold"))
            if lbl:
                self.canvas.create_text(cx, cy + 20,
                    text=lbl[:20], fill=BG, font=("Helvetica", 7))

            # Vertical queue dots
            customers = self._queue_data.get(cid, [])
            dot_step  = self.DOT_R * 2 + self.DOT_GAP
            max_show  = min(len(customers), 10)
            for j in range(max_show):
                dot_cx = cx
                dot_cy = y1 + 16 + j * dot_step
                r = self.DOT_R
                self.canvas.create_oval(
                    dot_cx - r, dot_cy - r, dot_cx + r, dot_cy + r,
                    fill=CUSTOMER_DOT, outline=SUBTEXT, width=1)
                svc = customers[j].get("service_time", "") if isinstance(customers[j], dict) else ""
                if svc:
                    self.canvas.create_text(dot_cx, dot_cy,
                        text=f"{svc:.0f}", fill=BG, font=("Helvetica", 5))

            if len(customers) > 10:
                extra_y = y1 + 16 + 10 * dot_step + 8
                self.canvas.create_text(cx, extra_y,
                    text=f"+{len(customers)-10} more", fill=SUBTEXT, font=("Helvetica", 7))

        self.canvas.create_text(w // 2, h - 12,
            text="● = waiting customer  |  number = service time (s)",
            fill=SUBTEXT, font=("Helvetica", 8))


class KPICard(ctk.CTkFrame):
    def __init__(self, parent, title: str, unit: str, color: str, **kwargs):
        super().__init__(parent, fg_color=CARD, corner_radius=10, **kwargs)
        ctk.CTkLabel(self, text=title, font=("Helvetica", 11),
                     text_color=SUBTEXT).pack(pady=(10, 2))
        self.value_lbl = ctk.CTkLabel(self, text="—",
                                       font=("Helvetica", 26, "bold"),
                                       text_color=color)
        self.value_lbl.pack()
        ctk.CTkLabel(self, text=unit, font=("Helvetica", 9),
                     text_color=SUBTEXT).pack(pady=(0, 10))

    def set_value(self, val) -> None:
        self.value_lbl.configure(text=str(val))


class MetricsDashboard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=PANEL, corner_radius=12, **kwargs)

        ctk.CTkLabel(self, text="Live KPI Dashboard",
                     font=("Helvetica", 14, "bold"),
                     text_color=GREEN).pack(pady=(12, 6))

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10)

        self.card_exec = KPICard(cards_frame, "Exec Time",  "ms",  KPI_COLORS["Exec Time"])
        self.card_wait = KPICard(cards_frame, "Avg Wait",   "sec", KPI_COLORS["Avg Wait"])
        self.card_mem  = KPICard(cards_frame, "Memory",     "KB",  KPI_COLORS["Memory"])
        self.card_thru = KPICard(cards_frame, "Throughput", "c/s", KPI_COLORS["Throughput"])
        for card in (self.card_exec, self.card_wait, self.card_mem, self.card_thru):
            card.pack(side="left", expand=True, fill="x", padx=4, pady=4)

        self.chart_frame   = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=6)
        self._chart_widget = None
        self._results: dict[int, dict] = {}   # keyed by scenario number

    def update_live(self, d: dict) -> None:
        self.card_exec.set_value(d.get("Exec Time (ms)", "—"))
        self.card_wait.set_value(d.get("Avg Wait (s)",   "—"))
        self.card_mem.set_value( d.get("Memory (KB)",    "—"))
        self.card_thru.set_value(d.get("Throughput (c/s)", "—"))

    def add_result(self, scenario: int, d: dict) -> None:
        self._results[scenario] = d
        self._render_chart()

    def reset(self) -> None:
        self._results.clear()
        if self._chart_widget:
            self._chart_widget.get_tk_widget().destroy()
            self._chart_widget = None

    def _render_chart(self) -> None:
        if not HAS_MPL or not self._results:
            return
        if self._chart_widget:
            self._chart_widget.get_tk_widget().destroy()
            self._chart_widget = None

        ordered   = sorted(self._results.items())
        sc_nums   = [sc for sc, _ in ordered]
        sc_labels = [f"Sc.{sc}" for sc in sc_nums]
        colors    = [SC_COLORS[sc] for sc in sc_nums]
        metrics   = ["Exec Time (ms)", "Avg Wait (s)", "Memory (KB)", "Throughput (c/s)"]

        fig, axes = plt.subplots(1, 4, figsize=(9, 2.5))
        fig.patch.set_facecolor(PANEL)
        for ax, metric in zip(axes, metrics):
            vals    = [r.get(metric, 0) for _, r in ordered]
            bars    = ax.bar(sc_labels, vals, color=colors, width=0.5)
            max_val = max(vals) if vals else 1
            ax.set_title(metric, color=TEXT, fontsize=7, pad=4)
            ax.set_facecolor(CARD)
            ax.tick_params(colors=SUBTEXT, labelsize=6)
            for spine in ax.spines.values():
                spine.set_edgecolor(SUBTEXT)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + max_val * 0.03,
                        f"{val:.3f}" if metric == "Throughput (c/s)" else f"{val:.1f}", ha="center", va="bottom",
                        color=TEXT, fontsize=6)
        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_widget = canvas
        plt.close(fig)

    def save_chart(self, path: str) -> None:
        if not HAS_MPL or not self._results:
            return
        ordered   = sorted(self._results.items())
        sc_nums   = [sc for sc, _ in ordered]
        sc_labels = [f"Sc.{sc}" for sc in sc_nums]
        colors    = [SC_COLORS[sc] for sc in sc_nums]
        metrics   = ["Exec Time (ms)", "Avg Wait (s)", "Memory (KB)", "Throughput (c/s)"]
        fig, axes = plt.subplots(1, 4, figsize=(12, 3))
        fig.patch.set_facecolor(PANEL)
        for ax, metric in zip(axes, metrics):
            vals    = [r.get(metric, 0) for _, r in ordered]
            bars    = ax.bar(sc_labels, vals, color=colors, width=0.5)
            max_val = max(vals) if vals else 1
            ax.set_title(metric, color=TEXT, fontsize=9)
            ax.set_facecolor(CARD)
            ax.tick_params(colors=SUBTEXT)
            for spine in ax.spines.values():
                spine.set_edgecolor(SUBTEXT)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + max_val * 0.03,
                        f"{val:.3f}" if metric == "Throughput (c/s)" else f"{val:.2f}", ha="center", va="bottom",
                        color=TEXT, fontsize=7)
        fig.tight_layout()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        fig.savefig(path, dpi=150, facecolor=PANEL)
        plt.close(fig)

    def get_results_list(self) -> list:
        return [r for _, r in sorted(self._results.items())]


class LogTerminal(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=PANEL, corner_radius=12, **kwargs)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(header, text="System Log",
                     font=("Helvetica", 13, "bold"),
                     text_color=GREEN).pack(side="left")
        ctk.CTkButton(header, text="Clear", width=60, height=24,
                      fg_color=CARD, hover_color=DGREEN,
                      command=self.clear).pack(side="right")
        self.textbox = ctk.CTkTextbox(self, font=("Courier", 11), fg_color=BG,
                                       text_color=TEXT, wrap="word", state="disabled")
        self.textbox.pack(fill="both", expand=True, padx=8, pady=8)

    def log(self, msg: str) -> None:
        self.textbox.configure(state="normal")
        self.textbox.insert("end", msg + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")


class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, on_start, on_stop, on_run_all, **kwargs):
        super().__init__(parent, fg_color=PANEL, corner_radius=12, **kwargs)

        ctk.CTkLabel(self, text="Control Panel",
                     font=("Helvetica", 13, "bold"),
                     text_color=GREEN).grid(row=0, column=0, columnspan=4,
                                            pady=(10,6), padx=10, sticky="w")

        ctk.CTkLabel(self, text="Scenario:", text_color=SUBTEXT,
                     font=("Helvetica", 11)).grid(row=1, column=0, padx=(10,4), pady=4)
        self.scenario_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(self,
            values=["1 — Queue + Insertion Sort",
                    "2 — Heap  + Insertion Sort",
                    "3 — Queue + Binary Search",
                    "4 — Heap  + Binary Search"],
            variable=self.scenario_var, width=220,
            fg_color=CARD, button_color=DGREEN,
        ).grid(row=1, column=1, padx=4, pady=4)

        ctk.CTkLabel(self, text="Speed:", text_color=SUBTEXT,
                     font=("Helvetica", 11)).grid(row=1, column=2, padx=(12,4))
        self.speed_var = ctk.DoubleVar(value=2.0)
        ctk.CTkSlider(self, from_=0.5, to=10.0, variable=self.speed_var,
                      width=120, button_color=GREEN).grid(row=1, column=3, padx=4)

        ctk.CTkLabel(self, text="Counters:", text_color=SUBTEXT,
                     font=("Helvetica", 11)).grid(row=2, column=0, padx=(10,4), pady=4)
        self.counters_var = ctk.StringVar(value="3")
        ctk.CTkOptionMenu(self, values=["1","2","3","4","5"],
                          variable=self.counters_var, width=80,
                          fg_color=CARD, button_color=DGREEN,
                          ).grid(row=2, column=1, padx=4, sticky="w")

        ctk.CTkLabel(self, text="Duration (s):", text_color=SUBTEXT,
                     font=("Helvetica", 11)).grid(row=2, column=2, padx=(12,4))
        self.duration_var = ctk.StringVar(value="120")
        ctk.CTkEntry(self, textvariable=self.duration_var,
                     width=70, fg_color=CARD).grid(row=2, column=3, padx=4, sticky="w")

        ctk.CTkLabel(self, text="Arrival Rate\n(cust/sec):", text_color=SUBTEXT,
                     font=("Helvetica", 10)).grid(row=3, column=0, padx=(10,4), pady=4)
        self.arrival_var = ctk.StringVar(value="0.5")
        ctk.CTkEntry(self, textvariable=self.arrival_var,
                     width=70, fg_color=CARD).grid(row=3, column=1, padx=4, sticky="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10, padx=10)

        self.btn_start = ctk.CTkButton(btn_frame, text="▶  Run Scenario", width=140,
                                        fg_color=DGREEN, hover_color=GREEN, command=on_start)
        self.btn_start.pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="⏹  Stop", width=90,
                      fg_color=CARD, hover_color=RED, command=on_stop).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="⚡  Run All 4 Scenarios", width=180,
                      fg_color="#2C3E6B", hover_color="#3B5998",
                      command=on_run_all).pack(side="left", padx=6)

    def get_scenario(self) -> int:
        return int(self.scenario_var.get().split("—")[0].strip())

    def get_speed(self) -> float:
        return round(self.speed_var.get(), 1)

    def get_counters(self) -> int:
        return int(self.counters_var.get())

    def get_duration(self) -> float:
        try:
            val = float(self.duration_var.get())
            if val <= 0:
                self.duration_var.set("120")
                return 120.0
            return min(val, 3600.0)
        except ValueError:
            self.duration_var.set("120")
            return 120.0

    def get_arrival_rate(self) -> float:
        try:
            val = float(self.arrival_var.get())
            if val <= 0:
                self.arrival_var.set("0.5")
                return 0.5
            return min(val, 5.0)
        except ValueError:
            self.arrival_var.set("0.5")
            return 0.5

    def set_running(self, running: bool) -> None:
        self.btn_start.configure(state="disabled" if running else "normal")


class MainWindow:
    def __init__(self) -> None:
        self.root = ctk.CTk()
        self.root.title("Smart Bank Service Simulation — EE367")
        self.root.geometry("1300x840")
        self.root.configure(fg_color=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._sim:         Optional[BankSimulation] = None
        self._running_all  = False
        self._all_scenario = 1

        self._build_ui()
        self._poll_ui_queue()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self.root, fg_color=PANEL, corner_radius=0, height=52)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="🏦  Smart Bank Service Simulation",
                     font=("Helvetica", 18, "bold"),
                     text_color=GREEN).pack(side="left", padx=20, pady=10)

        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=6)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        self.canvas_panel = SimulationCanvas(main, num_counters=3)
        self.canvas_panel.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        self.dashboard = MetricsDashboard(main)
        self.dashboard.grid(row=0, column=1, sticky="nsew")

        bottom = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom.pack(fill="both", padx=10, pady=(0,8))
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=3)

        self.control = ControlPanel(bottom,
                                     on_start=self._on_start,
                                     on_stop=self._on_stop,
                                     on_run_all=self._on_run_all)
        self.control.grid(row=0, column=0, sticky="nsew", padx=(0,5))

        self.log = LogTerminal(bottom)
        self.log.grid(row=0, column=1, sticky="nsew")

    def _make_sim(self, scenario: int) -> BankSimulation:
        return BankSimulation(
            scenario=scenario,
            num_counters=self.control.get_counters(),
            arrival_rate=self.control.get_arrival_rate(),
            sim_duration=self.control.get_duration(),
            speed=self.control.get_speed(),
            log_cb=lambda msg: self.root.after(0, self.log.log, msg),
        )

    def _reset_canvas(self) -> None:
        self.canvas_panel.reset(self.control.get_counters())

    def _on_start(self) -> None:
        if self._sim and self._sim.running:
            return
        if self.control.get_arrival_rate() <= 0:
            self.log.log("⚠️  Arrival rate must be greater than 0. Reset to 0.5.")
            return
        if self.control.get_duration() <= 0:
            self.log.log("⚠️  Duration must be greater than 0. Reset to 120.")
            return
        scenario = self.control.get_scenario()
        self._reset_canvas()
        self.log.log(f"\n{'═'*45}")
        self.log.log(f"  Starting {SCENARIO_LABELS[scenario]}")
        self.log.log(f"  Counters={self.control.get_counters()}, "
                     f"Speed={self.control.get_speed()}x, "
                     f"ArrivalRate={self.control.get_arrival_rate()}")
        self.log.log(f"{'═'*45}")
        self._sim = self._make_sim(scenario)
        self.control.set_running(True)
        self._sim.start()

    def _on_stop(self) -> None:
        if self._sim:
            self._sim.stop()
        self._running_all = False
        self.control.set_running(False)

    def _on_run_all(self) -> None:
        if self._running_all or (self._sim and self._sim.running):
            return
        self.dashboard.reset()
        self._running_all  = True
        self._all_scenario = 1
        self._run_next_scenario()

    def _run_next_scenario(self) -> None:
        if not self._running_all or self._all_scenario > 4:
            self._running_all = False
            self.control.set_running(False)
            self._export_all()
            return
        sc = self._all_scenario
        self._reset_canvas()
        self.log.log(f"\n{'═'*45}")
        self.log.log(f"  AUTO-RUN  Scenario {sc}: {SCENARIO_LABELS[sc]}")
        self.log.log(f"{'═'*45}")
        self._sim = self._make_sim(sc)
        self.control.set_running(True)
        self._sim.start()

    def _poll_ui_queue(self) -> None:
        if self._sim:
            try:
                while True:
                    self._handle_message(self._sim.ui_queue.get_nowait())
            except queue.Empty:
                pass
        self.root.after(50, self._poll_ui_queue)

    def _handle_message(self, msg: dict) -> None:
        t    = msg["type"]
        data = msg["data"]

        if t == "arrival":
            self.canvas_panel.update_all_queues(data.get("queue_list", []))

        elif t == "serving":
            cid  = data["counter_id"]
            cust = data["customer"]
            self.canvas_panel.update_counter(
                cid, "busy", f"{cust['id']}  svc={cust['service_time']:.1f}s")

        elif t == "counter_free":
            self.canvas_panel.update_counter(data["counter_id"], "free", "")

        elif t == "done":
            tracker_dict = data["tracker"]
            scenario_num = self._sim.scenario
            self.dashboard.update_live(tracker_dict)
            self.dashboard.add_result(scenario_num, tracker_dict)

            if self._running_all:
                self._all_scenario += 1
                self.root.after(600, self._run_next_scenario)
            else:
                self.control.set_running(False)
                self._export_all()

    def _export_all(self) -> None:
        results = self.dashboard.get_results_list()
        if not results:
            return
        import shutil
        base       = os.path.join(os.path.dirname(__file__), "..", "Results")
        csv_path   = os.path.join(base, "Performance_Data.csv")
        xlsx_path  = os.path.join(base, "Performance_Data.xlsx")
        chart_path = os.path.join(base, "KPI_Comparison_Charts.png")

        # Rotate current → previous before saving new files
        for fp, prev in [
            (csv_path,   os.path.join(base, "Performance_Data_previous.csv")),
            (xlsx_path,  os.path.join(base, "Performance_Data_previous.xlsx")),
            (chart_path, os.path.join(base, "KPI_Comparison_Charts_previous.png")),
        ]:
            if os.path.exists(fp):
                shutil.move(fp, prev)   # rename current → previous

        export_csv(results, csv_path)
        export_xlsx(results, xlsx_path)
        self.dashboard.save_chart(chart_path)
        self.log.log("\n✅ Results exported to Results/")

    def _on_close(self) -> None:
        if self._sim:
            self._sim.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
