import tempfile
import threading
import shutil
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from tkinterdnd2 import DND_FILES, TkinterDnD
from pypdf import PdfWriter
from natsort import natsorted


class PDFZipMerger(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        tb.Style("flatly")
        self.title("PDF ZIP Merger")
        self.geometry("720x420")
        self.zip_file = None

        tb.Label(self, text="PDF ZIP Merger", font=("Segoe UI", 20, "bold")).pack(pady=12)

        self.drop = tb.Label(
            self,
            text="Drag && Drop ZIP Here\n\nor\n\nClick Browse",
            relief="ridge",
            anchor="center",
            padding=30
        )
        self.drop.pack(fill="x", padx=20)
        self.drop.drop_target_register(DND_FILES)
        self.drop.dnd_bind("<<Drop>>", self.on_drop)

        tb.Button(self, text="Browse ZIP", command=self.browse, bootstyle="primary").pack(pady=10)

        self.status = tb.Label(self, text="No ZIP selected")
        self.status.pack()

        self.progress = tb.Progressbar(self, maximum=100)
        self.progress.pack(fill="x", padx=20, pady=10)

        tb.Button(self, text="Merge PDFs", command=self.merge_clicked, bootstyle="success").pack(pady=12)

    def browse(self):
        f = filedialog.askopenfilename(filetypes=[("ZIP Files","*.zip")])
        if f:
            self.zip_file = f
            self.status.configure(text=Path(f).name)

    def on_drop(self, event):
        p = event.data.strip("{}")
        if p.lower().endswith(".zip"):
            self.zip_file = p
            self.status.configure(text=Path(p).name)
        else:
            messagebox.showerror("Error","Please drop a ZIP file.")

    def merge_clicked(self):
        if not self.zip_file:
            messagebox.showerror("Error","Please select a ZIP file.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf",
                                           filetypes=[("PDF","*.pdf")])
        if out:
            threading.Thread(target=self.merge, args=(out,), daemon=True).start()

    def update_ui(self, text=None, value=None):
        def f():
            if text is not None:
                self.status.configure(text=text)
            if value is not None:
                self.progress["value"] = value
        self.after(0, f)

    def merge(self, outfile):
        tmp = tempfile.mkdtemp()
        skipped = []
        try:
            self.update_ui("Extracting ZIP...",5)
            with zipfile.ZipFile(self.zip_file) as z:
                z.extractall(tmp)

            pdfs = natsorted(Path(tmp).rglob("*.pdf"), key=lambda p: str(p))
            if not pdfs:
                self.after(0, lambda: messagebox.showerror("Error","No PDFs found in ZIP."))
                return

            writer = PdfWriter()
            total = len(pdfs)

            for i,pdf in enumerate(pdfs,1):
                try:
                    writer.append(str(pdf))
                except Exception:
                    skipped.append(pdf.name)
                self.update_ui(f"Merging {i}/{total}", int(i*90/total))

            with open(outfile,"wb") as f:
                writer.write(f)
            writer.close()

            log = Path(outfile).with_suffix(".log.txt")
            with open(log,"w",encoding="utf-8") as fp:
                fp.write("Skipped PDFs\n")
                fp.write("="*40+"\n")
                fp.write("\n".join(skipped) if skipped else "None")

            self.update_ui("Completed",100)
            self.after(0, lambda: messagebox.showinfo(
                "Done",
                f"Merged {total-len(skipped)} PDF(s)\nSkipped {len(skipped)}"
            ))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    PDFZipMerger().mainloop()
