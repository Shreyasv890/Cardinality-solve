"""Interactive Cardinality Problem Solver
Python + SymPy (equations) + Tkinter (interface)

Install:  pip install sympy
Run:      python cardinality_solver.py
"""
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from sympy import symbols, linsolve, S

# ----------------------------------------------------------------------
# 1. DATA: names, equations and diagram geometry
# ----------------------------------------------------------------------
# t = total (e.g. tAB = n(A ∩ B)), o = "only" region (e.g. oAB = A ∩ B only)
NAMES = {
    2: {"tA": "n(A)", "tB": "n(B)", "tAB": "n(A ∩ B)", "tU": "n(A ∪ B)",
        "oA": "n(A only)", "oB": "n(B only)"},
    3: {"tA": "n(A)", "tB": "n(B)", "tC": "n(C)", "tAB": "n(A ∩ B)",
        "tAC": "n(A ∩ C)", "tBC": "n(B ∩ C)", "tABC": "n(A ∩ B ∩ C)",
        "tU": "n(A ∪ B ∪ C)", "oA": "n(A only)", "oB": "n(B only)",
        "oC": "n(C only)", "oAB": "n(A ∩ B only)", "oAC": "n(A ∩ C only)",
        "oBC": "n(B ∩ C only)"},
}
FIELDS = {2: ["tA", "tB", "tAB", "tU"],
          3: ["tA", "tB", "tC", "tAB", "tAC", "tBC", "tABC", "tU"]}
ORDER = {2: ["tA", "tB", "tAB", "tU", "oA", "oB"],
         3: ["oA", "oB", "oC", "oAB", "oAC", "oBC", "tABC", "tU",
             "tA", "tB", "tC", "tAB", "tAC", "tBC"]}

# Each equation: LEFT = sum(coefficient * variable)
EQUATIONS = {
    2: [("tU", [(1, "tA"), (1, "tB"), (-1, "tAB")]),
        ("tA", [(1, "oA"), (1, "tAB")]),
        ("tB", [(1, "oB"), (1, "tAB")]),
        ("tU", [(1, "oA"), (1, "oB"), (1, "tAB")])],
    3: [("tA", [(1, "oA"), (1, "oAB"), (1, "oAC"), (1, "tABC")]),
        ("tB", [(1, "oB"), (1, "oAB"), (1, "oBC"), (1, "tABC")]),
        ("tC", [(1, "oC"), (1, "oAC"), (1, "oBC"), (1, "tABC")]),
        ("tAB", [(1, "oAB"), (1, "tABC")]),
        ("tAC", [(1, "oAC"), (1, "tABC")]),
        ("tBC", [(1, "oBC"), (1, "tABC")]),
        ("tU", [(1, "tA"), (1, "tB"), (1, "tC"), (-1, "tAB"), (-1, "tAC"),
                (-1, "tBC"), (1, "tABC")]),
        ("tU", [(1, "oA"), (1, "oB"), (1, "oC"), (1, "oAB"), (1, "oAC"),
                (1, "oBC"), (1, "tABC")])],
}

# circles: (x, y, radius, colour, letter, letter_x, letter_y)
GEO = {
    2: {"size": (360, 240),
        "circles": [(125, 125, 88, "#2f6fe4", "A", 52, 38),
                    (235, 125, 88, "#e0483e", "B", 308, 38)],
        "regions": [("oA", 82, 125), ("tAB", 180, 125), ("oB", 278, 125)],
        "map": {"10": "oA", "01": "oB", "11": "tAB"}},
    3: {"size": (360, 320),
        "circles": [(180, 112, 82, "#2f6fe4", "A", 180, 16),
                    (132, 200, 82, "#2ea35a", "B", 40, 292),
                    (228, 200, 82, "#f08a24", "C", 320, 292)],
        "regions": [("oA", 180, 62), ("oB", 88, 230), ("oC", 272, 230),
                    ("oAB", 130, 148), ("oAC", 230, 148), ("oBC", 180, 248),
                    ("tABC", 180, 185)],
        "map": {"100": "oA", "010": "oB", "001": "oC", "110": "oAB",
                "101": "oAC", "011": "oBC", "111": "tABC"}},
}


# ----------------------------------------------------------------------
# 2. SOLVER (no GUI code here, so it can be tested on its own)
# ----------------------------------------------------------------------
def fmt(terms, show):
    """[(1,'tA'),(-1,'tAB')] -> 'n(A) − n(A ∩ B)'"""
    out = ""
    for i, (c, k) in enumerate(terms):
        out += (" − " if c < 0 else " + ") if i else ("−" if c < 0 else "")
        out += str(show(k))
    return out


