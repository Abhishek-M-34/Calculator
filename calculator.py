"""
Smart Calculator — CustomTkinter + Groq AI (Llama‑3.3‑70B)
Features:
  • Modern dark UI with CustomTkinter
  • Standard & Scientific modes
  • Natural‑language math via Groq (free, 14 400 req/day)
  • Full calculation history with one‑click recall
  • Keyboard support
  • Safe expression evaluator (no raw eval on user text)
"""

import customtkinter as ctk
import threading
from datetime import datetime

from calculator_core import evaluate_expression, groq_math_query, GROQ_AVAILABLE

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":           "#0d0d1a",
    "display_bg":   "#13132b",
    "panel_bg":     "#16162e",
    "num":          "#1c1c38",
    "num_h":        "#26264a",
    "op":           "#1e1045",
    "op_h":         "#2e1e60",
    "eq":           "#5b21b6",
    "eq_h":         "#4c1d95",
    "del":          "#0d2d1e",
    "del_h":        "#144d32",
    "ac":           "#2d1010",
    "ac_h":         "#4a1818",
    "sci":          "#0e2233",
    "sci_h":        "#193448",
    "paren":        "#1a103a",
    "paren_h":      "#281858",
    "txt":          "#e8e8f8",
    "txt_op":       "#a78bfa",
    "txt_eq":       "#ffffff",
    "txt_sci":      "#38bdf8",
    "txt_dim":      "#64648a",
    "txt_del":      "#4ade80",
    "txt_ac":       "#f87171",
    "accent":       "#7c3aed",
    "accent2":      "#06b6d4",
    "border":       "#2d2d5a",
    "chat_bg":      "#0a0a18",
    "user_msg":     "#1a1a40",
    "bot_msg":      "#111128",
    "green":        "#4ade80",
    "red":          "#f87171",
    "yellow":       "#fbbf24",
}


# Math evaluation is delegated to calculator_core.evaluate_expression.
# That module also contains the Groq helper used by the AI mode.


