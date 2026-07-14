"""Guardrail: flag any self.X used but never defined as a method, a class-level
attribute, or an instance attribute (self.X = ...). Skips classes that inherit
from an external base (their attrs can't be known statically)."""
import ast, sys, glob

def class_defines(cls):
    names = set()
    # methods
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(n.name)
        # class-level constants: NAME = ... / NAME: T = ...
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    for e in t.elts:
                        if isinstance(e, ast.Name):
                            names.add(e.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
    # instance attrs assigned anywhere in the class
    for node in ast.walk(cls):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
           and node.value.id == "self" and isinstance(node.ctx, ast.Store):
            names.add(node.attr)
    return names

def has_external_base(cls):
    for b in cls.bases:
        if isinstance(b, ast.Name) and b.id == "object":
            continue
        return True          # any real base -> may inherit attrs
    return False

def check_file(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    out = []
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if has_external_base(cls):
            continue
        defined = class_defines(cls)
        for node in ast.walk(cls):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
               and node.value.id == "self" and isinstance(node.ctx, ast.Load):
                a = node.attr
                if a in defined or (a.startswith("__") and a.endswith("__")):
                    continue
                out.append(f"{path}:{node.lineno}  {cls.name}.{a}")
    return out

allp = []
for f in sorted(glob.glob("echoquill/*.py")):
    allp += check_file(f)
if allp:
    print("WIRING PROBLEMS:"); print("\n".join(allp)); sys.exit(1)
print("WIRING OK - every self.X reference resolves to a method/attr.")
