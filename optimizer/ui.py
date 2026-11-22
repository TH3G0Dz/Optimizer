import threading
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import messagebox, ttk

from .apps import (
    delete_leftover_folder,
    list_desktop_apps,
    list_installed_apps,
    open_windows_apps_settings,
    review_leftover_folder,
    uninstall_app,
)
from .cleanup import delete_files, review_files
from .importance import classify
from .models import InstalledApp, SystemFeature
from .scanner import format_size, list_children, list_drives
from .system import (
    list_drive_usage,
    list_system_features,
    open_optimize_drives,
    open_startup_settings,
    open_storage_settings,
    open_system_feature,
    open_task_manager,
)


class OptimizerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Optimizer")
        self.geometry("1180x700")
        self.minsize(850, 500)
        self.paths: dict[str, Path] = {}
        self.loaded: set[str] = set()
        self.apps_by_item: dict[str, InstalledApp] = {}
        self.pending_leftovers: dict[str, InstalledApp] = {}
        self.features_by_item: dict[str, SystemFeature] = {}
        self.status = tk.StringVar(value="Selecione uma pasta para começar.")
        self._build_ui()
        self._load_drives()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="Optimizer", font=("Segoe UI", 20, "bold")).pack(
            side="left"
        )
        ttk.Label(
            header, text="Exclusão permanente somente após revisão e confirmação."
        ).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        files_tab = ttk.Frame(notebook)
        apps_tab = ttk.Frame(notebook)
        optimization_tab = ttk.Frame(notebook)
        functions_tab = ttk.Frame(notebook)
        notebook.add(files_tab, text="Arquivos")
        notebook.add(apps_tab, text="Aplicativos")
        notebook.add(optimization_tab, text="Otimização")
        notebook.add(functions_tab, text="Funções")
        self._build_files_tab(files_tab)
        self._build_apps_tab(apps_tab)
        self._build_optimization_tab(optimization_tab)
        self._build_functions_tab(functions_tab)
        ttk.Label(self, textvariable=self.status, padding=(12, 4)).pack(fill="x")

    def _build_files_tab(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, padding=8)
        actions.pack(fill="x")
        self.review_button = ttk.Button(
            actions,
            text="Revisar arquivos selecionados",
            command=self._review_selected,
            state="disabled",
        )
        self.review_button.pack(side="left")
        ttk.Label(
            actions, text="Pastas e arquivos críticos permanecem protegidos."
        ).pack(side="right")

        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        columns = ("size", "importance", "reason")
        self.file_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="extended"
        )
        self.file_tree.heading("#0", text="Pasta ou arquivo")
        self.file_tree.heading("size", text="Tamanho")
        self.file_tree.heading("importance", text="Importância")
        self.file_tree.heading("reason", text="Motivo")
        self.file_tree.column("#0", width=330)
        self.file_tree.column("size", width=100, anchor="e")
        self.file_tree.column("importance", width=100, anchor="center")
        self.file_tree.column("reason", width=450)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        self.file_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.file_tree.bind("<<TreeviewOpen>>", self._on_open)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_apps_tab(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, padding=8)
        actions.pack(fill="x")
        ttk.Button(actions, text="Atualizar aplicativos", command=self._load_apps).pack(
            side="left"
        )
        self.uninstall_button = ttk.Button(
            actions,
            text="Desinstalar selecionado",
            command=self._uninstall_selected,
            state="disabled",
        )
        self.uninstall_button.pack(side="left", padx=4)
        self.leftover_button = ttk.Button(
            actions,
            text="Revisar pasta residual",
            command=self._delete_leftover_selected,
            state="disabled",
        )
        self.leftover_button.pack(side="left", padx=4)
        ttk.Button(
            actions,
            text="Configurações do Windows",
            command=self._open_apps_settings,
        ).pack(side="left", padx=4)
        columns = ("source", "publisher", "version", "status")
        self.apps_tree = ttk.Treeview(
            parent, columns=columns, show="tree headings", selectmode="browse"
        )
        self.apps_tree.heading("#0", text="Aplicativo")
        self.apps_tree.heading("source", text="Tipo")
        self.apps_tree.heading("publisher", text="Publicador")
        self.apps_tree.heading("version", text="Versão")
        self.apps_tree.heading("status", text="Pasta ou proteção")
        self.apps_tree.column("#0", width=260)
        self.apps_tree.column("source", width=90, anchor="center")
        self.apps_tree.column("publisher", width=180)
        self.apps_tree.column("version", width=100)
        self.apps_tree.column("status", width=470)
        self.apps_tree.pack(fill="both", expand=True)
        self.apps_tree.bind("<<TreeviewSelect>>", self._on_app_select)
        self._load_apps()

    def _build_optimization_tab(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, padding=8)
        actions.pack(fill="x")
        ttk.Button(
            actions, text="Atualizar discos", command=self._load_drive_usage
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Armazenamento do Windows",
            command=self._open_storage_settings,
        ).pack(side="left", padx=4)
        ttk.Button(
            actions, text="Apps de inicialização", command=self._open_startup_settings
        ).pack(side="left", padx=4)
        ttk.Button(
            actions, text="Gerenciador de Tarefas", command=self._open_task_manager
        ).pack(side="left", padx=4)
        ttk.Button(
            actions, text="Otimizar unidades", command=self._open_optimize_drives
        ).pack(side="left", padx=4)
        columns = ("total", "used", "free", "percent")
        self.drives_tree = ttk.Treeview(parent, columns=columns, show="tree headings")
        self.drives_tree.heading("#0", text="Unidade")
        self.drives_tree.heading("total", text="Total")
        self.drives_tree.heading("used", text="Usado")
        self.drives_tree.heading("free", text="Livre")
        self.drives_tree.heading("percent", text="Uso")
        self.drives_tree.column("#0", width=240)
        for column in columns:
            self.drives_tree.column(column, width=140, anchor="e")
        self.drives_tree.pack(fill="both", expand=True)
        self._load_drive_usage()

    def _build_functions_tab(self, parent: ttk.Frame) -> None:
        actions = ttk.Frame(parent, padding=8)
        actions.pack(fill="x")
        self.open_feature_button = ttk.Button(
            actions,
            text="Abrir configuração selecionada",
            command=self._open_selected_feature,
            state="disabled",
        )
        self.open_feature_button.pack(side="left")
        ttk.Label(
            actions,
            text="Ajustes oficiais do Windows; serviços críticos não são alterados automaticamente.",
        ).pack(side="right")
        columns = ("effect", "risk")
        self.functions_tree = ttk.Treeview(
            parent, columns=columns, show="tree headings", selectmode="browse"
        )
        self.functions_tree.heading("#0", text="Função")
        self.functions_tree.heading("effect", text="Possível benefício")
        self.functions_tree.heading("risk", text="Risco")
        self.functions_tree.column("#0", width=260)
        self.functions_tree.column("effect", width=650)
        self.functions_tree.column("risk", width=100, anchor="center")
        self.functions_tree.pack(fill="both", expand=True)
        self.functions_tree.bind("<<TreeviewSelect>>", self._on_feature_select)
        for feature in list_system_features():
            item = self.functions_tree.insert(
                "", "end", text=feature.name, values=(feature.effect, feature.risk)
            )
            self.features_by_item[item] = feature

    def _load_drives(self) -> None:
        for drive in list_drives():
            result = classify(drive, is_dir=True)
            item = self.file_tree.insert(
                "",
                "end",
                text=str(drive),
                values=("", result.importance.value, result.reason),
            )
            self.paths[item] = drive
            self.file_tree.insert(item, "end", text="Carregando...")

    def _on_open(self, _event=None) -> None:
        item = self.file_tree.focus()
        if not item or item in self.loaded or item not in self.paths:
            return
        self.loaded.add(item)
        self.status.set(f"Lendo {self.paths[item]}...")
        threading.Thread(
            target=self._read_folder, args=(item, self.paths[item]), daemon=True
        ).start()

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
            self.file_tree.insert(
                parent, "end", text="Acesso indisponível", values=("", "Revisar", error)
            )
            self.status.set(error)
            return
        for entry in entries:
            item = self.file_tree.insert(
                parent,
                "end",
                text=entry.path.name or str(entry.path),
                values=(
                    format_size(entry.size),
                    entry.classification.importance.value,
                    entry.classification.reason,
                ),
            )
            self.paths[item] = entry.path
            if entry.is_dir:
                self.file_tree.insert(item, "end", text="Carregando...")
        self.status.set(f"{len(entries)} itens em {self.paths[parent]}")

    def _on_select(self, _event=None) -> None:
        selected = self.file_tree.selection()
        paths = [self.paths[item] for item in selected if item in self.paths]
        can_review = (
            bool(paths)
            and len(paths) == len(selected)
            and all(path.is_file() and not path.is_symlink() for path in paths)
        )
        self.review_button.configure(state="normal" if can_review else "disabled")
        if paths:
            self.status.set(
                str(paths[0])
                if len(paths) == 1
                else f"{len(paths)} arquivos selecionados."
            )

    def _review_selected(self) -> None:
        selected = self.file_tree.selection()
        items = [item for item in selected if item in self.paths]
        if not items:
            return
        try:
            reviews = review_files(self.paths[item] for item in items)
        except (OSError, ValueError) as error:
            messagebox.showerror("Optimizer", str(error), parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title("Revisar arquivo")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        content = ttk.Frame(dialog, padding=18)
        content.pack(fill="both", expand=True)
        total_size = sum(review.size for review in reviews)
        ttk.Label(
            content,
            text=f"{len(reviews)} arquivo(s) • {format_size(total_size)}",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        review_tree = ttk.Treeview(
            content,
            columns=("size", "importance", "reason"),
            show="tree headings",
            height=min(12, len(reviews)),
        )
        review_tree.heading("#0", text="Arquivo")
        review_tree.heading("size", text="Tamanho")
        review_tree.heading("importance", text="Importância")
        review_tree.heading("reason", text="Motivo")
        review_tree.column("#0", width=360)
        review_tree.column("size", width=100, anchor="e")
        review_tree.column("importance", width=100, anchor="center")
        review_tree.column("reason", width=360)
        for review in reviews:
            review_tree.insert(
                "",
                "end",
                text=str(review.path),
                values=(
                    format_size(review.size),
                    review.classification.importance.value,
                    review.classification.reason,
                ),
            )
        review_tree.pack(fill="both", expand=True, pady=12)
        ttk.Label(
            content,
            text="A exclusão será permanente. Confirme somente se reconhece os arquivos.",
            wraplength=700,
        ).pack(anchor="w")
        buttons = ttk.Frame(content)
        buttons.pack(anchor="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(
            side="left", padx=6
        )
        ttk.Button(
            buttons,
            text="Excluir permanentemente",
            command=lambda: self._confirm_delete(dialog, items, reviews),
        ).pack(side="left")

    def _confirm_delete(
        self, dialog: tk.Toplevel, items: list[str], reviews: list
    ) -> None:
        confirmed = messagebox.askyesno(
            "Confirmar exclusão permanente",
            f"Você tem certeza que deseja excluir permanentemente {len(reviews)} arquivo(s) selecionado(s)?\n\nEsta ação não pode ser desfeita.",
            icon="warning",
            parent=dialog,
        )
        if not confirmed:
            return
        deleted, failures = delete_files(review.path for review in reviews)
        deleted_set = set(deleted)
        for item in items:
            path = self.paths.get(item)
            if path and path.resolve() in deleted_set:
                self.paths.pop(item, None)
                self.file_tree.delete(item)
        dialog.destroy()
        self.status.set(
            f"{len(deleted)} arquivo(s) excluído(s); {len(failures)} falha(s)."
        )
        if failures:
            details = "\n".join(f"{path}: {error}" for path, error in failures[:5])
            messagebox.showwarning(
                "Optimizer",
                f"Alguns arquivos não foram excluídos:\n\n{details}",
                parent=self,
            )
        else:
            messagebox.showinfo(
                "Optimizer",
                f"{len(deleted)} arquivo(s) excluído(s) permanentemente.",
                parent=self,
            )

    def _load_drive_usage(self) -> None:
        threading.Thread(target=self._read_drive_usage, daemon=True).start()

    def _read_drive_usage(self) -> None:
        drives = list_drive_usage()
        self.after(0, self._show_drive_usage, drives)

    def _show_drive_usage(self, drives: list) -> None:
        self.drives_tree.delete(*self.drives_tree.get_children())
        for drive in drives:
            percent = (drive.used / drive.total * 100) if drive.total else 0
            self.drives_tree.insert(
                "",
                "end",
                text=str(drive.path),
                values=(
                    format_size(drive.total),
                    format_size(drive.used),
                    format_size(drive.free),
                    f"{percent:.1f}%",
                ),
            )

    def _open_storage_settings(self) -> None:
        open_storage_settings()

    def _open_startup_settings(self) -> None:
        open_startup_settings()

    def _open_task_manager(self) -> None:
        open_task_manager()

    def _open_optimize_drives(self) -> None:
        open_optimize_drives()

    def _load_apps(self) -> None:
        self.status.set("Lendo aplicativos registrados...")
        self.uninstall_button.configure(state="disabled")
        self.leftover_button.configure(state="disabled")
        threading.Thread(target=self._read_apps, daemon=True).start()

    def _read_apps(self) -> None:
        apps = list_installed_apps()
        self.after(0, self._show_apps, apps)

    def _show_apps(self, apps: list[InstalledApp]) -> None:
        self.apps_tree.delete(*self.apps_tree.get_children())
        self.apps_by_item.clear()
        display_apps = list(apps)
        installed_ids = {app.identifier for app in apps}
        for pending in self.pending_leftovers.values():
            if pending.identifier not in installed_ids and pending.location:
                display_apps.append(
                    replace(
                        pending,
                        removable=False,
                        protected_reason="Desinstalado; pasta residual disponível para revisão.",
                    )
                )
        display_apps.sort(key=lambda app: (app.name.casefold(), app.source))
        for app in display_apps:
            status = app.protected_reason or app.location or "Pasta não informada"
            item = self.apps_tree.insert(
                "",
                "end",
                text=app.name,
                values=(app.source, app.publisher, app.version, status),
            )
            self.apps_by_item[item] = app
        self.status.set(f"{len(display_apps)} aplicativos encontrados.")

    def _selected_app(self) -> InstalledApp | None:
        selected = self.apps_tree.selection()
        return self.apps_by_item.get(selected[0]) if selected else None

    def _on_app_select(self, _event=None) -> None:
        app = self._selected_app()
        self.uninstall_button.configure(
            state="normal" if app and app.removable else "disabled"
        )
        self.leftover_button.configure(
            state=(
                "normal"
                if app and app.source == "Desktop" and app.location
                else "disabled"
            )
        )
        if app:
            self.status.set(app.protected_reason or app.location or app.name)

    def _uninstall_selected(self) -> None:
        app = self._selected_app()
        if not app or not app.removable:
            return
        if not messagebox.askyesno(
            "Confirmar desinstalação",
            f"Você tem certeza que deseja desinstalar {app.name}?\n\n"
            "O desinstalador oficial será executado. Dados do aplicativo podem permanecer.",
            icon="warning",
            parent=self,
        ):
            return
        self.uninstall_button.configure(state="disabled")
        self.status.set(f"Iniciando desinstalação de {app.name}...")
        threading.Thread(target=self._run_uninstall, args=(app,), daemon=True).start()

    def _run_uninstall(self, app: InstalledApp) -> None:
        error = None
        try:
            uninstall_app(app)
        except (OSError, ValueError) as caught:
            error = str(caught)
        self.after(0, self._finish_uninstall, app, error)

    def _finish_uninstall(self, app: InstalledApp, error: str | None) -> None:
        if error:
            messagebox.showerror("Optimizer", error, parent=self)
            self._on_app_select()
            return
        if app.source == "Windows":
            messagebox.showinfo(
                "Optimizer",
                f"{app.name} foi removido para o usuário atual.",
                parent=self,
            )
            self._load_apps()
            return
        if app.location:
            self.pending_leftovers[app.identifier] = app
        self.status.set(
            "Desinstalador aberto. Conclua-o e depois revise a pasta residual."
        )
        messagebox.showinfo(
            "Optimizer",
            "O desinstalador oficial foi aberto. Conclua o processo e depois use "
            "Revisar pasta residual.",
            parent=self,
        )
        self._on_app_select()

    def _delete_leftover_selected(self) -> None:
        app = self._selected_app()
        if not app:
            return
        installed = list_desktop_apps()
        try:
            folder = review_leftover_folder(app, installed)
        except (OSError, ValueError) as error:
            messagebox.showerror("Optimizer", str(error), parent=self)
            return
        if not messagebox.askyesno(
            "Confirmar exclusão permanente",
            "Você tem certeza que deseja excluir permanentemente a pasta residual?\n\n"
            f"{folder}\n\nEsta ação não pode ser desfeita.",
            icon="warning",
            parent=self,
        ):
            return
        self.leftover_button.configure(state="disabled")
        self.status.set(f"Excluindo pasta residual {folder}...")
        threading.Thread(
            target=self._run_leftover_delete,
            args=(app, installed),
            daemon=True,
        ).start()

    def _run_leftover_delete(
        self, app: InstalledApp, installed: list[InstalledApp]
    ) -> None:
        deleted = None
        error = None
        try:
            deleted = delete_leftover_folder(app, installed)
        except (OSError, ValueError) as caught:
            error = str(caught)
        self.after(0, self._finish_leftover_delete, app, deleted, error)

    def _finish_leftover_delete(
        self, app: InstalledApp, deleted: Path | None, error: str | None
    ) -> None:
        if error:
            messagebox.showerror("Optimizer", error, parent=self)
            self._on_app_select()
            return
        self.pending_leftovers.pop(app.identifier, None)
        self.status.set(f"Pasta residual excluída: {deleted}")
        messagebox.showinfo(
            "Optimizer", f"Pasta residual excluída:\n\n{deleted}", parent=self
        )
        self._load_apps()

    def _open_apps_settings(self) -> None:
        try:
            open_windows_apps_settings()
        except OSError as error:
            messagebox.showerror("Optimizer", str(error))

    def _on_feature_select(self, _event=None) -> None:
        selected = self.functions_tree.selection()
        self.open_feature_button.configure(
            state="normal"
            if selected and selected[0] in self.features_by_item
            else "disabled"
        )

    def _open_selected_feature(self) -> None:
        selected = self.functions_tree.selection()
        if not selected:
            return
        feature = self.features_by_item.get(selected[0])
        if not feature:
            return
        try:
            open_system_feature(feature)
        except OSError as error:
            messagebox.showerror("Optimizer", str(error), parent=self)


def run() -> None:
    OptimizerApp().mainloop()
