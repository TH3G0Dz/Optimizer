import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import __version__
from .apps import (
    APP_FILTERS,
    delete_leftover_folder,
    list_desktop_apps,
    list_installed_apps,
    open_windows_apps_settings,
    prepare_installed_apps,
    review_leftover_folder,
    uninstall_app,
)
from .cleanup import delete_files, review_files
from .importance import classify
from .models import AppInventory, Importance, InstalledApp, SystemFeature
from .scanner import filter_entries, format_size, list_children, list_drives
from .system import (
    list_drive_usage,
    list_system_features,
    open_optimize_drives,
    open_startup_settings,
    open_storage_settings,
    open_system_feature,
    open_task_manager,
)
from .theme import apply_theme

FILE_IMPORTANCE_OPTIONS = ("Todas", "Baixo", "Revisar", "Médio", "Alto", "Crítico")
FILE_SIZE_OPTIONS = {
    "Qualquer tamanho": 0,
    "1 MB+": 1024**2,
    "100 MB+": 100 * 1024**2,
    "1 GB+": 1024**3,
}
FILE_SORT_OPTIONS = ("Nome", "Maior primeiro", "Menor primeiro")


class OptimizerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        apply_theme(self)
        self.title("Optimizer")
        self.geometry("1280x760")
        self.minsize(960, 620)
        self.paths: dict[str, Path] = {}
        self.loaded: set[str] = set()
        self.folder_items: set[str] = set()
        self.folder_requests: dict[str, int] = {}
        self.active_folder_item: str | None = None
        self.file_query = tk.StringVar()
        self.file_importance = tk.StringVar(value=FILE_IMPORTANCE_OPTIONS[0])
        self.file_minimum_size = tk.StringVar(value=next(iter(FILE_SIZE_OPTIONS)))
        self.file_sort = tk.StringVar(value=FILE_SORT_OPTIONS[0])
        self.files_count = tk.StringVar(value="Abra uma pasta para filtrar.")
        self.apps_by_item: dict[str, InstalledApp] = {}
        self.pending_leftovers: dict[str, InstalledApp] = {}
        self.features_by_item: dict[str, SystemFeature] = {}
        self.app_inventory = AppInventory(())
        self.app_query = tk.StringVar()
        self.app_category = tk.StringVar(value=APP_FILTERS[0])
        self.apps_count = tk.StringVar(value="Carregando inventário...")
        self.total_capacity = tk.StringVar(value="—")
        self.total_used = tk.StringVar(value="—")
        self.total_free = tk.StringVar(value="—")
        self.status = tk.StringVar(value="Selecione uma pasta para começar.")
        self._build_ui()
        self._load_drives()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="Surface.TFrame", padding=(22, 17))
        header.pack(fill="x")
        identity = ttk.Frame(header, style="Surface.TFrame")
        identity.pack(side="left")
        ttk.Label(identity, text="OPTIMIZER / SISTEMA", style="Brand.TLabel").pack(
            anchor="w"
        )
        ttk.Label(identity, text="Espaço sob controle.", style="Title.TLabel").pack(
            anchor="w", pady=(1, 1)
        )
        ttk.Label(
            identity,
            text="Revise, entenda e libere armazenamento sem apagar às cegas.",
            style="Subtitle.TLabel",
        ).pack(anchor="w")
        trust = ttk.Frame(header, style="Surface.TFrame")
        trust.pack(side="right")
        ttk.Label(trust, text="●  PROCESSAMENTO LOCAL", style="Safe.TLabel").pack(
            anchor="e"
        )
        ttk.Label(trust, text=f"Versão {__version__}", style="Subtitle.TLabel").pack(
            anchor="e", pady=(5, 0)
        )

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(14, 12))
        files_tab = ttk.Frame(self.notebook)
        apps_tab = ttk.Frame(self.notebook)
        optimization_tab = ttk.Frame(self.notebook)
        functions_tab = ttk.Frame(self.notebook)
        self.notebook.add(files_tab, text="Arquivos")
        self.notebook.add(apps_tab, text="Aplicativos")
        self.notebook.add(optimization_tab, text="Otimização")
        self.notebook.add(functions_tab, text="Funções")
        self._build_files_tab(files_tab)
        self._build_apps_tab(apps_tab)
        self._build_optimization_tab(optimization_tab)
        self._build_functions_tab(functions_tab)
        status_bar = ttk.Frame(self, style="Surface.TFrame", padding=(18, 8))
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, text="●", style="Safe.TLabel", width=2, anchor="w").pack(
            side="left"
        )
        ttk.Label(status_bar, textvariable=self.status, style="Status.TLabel").pack(
            side="left", fill="x", expand=True
        )
        ttk.Label(
            status_bar,
            text="Ctrl+F buscar  •  F5 atualizar",
            style="Status.TLabel",
        ).pack(side="right")
        self.bind_all("<Control-f>", self._focus_app_search)
        self.bind_all("<F5>", self._refresh_active_view)

    def _section_header(self, parent: ttk.Frame, title: str, subtitle: str) -> None:
        header = ttk.Frame(parent, padding=(6, 13, 6, 9))
        header.pack(fill="x")
        ttk.Label(header, text=title, style="Section.TLabel").pack(anchor="w")
        ttk.Label(header, text=subtitle, style="Muted.TLabel").pack(
            anchor="w", pady=(3, 0)
        )

    def _place_tree(self, parent: ttk.Frame, tree: ttk.Treeview) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        vertical = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

    def _build_files_tab(self, parent: ttk.Frame) -> None:
        self._section_header(
            parent,
            "Explorador seguro",
            "Abra pastas sob demanda. A importância explica o risco antes da ação.",
        )
        filters = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text="Buscar", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        self.file_search = ttk.Entry(filters, textvariable=self.file_query, width=25)
        self.file_search.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Importância", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        importance_filter = ttk.Combobox(
            filters,
            textvariable=self.file_importance,
            values=FILE_IMPORTANCE_OPTIONS,
            state="readonly",
            width=10,
        )
        importance_filter.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Tamanho", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        size_filter = ttk.Combobox(
            filters,
            textvariable=self.file_minimum_size,
            values=tuple(FILE_SIZE_OPTIONS),
            state="readonly",
            width=17,
        )
        size_filter.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Ordenar", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        sort_filter = ttk.Combobox(
            filters,
            textvariable=self.file_sort,
            values=FILE_SORT_OPTIONS,
            state="readonly",
            width=15,
        )
        sort_filter.pack(side="left")
        ttk.Label(
            filters, textvariable=self.files_count, style="SurfaceMuted.TLabel"
        ).pack(side="right")

        actions = ttk.Frame(parent, padding=(0, 0, 0, 9))
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="Aplicar na pasta atual",
            command=self._apply_file_filters,
            style="Primary.TButton",
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Mostrar baixa importância",
            command=self._show_low_importance,
        ).pack(side="left", padx=4)
        ttk.Button(
            actions,
            text="Limpar filtros",
            command=self._clear_file_filters,
        ).pack(side="left", padx=4)
        self.review_button = ttk.Button(
            actions,
            text="Revisar arquivos selecionados",
            command=self._review_selected,
            state="disabled",
            style="Danger.TButton",
        )
        self.review_button.pack(side="left", padx=(12, 0))
        ttk.Label(
            actions,
            text="Pastas, atalhos e áreas críticas permanecem protegidos.",
            style="Muted.TLabel",
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
        self.file_tree.tag_configure("Crítico", foreground="#FF8A8A")
        self.file_tree.tag_configure("Alto", foreground="#F5C56B")
        self.file_tree.tag_configure("Baixo", foreground="#6FE0AB")
        self._place_tree(tree_frame, self.file_tree)
        self.file_tree.bind("<<TreeviewOpen>>", self._on_open)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_select)
        self.file_search.bind("<Return>", self._apply_file_filters)
        importance_filter.bind("<<ComboboxSelected>>", self._apply_file_filters)
        size_filter.bind("<<ComboboxSelected>>", self._apply_file_filters)
        sort_filter.bind("<<ComboboxSelected>>", self._apply_file_filters)

    def _build_apps_tab(self, parent: ttk.Frame) -> None:
        self._section_header(
            parent,
            "Aplicativos instalados",
            "Desinstale pelo mecanismo oficial. Resíduos só aparecem após o app sair do Registro.",
        )
        filters = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text="Buscar", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        self.app_search = ttk.Entry(filters, textvariable=self.app_query, width=31)
        self.app_search.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Mostrar", style="SurfaceMuted.TLabel").pack(
            side="left", padx=(0, 7)
        )
        category = ttk.Combobox(
            filters,
            textvariable=self.app_category,
            values=APP_FILTERS,
            state="readonly",
            width=14,
        )
        category.pack(side="left")
        ttk.Label(
            filters, textvariable=self.apps_count, style="SurfaceMuted.TLabel"
        ).pack(side="right")

        actions = ttk.Frame(parent, padding=(0, 0, 0, 9))
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="Atualizar inventário",
            command=self._load_apps,
            style="Primary.TButton",
        ).pack(side="left")
        self.uninstall_button = ttk.Button(
            actions,
            text="Desinstalar selecionado",
            command=self._uninstall_selected,
            state="disabled",
            style="Danger.TButton",
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
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        columns = ("source", "publisher", "version", "status")
        self.apps_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="browse"
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
        self.apps_tree.tag_configure("protected", foreground="#F5C56B")
        self.apps_tree.tag_configure("removable", foreground="#DDE8FA")
        self.apps_tree.tag_configure("leftover", foreground="#6FE0AB")
        self._place_tree(tree_frame, self.apps_tree)
        self.apps_tree.bind("<<TreeviewSelect>>", self._on_app_select)
        self.app_query.trace_add("write", self._on_app_filter)
        category.bind("<<ComboboxSelected>>", self._on_app_filter)
        self._load_apps()

    def _build_optimization_tab(self, parent: ttk.Frame) -> None:
        self._section_header(
            parent,
            "Visão do armazenamento",
            "Compare capacidade, uso e espaço livre antes de abrir ferramentas do Windows.",
        )
        cards = ttk.Frame(parent)
        cards.pack(fill="x", pady=(0, 10))
        for index, (title, value) in enumerate(
            (
                ("CAPACIDADE TOTAL", self.total_capacity),
                ("ESPAÇO USADO", self.total_used),
                ("ESPAÇO LIVRE", self.total_free),
            )
        ):
            card = ttk.Frame(cards, style="Card.TFrame", padding=(16, 13))
            card.grid(
                row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0)
            )
            cards.columnconfigure(index, weight=1)
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=value, style="CardValue.TLabel").pack(
                anchor="w", pady=(4, 0)
            )

        actions = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(
            actions,
            text="Atualizar discos",
            command=self._load_drive_usage,
            style="Primary.TButton",
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
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        columns = ("total", "used", "free", "percent")
        self.drives_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings"
        )
        self.drives_tree.heading("#0", text="Unidade")
        self.drives_tree.heading("total", text="Total")
        self.drives_tree.heading("used", text="Usado")
        self.drives_tree.heading("free", text="Livre")
        self.drives_tree.heading("percent", text="Uso")
        self.drives_tree.column("#0", width=240)
        for column in columns:
            self.drives_tree.column(column, width=140, anchor="e")
        self._place_tree(tree_frame, self.drives_tree)
        self._load_drive_usage()

    def _build_functions_tab(self, parent: ttk.Frame) -> None:
        self._section_header(
            parent,
            "Ajustes recomendados",
            "Cada item abre a página oficial do Windows. O Optimizer não altera serviços críticos.",
        )
        actions = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.open_feature_button = ttk.Button(
            actions,
            text="Abrir configuração selecionada",
            command=self._open_selected_feature,
            state="disabled",
            style="Primary.TButton",
        )
        self.open_feature_button.pack(side="left")
        ttk.Label(
            actions,
            text="Revise o impacto antes de desativar qualquer função.",
            style="SurfaceMuted.TLabel",
        ).pack(side="right")
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        columns = ("effect", "risk")
        self.functions_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="browse"
        )
        self.functions_tree.heading("#0", text="Função")
        self.functions_tree.heading("effect", text="Possível benefício")
        self.functions_tree.heading("risk", text="Risco")
        self.functions_tree.column("#0", width=260)
        self.functions_tree.column("effect", width=650)
        self.functions_tree.column("risk", width=100, anchor="center")
        self.functions_tree.tag_configure("Baixo", foreground="#6FE0AB")
        self.functions_tree.tag_configure("Médio", foreground="#F5C56B")
        self.functions_tree.tag_configure("Alto", foreground="#FF8A8A")
        self._place_tree(tree_frame, self.functions_tree)
        self.functions_tree.bind("<<TreeviewSelect>>", self._on_feature_select)
        for feature in list_system_features():
            item = self.functions_tree.insert(
                "",
                "end",
                text=feature.name,
                values=(feature.effect, feature.risk),
                tags=(feature.risk,),
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
                tags=(result.importance.value,),
            )
            self.paths[item] = drive
            self.folder_items.add(item)
            self.file_tree.insert(item, "end", text="Carregando...")

    def _on_open(self, _event=None) -> None:
        self._load_folder(self.file_tree.focus())

    def _load_folder(self, item: str, *, force: bool = False) -> None:
        if (
            not item
            or not self.file_tree.exists(item)
            or item not in self.folder_items
            or item not in self.paths
            or (item in self.loaded and not force)
        ):
            return
        self.loaded.add(item)
        self.active_folder_item = item
        request = self.folder_requests.get(item, 0) + 1
        self.folder_requests[item] = request
        self.files_count.set("Lendo pasta...")
        self.status.set(f"Lendo {self.paths[item]}...")
        threading.Thread(
            target=self._read_folder,
            args=(item, self.paths[item], request),
            daemon=True,
        ).start()

    def _read_folder(self, item: str, path: Path, request: int) -> None:
        try:
            entries = list_children(path)
            self.after(0, self._show_entries, item, entries, None, request)
        except OSError as error:
            self.after(0, self._show_entries, item, [], str(error), request)

    def _show_entries(
        self,
        parent: str,
        entries: list,
        error: str | None,
        request: int,
    ) -> None:
        if (
            not self.file_tree.exists(parent)
            or self.folder_requests.get(parent) != request
        ):
            return
        for child in self.file_tree.get_children(parent):
            self._forget_tree_item(child)
            self.file_tree.delete(child)
        if error:
            self.loaded.discard(parent)
            self.file_tree.insert(
                parent, "end", text="Acesso indisponível", values=("", "Revisar", error)
            )
            self.status.set(error)
            self.files_count.set("Pasta indisponível")
            return
        selected_importance = next(
            (
                importance
                for importance in Importance
                if importance.value == self.file_importance.get()
            ),
            None,
        )
        visible = filter_entries(
            entries,
            query=self.file_query.get(),
            importance=selected_importance,
            minimum_size=FILE_SIZE_OPTIONS[self.file_minimum_size.get()],
            sort_by=self.file_sort.get(),
        )
        for entry in visible:
            item = self.file_tree.insert(
                parent,
                "end",
                text=entry.path.name or str(entry.path),
                values=(
                    format_size(entry.size),
                    entry.classification.importance.value,
                    entry.classification.reason,
                ),
                tags=(entry.classification.importance.value,),
            )
            self.paths[item] = entry.path
            if entry.is_dir:
                self.folder_items.add(item)
                self.file_tree.insert(item, "end", text="Carregando...")
        self.active_folder_item = parent
        self.files_count.set(f"{len(visible)} de {len(entries)} itens")
        self.status.set(
            f"{len(visible)} de {len(entries)} itens em {self.paths[parent]}"
        )

    def _forget_tree_item(self, item: str) -> None:
        if self.file_tree.exists(item):
            for child in self.file_tree.get_children(item):
                self._forget_tree_item(child)
        self.paths.pop(item, None)
        self.loaded.discard(item)
        self.folder_items.discard(item)
        self.folder_requests.pop(item, None)
        if self.active_folder_item == item:
            self.active_folder_item = None

    def _current_folder_item(self) -> str | None:
        item = self.file_tree.focus()
        while item and item not in self.folder_items:
            item = self.file_tree.parent(item)
        if item:
            return item
        if self.active_folder_item and self.file_tree.exists(self.active_folder_item):
            return self.active_folder_item
        return None

    def _apply_file_filters(self, _event=None) -> None:
        item = self._current_folder_item()
        if not item:
            self.status.set("Abra ou selecione uma pasta antes de aplicar os filtros.")
            return
        for child in self.file_tree.get_children(item):
            self._forget_tree_item(child)
            self.file_tree.delete(child)
        self.loaded.discard(item)
        self.file_tree.insert(item, "end", text="Carregando...")
        self.file_tree.item(item, open=True)
        self._load_folder(item, force=True)

    def _show_low_importance(self) -> None:
        self.file_importance.set(Importance.LOW.value)
        self.file_minimum_size.set(next(iter(FILE_SIZE_OPTIONS)))
        self._apply_file_filters()

    def _clear_file_filters(self) -> None:
        self.file_query.set("")
        self.file_importance.set(FILE_IMPORTANCE_OPTIONS[0])
        self.file_minimum_size.set(next(iter(FILE_SIZE_OPTIONS)))
        self.file_sort.set(FILE_SORT_OPTIONS[0])
        self._apply_file_filters()

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
        dialog.title("Revisar exclusão")
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
        review_tree.tag_configure("Crítico", foreground="#FF8A8A")
        review_tree.tag_configure("Alto", foreground="#F5C56B")
        review_tree.tag_configure("Baixo", foreground="#6FE0AB")
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
                tags=(review.classification.importance.value,),
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
            style="Danger.TButton",
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
        dialog.destroy()
        self.review_button.configure(state="disabled")
        self.status.set(f"Excluindo {len(reviews)} arquivo(s)...")
        threading.Thread(
            target=self._delete_reviewed_files,
            args=(items, reviews),
            daemon=True,
        ).start()

    def _delete_reviewed_files(self, items: list[str], reviews: list) -> None:
        deleted, failures = delete_files(review.path for review in reviews)
        self.after(0, self._finish_file_delete, items, deleted, failures)

    def _finish_file_delete(
        self,
        items: list[str],
        deleted: list[Path],
        failures: list[tuple[Path, str]],
    ) -> None:
        deleted_set = set(deleted)
        for item in items:
            path = self.paths.get(item)
            if path and path.resolve() in deleted_set:
                self._forget_tree_item(item)
                self.file_tree.delete(item)
        self.status.set(
            f"{len(deleted)} arquivo(s) excluído(s); {len(failures)} falha(s)."
        )
        self._on_select()
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
        total_capacity = sum(drive.total for drive in drives)
        total_used = sum(drive.used for drive in drives)
        total_free = sum(drive.free for drive in drives)
        self.total_capacity.set(format_size(total_capacity))
        self.total_used.set(format_size(total_used))
        self.total_free.set(format_size(total_free))
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
        self.apps_count.set("Carregando inventário...")
        self.uninstall_button.configure(state="disabled")
        self.leftover_button.configure(state="disabled")
        threading.Thread(target=self._read_apps, daemon=True).start()

    def _read_apps(self) -> None:
        try:
            inventory = list_installed_apps()
        except (OSError, ValueError, RuntimeError) as error:
            self.after(0, self._show_apps_error, str(error))
            return
        self.after(0, self._show_apps, inventory)

    def _show_apps(self, inventory: AppInventory) -> None:
        self.app_inventory = inventory
        self._render_apps()
        if inventory.warnings:
            self.status.set("; ".join(inventory.warnings))
        else:
            self.status.set(f"{len(inventory.apps)} aplicativos encontrados.")

    def _show_apps_error(self, error: str) -> None:
        self.apps_count.set("Inventário indisponível")
        self.status.set(f"Falha ao carregar aplicativos: {error}")
        messagebox.showerror(
            "Falha no inventário",
            f"Não foi possível carregar os aplicativos.\n\n{error}",
            parent=self,
        )

    def _on_app_filter(self, *_args) -> None:
        self._render_apps()

    def _render_apps(self) -> None:
        self.apps_tree.delete(*self.apps_tree.get_children())
        self.apps_by_item.clear()
        display_apps = prepare_installed_apps(
            self.app_inventory.apps,
            self.pending_leftovers.values(),
            query=self.app_query.get(),
            category=self.app_category.get(),
        )
        all_apps = prepare_installed_apps(
            self.app_inventory.apps, self.pending_leftovers.values()
        )
        for app in display_apps:
            status = app.protected_reason or app.location or "Pasta não informada"
            source = "Resíduo" if app.pending_leftover else app.source
            tag = (
                "leftover"
                if app.pending_leftover
                else "removable"
                if app.removable
                else "protected"
            )
            item = self.apps_tree.insert(
                "",
                "end",
                text=app.name,
                values=(source, app.publisher, app.version, status),
                tags=(tag,),
            )
            self.apps_by_item[item] = app
        self.apps_count.set(f"{len(display_apps)} de {len(all_apps)} itens")

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

    def _focus_app_search(self, _event=None) -> str:
        if self.notebook.index("current") == 0:
            self.file_search.focus_set()
            self.file_search.selection_range(0, "end")
        else:
            self.notebook.select(1)
            self.app_search.focus_set()
            self.app_search.selection_range(0, "end")
        return "break"

    def _refresh_active_view(self, _event=None) -> str:
        current = self.notebook.index("current")
        if current == 0:
            self.file_tree.delete(*self.file_tree.get_children())
            self.paths.clear()
            self.loaded.clear()
            self.folder_items.clear()
            self.folder_requests.clear()
            self.active_folder_item = None
            self.files_count.set("Abra uma pasta para filtrar.")
            self._load_drives()
            self.status.set("Unidades atualizadas.")
        elif current == 1:
            self._load_apps()
        elif current == 2:
            self._load_drive_usage()
            self.status.set("Atualizando uso dos discos...")
        return "break"


def run() -> None:
    OptimizerApp().mainloop()
