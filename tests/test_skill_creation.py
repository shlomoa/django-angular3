"""Regression tests for skill creation supporting-file references."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_CREATION = REPOSITORY_ROOT / "skill_creation"
SKILL_FILES = sorted((SKILL_CREATION / "skills").glob("*.md"))
OBSOLETE_DIRECTIVE = re.compile(r"\{\{(?:context|template):")
FRONTMATTER = re.compile(r"```yaml\n---\n(.*?)\n---\n```", re.DOTALL)
WHEN_TO_USE = re.compile(r"^when_to_use:", re.MULTILINE)
SHARED_REFERENCE = re.compile(r"\[[^\]]+\]\((\.\./shared/[^)]+)\)")
ON_DEMAND_READ = re.compile(r"read (?:this )?on demand")


class SkillCreationReferenceTests(unittest.TestCase):
    def test_working_set_uses_no_obsolete_inclusion_directives(self) -> None:
        for path in SKILL_CREATION.rglob("*.md"):
            with self.subTest(path=path.relative_to(REPOSITORY_ROOT)):
                self.assertNotRegex(path.read_text(), OBSOLETE_DIRECTIVE)

    def test_all_skill_working_copies_retain_when_to_use_frontmatter(self) -> None:
        self.assertEqual(len(SKILL_FILES), 11)
        for path in SKILL_FILES:
            with self.subTest(path=path.relative_to(REPOSITORY_ROOT)):
                match = FRONTMATTER.search(path.read_text())
                self.assertIsNotNone(match)
                self.assertRegex(match.group(1), WHEN_TO_USE)

    def test_shared_references_are_on_demand_relative_markdown_links(self) -> None:
        for path in SKILL_FILES:
            content = path.read_text()
            references = SHARED_REFERENCE.findall(content)
            for reference in references:
                with self.subTest(
                    path=path.relative_to(REPOSITORY_ROOT), reference=reference
                ):
                    self.assertTrue((path.parent / reference).is_file())
            if references:
                self.assertRegex(content, ON_DEMAND_READ)
