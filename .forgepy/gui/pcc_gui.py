#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
except Exception as exc:  # pragma: no cover - Windows normally ships tkinter
    tkinter_error = exc
    tk = None  # type: ignore[assignment]
else:
    tkinter_error = None

APP_TITLE = "ForgePY Project Control Center — U5"
BG = "#17191d"
PANEL = "#202329"
PANEL_2 = "#292d34"
BORDER = "#373c45"
TEXT = "#e8eaf0"
MUTED = "#a3a8b3"
ACCENT = "#5b8cff"
GOOD = "#4fb286"
WARN = "#d6a64c"
BAD = "#d86161"


def backend_argv(root: Path, *args: str) -> list[str]:
    runtime = root / ".forgepy" / "runtime" / "forgepy.py"
    return [sys.executable, str(runtime), "--root", str(root), *args]


def run_capture(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0
    return subprocess.run(
        backend_argv(root, *args), cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", check=False, creationflags=creationflags,
    )


def load_json_command(root: Path, *args: str) -> Any:
    cp = run_capture(root, *args)
    if cp.returncode != 0:
        raise RuntimeError(cp.stdout.strip() or f"ForgePY command failed: {' '.join(args)}")
    return json.loads(cp.stdout)


def open_path(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class PCCApp:
    def __init__(self, root: Path):
        assert tk is not None
        self.root_path = root.resolve()
        self.runtime_path = self.root_path / ".forgepy" / "runtime" / "forgepy.py"
        self.window = tk.Tk()
        self.window.title(APP_TITLE)
        self.window.geometry("1280x820")
        self.window.minsize(1040, 680)
        self.window.configure(bg=BG)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.proc: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.status: dict[str, Any] = {}
        self.operation_rows: list[dict[str, Any]] = []
        self.patch_rows: list[dict[str, Any]] = []
        self.build_plan: dict[str, Any] = {}
        self.frames: dict[str, tk.Frame] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self.busy = False
        self.refreshing = False
        self.refresh_pending = False
        self._log_chunks = 0
        self.action_buttons: list[tk.Widget] = []
        self._configure_style()
        self._build_shell()
        self.window.after(100, self._poll_queue)
        self.refresh_all()

    def _configure_style(self) -> None:
        style = ttk.Style(self.window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL_2, foreground=TEXT, relief="flat", padding=(8, 6))
        style.map("Treeview", background=[("selected", "#34558f")], foreground=[("selected", "#ffffff")])
        style.configure("TSeparator", background=BORDER)

    def _build_shell(self) -> None:
        header = tk.Frame(self.window, bg=PANEL, height=76, highlightbackground=BORDER, highlightthickness=0)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        self.project_label = tk.Label(header, text="Loading project…", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 16))
        self.project_label.pack(side="left", padx=(20, 8), pady=18)
        self.health_label = tk.Label(header, text="CHECKING", bg=PANEL_2, fg=MUTED, font=("Segoe UI Semibold", 9), padx=10, pady=5)
        self.health_label.pack(side="left", padx=8)
        self.header_meta = tk.Label(header, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.header_meta.pack(side="right", padx=(8, 20))
        header_refresh = tk.Button(header, text="Refresh", command=self.refresh_all, bd=0, relief="flat",
                                   bg=PANEL_2, fg=TEXT, activebackground=ACCENT, activeforeground="#ffffff",
                                   font=("Segoe UI Semibold", 8), padx=10, pady=5, cursor="hand2")
        header_refresh.pack(side="right", padx=8)

        body = tk.Frame(self.window, bg=BG)
        body.pack(fill="both", expand=True)
        nav = tk.Frame(body, bg="#14161a", width=168)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        content = tk.Frame(body, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        self.content = content

        tk.Label(nav, text="FORGEPY", bg="#14161a", fg=MUTED, font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=18, pady=(18, 8))
        for name in ("Dashboard", "Build Plan", "Operations", "Patches", "Git", "Recovery", "Logs", "Settings"):
            b = tk.Button(nav, text=name, command=lambda n=name: self.show_page(n), anchor="w", bd=0, relief="flat",
                          bg="#14161a", fg=TEXT, activebackground=PANEL_2, activeforeground=TEXT,
                          font=("Segoe UI", 10), padx=18, pady=9, cursor="hand2")
            b.pack(fill="x", padx=6, pady=1)
            self.nav_buttons[name] = b

        self._build_dashboard()
        self._build_build_plan()
        self._build_operations()
        self._build_patches()
        self._build_git()
        self._build_recovery()
        self._build_logs()
        self._build_settings()
        self.show_page("Dashboard")

        status = tk.Frame(self.window, bg=PANEL, height=30)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        self.footer = tk.Label(status, text="Ready", bg=PANEL, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.footer.pack(fill="both", padx=12)

    def _page(self, name: str, title: str, subtitle: str) -> tuple[tk.Frame, tk.Frame]:
        frame = tk.Frame(self.content, bg=BG)
        self.frames[name] = frame
        heading = tk.Frame(frame, bg=BG)
        heading.pack(fill="x", padx=24, pady=(22, 14))
        tk.Label(heading, text=title, bg=BG, fg=TEXT, font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(heading, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))
        area = tk.Frame(frame, bg=BG)
        area.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        return frame, area

    def _button(self, parent: tk.Widget, text: str, command: Callable[[], None], *, primary: bool = False, danger: bool = False) -> tk.Button:
        bg = BAD if danger else (ACCENT if primary else PANEL_2)
        b = tk.Button(parent, text=text, command=command, bg=bg, fg="#ffffff" if primary or danger else TEXT,
                      activebackground=bg, activeforeground="#ffffff", relief="flat", bd=0,
                      padx=14, pady=8, font=("Segoe UI Semibold", 9), cursor="hand2")
        self.action_buttons.append(b)
        return b

    def _card(self, parent: tk.Widget, title: str) -> tuple[tk.Frame, tk.Label]:
        f = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(f, text=title.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=14, pady=(11, 4))
        value = tk.Label(f, text="—", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 14), anchor="w")
        value.pack(fill="x", padx=14, pady=(0, 12))
        return f, value

    def _build_dashboard(self) -> None:
        _, area = self._page("Dashboard", "Project Dashboard", "One place for health, certification, build, test and run operations.")
        cards = tk.Frame(area, bg=BG)
        cards.pack(fill="x")
        self.card_values: dict[str, tk.Label] = {}
        for key, title in (("source", "Source"), ("gate", "Certification"), ("components", "Components"), ("patches", "Patch Inbox")):
            card, value = self._card(cards, title)
            card.pack(side="left", fill="x", expand=True, padx=(0 if key == "source" else 6, 0))
            self.card_values[key] = value
        action = tk.Frame(area, bg=BG)
        action.pack(fill="x", pady=(18, 10))
        for text, cmd, primary in (("FULL GATE", "full", True), ("QUICK GATE", "quick", False), ("BUILD", "build", False), ("TEST", "test", False), ("RUN", "run", False), ("DOCTOR", "doctor", False)):
            self._button(action, text, lambda c=cmd: self.run_backend(c), primary=primary).pack(side="left", padx=(0, 8))
        detail = tk.Frame(area, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        detail.pack(fill="both", expand=True, pady=(8, 0))
        tk.Label(detail, text="PROJECT SUMMARY", bg=PANEL, fg=MUTED, font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=14, pady=(12, 4))
        self.dashboard_summary = tk.Label(detail, text="", justify="left", anchor="nw", bg=PANEL, fg=TEXT, font=("Consolas", 10))
        self.dashboard_summary.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _build_build_plan(self) -> None:
        _, area = self._page("Build Plan", "Automatic Build Plan", "Repository scan results used to synthesize build, test and run operations. Nothing opaque: every target shows its evidence and working directory.")
        top = tk.Frame(area, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        self.plan_summary = tk.Label(top, text="Scanning…", bg=BG, fg=TEXT, justify="left", anchor="w", font=("Consolas", 9))
        self.plan_summary.pack(side="left", fill="x", expand=True)
        self._button(top, "Force Rescan", self.rescan_project, primary=True).pack(side="right")
        self._button(top, "Pin as Adapter", self.pin_discovered_adapter).pack(side="right", padx=8)

        paned = tk.PanedWindow(area, orient="vertical", bg=BG, sashwidth=6, bd=0, relief="flat")
        paned.pack(fill="both", expand=True)
        upper = tk.Frame(paned, bg=BG)
        lower = tk.Frame(paned, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        paned.add(upper, stretch="always", minsize=220)
        paned.add(lower, stretch="always", minsize=150)
        cols = ("kind", "cwd", "confidence", "markers")
        self.plan_tree = ttk.Treeview(upper, columns=cols, show="headings", selectmode="browse")
        for c, w in (("kind", 120), ("cwd", 280), ("confidence", 100), ("markers", 520)):
            self.plan_tree.heading(c, text=c.upper())
            self.plan_tree.column(c, width=w, anchor="w", stretch=(c == "markers"))
        self.plan_tree.pack(fill="both", expand=True)
        tk.Label(lower, text="DEFAULTS / WARNINGS / UNRESOLVED", bg=PANEL, fg=MUTED, font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=12, pady=(10, 4))
        self.plan_text = tk.Text(lower, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Consolas", 9), wrap="word", height=8)
        self.plan_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.plan_text.configure(state="disabled")

    def _refresh_build_plan_view(self) -> None:
        plan = self.build_plan or {}
        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)
        for idx, row in enumerate(plan.get("components") or []):
            self.plan_tree.insert("", "end", iid=str(idx), values=(row.get("kind"), row.get("cwd"), row.get("confidence"), ", ".join(str(x) for x in row.get("markers") or [])))
        self.plan_summary.configure(text=(
            f"Components: {plan.get('componentCount', 0)}    Markers: {plan.get('markerCount', 0)}    "
            f"Generated ops: {len(plan.get('operations') or [])}    Cache: {'HIT' if plan.get('cacheHit') else 'FRESH'}\n"
            f"Kinds: {', '.join(plan.get('kinds') or []) or 'none'}    Signature: {str(plan.get('signature') or '')[:16]}"
        ))
        lines = ["DEFAULT SEMANTIC OPERATIONS"]
        defaults = plan.get("defaults") or {}
        if defaults:
            for key, members in defaults.items():
                lines.append(f"  {key:<18} → {', '.join(str(x) for x in members)}")
        else:
            lines.append("  (none)")
        warnings = plan.get("warnings") or []
        lines.extend(["", "WARNINGS"])
        lines.extend([f"  • {x}" for x in warnings] or ["  (none)"])
        unresolved = plan.get("unresolved") or []
        lines.extend(["", "UNRESOLVED / MANUAL CONFIGURATION"])
        lines.extend([f"  • {x.get('message') if isinstance(x, dict) else x}" for x in unresolved] or ["  (none)"])
        self._set_text(self.plan_text, "\n".join(lines))

    def rescan_project(self) -> None:
        self.run_backend("rescan")

    def pin_discovered_adapter(self) -> None:
        if not messagebox.askyesno(APP_TITLE, "Pin the current automatic build plan as a project-local ForgePY adapter?\n\nThis is useful when you want the discovered commands reviewed and stable. Existing project-owned adapters are never overwritten."):
            return
        self.run_backend("onboarding-apply")

    def _build_operations(self) -> None:
        _, area = self._page("Operations", "Operations", "Normalized project actions, component ownership, and provider source. Use filters to keep large monorepos manageable.")
        filters = tk.Frame(area, bg=BG)
        filters.pack(fill="x", pady=(0, 8))
        tk.Label(filters, text="Search", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.ops_search = tk.StringVar()
        search = tk.Entry(filters, textvariable=self.ops_search, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, font=("Segoe UI", 9))
        search.pack(side="left", fill="x", expand=True, padx=(8, 12), ipady=5)
        self.ops_category = tk.StringVar(value="all")
        category = ttk.Combobox(filters, textvariable=self.ops_category, values=("all", "gate", "build", "build-release", "test", "run", "other"), state="readonly", width=14)
        category.pack(side="left")
        self.ops_search.trace_add("write", lambda *_: self._render_operations())
        category.bind("<<ComboboxSelected>>", lambda _e: self._render_operations())
        cols = ("key", "category", "component", "provider", "label")
        self.ops_tree = ttk.Treeview(area, columns=cols, show="headings", selectmode="browse")
        widths = {"key": 250, "category": 90, "component": 150, "provider": 120, "label": 350}
        for c in cols:
            self.ops_tree.heading(c, text=c.upper())
            self.ops_tree.column(c, width=widths[c], anchor="w", stretch=(c == "label"))
        self.ops_tree.pack(fill="both", expand=True)
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Run Selected", self.run_selected_operation, primary=True).pack(side="left")
        self._button(bar, "Refresh", self.refresh_operations).pack(side="left", padx=8)

    def _render_operations(self) -> None:
        if not hasattr(self, "ops_tree"):
            return
        for item in self.ops_tree.get_children():
            self.ops_tree.delete(item)
        query = self.ops_search.get().strip().casefold() if hasattr(self, "ops_search") else ""
        category = self.ops_category.get().strip().casefold() if hasattr(self, "ops_category") else "all"
        visible = []
        for idx, row in enumerate(self.operation_rows):
            row_category = str(row.get("category") or "other").casefold()
            haystack = " ".join(str(row.get(k) or "") for k in ("key", "category", "label", "_provider", "_source", "_component")).casefold()
            if category != "all" and row_category != category:
                continue
            if query and query not in haystack:
                continue
            visible.append((idx, row))
        for source_idx, row in visible:
            provider_name = row.get("_provider") or row.get("_source") or "project"
            component = row.get("_component") or ("default" if row.get("_defaultAlias") else "—")
            self.ops_tree.insert("", "end", iid=str(source_idx), values=(row.get("key"), row.get("category"), component, provider_name, row.get("label")))

    def _build_patches(self) -> None:
        _, area = self._page("Patches", "Patch Intake", "Root-drop patches are inspected first and never auto-applied.")
        cols = ("path", "kind", "bytes", "hash")
        self.patch_tree = ttk.Treeview(area, columns=cols, show="headings", selectmode="browse")
        for c, w in (("path", 420), ("kind", 130), ("bytes", 100), ("hash", 220)):
            self.patch_tree.heading(c, text=c.upper())
            self.patch_tree.column(c, width=w, anchor="w", stretch=(c == "path"))
        self.patch_tree.pack(fill="both", expand=True)
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Validate", self.validate_selected_patch).pack(side="left")
        self._button(bar, "Apply", self.apply_selected_patch, primary=True).pack(side="left", padx=8)
        self._button(bar, "Refresh", self.refresh_patches).pack(side="left")

    def _build_git(self) -> None:
        _, area = self._page("Git", "Git", "Safe repository operations: GREEN commits, fast-forward pulls and upstream-only pushes.")
        self.git_summary = tk.Label(area, text="", bg=BG, fg=TEXT, justify="left", anchor="w", font=("Consolas", 10))
        self.git_summary.pack(fill="x", pady=(0, 10))
        cols = ("sha", "date", "subject")
        self.git_tree = ttk.Treeview(area, columns=cols, show="headings")
        for c, w in (("sha", 110), ("date", 190), ("subject", 480)):
            self.git_tree.heading(c, text=c.upper())
            self.git_tree.column(c, width=w, anchor="w", stretch=(c == "subject"))
        self.git_tree.pack(fill="both", expand=True)
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Commit GREEN", self.commit_green, primary=True).pack(side="left")
        self._button(bar, "Pull FF", lambda: self.run_backend("git-pull")).pack(side="left", padx=8)
        self._button(bar, "Push", lambda: self.run_backend("push")).pack(side="left")
        self._button(bar, "Refresh", self.refresh_git).pack(side="left", padx=8)

    def _build_recovery(self) -> None:
        _, area = self._page("Recovery", "Recovery & Evidence", "Inspect the last GREEN/failure state and create portable diagnostics without destructive recovery guesses.")
        self.recovery_text = tk.Text(area, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Consolas", 10), wrap="word")
        self.recovery_text.pack(fill="both", expand=True)
        self.recovery_text.configure(state="disabled")
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Create Debug Bundle", lambda: self.run_backend("debug-bundle"), primary=True).pack(side="left")
        self._button(bar, "Open State", lambda: open_path(self.state_dir())).pack(side="left", padx=8)
        self._button(bar, "Open Artifacts", lambda: open_path(self.root_path / ".forgepy" / "artifacts")).pack(side="left")

    def _build_logs(self) -> None:
        _, area = self._page("Logs", "Live Console", "Build, test, gate and diagnostic output from the same backend used by CLI and Cortex/Forge clients.")
        self.log_text = tk.Text(area, bg="#101216", fg="#d8dbe2", insertbackground=TEXT, relief="flat", font=("Consolas", 9), wrap="word")
        self.log_text.pack(fill="both", expand=True)
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Clear", lambda: self.log_text.delete("1.0", "end")).pack(side="left")
        self._button(bar, "Open Log Folder", lambda: open_path(self.state_dir() / "logs")).pack(side="left", padx=8)
        self.cancel_button = self._button(bar, "Cancel Operation", self.cancel_backend, danger=True)
        self.action_buttons.remove(self.cancel_button)
        self.cancel_button.configure(state="disabled")
        self.cancel_button.pack(side="right")

    def _build_settings(self) -> None:
        _, area = self._page("Settings", "Project Provider", "Identity, provider precedence, capabilities and local runtime configuration.")
        self.settings_text = tk.Text(area, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Consolas", 10), wrap="word")
        self.settings_text.pack(fill="both", expand=True)
        self.settings_text.configure(state="disabled")
        bar = tk.Frame(area, bg=BG)
        bar.pack(fill="x", pady=(10, 0))
        self._button(bar, "Force Rescan", self.rescan_project, primary=True).pack(side="left")
        self._button(bar, "Refresh Snapshot", self.refresh_all).pack(side="left", padx=8)
        self._button(bar, "Open Project", lambda: open_path(self.root_path)).pack(side="left")

    def show_page(self, name: str) -> None:
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
        for n, button in self.nav_buttons.items():
            button.configure(bg=PANEL_2 if n == name else "#14161a")

    def state_dir(self) -> Path:
        generated = self.root_path / ".forgepy" / "state" / "generated.project.control.json"
        try:
            data = json.loads(generated.read_text(encoding="utf-8"))
            rel = data.get("stateDirectory") or ".forgepy/state"
            return (self.root_path / str(rel)).resolve()
        except Exception:
            return self.root_path / ".forgepy" / "state"

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def refresh_all(self) -> None:
        if not self.runtime_path.is_file():
            messagebox.showerror(APP_TITLE, f"ForgePY runtime is missing:\n{self.runtime_path}")
            return
        if self.refreshing:
            self.refresh_pending = True
            return
        self.refreshing = True
        self.footer.configure(text="Refreshing project snapshot…")
        def worker() -> None:
            try:
                snapshot = load_json_command(self.root_path, "snapshot")
                self.output_queue.put(("refresh", snapshot))
            except Exception as exc:
                self.output_queue.put(("refresh_error", str(exc)))
        threading.Thread(target=worker, daemon=True, name="forgepy-gui-refresh").start()

    def refresh_operations(self) -> None:
        self.refresh_all()

    def refresh_patches(self) -> None:
        self.refresh_all()

    def refresh_git(self) -> None:
        self.refresh_all()

    def _apply_refresh(self, snapshot: dict[str, Any]) -> None:
        status = snapshot.get("status") or {}
        ops = snapshot.get("operations") or []
        patches = snapshot.get("patches") or []
        history = snapshot.get("gitHistory") or []
        self.build_plan = snapshot.get("buildPlan") or {}
        self.status = status
        self.operation_rows = ops
        self.patch_rows = patches
        p = status.get("project") or {}
        g = status.get("git") or {}
        provider = status.get("provider") or status.get("discovery") or {}
        scan = status.get("scan") or {}
        self.project_label.configure(text=str(p.get("name") or self.root_path.name))
        green = bool(status.get("greenCurrent"))
        gate = status.get("lastGate") or {}
        if green:
            self.health_label.configure(text="GREEN", bg=GOOD, fg="#ffffff")
        elif gate.get("result") == "FAIL":
            self.health_label.configure(text="GATE FAILED", bg=BAD, fg="#ffffff")
        else:
            self.health_label.configure(text="UNCERTIFIED", bg=WARN, fg="#111111")
        head = str(g.get("head") or "")[:10]
        self.header_meta.configure(text=f"{g.get('branch') or '(no branch)'}  {head}    {provider.get('name') or provider.get('providerName') or provider.get('type') or 'ForgePY'}")
        self.card_values["source"].configure(text="CLEAN" if status.get("sourceClean") else "MODIFIED", fg=GOOD if status.get("sourceClean") else WARN)
        self.card_values["gate"].configure(text="GREEN" if green else str(gate.get("result") or "NONE"), fg=GOOD if green else (BAD if gate.get("result") == "FAIL" else WARN))
        self.card_values["components"].configure(text=str(scan.get("componentCount", 0)), fg=GOOD if scan.get("componentCount", 0) else WARN)
        self.card_values["patches"].configure(text=str(status.get("patchCandidates", 0)))
        unresolved = scan.get("unresolved") or []
        summary = [
            f"Root          : {self.root_path}",
            f"Project UUID  : {p.get('uuid') or '(run install/init to assign)'}",
            f"Kind          : {p.get('kind') or 'generic'}",
            f"Provider      : {provider.get('name') or provider.get('type') or 'ForgePY auto'}",
            f"Provider src  : {(status.get('discovery') or {}).get('source') or 'forgepy-generated'}",
            f"Components    : {scan.get('componentCount', 0)}  ({', '.join(scan.get('kinds') or []) or 'none'})",
            f"Discovery     : {'cache hit' if scan.get('cacheHit') else 'fresh scan'} / {scan.get('markerCount', 0)} marker(s) / {len(unresolved)} unresolved",
            f"Git           : {'ready' if g.get('ready') else 'unavailable'} / {'clean' if g.get('clean') else 'modified'}",
            f"Operations    : {status.get('operations', 0)}",
            f"Patch inbox   : {status.get('patchCandidates', 0)}",
        ]
        self.dashboard_summary.configure(text="\n".join(summary))
        self.footer.configure(text=f"{'BUSY' if self.busy else 'Ready'}  |  {scan.get('componentCount',0)} components  |  {provider.get('type') or 'forgepy-auto'}  |  ForgePY {status.get('runtime',{}).get('version','')}")
        self._render_operations()
        for item in self.patch_tree.get_children(): self.patch_tree.delete(item)
        for idx, row in enumerate(patches):
            digest = row.get("sha256") or row.get("hashStatus") or "deferred"
            self.patch_tree.insert("", "end", iid=str(idx), values=(row.get("path"), row.get("kind"), row.get("bytes"), digest))
        self.git_summary.configure(text=(
            f"Branch: {g.get('branch') or '(detached)'}    HEAD: {head or '—'}    "
            f"Staged: {g.get('staged',0)}    Unstaged: {g.get('unstaged',0)}    Untracked: {g.get('untracked',0)}    "
            f"Ahead/Behind: {g.get('ahead')}/{g.get('behind')}"
        ))
        for item in self.git_tree.get_children(): self.git_tree.delete(item)
        for idx, row in enumerate(history):
            self.git_tree.insert("", "end", iid=str(idx), values=(str(row.get("sha") or "")[:10], row.get("date"), row.get("subject")))
        self._refresh_build_plan_view()
        self._refresh_recovery_view()
        self._refresh_settings_view()

    def _refresh_recovery_view(self) -> None:
        sdir = self.state_dir()
        blocks = []
        for title, name in (("LAST GREEN", "last-green.json"), ("LAST GATE", "last-gate.json"), ("LAST FAILURE", "last-failure.json")):
            p = sdir / name
            blocks.append(title)
            if p.is_file():
                try: blocks.append(json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2)[:7000])
                except Exception as exc: blocks.append(f"Unreadable: {exc}")
            else: blocks.append("(none)")
            blocks.append("")
        self._set_text(self.recovery_text, "\n".join(blocks))

    def _refresh_settings_view(self) -> None:
        p = self.status.get("project") or {}
        d = self.status.get("discovery") or {}
        caps = self.status.get("capabilities") or []
        scan = self.status.get("scan") or {}
        lines = [
            f"Project root      : {self.root_path}",
            f"Project ID        : {p.get('id')}",
            f"Project UUID      : {p.get('uuid') or '(not initialized)'}",
            f"Project kind      : {p.get('kind')}",
            f"Provider          : {d.get('providerName') or d.get('provider')}",
            f"Provider source   : {d.get('source')}",
            f"Provider priority : {d.get('precedence')}",
            f"Precedence order  : {' > '.join(d.get('precedenceOrder') or [])}",
            f"Scan cache        : {'HIT' if scan.get('cacheHit') else 'FRESH'}",
            f"Scan components   : {scan.get('componentCount', 0)}",
            f"Scan markers      : {scan.get('markerCount', 0)}",
            f"Scan signature    : {scan.get('signature')}",
            "",
            "CAPABILITIES",
        ]
        for cap in caps:
            evidence = ", ".join(str(x) for x in cap.get("evidence") or [])
            lines.append(f"  {cap.get('key',''):<24} {cap.get('confidence',''):<10} {cap.get('label','')}  [{evidence}]")
        self._set_text(self.settings_text, "\n".join(lines))

    def run_selected_operation(self) -> None:
        sel = self.ops_tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select an operation first.")
            return
        row = self.operation_rows[int(sel[0])]
        key = str(row.get("key") or "")
        if not key:
            return
        risk = str(row.get("risk") or "read")
        if risk == "danger" and not messagebox.askyesno(APP_TITLE, f"Run dangerous operation {key}?"):
            return
        self.run_backend(key)

    def selected_patch(self) -> dict[str, Any] | None:
        sel = self.patch_tree.selection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select a patch first.")
            return None
        return self.patch_rows[int(sel[0])]

    def validate_selected_patch(self) -> None:
        row = self.selected_patch()
        if row:
            self.run_backend("patch-check", str(row.get("path") or ""))

    def apply_selected_patch(self) -> None:
        row = self.selected_patch()
        if not row: return
        path = str(row.get("path") or "")
        if row.get("kind") != "unified-diff":
            messagebox.showinfo(APP_TITLE, "Generic ForgePY only applies raw .patch files. ZIP transports must go through a project-owned provider.")
            return
        if not messagebox.askyesno(APP_TITLE, f"Validate and apply this patch?\n\n{path}\n\nThe patch will be archived with a lineage receipt."):
            return
        self.run_backend("patch-apply", path)

    def commit_green(self) -> None:
        message = simpledialog.askstring(APP_TITLE, "Commit message (leave blank for ForgePY default):", parent=self.window)
        if message is None:
            return
        args = ("commit-green", message) if message.strip() else ("commit-green",)
        self.run_backend(*args)

    def set_busy(self, value: bool) -> None:
        self.busy = value
        state = "disabled" if value else "normal"
        for widget in self.action_buttons:
            try: widget.configure(state=state)
            except tk.TclError: pass
        if hasattr(self, "cancel_button"):
            self.cancel_button.configure(state="normal" if value else "disabled")
        self.footer.configure(text="Operation running…" if value else "Ready")

    def cancel_backend(self) -> None:
        proc = self.proc
        if not proc or proc.poll() is not None:
            return
        if not messagebox.askyesno(APP_TITLE, "Cancel the running ForgePY operation and its child processes?"):
            return
        self.append_log("[GUI] Cancellation requested; terminating backend process tree…\n")
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                os.killpg(proc.pid, signal.SIGTERM)
        except Exception as exc:
            self.append_log(f"[GUI WARN] Tree cancellation failed: {exc}; terminating backend process directly.\n")
            try: proc.terminate()
            except Exception: pass

    def append_log(self, text: str) -> None:
        self.log_text.insert("end", text)
        self._log_chunks += 1
        if self._log_chunks % 200 == 0:
            try:
                lines = int(self.log_text.index("end-1c").split(".", 1)[0])
                if lines > 20000:
                    self.log_text.delete("1.0", f"{lines - 16000}.0")
            except Exception:
                pass
        self.log_text.see("end")

    def run_backend(self, *args: str) -> None:
        if self.busy:
            messagebox.showinfo(APP_TITLE, "Another ForgePY operation is already running in this GUI.")
            return
        self.show_page("Logs")
        self.set_busy(True)
        self.append_log(f"\n> ForgePY {' '.join(args)}\n")
        def worker() -> None:
            creationflags = 0
            popen_extra: dict[str, Any] = {}
            if os.name == "nt":
                creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) | int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            else:
                popen_extra["start_new_session"] = True
            try:
                self.proc = subprocess.Popen(
                    backend_argv(self.root_path, *args), cwd=str(self.root_path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=creationflags, **popen_extra,
                )
                assert self.proc.stdout is not None
                for line in self.proc.stdout:
                    self.output_queue.put(("log", line))
                code = self.proc.wait()
                self.output_queue.put(("done", (args, code)))
            except Exception as exc:
                self.output_queue.put(("error", str(exc)))
                self.output_queue.put(("done", (args, 2)))
            finally:
                self.proc = None
        threading.Thread(target=worker, daemon=True, name="forgepy-gui-operation").start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.output_queue.get_nowait()
                if kind == "log": self.append_log(str(payload))
                elif kind == "error":
                    self.append_log(f"[GUI ERROR] {payload}\n")
                    messagebox.showerror(APP_TITLE, str(payload))
                elif kind == "done":
                    args, code = payload
                    self.append_log(f"[GUI] Exit code: {code}\n")
                    self.set_busy(False)
                    self.refresh_all()
                elif kind == "refresh":
                    self.refreshing = False
                    self._apply_refresh(payload)
                    if self.refresh_pending:
                        self.refresh_pending = False
                        self.window.after(20, self.refresh_all)
                elif kind == "refresh_error":
                    self.refreshing = False
                    self.append_log(f"[GUI ERROR] Refresh failed: {payload}\n")
                    self.footer.configure(text="Refresh failed — see Logs")
                    if self.refresh_pending:
                        self.refresh_pending = False
                        self.window.after(20, self.refresh_all)
        except queue.Empty:
            pass
        self.window.after(100, self._poll_queue)

    def on_close(self) -> None:
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno(APP_TITLE, "A ForgePY operation is running. Close the GUI and leave the backend operation running?"):
                return
        self.window.destroy()

    def run(self) -> int:
        self.window.mainloop()
        return 0


def cli_fallback(root: Path, reason: object | None = None) -> int:
    why = reason if reason is not None else tkinter_error
    print(f"[WARN] ForgePY GUI unavailable: {why}")
    print("[INFO] Falling back to the console Project Control Center.")
    return subprocess.call(backend_argv(root, "menu"), cwd=str(root))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ForgePY graphical Project Control Center")
    ap.add_argument("--root", default=os.getcwd())
    ns = ap.parse_args(argv)
    root = Path(ns.root).resolve()
    if tk is None:
        return cli_fallback(root)
    try:
        return PCCApp(root).run()
    except Exception as exc:
        # Importing tkinter is not enough on headless/minimal environments; window creation can still fail.
        return cli_fallback(root, exc)


if __name__ == "__main__":
    raise SystemExit(main())
