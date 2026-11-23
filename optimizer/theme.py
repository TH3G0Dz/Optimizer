import tkinter as tk
from tkinter import ttk

BACKGROUND = "#0B1220"
SURFACE = "#111A2C"
SURFACE_RAISED = "#17243A"
BORDER = "#253654"
TEXT = "#F4F7FC"
MUTED = "#A8B4C7"
ACCENT = "#4F8CFF"
ACCENT_HOVER = "#6EA2FF"
DANGER = "#EF6262"
SUCCESS = "#39C98A"
WARNING = "#F5B84B"


def apply_theme(root: tk.Tk) -> None:
    root.configure(background=BACKGROUND)
    root.option_add("*Font", ("Segoe UI", 10))
    root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BACKGROUND, foreground=TEXT)
    style.configure("TFrame", background=BACKGROUND)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("Card.TFrame", background=SURFACE_RAISED, relief="flat")

    style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
    style.configure(
        "Brand.TLabel",
        background=SURFACE,
        foreground=ACCENT_HOVER,
        font=("Segoe UI Semibold", 9),
    )
    style.configure(
        "Title.TLabel",
        background=SURFACE,
        foreground=TEXT,
        font=("Segoe UI Semibold", 21),
    )
    style.configure(
        "Subtitle.TLabel",
        background=SURFACE,
        foreground=MUTED,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Section.TLabel",
        background=BACKGROUND,
        foreground=TEXT,
        font=("Segoe UI Semibold", 14),
    )
    style.configure("Muted.TLabel", background=BACKGROUND, foreground=MUTED)
    style.configure("SurfaceMuted.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("CardTitle.TLabel", background=SURFACE_RAISED, foreground=MUTED)
    style.configure(
        "CardValue.TLabel",
        background=SURFACE_RAISED,
        foreground=TEXT,
        font=("Segoe UI Semibold", 18),
    )
    style.configure("Status.TLabel", background=SURFACE, foreground=MUTED)
    style.configure(
        "Safe.TLabel",
        background=SURFACE,
        foreground=SUCCESS,
        font=("Segoe UI Semibold", 9),
    )

    style.configure(
        "TButton",
        background=SURFACE_RAISED,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=SURFACE_RAISED,
        darkcolor=SURFACE_RAISED,
        padding=(13, 8),
        relief="flat",
        focusthickness=2,
        focuscolor=ACCENT,
    )
    style.map(
        "TButton",
        background=[("active", BORDER), ("disabled", SURFACE)],
        foreground=[("disabled", "#65738A")],
    )
    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#FFFFFF",
        bordercolor=ACCENT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_HOVER), ("disabled", "#294770")],
        foreground=[("disabled", "#8296B4")],
    )
    style.configure(
        "Danger.TButton",
        background=DANGER,
        foreground="#FFFFFF",
        bordercolor=DANGER,
        lightcolor=DANGER,
        darkcolor=DANGER,
    )
    style.map(
        "Danger.TButton",
        background=[
            ("disabled", "#4A2B36"),
            ("active", "#FF7777"),
        ],
        foreground=[("disabled", "#9C7781")],
    )

    style.configure("TNotebook", background=BACKGROUND, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=BACKGROUND,
        foreground=MUTED,
        borderwidth=0,
        padding=(18, 11),
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE_RAISED), ("active", SURFACE)],
        foreground=[("selected", TEXT), ("active", TEXT)],
    )

    style.configure(
        "Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        rowheight=31,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#244E86")],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure(
        "Treeview.Heading",
        background=SURFACE_RAISED,
        foreground=MUTED,
        bordercolor=BORDER,
        lightcolor=SURFACE_RAISED,
        darkcolor=SURFACE_RAISED,
        padding=(10, 9),
        relief="flat",
        font=("Segoe UI Semibold", 9),
    )
    style.map("Treeview.Heading", background=[("active", BORDER)])

    style.configure(
        "TEntry",
        fieldbackground=SURFACE_RAISED,
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=(10, 8),
    )
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE_RAISED,
        background=SURFACE_RAISED,
        foreground=TEXT,
        arrowcolor=MUTED,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=(8, 6),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE_RAISED)],
        foreground=[("readonly", TEXT)],
    )
    style.configure(
        "Accent.Horizontal.TProgressbar",
        background=ACCENT,
        troughcolor=SURFACE,
        bordercolor=SURFACE,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=9,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=SURFACE_RAISED,
        troughcolor=BACKGROUND,
        bordercolor=BACKGROUND,
        arrowcolor=MUTED,
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=SURFACE_RAISED,
        troughcolor=BACKGROUND,
        bordercolor=BACKGROUND,
        arrowcolor=MUTED,
    )
