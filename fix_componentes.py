import codecs

codigo = """

class Card(tk.Frame):
    def __init__(self, parent, bg_color, corner_radius=10, **kwargs):
        super().__init__(parent, bg=bg_color, **kwargs)
        self.corner_radius = corner_radius
        self.configure(relief="flat", bd=0)

class ModernButton(tk.Frame):
    def __init__(self, parent, text, command, bg, hover_bg, fg="white", font=None, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.bg = bg
        self.hover_bg = hover_bg
        
        self.btn = tk.Button(self, text=text, command=command, bg=bg, activebackground=hover_bg,
                             fg=fg, activeforeground=fg, font=font, relief="flat", bd=0, cursor="hand2")
        self.btn.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.btn.bind("<Enter>", self.on_enter)
        self.btn.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        self.btn['background'] = self.hover_bg
        
    def on_leave(self, e):
        self.btn['background'] = self.bg
        
    def config(self, **kwargs):
        self.btn.config(**kwargs)
"""

with codecs.open('app/frontend/componentes_ui.py', 'a', 'utf-8') as file:
    file.write(codigo)

print("Componentes custom anadidos.")
