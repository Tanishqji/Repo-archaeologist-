import re
from typing import Dict, List
from app.analyzer.models import EndpointInfo

ROUTE_PATTERNS = [
    # FastAPI / Starlette / Flask decorators: @app.get("/items"), @router.post("/users")
    re.compile(r"""@(?:\w+\.)?(get|post|put|delete|patch|options|head)\s*\(\s*["']([^"']+)["']""", re.IGNORECASE),
    # Flask @app.route("/items", methods=["GET", "POST"])
    re.compile(r"""@(?:\w+\.)?route\s*\(\s*["']([^"']+)["'](?:.*methods=\s*\[(.*?)\])?""", re.IGNORECASE),
    # Express / Fastify / Koa: app.get('/items', ...), router.post('/users', ...)
    re.compile(r"""(?:\b(?:app|router|server))\.(get|post|put|delete|patch|options|head)\s*\(\s*["']([^"']+)["']""", re.IGNORECASE),
    # Spring Boot: @GetMapping("/items"), @PostMapping("/users")
    re.compile(r"""@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*(?:value\s*=\s*)?["']([^"']+)["']""", re.IGNORECASE),
    # Go (Gin, Echo): r.GET("/items", ...), e.POST("/users", ...)
    re.compile(r"""\b(?:r|router|e|g|api)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["']([^"']+)["']"""),
]

def detect_routes(files: Dict[str, str]) -> List[EndpointInfo]:
    endpoints: List[EndpointInfo] = []
    seen = set()

    for path, content in files.items():
        # Only inspect code files
        if not path.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php", ".rs")):
            continue

        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                groups = match.groups()
                method = "GET"
                route_path = "/"

                if len(groups) == 2:
                    g0, g1 = groups[0], groups[1]
                    if g0.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "REQUEST"):
                        method = g0.upper() if g0.upper() != "REQUEST" else "ANY"
                        route_path = g1
                    else:
                        route_path = g0
                        if g1:  # Flask methods list
                            methods_str = g1.replace("'", "").replace('"', "").replace(" ", "")
                            method = methods_str.split(",")[0].upper() if methods_str else "GET"

                key = (method, route_path, path)
                if key not in seen:
                    seen.add(key)
                    endpoints.append(
                        EndpointInfo(
                            method=method,
                            path=route_path,
                            file=path,
                        )
                    )

    # Sort endpoints by path
    return sorted(endpoints, key=lambda x: (x.path, x.method))