def solve_simultaneous(m, v, steps):
    """Fallback: let SymPy solve the remaining equations together."""
    todo = [k for k in NAMES[m] if k not in v]
    sym = {k: symbols(k) for k in NAMES[m]}
    exprs = []
    for left, right in EQUATIONS[m]:
        e = sym[left] - sum(c * sym[k] for c, k in right)
        e = e.subs({sym[k]: v[k] for k in v})
        if e.free_symbols:
            exprs.append(e)
    if not todo or not exprs:
        return False
    solution = linsolve(exprs, [sym[k] for k in todo])
    if solution == S.EmptySet:
        return False
    found = False
    for k, val in zip(todo, list(solution)[0]):
        if val.is_number:
            v[k] = int(val) if val.is_integer else val
            steps.append((NAMES[m][k], "found by solving the remaining equations together", "", v[k]))
            found = True
    return found


def solve(m, given):
    """given = {'tA': 15, ...}. Returns values, steps, errors, unknowns."""
    v, steps, errors = dict(given), [], []
    eqs = EQUATIONS[m]
    while True:
        progress = False
        for left, right in eqs:
            names = [left] + [k for _, k in right]
            unknown = [k for k in names if k not in v]
            if len(unknown) != 1:          # need exactly one unknown
                continue
            t = unknown[0]
            if t == left:
                terms = list(right)
            else:                          # rearrange the equation for t
                ct = next(c for c, k in right if k == t)
                terms = [(1, left)] + [(-c, k) for c, k in right if k != t]
                terms = [(c * ct, k) for c, k in terms]
            terms.sort(key=lambda p: -p[0])
            val = sum(c * v[k] for c, k in terms)
            steps.append((NAMES[m][t], fmt(terms, lambda k: NAMES[m][k]),
                          fmt(terms, lambda k: v[k]), val))
            v[t] = val
            progress = True
        if not progress:
            progress = solve_simultaneous(m, v, steps)
        if not progress:
            break

    for k in v:                            # impossible values
        if k not in given and (v[k] < 0 or v[k] != int(v[k])):
            errors.append(f"{NAMES[m][k]} works out to {v[k]}, which is impossible.")
    for left, right in eqs:                # contradictions
        names = [left] + [k for _, k in right]
        if all(k in v for k in names):
            total = sum(c * v[k] for c, k in right)
            if total != v[left]:
                errors.append(f"Values contradict each other: {NAMES[m][left]} = "
                              f"{fmt(right, lambda k: v[k])} = {total}, "
                              f"but {NAMES[m][left]} is {v[left]}.")
                break
    unknown = [k for k in ORDER[m] if k not in v]
    return {"v": v, "given": set(given), "steps": steps,
            "errors": errors, "unknown": unknown}


# ----------------------------------------------------------------------
# 3. INTERFACE (Tkinter)
# ----------------------------------------------------------------------
SC = 1.25  # drawing scale


