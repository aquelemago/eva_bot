#!/usr/bin/env python3
"""Documentation auditor for evabot.

Compares Python source code against documentation in documentacao-projeto/,
identifying:
  - Functions/classes in code but not documented (lacunas)
  - Functions/classes mentioned in docs but not in code (obsolescencia)
  - Naming mismatches between code and docs
  - Other inconsistencies

Usage:
    python3 tools/doc-audit.py                    # audit main.py + all docs
    python3 tools/doc-audit.py main.py             # specific source
    python3 tools/doc-audit.py src/                # entire directory
    python3 tools/doc-audit.py --doc-only         # only check doc structure
"""

import ast
import re
import sys
from pathlib import Path

DOC_DIR = Path("documentacao-projeto")
PYTHON_ID_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
FUNC_CALL_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
BACKTICK_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)`")
TABLE_ROW_RE = re.compile(r"^\|.*\|.*\|.*\|.*\|.*\|.*\|")
IGNORED_DOC_SYMBOLS = {
    "True", "False", "None",
    "AGENTS.md", "SKILL.md", "main.py", "credenciais.env",
    "credenciais.env.example", "emails_processados.txt", "requirements.txt",
    "README.md",
    "evabot", "sentry", "playwright", "selenium",
    "Acoes", "Detalhar", "Reenviar", "Expirado", "expirado",
    "skip_expirado", "skip_sem_documento_acionavel",
    "loginbtn", "nextBtn",
    "emails_processados", "bot.log",
}

EXTRA_KEYWORDS = {
    "WebDriverWait", "EC", "By", "Keys", "ActionChains", "Options",
    "Chrome", "Firefox", "Edge",
    "os", "sys", "time", "json", "re", "logging", "subprocess",
    "load_dotenv", "find_element", "find_elements",
}


def _should_filter_doc_symbol(name: str, code_symbols: set) -> bool:
    if name in IGNORED_DOC_SYMBOLS:
        return True
    if name in EXTRA_KEYWORDS:
        return True
    if re.match(r'^[A-Z][A-Z_]*$', name):
        return True
    if '.' in name:
        return True
    if re.match(r'^[a-z]+$', name) and name not in code_symbols:
        return True
    if re.search(r'\.(md|py|txt|env|example|json|yml|yaml|toml|cfg|ini)$', name):
        return True
    return False


def extract_code_symbols(source_code: str) -> dict:
    """Return {name: {'type': 'function'|'class'|'method', 'params': [...], 'file': str}}."""
    symbols = {}
    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            symbols[node.name] = {"type": "function", "params": params, "line": node.lineno}
        elif isinstance(node, ast.AsyncFunctionDef):
            params = [arg.arg for arg in node.args.args]
            symbols[node.name] = {"type": "async_function", "params": params, "line": node.lineno}
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            symbols[node.name] = {"type": "class", "methods": methods, "line": node.lineno}
    return symbols


def extract_doc_symbols(markdown_text: str, filename: str) -> dict:
    """Return {name: {'mentions': [(line, context)], 'file': str}} from markdown."""
    symbols = {}
    lines = markdown_text.split("\n")

    # Track Python code blocks to parse them with AST
    in_code_block = False
    code_buffer = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        line_no = i + 1

        # Track code blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_buffer)
                try:
                    block_symbols = extract_code_symbols(code_text)
                    for name, info in block_symbols.items():
                        if name not in symbols:
                            symbols[name] = {"mentions": [], "file": filename}
                        symbols[name]["mentions"].append((line_no, "[codeblock]"))
                except SyntaxError:
                    pass
                code_buffer = []
            else:
                lang = stripped[3:].strip().lower()
                if lang in ("", "python", "py"):
                    in_code_block = True
            continue
        if in_code_block:
            code_buffer.append(line)
            continue

        # Skip tables (data rows)
        if TABLE_ROW_RE.match(stripped):
            continue

        # 1. Backtick-quoted identifiers
        for match in BACKTICK_RE.finditer(line):
            name = match.group(1)
            if name not in symbols:
                symbols[name] = {"mentions": [], "file": filename}
            symbols[name]["mentions"].append((line_no, line.strip()[:80]))

        # 2. Function calls: name(
        for match in FUNC_CALL_RE.finditer(line):
            name = match.group(1)
            if name in ("if", "for", "while", "with", "not", "or", "and", "in",
                        "is", "def", "class", "return", "import", "from", "as",
                        "elif", "else", "try", "except", "finally", "raise",
                        "break", "continue", "pass", "lambda", "yield", "assert",
                        "del", "global", "nonlocal", "print", "len", "str", "int",
                        "list", "dict", "set", "tuple", "range", "sorted",
                        "enumerate", "zip", "map", "filter", "type", "isinstance",
                        "hasattr", "getattr", "setattr", "super", "open"):
                continue
            if name not in symbols:
                symbols[name] = {"mentions": [], "file": filename}
            symbols[name]["mentions"].append((line_no, line.strip()[:80]))

    return symbols


def audit_code_vs_docs(code_symbols: dict, doc_symbols: dict) -> dict:
    """Compare code symbols against doc symbols and return issues."""
    result = {
        "documented_and_present": [],
        "in_code_not_in_docs": [],
        "in_docs_not_in_code": [],
        "in_docs_ignored": [],
        "name_mismatches": [],
    }

    code_names = set(code_symbols.keys())
    doc_names = set(doc_symbols.keys())

    known_aliases = {
        "clicar_acoes_usuario_por_indice": "clicar_acoes_usuario",
    }

    for name in sorted(code_names & doc_names):
        result["documented_and_present"].append(name)

    alias_targets = set(known_aliases.values())
    for name in sorted(code_names - doc_names):
        if name not in alias_targets:
            result["in_code_not_in_docs"].append(name)

    for name in sorted(doc_names - code_names):
        actual = known_aliases.get(name, name)
        if actual != name:
            result["name_mismatches"].append((name, actual))
        elif _should_filter_doc_symbol(name, code_names):
            result["in_docs_ignored"].append(name)
        else:
            result["in_docs_not_in_code"].append(name)

    return result


SELECTOR_KEYWORDS = (
    "apps-menu-item", "pre-admission", "s-employee", "btn-actions",
    "username-input", "password-input", "loginbtn", "nextBtn",
    "p-paginator", "ui-dropdown", "s-button", "ui-menuitem",
    "ui-tabview", "ui-confirmdialog", "ui-dialog", "ui-table",
    "ui-helper", "ui-chkbox", "ui-inputtext", "close-popup",
    "close-modal", "stieredmenu", "data-testid",
)

SELETOR_LINE_RE = re.compile(r"""['"]([a-zA-Z0-9_\-\.#\[\]\/:@]+(?:-[a-zA-Z0-9]+)*)['"]""")


def _is_selector_candidate(s: str) -> bool:
    if len(s) > 60 or len(s) < 3:
        return False
    if s.startswith(("http", "file://", "data:", "#")):
        return False
    if any(kw in s for kw in SELECTOR_KEYWORDS):
        return True
    if re.match(r'^[.#\[/]', s):
        return True
    return False


def _extract_code_selectors(code: str) -> set:
    selectors = set()
    for line in code.splitlines():
        for match in SELETOR_LINE_RE.finditer(line):
            cand = match.group(1).strip()
            if _is_selector_candidate(cand):
                selectors.add(cand)
    return selectors


def _is_file_ref(s: str) -> bool:
    return bool(re.search(r'\.(md|py|txt|env|example|json|yml|gitignore|log)$', s))

def _is_python_expr(s: str) -> bool:
    return '(' in s or '=' in s or ')' in s or '[' in s or ']' in s or '=>' in s

def _is_url_or_plugin(s: str) -> bool:
    return '@' in s or s.startswith(("http", "file:", "data:", "www."))

def _is_path_like(s: str) -> bool:
    if '/' in s and not s.startswith(('.//', '//', './', '/')):
        return True
    if s.startswith(('logs/', 'venv/', '__pycache__/', '.agents/', 'documentacao-projeto/')):
        return True
    return False

def _looks_like_css_selector(s: str) -> bool:
    if not s:
        return False
    if _is_file_ref(s) or _is_python_expr(s) or _is_url_or_plugin(s) or _is_path_like(s):
        return False
    if any(kw in s for kw in SELECTOR_KEYWORDS):
        return True
    if re.match(r'^[.#\[/\w]', s) and re.search(r'[.#\[:>\]]', s):
        return True
    return False

def _doc_extract_selectors(text: str) -> set:
    selectors = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("|") or stripped.startswith("#"):
            continue
        for match in re.finditer(r'`([^`]+)`', line):
            cand = match.group(1).strip()
            if len(cand) < 2 or len(cand) > 60:
                continue
            if _looks_like_css_selector(cand):
                selectors.add(cand)
    return selectors


def audit_selectors(code: str, doc_texts: dict) -> dict:
    doc_selector_set = set()
    for text in doc_texts.values():
        doc_selector_set |= _doc_extract_selectors(text)

    code_selector_set = _extract_code_selectors(code)

    return {
        "in_docs_not_in_code": sorted(doc_selector_set - code_selector_set),
        "in_code_not_in_docs": sorted(code_selector_set - doc_selector_set),
    }


def audit_security_mentions(code: str, doc_texts: dict) -> list:
    """Check that docs mentioning MODO_TESTE match code reality."""
    issues = []

    modo_in_code = "MODO_TESTE" in code
    modo_in_docs = any("MODO_TESTE" in text for text in doc_texts.values())

    if modo_in_code != modo_in_docs:
        issues.append(
            f"MODO_TESTE: {'presente no codigo' if modo_in_code else 'ausente do codigo'}"
            f" mas {'presente' if modo_in_docs else 'ausente'} na documentacao"
        )

    return issues


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit documentation against source code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("source", nargs="?", default="main.py",
                        help="Source file or directory (default: main.py)")
    parser.add_argument("--doc-dir", default=str(DOC_DIR),
                        help="Documentation directory (default: documentacao-projeto/)")
    parser.add_argument("--doc-only", action="store_true",
                        help="Only check documentation structure, skip code audit")

    args = parser.parse_args()

    doc_path = Path(args.doc_dir)
    if not doc_path.is_dir():
        print(f"[ERRO] Diretorio documental nao encontrado: {doc_path}", file=sys.stderr)
        sys.exit(1)

    # ── Read documentation ──
    doc_files = sorted(doc_path.glob("*.md"))
    if not doc_files:
        print(f"[ERRO] Nenhum arquivo .md encontrado em {doc_path}", file=sys.stderr)
        sys.exit(1)

    doc_texts = {}
    all_doc_symbols = {}
    for mdf in doc_files:
        text = mdf.read_text(encoding="utf-8")
        doc_texts[mdf.name] = text
        symbols = extract_doc_symbols(text, mdf.name)
        for name, info in symbols.items():
            if name not in all_doc_symbols:
                all_doc_symbols[name] = {"mentions": [], "files": set()}
            all_doc_symbols[name]["mentions"].extend(info["mentions"])
            all_doc_symbols[name]["files"].add(mdf.name)

    # ── Read source code ──
    src_path = Path(args.source)
    if src_path.is_dir():
        py_files = sorted(src_path.rglob("*.py"))
    elif src_path.is_file():
        py_files = [src_path]
    else:
        print(f"[ERRO] Caminho nao encontrado: {src_path}", file=sys.stderr)
        sys.exit(1)

    all_code_symbols = {}
    code_texts = {}
    for pyf in py_files:
        # Skip __pycache__, venv
        if any(p.startswith("__") or p == "venv" or p == ".git"
               for p in pyf.relative_to(pyf.anchor).parts):
            continue
        try:
            code = pyf.read_text(encoding="utf-8")
        except Exception:
            continue
        code_texts[pyf.name] = code
        symbols = extract_code_symbols(code)
        for name, info in symbols.items():
            info["file"] = pyf.name
            all_code_symbols[name] = info

    # ── Print report ──
    print("=" * 70)
    print(" DOCUMENTACAO vs CODIGO - RELATORIO DE AUDITORIA")
    print("=" * 70)
    print()

    # ── Documentation files ──
    print("--- ARQUIVOS DE DOCUMENTACAO ---")
    for mdf in doc_files:
        size = len(doc_texts[mdf.name])
        print(f"  {mdf.name} ({size} chars)")
    print()

    # ── Source files ──
    print("--- ARQUIVOS DE CODIGO ANALISADOS ---")
    for pyf in py_files:
        if pyf.name in code_texts:
            size = len(code_texts[pyf.name])
            symbols = all_code_symbols
            print(f"  {pyf.name} ({size} chars, {len(symbols)} simbolos)")
    print()

    if args.doc_only:
        return

    # ── Audit ──
    print("--- AUDITORIA DE SIMBOLOS ---")
    audit = audit_code_vs_docs(all_code_symbols, all_doc_symbols)

    if audit["documented_and_present"]:
        print(f"\n  [OK] Documentados e presentes no codigo ({len(audit['documented_and_present'])}):")
        for name in audit["documented_and_present"]:
            docs_info = all_doc_symbols.get(name, {})
            code_info = all_code_symbols.get(name, {})
            files = docs_info.get("files", set())
            code_file = code_info.get("file", "?")
            sym_type = code_info.get("type", "?")
            print(f"       {name:<40} ({sym_type}) em {code_file}")
            for f in sorted(files):
                print(f"       {'':40}  doc: {f}")

    if audit["in_code_not_in_docs"]:
        print(f"\n  [LACUNA] No codigo mas NAO documentados ({len(audit['in_code_not_in_docs'])}):")
        for name in audit["in_code_not_in_docs"]:
            code_info = all_code_symbols.get(name, {})
            code_file = code_info.get("file", "?")
            sym_type = code_info.get("type", "?")
            print(f"       {name:<40} ({sym_type}) em {code_file}")

    if audit["in_docs_not_in_code"]:
        print(f"\n  [OBSOLETO] Na documentacao mas NAO no codigo ({len(audit['in_docs_not_in_code'])}):")
        for name in audit["in_docs_not_in_code"]:
            docs_info = all_doc_symbols.get(name, {})
            files = docs_info.get("files", set())
            print(f"       {name:<40} mencionado em {', '.join(sorted(files))}")

    if audit["in_docs_ignored"]:
        print(f"\n  [IGNORADO] Referencias nao-rastreaveis (env, arquivos, modulos) ({len(audit['in_docs_ignored'])}):")
        for name in audit["in_docs_ignored"]:
            docs_info = all_doc_symbols.get(name, {})
            files = docs_info.get("files", set())
            print(f"       {name:<40} em {', '.join(sorted(files))}")

    if audit["name_mismatches"]:
        print(f"\n  [DIVERGENCIA] Nomes diferentes entre doc e codigo ({len(audit['name_mismatches'])}):")
        for doc_name, code_name in audit["name_mismatches"]:
            print(f"       Documentacao chama de '{doc_name}'")
            print(f"       Codigo chama de     '{code_name}'")

    # ── Selector audit ──
    combined_code = "\n".join(code_texts.values())
    selector_audit = audit_selectors(combined_code, doc_texts)

    print(f"\n--- SELETORES CSS/XPath ---")
    if selector_audit["in_docs_not_in_code"]:
        print(f"\n  [OBSOLETO] Na documentacao mas NAO no codigo ({len(selector_audit['in_docs_not_in_code'])}):")
        for sel in selector_audit["in_docs_not_in_code"]:
            print(f"       {sel}")
    if selector_audit["in_code_not_in_docs"]:
        print(f"\n  [LACUNA] No codigo mas NAO na documentacao ({len(selector_audit['in_code_not_in_docs'])}):")
        for sel in selector_audit["in_code_not_in_docs"]:
            print(f"       {sel}")

    # ── Security / env audit ──
    sec_issues = audit_security_mentions(combined_code, doc_texts)
    if sec_issues:
        print(f"\n--- INCONSISTENCIAS DE AMBIENTE ---")
        for issue in sec_issues:
            print(f"  [!] {issue}")

    # ── Summary ──
    print()
    print("=" * 70)
    total_code = len(all_code_symbols)
    documented = len(audit["documented_and_present"])
    lacunas = len(audit["in_code_not_in_docs"])
    obsoletos = len(audit["in_docs_not_in_code"])
    ignorados = len(audit["in_docs_ignored"])
    divergencias = len(audit["name_mismatches"])

    if total_code > 0:
        pct = documented * 100 // total_code
    else:
        pct = 0

    print(f"  Total de simbolos no codigo:    {total_code}")
    print(f"  Documentados:                    {documented} ({pct}%)")
    print(f"  Lacunas (code sem doc):          {lacunas}")
    print(f"  Obsoletos (doc sem code):        {obsoletos}")
    print(f"  Ignorados (falso positivo):      {ignorados}")
    print(f"  Divergencias de nome:            {divergencias}")

    if lacunas or obsoletos or divergencias:
        print()
        print("  Recomendacao:")
        if lacunas:
            print(f"    - Adicionar {lacunas} simbolo(s) faltantes na documentacao")
        if obsoletos:
            print(f"    - Revisar {obsoletos} referencia(s) obsoletas na documentacao")
        if divergencias:
            print(f"    - Corrigir {divergencias} divergencia(s) de nome")
    print("=" * 70)


if __name__ == "__main__":
    main()
