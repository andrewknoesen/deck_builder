import asyncio
import re
from typing import List

import aiohttp

from app.ai.ingestion.base import (
    ContentSplitter,
    IngestionDocument,
    IngestionSource,
    SectionParser,
)
from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import SentenceTransformerEmbedder


class WebSource(IngestionSource):
    """Downloads content from a web URL."""

    def __init__(self, url: str):
        self.url = url

    def load(self, context: PipelineContext) -> IngestionDocument:
        """Downloads the rules text."""
        print(f"Downloading rules from {self.url}...")

        # Determine if we are in an async loop or not.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # In a real app we'd likely make load() async or use a sync client.
            # For this script usage, we'll assume it's main entry point or okay to block if needed (but can't block loop).
            raise NotImplementedError(
                "Async execution needed for aiohttp in sync method"
            )
        else:
            return asyncio.run(self._download())

    async def _download(self) -> IngestionDocument:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download: {response.status}")
                text = await response.text(encoding="utf-8", errors="ignore")
                return IngestionDocument(
                    content=text,
                    source_id=self.url,
                    metadata={"source_type": "web", "url": self.url},
                )


class MtgRulesContentSplitter(ContentSplitter):
    """Splits the Big Text File into Rules and Glossary."""

    def split(
        self, document: IngestionDocument, context: PipelineContext
    ) -> List[IngestionDocument]:
        text = document.content

        # 1. Find Rules Start
        rules_start_match = re.search(r"^1\. Game Concepts", text, re.MULTILINE)
        rules_start_idx = rules_start_match.start() if rules_start_match else 0

        # 2. Find Glossary Start
        glossary_match = re.search(r"^Glossary$", text, re.MULTILINE)

        # 3. Find Credits Start (End of Glossary)
        credits_match = re.search(r"^Credits$", text, re.MULTILINE)

        parts = []

        # Rules Section
        rules_end = glossary_match.start() if glossary_match else len(text)
        rules_text = text[rules_start_idx:rules_end]
        parts.append(
            IngestionDocument(
                content=rules_text,
                source_id=f"{document.source_id}#rules",
                metadata={**document.metadata, "section": "rules"},
            )
        )

        # Glossary Section
        if glossary_match:
            glossary_start = glossary_match.end()
            glossary_end = credits_match.start() if credits_match else len(text)
            glossary_text = text[glossary_start:glossary_end]
            parts.append(
                IngestionDocument(
                    content=glossary_text,
                    source_id=f"{document.source_id}#glossary",
                    metadata={**document.metadata, "section": "glossary"},
                )
            )

        return parts


class MtgRuleParser(SectionParser):
    """Parses the 'Rules' section into individual rules."""

    RULE_PATTERN = re.compile(r"^(\d{3}(?:\.\d+)?(?:[a-z]+)?)\.?\s+(.*)", re.MULTILINE)

    def parse(
        self, section: IngestionDocument, context: PipelineContext
    ) -> List[ProcessedChunk]:
        chunks = []
        lines = section.content.splitlines()

        current_rule_id = None
        current_text_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = self.RULE_PATTERN.match(line)
            if match:
                # Flush previous rule
                if current_rule_id:
                    chunks.append(
                        self._create_chunk(current_rule_id, current_text_lines, section)
                    )

                # Start new rule
                current_rule_id = match.group(1)
                current_text_lines = [match.group(2)]
            else:
                # Continuation of previous rule
                if current_rule_id:
                    current_text_lines.append(line)

        # Flush last rule
        if current_rule_id:
            chunks.append(
                self._create_chunk(current_rule_id, current_text_lines, section)
            )

        return chunks

    def _create_chunk(
        self, rule_id: str, text_lines: List[str], section: IngestionDocument
    ) -> ProcessedChunk:
        full_text = " ".join(text_lines).strip()
        return ProcessedChunk(
            id=f"rule_{rule_id}",
            text=f"{rule_id} {full_text}",
            metadata={**section.metadata, "rule_id": rule_id, "type": "rule"},
            source_document_id=section.source_id,
        )


class MtgGlossaryParser(SectionParser):
    """Parses the 'Glossary' section into terms."""

    def parse(
        self, section: IngestionDocument, context: PipelineContext
    ) -> List[ProcessedChunk]:
        chunks = []
        lines = section.content.splitlines()

        # Current Glossary logic:
        # A term is a single line, not ending in period (usually).
        # Followed by one or more lines of definition.
        # Blank lines separate entries.

        paragraphs: List[List[str]] = []
        buf: List[str] = []
        for line in lines:
            if not line.strip():
                if buf:
                    paragraphs.append(buf)
                    buf = []
            else:
                buf.append(line.strip())
        if buf:
            paragraphs.append(buf)

        for p in paragraphs:
            if not p:
                continue

            # Heuristic: First line is term.
            term = p[0]
            definition = " ".join(p[1:]) if len(p) > 1 else ""

            if definition:
                full_text = f"{term}\n{definition}"
                chunks.append(
                    ProcessedChunk(
                        id=f"glossary_{term.replace(' ', '_').lower()}",
                        text=full_text,
                        metadata={**section.metadata, "term": term, "type": "glossary"},
                        source_document_id=section.source_id,
                    )
                )

        return chunks


def run_ingestion():
    """Main execution function."""
    print("Starting Ingestion Pipeline...")

    # 1. Setup
    context = PipelineContext(execution_id="run_1", timestamp=0)
    source = WebSource(
        url="https://media.wizards.com/2026/downloads/MagicCompRules%2020260116.txt"
    )
    splitter = MtgRulesContentSplitter()
    rule_parser = MtgRuleParser()
    glossary_parser = MtgGlossaryParser()
    embedder = SentenceTransformerEmbedder()
    store = ChromaVectorStore(embedding_model=embedder)

    # 2. Load
    doc = source.load(context)
    print(f"Loaded {len(doc.content)} characters.")

    # 3. Split
    sections = splitter.split(doc, context)
    print(
        f"Split into {len(sections)} sections: {[s.metadata.get('section') for s in sections]}"
    )

    # 4. Parse & Embed & Upsert
    for section in sections:
        section_type = section.metadata.get("section")
        pass
        if section_type == "rules":
            chunks = rule_parser.parse(section, context)
        elif section_type == "glossary":
            chunks = glossary_parser.parse(section, context)
        else:
            continue

        print(f"Parsed {len(chunks)} chunks for section '{section_type}'.")

        print("Embedding...")
        embedder.embed(chunks, context)

        print("Upserting...")
        store.upsert(chunks, context)

    print("Ingestion Complete.")


if __name__ == "__main__":
    run_ingestion()