class SolverTab(ttk.Frame):
    def __init__(self, parent, m):
        super().__init__(parent, padding=8)
        self.m, self.result = m, None
        self.vars = {k: tk.StringVar() for k in NAMES[m]}
        w, h = GEO[m]["size"]

        self.canvas = tk.Canvas(self, width=w * SC, height=h * SC, bg="white",
                                highlightthickness=1, highlightbackground="#cfd9ea")
        self.canvas.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        self.canvas.bind("<Button-1>", self.on_click)

        box = ttk.LabelFrame(self, text="Known values (leave unknown blank)", padding=10)
        box.grid(row=0, column=1, padx=8, pady=8, sticky="n")
        for i, k in enumerate(FIELDS[m]):
            ttk.Label(box, text=NAMES[m][k]).grid(row=i, column=0, sticky="w", pady=3)
            e = ttk.Entry(box, textvariable=self.vars[k], width=8)
            e.grid(row=i, column=1, padx=(12, 0))
            e.bind("<Return>", lambda ev: self.run())
        n = len(FIELDS[m])
        ttk.Button(box, text="Find Missing Values" if m == 2 else "Calculate",
                   command=self.run).grid(row=n, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        ttk.Button(box, text="Reset", command=self.reset).grid(
            row=n + 1, column=0, columnspan=2, sticky="ew")
        ttk.Label(box, text="Tip: click a region in\nthe diagram to enter it.",
                  foreground="#5b6b86").grid(row=n + 2, column=0, columnspan=2, pady=(8, 0))

        self.out = tk.Text(self, height=14, width=78, wrap="word", state="disabled",
                           font=("Cambria", 11))
        self.out.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        for tag, colour in (("ok", "#1b7a3a"), ("solved", "#1b7a3a"),
                            ("warn", "#9a6200"), ("err", "#b3261e")):
            self.out.tag_config(tag, foreground=colour)
        self.out.tag_config("title", font=("Cambria", 12, "bold"))

        for var in self.vars.values():     # any edit clears the old result
            var.trace_add("write", self.on_edit)
        self.draw()

    # ---- diagram -------------------------------------------------------
    def draw(self):
        c, g = self.canvas, GEO[self.m]
        c.delete("all")
        for x, y, r, col, letter, lx, ly in g["circles"]:
            c.create_oval((x - r) * SC, (y - r) * SC, (x + r) * SC, (y + r) * SC,
                          outline=col, width=3)
            c.create_text(lx * SC, ly * SC, text=letter, fill=col,
                          font=("Helvetica", 22, "bold"))
        res = self.result
        size = 20 if self.m == 2 else 15
        for key, x, y in g["regions"]:
            text, colour = "?", "#8a97ad"
            given = self.vars[key].get().strip()
            if res and not res["errors"] and key in res["v"]:
                text = str(res["v"][key])
                colour = "black" if key in res["given"] else "#1b7a3a"
            elif given:
                text, colour = given, "black"
            c.create_text(x * SC, y * SC, text=text, fill=colour,
                          font=("Helvetica", size, "bold"))

    def on_click(self, event):
        g = GEO[self.m]
        x, y = event.x / SC, event.y / SC
        key = g["map"].get("".join("1" if (x - cx) ** 2 + (y - cy) ** 2 <= r * r else "0"
                                   for cx, cy, r, *_ in g["circles"]))
        if not key:
            return
        s = simpledialog.askstring("Region value",
                                   f"Enter {NAMES[self.m][key]} (blank to clear):",
                                   initialvalue=self.vars[key].get(), parent=self)
        if s is None:
            return
        s = s.strip()
        if s == "" or s.isdigit():
            self.vars[key].set(s)
        else:
            messagebox.showerror("Invalid value", "Please enter a whole number (0 or more).")

    # ---- actions -------------------------------------------------------
    def on_edit(self, *_):
        self.result = None
        self.draw()
        self.show(None)

    def run(self):
        given, bad = {}, []
        for k, var in self.vars.items():
            s = var.get().strip()
            if s.isdigit():
                given[k] = int(s)
            elif s:
                bad.append(NAMES[self.m][k])
        if bad:
            self.show({"errors": ["Use whole numbers (0 or more) for: " + ", ".join(bad)]})
            return
        self.result = solve(self.m, given) if given else None
        self.draw()
        self.show(self.result or {"empty": True})

    def reset(self):
        for var in self.vars.values():
            var.set("")

    def show(self, r):
        t = self.out
        t.config(state="normal")
        t.delete("1.0", "end")
        w = lambda s, tag=None: t.insert("end", s, tag)
        if r is None:
            pass
        elif r.get("empty"):
            w("Enter some known values or click regions in the diagram.\n", "warn")
        elif r["errors"]:
            w("Check your values\n", "err")
            for e in r["errors"]:
                w("• " + e + "\n")
        else:
            if r["unknown"]:
                w("Not enough information. Still unknown: "
                  + ", ".join(NAMES[self.m][k] for k in r["unknown"]) + "\n", "warn")
            else:
                w("Results\n", "ok")
            for k in ORDER[self.m]:
                solved = k in r["v"] and k not in r["given"]
                w(f"  {NAMES[self.m][k]} = {r['v'].get(k, '?')}\n", "solved" if solved else None)
            w("\nStep-by-step solution\n", "title")
            if not r["steps"]:
                w("Every value was already given.\n")
            for i, (name, sym, num, val) in enumerate(r["steps"], 1):
                w(f"{i}. {name} = {sym}\n")
                if num:
                    w(f"      = {num}\n")
                w(f"      = {val}\n")
        t.config(state="disabled")


def main():
    root = tk.Tk()
    root.title("Interactive Cardinality Problem Solver")
    tabs = ttk.Notebook(root)
    tabs.add(SolverTab(tabs, 2), text="  Two Sets  ")
    tabs.add(SolverTab(tabs, 3), text="  Three Sets  ")
    tabs.pack(fill="both", expand=True, padx=6, pady=6)
    root.mainloop()


if __name__ == "__main__":
    main()
