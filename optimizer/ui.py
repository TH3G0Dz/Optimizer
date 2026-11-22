import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .apps import list_installed_apps, open_windows_apps_settings
from .importance import classify
from .scanner import format_size, list_children, list_drives


class OptimizerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Optimizer")
        self.geometry("1180x700")
        self.minsize(850, 500)
        self.paths: dict[str, Path] = {}
        self.loaded: set[str] = set()
        self.status = tk.StringVar(value="Selecione uma pasta para começar.")
        self._build_ui()
        self._load_drives()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Optimizer", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(header, text="Inventário local; nenhuma exclusão automática.").pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        files_tab = ttk.Frame(notebook)
        apps_tab = ttk.Frame(notebook)
        notebook.add(files_tab, text="Arquivos")
        notebook.add(apps_tab, text="Aplicativos")
        self._build_files_tab(files_tab)
        self._build_apps_tab(apps_tab)
        ttk.Label(self, textvariable=self.status, padding=(12, 4)).pack(fill="x")

    def _build_files_tab(self, parent: ttk.Frame) -> None:
        columns = ("size", "importance", "reason")
        self.file_tree = ttk.Treeview(parent, columns=columns, show="tree headings")
        self.file_tree.heading("#0", text="Pasta ou arquivo")
        self.file_tree.heading("size", text="Tamanho")
        self.file_tree.heading("importance", text="Importância")
        self.file_tree.heading("reason", text="Motivo")
        self.file_tree.column("#0", width=330)
        self.file_tree.column("size", width=100, anchor="e")
        self.file_tree.column("importance", width=100, anchor="center")
        self.file_tree.column("reason", width=450)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        self.file_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.file_tree.bind("<<TreeviewOpen>>", self._on_open)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_apps_tab(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, padding=8)
        actions.pack(fill="x")
        ttk.Button(actions, text="Carregar aplicativos", command=self._load_apps).pack(side="left")
        ttk.Button(actions, text="Abrir desinstalação do Windows", command=self._open_apps_settings).pack(side="left", padx=8)
        ttk.Label(actions, text="Resíduos serão analisados em uma versão futura.").pack(side="right")
        columns = ("publisher", "version", "location")
        self.apps_tree = ttk.Treeview(parent, columns=columns, show="tree headings")
        self.apps_tree.heading("#0", text="Aplicativo")
        self.apps_tree.heading("publisher", text="Publicador")
        self.apps_tree.heading("version", text="Versão")
        self.apps_tree.heading("location", text="Local")
        self.apps_tree.column("#0", width=300)
        self.apps_tree.column("publisher", width=220)
        self.apps_tree.column("version", width=120)
        self.apps_tree.column("location", width=450)
        self.apps_tree.pack(fill="both", expand=True)

    def _load_drives(self) -> None:
        for drive in list_drives():
            result = classify(drive, is_dir=True)
            item = self.file_tree.insert("", "end", text=str(drive), values=("", result.importance.value, result.reason))
            self.paths[item] = drive
            self.file_tree.insert(item, "end", text="Carregando...")

    def _on_open(self, _event=None) -> None:
        item = self.file_tree.focus()
        if not item or item in self.loaded or item not in self.paths:
            return
        self.loaded.add(item)
        self.status.set(f"Lendo {self.paths[item]}...")
        threading.Thread(target=self._read_folder, args=(item, self.paths[item]), daemon=True).start()

    def _read_folder(self, item: str, path: Path) -> None:
        try:
            entries = list_children(path)
            self.after(0, self._show_entries, item, entries, None)
        except OSError as error:
            self.after(0, self._show_entries, item, [], str(error))

    def _show_entries(self, parent: str, entries: list, error: str | None) -> None:
        for child in self.file_tree.get_children(parent):
            self.file_tree.delete(child)
        if error:
            self.file_tree.insert(parent, "end", text="Acesso indisponível", values=("", "Revisar", error))
            self.status.set(error)
            return
        for entry in entries:
            item = self.file_tree.insert(
                parent,
                "end",
                text=entry.path.name or str(entry.path),
                values=(format_size(entry.size), entry.classification.importance.value, entry.classification.reason),
            )
            self.paths[item] = entry.path
            if entry.is_dir:
                self.file_tree.insert(item, "end", text="Carregando...")
        self.status.set(f"{len(entries)} itens em {self.paths[parent]}")

    def _on_select(self, _event=None) -> None:
        selected = self.file_tree.selection()
        if selected and selected[0] in self.paths:
            self.status.set(str(self.paths[selected[0]]))

    def _load_apps(self) -> None:
        self.status.set("Lendo aplicativos registrados...")
        threading.Thread(target=self._read_apps, daemon=True).start()

    def _read_apps(self) -> None:
        apps = list_installed_apps()
        self.after(0, self._show_apps, apps)

    def _show_apps(self, apps: list) -> None:
        self.apps_tree.delete(*self.apps_tree.get_children())
        for app in apps:
            self.apps_tree.insert("", "end", text=app.name, values=(app.publisher, app.version, app.location))
        self.status.set(f"{len(apps)} aplicativos encontrados.")

    def _open_apps_settings(self) -> None:
        try:
            open_windows_apps_settings()
        except OSError as error:
            messagebox.showerror("Optimizer", str(error))


def run() -> None:
    OptimizerApp().mainloop()

