import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from template_registry import EXPLANATION_TEMPLATES


class TemplateEngine:

    def render(self, template_name: str, variables: dict) -> str:
        template = EXPLANATION_TEMPLATES.get(template_name)
        if not template:
            return f"[NO TEMPLATE: {template_name}]"
        try:
            return template.format(**variables)
        except KeyError as e:
            return f"[TEMPLATE ERROR: Missing variable {e}]"