"""Pattern definitions for detecting AI code smells."""

from dataclasses import dataclass


@dataclass
class Pattern:
    id: str
    name: str
    severity: str  # "critical", "warning", "info"
    description: str
    pattern: str  # regex
    languages: list[str]  # file extensions
    suggestion: str


# ── AI Code Smells ──────────────────────────────────────────────

AI_SMELLS = [
    Pattern(
        id="broad-except",
        name="Broad Exception Handler",
        severity="warning",
        description="Catching all exceptions hides real bugs. AI loves this pattern.",
        pattern=r"except\s+Exception(\s+as\s+\w+)?:",
        languages=[".py"],
        suggestion="Catch specific exceptions (ValueError, KeyError, etc.) or re-raise.",
    ),
    Pattern(
        id="bare-except",
        name="Bare Except",
        severity="critical",
        description="Bare except catches everything including KeyboardInterrupt. Classic AI move.",
        pattern=r"except\s*:",
        languages=[".py"],
        suggestion="Catch specific exceptions. Never use bare except.",
    ),
    Pattern(
        id="pass-in-except",
        name="Silent Error Suppression",
        severity="warning",
        description="Except block with just 'pass'. Errors disappear silently.",
        pattern=r"except\s+.*:\s*\n\s*pass",
        languages=[".py"],
        suggestion="Log the error or handle it. Silent failures are dangerous.",
    ),
    Pattern(
        id="restating-comment",
        name="Comment Restates Code",
        severity="info",
        description="Comment just repeats what the code does. AI loves narrating code.",
        pattern=r"#\s*(increment|decrement|add|remove|set|get|check|return|print|log|update|create|delete|initialize|append|split|join)\s+",
        languages=[".py"],
        suggestion="Remove comments that restate the code. Explain WHY, not WHAT.",
    ),
    Pattern(
        id="placeholder-var",
        name="Placeholder Variable Names",
        severity="warning",
        description="Variables named 'temp', 'data', 'result', 'foo'. AI generates these by default.",
        pattern=r"\b(temp\d*|data\d*|result\d*|foo|bar|baz|dummy|placeholder|stuff|things?)\s*=",
        languages=[".py", ".js", ".ts", ".jsx", ".tsx"],
        suggestion="Use descriptive names that explain the variable's purpose.",
    ),
    Pattern(
        id="long-function",
        name="Function Too Long",
        severity="warning",
        description="Function over 50 lines. AI tends to write monolithic functions.",
        pattern=r"def\s+\w+.*:$",
        languages=[".py"],
        suggestion="Break into smaller functions. Each function should do one thing.",
    ),
    Pattern(
        id="generic-func-name",
        name="Generic Function Name",
        severity="info",
        description="Function named 'process_data', 'handle_request', etc. Not descriptive.",
        pattern=r"def\s+(process_data|handle_request|do_thing|run_task|main_func|helper|utility|process|handle|run|do|execute)\s*\(",
        languages=[".py"],
        suggestion="Name functions after what they specifically do.",
    ),
    Pattern(
        id="js-console-log",
        name="Leftover console.log",
        severity="info",
        description="Debug console.log left in production code.",
        pattern=r"console\.log\s*\(",
        languages=[".js", ".ts", ".jsx", ".tsx"],
        suggestion="Remove debug logs or replace with proper logging.",
    ),
    Pattern(
        id="js-broad-catch",
        name="Broad Catch Block",
        severity="warning",
        description="Catch block that catches everything without handling specifics.",
        pattern=r"catch\s*\(\s*\w+\s*\)\s*\{",
        languages=[".js", ".ts", ".jsx", ".tsx"],
        suggestion="Handle specific error types or at least log the error properly.",
    ),
    Pattern(
        id="todo-left-in",
        name="TODO/FIXME Left In",
        severity="info",
        description="TODO or FIXME comment left in code. AI scaffolds these often.",
        pattern=r"#\s*(TODO|FIXME|HACK|XXX|NOQA)",
        languages=[".py"],
        suggestion="Resolve or create a tracked issue for each TODO.",
    ),
    Pattern(
        id="js-todo-left-in",
        name="TODO/FIXME Left In",
        severity="info",
        description="TODO or FIXME comment left in code.",
        pattern=r"//\s*(TODO|FIXME|HACK|XXX)",
        languages=[".js", ".ts", ".jsx", ".tsx"],
        suggestion="Resolve or create a tracked issue for each TODO.",
    ),
    Pattern(
        id="magic-number",
        name="Magic Numbers",
        severity="info",
        description="Unexplained numeric literals. AI rarely names constants.",
        pattern=r"(?<!['\"#/\w])(?<!def\s)(?<!class\s)(?<!return\s)(?<!\w)(\d{2,})(?!\w)(?!['\"])(?!\s*[;,]?\s*[\)\]}])",
        languages=[".py", ".js", ".ts"],
        suggestion="Extract into named constants.",
    ),
    Pattern(
        id="unused-import",
        name="Potentially Unused Import",
        severity="info",
        description="AI tends to import more than needed.",
        pattern=r"^import\s+\w+\s*$|^from\s+\w+\s+import\s+\w+",
        languages=[".py"],
        suggestion="Remove unused imports to keep code clean.",
    ),
    Pattern(
        id="docstring-everything",
        name="Over-documented Simple Code",
        severity="info",
        description="Docstrings on trivial functions. AI documents everything.",
        pattern=r'"""\s*(Return|Get|Set|Check|Return|Returns)\s+',
        languages=[".py"],
        suggestion="Only document non-obvious behavior.",
    ),
]