# ── Main Application ──────────────────────────────────────────────────────────
class SmartCalculator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Smart Calculator")
        self.geometry("480x740")
        self.minsize(420, 680)
        self.configure(fg_color=C["bg"])

        # ── State ─────────────────────────────────────────────────────────────
        self.expression   = ""
        self.just_evaled  = False
        self.history: list[str] = []
        self.mode         = "standard"   # standard | scientific | ai
        self.groq_key     = None
        self.ai_connected = False
        self.units        = "deg"  # deg | rad

        # ── Widgets ───────────────────────────────────────────────────────────
        self._header()
        self._display()
        self._tabs()
        self._standard_pad()
        self._sci_pad()
        self._ai_pad()

        # Start in standard mode
        self._switch("standard")

        # Keyboard
        self.bind("<Key>",       self._key)
        self.bind("<Return>",    lambda _: self._evaluate())
        self.bind("<BackSpace>", lambda _: self._backspace())
        self.bind("<Escape>",    lambda _: self._ac())

    # ══════════════════════════════════════════════════════════════════════════
    #  HEADER
    # ══════════════════════════════════════════════════════════════════════════
    def _header(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=(14, 0))

        ctk.CTkLabel(
            f, text="✦  Smart Calculator",
            font=ctk.CTkFont("Segoe UI", 17, "bold"),
            text_color=C["accent"]
        ).pack(side="left")

        self.clock_lbl = ctk.CTkLabel(
            f, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=C["txt_dim"]
        )
        self.clock_lbl.pack(side="right")
        self._tick()

    def _tick(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%H:%M"))
        self.after(10_000, self._tick)

    # ══════════════════════════════════════════════════════════════════════════
    #  DISPLAY
    # ══════════════════════════════════════════════════════════════════════════
    def _display(self):
        frame = ctk.CTkFrame(
            self, fg_color=C["display_bg"], corner_radius=16,
            border_width=1, border_color=C["border"]
        )
        frame.pack(fill="x", padx=18, pady=(10, 0))

        self.expr_lbl = ctk.CTkLabel(
            frame, text="", anchor="e",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=C["txt_dim"]
        )
        self.expr_lbl.pack(fill="x", padx=14, pady=(10, 0))

        self.disp_var = ctk.StringVar(value="0")
        self.disp_entry = ctk.CTkEntry(
            frame,
            textvariable=self.disp_var,
            font=ctk.CTkFont("Segoe UI", 40, "bold"),
            fg_color="transparent",
            border_width=0,
            text_color=C["txt"],
            justify="right",
            state="readonly"
        )
        self.disp_entry.pack(fill="x", padx=8)

        # History strip
        hist_row = ctk.CTkFrame(frame, fg_color="transparent")
        hist_row.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            hist_row, text="LAST",
            font=ctk.CTkFont("Segoe UI", 8, "bold"),
            text_color=C["txt_dim"]
        ).pack(side="left")

        self.hist_lbl = ctk.CTkLabel(
            hist_row, text="—",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["txt_dim"],
            anchor="e"
        )
        self.hist_lbl.pack(side="right", fill="x", expand=True)

    def _set_display(self, val: str):
        self.disp_var.set(val[-22:] if len(val) > 22 else val)

    # ══════════════════════════════════════════════════════════════════════════
    #  MODE TABS
    # ══════════════════════════════════════════════════════════════════════════
    def _tabs(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=(10, 0))

        self._tab_btns = {}
        for label, mode in [("⌨  Standard", "standard"),
                             ("∫  Scientific", "scientific"),
                             ("🤖  AI Mode", "ai")]:
            b = ctk.CTkButton(
                f, text=label,
                command=lambda m=mode: self._switch(m),
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                height=30, corner_radius=20,
                fg_color="transparent",
                text_color=C["txt_dim"],
                hover_color=C["num_h"]
            )
            b.pack(side="left", padx=3)
            self._tab_btns[mode] = b

    def _switch(self, mode: str):
        self.mode = mode
        for m, b in self._tab_btns.items():
            if m == mode:
                b.configure(fg_color=C["accent"], text_color=C["txt_eq"])
            else:
                b.configure(fg_color="transparent", text_color=C["txt_dim"])

        for panel, m in [(self._std_frame, "standard"),
                          (self._sci_frame, "scientific"),
                          (self._ai_frame,  "ai")]:
            if m == mode:
                panel.pack(fill="both", expand=True, padx=18, pady=(8, 14))
            else:
                panel.pack_forget()
                
        # Update display for AI Mode
        if mode == "ai":
            self.disp_entry.configure(font=ctk.CTkFont("Segoe UI", 28, "bold"))
            self.disp_var.set("AI Mode Enabled")
            self.expr_lbl.configure(text="")
        else:
            self.disp_entry.configure(font=ctk.CTkFont("Segoe UI", 40, "bold"))
            self.expr_lbl.configure(text=self.expression[-34:] if self.expression else "")
            self._set_display(self.expression or "0")

    # ══════════════════════════════════════════════════════════════════════════
    #  STANDARD KEYPAD
    # ══════════════════════════════════════════════════════════════════════════
    def _standard_pad(self):
        self._std_frame = ctk.CTkFrame(self, fg_color="transparent")

        layout = [
            [("AC", "ac"),   ("(", "paren"), (")", "paren"), ("%",  "op")],
            [("7", "num"),   ("8", "num"),   ("9",  "num"),  ("÷",  "op")],
            [("4", "num"),   ("5", "num"),   ("6",  "num"),  ("×",  "op")],
            [("1", "num"),   ("2", "num"),   ("3",  "num"),  ("−",  "op")],
            [("⌫", "del"),   ("0", "num"),   (".",  "num"),  ("+",  "op")],
            [("=", "eq", 4)],
        ]
        self._render_pad(self._std_frame, layout, btn_h=58)

    # ══════════════════════════════════════════════════════════════════════════
    #  SCIENTIFIC KEYPAD
    # ══════════════════════════════════════════════════════════════════════════
    def _sci_pad(self):
        self._sci_frame = ctk.CTkFrame(self, fg_color="transparent")

        layout = [
            [("sin",  "sci"), ("cos",  "sci"), ("tan", "sci"), ("AC",  "ac")],
            [("log",  "sci"), ("ln",   "sci"), ("√",   "sci"), ("x²",  "sci")],
            [("xʸ",   "sci"), ("π",    "sci"), ("e",   "sci"), ("%",   "op")],
            [("(",  "paren"), (")",  "paren"), ("⌫",  "del"), ("÷",   "op")],
            [("7",    "num"), ("8",    "num"), ("9",   "num"), ("×",   "op")],
            [("4",    "num"), ("5",    "num"), ("6",   "num"), ("−",   "op")],
            [("1",    "num"), ("2",    "num"), ("3",   "num"), ("+",   "op")],
            [("00",   "num"), ("0",    "num"), (".",   "num"), ("=",   "eq")],
        ]
        
        # Unit toggle frame
        self.unit_frame = ctk.CTkFrame(self._sci_frame, fg_color="transparent")
        self.unit_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        self.deg_btn = ctk.CTkButton(
            self.unit_frame, text="DEG", width=40, height=24, corner_radius=6,
            command=lambda: self._set_units("deg"),
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            fg_color=C["accent"], text_color=C["txt_eq"]
        )
        self.deg_btn.pack(side="right", padx=2)
        
        self.rad_btn = ctk.CTkButton(
            self.unit_frame, text="RAD", width=40, height=24, corner_radius=6,
            command=lambda: self._set_units("rad"),
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            fg_color="transparent", text_color=C["txt_dim"]
        )
        self.rad_btn.pack(side="right", padx=2)

        pad_f = ctk.CTkFrame(self._sci_frame, fg_color="transparent")
        pad_f.pack(fill="both", expand=True)
        self._render_pad(pad_f, layout, btn_h=44)

    def _set_units(self, unit: str):
        self.units = unit
        if unit == "deg":
            self.deg_btn.configure(fg_color=C["accent"], text_color=C["txt_eq"])
            self.rad_btn.configure(fg_color="transparent", text_color=C["txt_dim"])
        else:
            self.rad_btn.configure(fg_color=C["accent"], text_color=C["txt_eq"])
            self.deg_btn.configure(fg_color="transparent", text_color=C["txt_dim"])

    # ── shared renderer ───────────────────────────────────────────────────────
    _STYLE = {
        "num":   ("num",   "num_h",  "txt"),
        "op":    ("op",    "op_h",   "txt_op"),
        "eq":    ("eq",    "eq_h",   "txt_eq"),
        "del":   ("del",   "del_h",  "txt_del"),
        "ac":    ("ac",    "ac_h",   "txt_ac"),
        "sci":   ("sci",   "sci_h",  "txt_sci"),
        "paren": ("paren", "paren_h","txt_op"),
    }

    def _render_pad(self, parent, layout, btn_h=64):
        for r, row in enumerate(layout):
            curr_c = 0
            for item in row:
                if len(item) == 3:
                    label, btype, cspan = item
                else:
                    label, btype = item
                    cspan = 1
                    
                bg_k, hv_k, fg_k = self._STYLE[btype]
                b = ctk.CTkButton(
                    parent, text=label,
                    command=lambda l=label: self._click(l),
                    font=ctk.CTkFont("Segoe UI", 20, "bold"),
                    height=btn_h, corner_radius=14,
                    fg_color=C[bg_k], hover_color=C[hv_k],
                    text_color=C[fg_k]
                )
                b.grid(row=r, column=curr_c, columnspan=cspan, padx=4, pady=4, sticky="nsew")
                curr_c += cspan
            parent.rowconfigure(r, weight=1)
        for c in range(4):
            parent.columnconfigure(c, weight=1)

    # ══════════════════════════════════════════════════════════════════════════
    #  AI PANEL
    # ══════════════════════════════════════════════════════════════════════════
    def _ai_pad(self):
        self._ai_frame = ctk.CTkFrame(self, fg_color="transparent")

        # ── API key row ───────────────────────────────────────────────────────
        key_frame = ctk.CTkFrame(
            self._ai_frame, fg_color=C["panel_bg"],
            corner_radius=12, border_width=1, border_color=C["border"]
        )
        key_frame.pack(fill="x", pady=(0, 6))

        self._key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="🔑  Paste your Groq API key (console.groq.com → free)",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", border_width=0,
            show="•"
        )
        self._key_entry.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=8)

        ctk.CTkButton(
            key_frame, text="Connect",
            command=self._connect_groq,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            width=82, height=30, corner_radius=10,
            fg_color=C["eq"], hover_color=C["eq_h"]
        ).pack(side="right", padx=(4, 10))

        # ── Status bar ────────────────────────────────────────────────────────
        self._ai_status = ctk.CTkLabel(
            self._ai_frame,
            text="● Not connected  —  get a FREE key at console.groq.com",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["red"]
        )
        self._ai_status.pack(anchor="w", pady=(0, 6))

        # ── Chat box ──────────────────────────────────────────────────────────
        self._chat = ctk.CTkTextbox(
            self._ai_frame,
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=C["chat_bg"],
            text_color=C["txt"],
            corner_radius=12,
            border_width=1, border_color=C["border"],
            wrap="word",
            state="disabled"
        )
        self._chat.pack(fill="both", expand=True, pady=(0, 8))
        self._chat_add("🤖 AI", (
            "Hi! I use Llama‑3.3‑70B via Groq (14 400 free requests/day).\n"
            "Ask me anything in plain English:\n"
            "  • 'What is 18% tip on a ₹850 bill?'\n"
            "  • 'Compound interest: ₹10 000 at 8% for 5 years'\n"
            "  • 'Convert 100 miles to km'\n"
            "  • 'Area of a circle with radius 7'\n"
            "Connect your API key above to get started!"
        ))

        # ── Input row ─────────────────────────────────────────────────────────
        inp_frame = ctk.CTkFrame(
            self._ai_frame, fg_color=C["panel_bg"],
            corner_radius=12, border_width=1, border_color=C["border"]
        )
        inp_frame.pack(fill="x")

        self._ai_inp = ctk.CTkEntry(
            inp_frame,
            placeholder_text="Ask anything… e.g. 'square root of 1764'",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color="transparent", border_width=0
        )
        self._ai_inp.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=10)
        self._ai_inp.bind("<Return>", lambda _: self._ai_ask())

        ctk.CTkButton(
            inp_frame, text="➤",
            command=self._ai_ask,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            width=44, height=36, corner_radius=10,
            fg_color=C["eq"], hover_color=C["eq_h"]
        ).pack(side="right", padx=(4, 10))

    # ── Groq connection ───────────────────────────────────────────────────────
    def _connect_groq(self):
        if not GROQ_AVAILABLE:
            self._ai_status.configure(
                text="● groq package not installed — run: pip install groq",
                text_color=C["red"]
            )
            return

        key = self._key_entry.get().strip()
        if not key:
            self._ai_status.configure(
                text="● Please paste a valid Groq API key",
                text_color=C["yellow"]
            )
            return

        try:
            # Simple validation via a quick math query
            resp = groq_math_query("1+1", api_key=key)
            self.groq_key = key
            self.ai_connected = True

            reqs = resp.get("remaining_requests", "Unknown")
            self._ai_status.configure(
                text=f"● Connected ✓  Llama‑3.3‑70B via Groq  ({reqs} reqs left)",
                text_color=C["green"]
            )
            self._chat_add("🤖 AI", "Connected! Ready to solve math in plain English. 🚀")
        except Exception as ex:
            self.ai_connected = False
            self._ai_status.configure(
                text=f"● Connection failed — {str(ex)[:60]}",
                text_color=C["red"]
            )

    # ── AI ask ────────────────────────────────────────────────────────────────
    def _ai_ask(self):
        q = self._ai_inp.get().strip()
        if not q:
            return
        self._ai_inp.delete(0, "end")
        self._chat_add("👤 You", q)

        if not self.ai_connected:
            self._chat_add("🤖 AI", "⚠️  Please connect a Groq API key first.")
            return

        self._chat_add("🤖 AI", "⏳  Thinking…")
        threading.Thread(target=self._groq_query, args=(q,), daemon=True).start()

    def _groq_query(self, question: str):
        try:
            resp = groq_math_query(question, api_key=self.groq_key)
            answer = resp.get("answer", "(no response)")
            reqs = resp.get("remaining_requests", "Unknown")
            msg = f"● Connected ✓  Llama‑3.3‑70B via Groq  ({reqs} reqs left)"
            self.after(0, lambda: self._ai_status.configure(text=msg, text_color=C["green"]))
        except Exception as ex:
            answer = f"Error: {ex}"

        self.after(0, lambda: self._replace_thinking(answer))

    def _replace_thinking(self, answer: str):
        self._chat.configure(state="normal")
        txt = self._chat.get("1.0", "end")
        txt = txt.replace("🤖 AI:\n⏳  Thinking…\n\n", "")
        self._chat.delete("1.0", "end")
        self._chat.insert("end", txt)
        self._chat.configure(state="disabled")
        self._chat_add("🤖 AI", answer)

    def _chat_add(self, sender: str, text: str):
        self._chat.configure(state="normal")
        self._chat.insert("end", f"{sender}:\n{text}\n\n")
        self._chat.configure(state="disabled")
        self._chat.see("end")

    # ══════════════════════════════════════════════════════════════════════════
    #  BUTTON / KEYBOARD LOGIC
    # ══════════════════════════════════════════════════════════════════════════
    _SCI_MAP = {
        "sin": "sin(",  "cos": "cos(",  "tan": "tan(",
        "log": "log10(","ln":  "log(",  "√":   "sqrt(",
        "x²":  "**2",   "xʸ":  "**",   "π":   "π",
        "e":   "e",
    }

    def _click(self, label: str):
        if self.mode == "ai": return
        if label == "=":       self._evaluate()
        elif label == "AC":    self._ac()
        elif label == "⌫":    self._backspace()
        elif label == "%":     self._percent()
        elif label in self._SCI_MAP:
            self._append(self._SCI_MAP[label])
        else:
            self._append(label)

    def _append(self, ch: str):
        if self.mode == "ai": return
        if self.just_evaled and ch not in "+-*/÷×−÷**":
            self.expression = ""
        self.just_evaled = False
        self.expression += ch
        self.expr_lbl.configure(text=self.expression[-34:])
        self._set_display(self.expression)

    def _evaluate(self):
        if self.mode == "ai":
            return

        expr = self.expression.strip()
        if not expr:
            return

        res = evaluate_expression(expr, mode=self.units)
        if "error" in res:
            err = res["error"]
            if "Division by zero" in err:
                self._set_display("÷ by zero")
            else:
                self._set_display("Syntax error")
            self.expression = ""
            self.just_evaled = True
            return

        result = res["result"]
        result_str = str(result)

        # History
        record = f"{expr} = {result_str}"
        self.history.append(record)
        if len(self.history) > 10:
            self.history.pop(0)
        self.hist_lbl.configure(text=record[-40:])

        self.expr_lbl.configure(text=f"{expr}  =")
        self._set_display(result_str)
        self.expression = result_str
        self.just_evaled = True

    def _ac(self):
        if self.mode == "ai": return
        self.expression = ""
        self.just_evaled = False
        self.expr_lbl.configure(text="")
        self._set_display("0")

    def _backspace(self):
        if self.mode == "ai": return
        if self.just_evaled:
            self._ac()
            return
        self.expression = self.expression[:-1]
        self.expr_lbl.configure(text=self.expression[-34:])
        self._set_display(self.expression or "0")

    def _percent(self):
        if self.mode == "ai":
            return
        try:
            res = evaluate_expression(self.expression)
            if "result" not in res:
                return
            val = float(res["result"])
            self.expression = str(val / 100)
            self._set_display(self.expression)
        except Exception:
            pass

    def _key(self, event):
        if self.mode == "ai": return
        ch = event.char
        if ch in "0123456789.+-*/()":
            self._append(ch)
        elif ch == "^":
            self._append("**")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SmartCalculator()
    app.mainloop()
