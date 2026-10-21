"""Parse the official ICD-10-CM tabular XML into a tree:

    chapter -> section -> category -> subcategory ... -> billable code

Billable codes are leaf <diag> elements. Where a 7th character applies (inherited
<sevenChrDef>), the leaf diag becomes an internal node whose children are the
7th-character codes (padded with 'X' placeholders to 6 characters).
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from functools import lru_cache

from src import config


@dataclass
# One node of the ICD-10-CM tree (chapter, section, category, subcategory or billable code)
class Node:
    id: str                      # "ch4", "E08-E13", "E11", "E11.22", "S82.001A"
    desc: str
    kind: str                    # chapter | section | category | subcategory | code
    parent: "Node | None" = None
    children: list = field(default_factory=list)
    n_codes: int = 0             # billable codes under this node (1 for a code)

    @property
    def is_code(self):
        return self.kind == "code"

    # Walk up the tree to the nearest node of the given kind (e.g. the section of a code)
    def ancestor(self, kind):
        n = self
        while n is not None and n.kind != kind:
            n = n.parent
        return n

    def path(self):
        """Human-readable hierarchy, e.g. 'Ch.4 Endocrine... > Diabetes mellitus (E08-E13) > E11 Type 2 ...'."""
        parts, n = [], self
        while n is not None:
            parts.append(n.label())
            n = n.parent
        return " > ".join(reversed(parts))

    # Short display text used in prompts and reports
    def label(self):
        if self.kind == "chapter":
            return f"Ch.{self.id[2:]} {self.desc}"
        if self.kind == "section":
            return self.desc  # already contains the range, e.g. "Diabetes mellitus (E08-E13)"
        return f"{self.id} {self.desc}"


# The whole ICD-10-CM tree, built once from the XML
class Catalog:
    def __init__(self, xml_path=config.ICD_XML):
        root = ET.parse(xml_path).getroot()
        self.version = root.findtext("version")
        self.nodes: dict[str, Node] = {}
        self.chapters: list[Node] = []
        # Walk chapters -> sections -> diag elements, building the tree
        for ch in root.findall("chapter"):
            chap = self._add(Node(f"ch{ch.findtext('name')}", ch.findtext("desc"), "chapter"))
            self.chapters.append(chap)
            for sec in ch.findall("section"):
                s = self._add(Node(sec.get("id"), sec.findtext("desc"), "section", chap))
                for d in sec.findall("diag"):
                    self._add_diag(d, s, "category", seventh=None)
                if s.children:
                    chap.children.append(s)
        # Count billable codes under every node (used for the MAX_CODES decision)
        for chap in self.chapters:
            self._count(chap)
        self.sections = [s for c in self.chapters for s in c.children]
        # separate map: some single-category sections share their id with the category (e.g. "E89")
        self.section_by_id = {s.id: s for s in self.sections}
        # Lookup of all billable codes, used to validate predictions
        self.codes = {k: n for k, n in self.nodes.items() if n.is_code}

    def _add(self, node):
        self.nodes[node.id] = node
        return node

    # Add one <diag> element and its descendants; leaves become billable codes, expanded with 7th characters when required
    def _add_diag(self, el, parent, kind, seventh):
        name, desc = el.findtext("name"), el.findtext("desc")
        sd = el.find("sevenChrDef")
        if sd is not None:
            seventh = [(e.get("char"), e.text) for e in sd.findall("extension")]
        kids = el.findall("diag")
        if not kids and not seventh:
            node = self._add(Node(name, desc, "code", parent))
        else:
            node = self._add(Node(name, desc, kind, parent))
            for k in kids:
                self._add_diag(k, node, "subcategory", seventh)
            if not kids:  # leaf diag that needs a 7th character
                base = name.replace(".", "").ljust(6, "X")
                for char, ext in seventh:
                    code = f"{base[:3]}.{base[3:]}{char}"
                    node.children.append(self._add(Node(code, f"{desc}, {ext}", "code", node)))
        parent.children.append(node)

    # Recursively count billable codes under a node
    def _count(self, node):
        node.n_codes = 1 if node.is_code else sum(self._count(c) for c in node.children)
        return node.n_codes

    # All billable codes below the given nodes (the candidate list for the final step)
    def codes_under(self, nodes):
        out = []
        for n in nodes:
            out.extend([n] if n.is_code else self.codes_under(n.children))
        return out

    def is_billable(self, code):
        return code in self.codes


@lru_cache(maxsize=1)
# Parse the XML only once per process
def get_catalog():
    return Catalog()


# Self-check: python -m src.catalog prints counts and a few example paths
if __name__ == "__main__":
    cat = get_catalog()
    print("version", cat.version, "| chapters", len(cat.chapters), "| sections", len(cat.sections),
          "| categories", sum(n.kind == "category" for n in cat.nodes.values()), "| billable codes", len(cat.codes))
    for c in ["S82.001A", "E11.22", "N39.0", "T07.XXXA", "Z23", "G35", "I47.1"]:
        n = cat.nodes.get(c)
        print(f"{c:10s}", "MISSING" if n is None else f"{n.kind:11s} billable={n.is_code} | {n.path()}")