# ── Security Issues ─────────────────────────────────────────────

SECURITY_PATTERNS = [
    Pattern(
        id="hardcoded-secret",
        name="Hardcoded Secret",
        severity="critical",
        description="Possible API key, password, or token in source code.",
        pattern=r"(?i)(api_key|secret|password|token|auth|private_key)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        languages=[".py", ".js", ".ts", ".jsx", ".tsx", ".env"],
        suggestion="Use environment variables. Never commit secrets.",
    ),
    Pattern(
        id="eval-usage",
        name="eval() Usage",
        severity="critical",
        description="eval() can execute arbitrary code. Extremely dangerous.",
        pattern=r"\beval\s*\(",
        languages=[".py", ".js", ".ts"],
        suggestion="Use ast.literal_eval() for Python or JSON.parse() for JS.",
    ),
    Pattern(
        id="exec-usage",
        name="exec() Usage",
        severity="critical",
        description="exec() can execute arbitrary code.",
        pattern=r"\bexec\s*\(",
        languages=[".py"],
        suggestion="Restructure to avoid dynamic code execution.",
    ),
    Pattern(
        id="sql-concat",
        name="SQL String Concatenation",
        severity="critical",
        description="SQL queries built with string concatenation. SQL injection risk.",
        pattern=r'(?:SELECT|INSERT|UPDATE|DELETE|DROP).*?\+\s*(?:f["\']|str\(|format\()|"(?:SELECT|INSERT|UPDATE|DELETE).*?\{',
        languages=[".py", ".js", ".ts"],
        suggestion="Use parameterized queries or an ORM.",
    ),
    Pattern(
        id="shell-true",
        name="subprocess with shell=True",
        severity="critical",
        description="Running subprocess with shell=True enables command injection.",
        pattern=r"subprocess\.\w+\(.*shell\s*=\s*True",
        languages=[".py"],
        suggestion="Use subprocess without shell=True, pass arguments as a list.",
    ),
    Pattern(
        id="pickle-load",
        name="pickle.load on Untrusted Data",
        severity="critical",
        description="pickle can execute arbitrary code during deserialization.",
        pattern=r"pickle\.load",
        languages=[".py"],
        suggestion="Use json or msgpack for untrusted data.",
    ),
    Pattern(
        id="unsafe-yaml",
        name="Unsafe YAML Load",
        severity="critical",
        description="yaml.load without SafeLoader can execute arbitrary code.",
        pattern=r"yaml\.load\s*\((?!.*Loader)",
        languages=[".py"],
        suggestion="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).",
    ),
    Pattern(
        id="cors-wildcard",
        name="CORS Wildcard",
        severity="warning",
        description="CORS set to allow all origins.",
        pattern=r"(?:Access-Control-Allow-Origin|cors|origin).*(?:\*|allow.*all)",
        languages=[".py", ".js", ".ts"],
        suggestion="Restrict to specific domains.",
    ),
    Pattern(
        id="no-input-validation",
        name="Missing Input Validation",
        severity="warning",
        description="User input used directly without validation.",
        pattern=r"request\.(args|form|json|data)\[",
        languages=[".py"],
        suggestion="Validate and sanitize all user input before use.",
    ),
]
