import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, END
from threading import Thread
from rapidfuzz import fuzz, process
import unidecode
import time

root = ttk.Window(themename="cosmo")  # Tema Moderno
root.title("Comparação de Planilhas")
root.geometry("600x450")

file_path1 = ""
file_path2 = ""
column_name = ""
loading = False
result_df = None


def select_file1():
    global file_path1
    file_path1 = filedialog.askopenfilename(
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )
    if file_path1:
        label_file1.config(text=f"📄 {file_path1.split('/')[-1]}")


def select_file2():
    global file_path2
    file_path2 = filedialog.askopenfilename(
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )
    if file_path2:
        label_file2.config(text=f"📄 {file_path2.split('/')[-1]}")


def normalize_text(text):
    if pd.isna(text):
        return ""
    return unidecode.unidecode(text.strip().lower())


def find_best_match(name, choices):
    if not choices or not name:
        return None, 0.0

    result = process.extractOne(name, choices, scorer=fuzz.ratio)

    if result is None:
        return None, 0.0

    match, score, _ = result
    return (match, score) if score >= 90 else (None, 0.0)


def animate_loading():
    global loading
    progress_bar.start(10)
    while loading:
        time.sleep(0.5)


def process_files():
    global column_name, loading, result_df
    column_name = entry_column.get().strip().lower()

    if not file_path1 or not file_path2:
        messagebox.showerror("Erro", "Selecione ambas as planilhas antes de continuar.")
        return
    if not column_name:
        messagebox.showerror("Erro", "Informe o nome da coluna a ser comparada.")
        return

    try:
        loading = True
        Thread(target=animate_loading, daemon=True).start()

        df1 = pd.read_excel(file_path1, header=0)
        df2 = pd.read_excel(file_path2, header=0)

        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()
        column_name = column_name.strip().lower()

        if column_name not in df1.columns or column_name not in df2.columns:
            loading = False
            progress_bar.stop()
            messagebox.showerror("Erro", f"A coluna '{column_name}' não foi encontrada.\nVerifique espaços, acentos ou variações.")
            return

        df1[column_name] = df1[column_name].apply(normalize_text)
        df2[column_name] = df2[column_name].apply(normalize_text)

        matches = df1[column_name].apply(lambda x: find_best_match(x, df2[column_name].tolist()))
        df1["match"] = matches.apply(lambda x: x[0])
        df1["score"] = matches.apply(lambda x: x[1])
        df1["duplicado"] = df1["match"].apply(lambda x: "Sim" if x else "Não")

        avg_score = df1[df1["duplicado"] == "Sim"]["score"].mean()
        avg_score = round(avg_score, 2) if not pd.isna(avg_score) else 0

        loading = False
        progress_bar.stop()
        loading_label.config(text=f"✅ Processamento concluído! Precisão média: {avg_score}%")

        result_df = df1[[column_name, "match", "score", "duplicado"]]

        result_window = ttk.Toplevel(root)
        result_window.title("Resultados")
        result_text = ttk.Text(result_window, wrap="word")
        result_text.pack(expand=True, fill="both", padx=10, pady=10)
        result_text.insert(END, result_df.to_string(index=False))

        btn_download = ttk.Button(root, text="📥 Baixar Resultados", command=download_results)
        btn_download.pack(pady=10)

    except Exception as e:
        loading = False
        progress_bar.stop()
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar os arquivos: {e}")


def download_results():
    global result_df
    if result_df is None:
        messagebox.showerror("Erro", "Nenhum resultado encontrado para download.")
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        ]
    )
    if save_path:
        result_df.to_excel(save_path, index=False)
        messagebox.showinfo("Sucesso", f"Resultados salvos em: {save_path}")


# Interface Moderna
frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Comparação de Planilhas", font=("Arial", 16, "bold")).pack(pady=10)

btn_file1 = ttk.Button(frame, text="📂 Selecionar Planilha 1", command=select_file1)
btn_file1.pack(pady=5)
label_file1 = ttk.Label(frame, text="Nenhum arquivo selecionado", foreground="blue")
label_file1.pack()

btn_file2 = ttk.Button(frame, text="📂 Selecionar Planilha 2", command=select_file2)
btn_file2.pack(pady=5)
label_file2 = ttk.Label(frame, text="Nenhum arquivo selecionado", foreground="blue")
label_file2.pack()

ttk.Label(frame, text="Nome da coluna para comparação:", font=("Arial", 10, "bold")).pack(pady=5)
entry_column = ttk.Entry(frame)
entry_column.pack(pady=5)

btn_process = ttk.Button(frame, text="🔍 Processar Planilhas", command=lambda: Thread(target=process_files).start())
btn_process.pack(pady=10)

loading_label = ttk.Label(frame, text="", foreground="red")
loading_label.pack()

progress_bar = ttk.Progressbar(frame, mode="indeterminate")
progress_bar.pack(fill="x", padx=10, pady=5)

root.mainloop()