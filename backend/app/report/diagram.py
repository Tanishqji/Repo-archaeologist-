import re
from typing import List
from app.report.schemas import ArchitectureComponent

def sanitize_mermaid_label(label: str) -> str:
    """
    Strips dangerous characters, unbalanced brackets, and HTML from node text.
    """
    cleaned = re.sub(r"<[^>]*>", "", label)  # Strip HTML tags
    cleaned = re.sub(r'["`\[\](){}]', '', cleaned)  # Strip brackets and quotes
    cleaned = cleaned.replace("-->", "to").replace("--", "-")
    return cleaned.strip()

def validate_mermaid_syntax(mermaid_str: str) -> bool:
    """
    Validates basic Mermaid flowchart syntax.
    """
    if not mermaid_str or not isinstance(mermaid_str, str):
        return False
    lines = [line.strip() for line in mermaid_str.strip().splitlines() if line.strip()]
    if not lines:
        return False
    first = lines[0].lower()
    valid_starters = ("graph td", "graph lr", "graph tb", "flowchart td", "flowchart lr", "flowchart tb")
    if not any(first.startswith(starter) for starter in valid_starters):
        return False
    return True

def generate_fallback_diagram(
    components: List[ArchitectureComponent],
    pattern: str = "Standard",
) -> str:
    """
    Generates a deterministic, guaranteed-valid Mermaid diagram from architecture components.
    """
    lines = ["flowchart TD", "    subgraph SystemArchitecture [System Architecture]"]

    if not components:
        lines.append('        Client["Client / Browser"] --> App["Application Server"]')
        lines.append('        App --> Storage[("Database / Storage")]')
        lines.append("    end")
        return "\n".join(lines)

    node_ids = []
    for idx, comp in enumerate(components):
        node_id = f"Node{idx + 1}"
        safe_name = sanitize_mermaid_label(comp.name) or f"Component {idx + 1}"
        safe_role = sanitize_mermaid_label(comp.role)
        label = f"{safe_name}: {safe_role}" if safe_role else safe_name
        lines.append(f'        {node_id}["{label}"]')
        node_ids.append(node_id)

    lines.append("    end")

    # Connect nodes linearly or hierarchically
    if len(node_ids) > 1:
        for i in range(len(node_ids) - 1):
            lines.append(f"    {node_ids[i]} --> {node_ids[i+1]}")

    return "\n".join(lines)

def build_validated_diagram(
    raw_mermaid: str,
    components: List[ArchitectureComponent],
    pattern: str = "Standard",
) -> str:
    """
    Validates and sanitizes proposed mermaid diagram, falling back to deterministic diagram on failure.
    """
    if raw_mermaid:
        # Strip code fences if present
        clean = raw_mermaid.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean = "\n".join(lines).strip()

        if validate_mermaid_syntax(clean):
            # Sanitize each line
            sanitized_lines = []
            for line in clean.splitlines():
                # Prevent raw html injection in labels
                sanitized_lines.append(re.sub(r"<[^>]*>", "", line))
            return "\n".join(sanitized_lines)

    return generate_fallback_diagram(components, pattern)
