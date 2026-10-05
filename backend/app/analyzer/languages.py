from typing import Dict, List
from app.analyzer.models import LanguageStat
from app.github.fetcher import TreeItem

# Extension to language fallback map
EXT_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
}

def analyze_languages(github_languages: Dict[str, int], tree: List[TreeItem]) -> List[LanguageStat]:
    stats: List[LanguageStat] = []
    
    # If GitHub languages data is provided, use it
    if github_languages:
        total_bytes = sum(github_languages.values())
        if total_bytes > 0:
            for lang, count in sorted(github_languages.items(), key=lambda x: x[1], reverse=True):
                pct = round((count / total_bytes) * 100, 1)
                stats.append(LanguageStat(name=lang, percent=pct, bytes=count))
            return stats

    # Fallback to extension counting across tree items
    ext_counts: Dict[str, int] = {}
    for item in tree:
        path = item.path.lower()
        for ext, lang in EXT_TO_LANG.items():
            if path.endswith(ext):
                ext_counts[lang] = ext_counts.get(lang, 0) + 1
                break

    total_files = sum(ext_counts.values())
    if total_files > 0:
        for lang, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / total_files) * 100, 1)
            stats.append(LanguageStat(name=lang, percent=pct, bytes=count))

    return stats
