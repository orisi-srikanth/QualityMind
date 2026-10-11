"""
Quality Knowledge Agent & Enterprise RAG Pipeline for QualityMind
Implements end-to-end document ingestion, record-aware chunking (preserving complete CSV rows),
metadata extraction, persistent ChromaDB vector storage, semantic retrieval, and source-grounded answer generation.
Fully functional in offline mode (LLM_PROVIDER="none") and with supported LLM providers.
"""
import os
import re
import csv
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import pymupdf

from backend.app.core.config import settings
from backend.app.core.llm import universal_llm
from backend.app.models.schemas import (
    KnowledgeStatusResponse,
    KnowledgeIngestResponse,
    KnowledgeQueryResponse,
    KnowledgeMatchItem
)
from backend.app.services.document_loader import (
    extract_records_from_file,
    infer_document_category,
)

class QualityKnowledgeAgent:
    """Enterprise RAG agent managing manufacturing quality standards, SOPs, and historical incident records."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        docs_directory: Optional[str] = None
    ):
        # Base directories
        self.persist_directory = os.path.abspath(
            persist_directory or getattr(settings, "KNOWLEDGE_DB_PATH", os.path.join(settings.DATA_DIR, "knowledge_db"))
        )
        self.collection_name = collection_name or getattr(
            settings, "KNOWLEDGE_COLLECTION_NAME", "qualityminds_quality_knowledge"
        )
        self.docs_directory = os.path.abspath(
            docs_directory or getattr(settings, "KNOWLEDGE_DOCS_PATH", os.path.join(settings.DATA_DIR, "knowledge_docs"))
        )
        
        os.makedirs(self.persist_directory, exist_ok=True)
        os.makedirs(self.docs_directory, exist_ok=True)

        # Initialize ChromaDB persistent client and local embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

        self.last_ingestion_info: Optional[Dict[str, Any]] = None

    def get_status(self) -> Dict[str, Any]:
        """Returns operational information about the ChromaDB knowledge collection and LLM state."""
        doc_count = self.collection.count()
        llm_mode = getattr(settings, "LLM_PROVIDER", "none").lower()
        llm_enabled = universal_llm.is_enabled() if hasattr(universal_llm, "is_enabled") else (llm_mode != "none")

        # Discover available source files across data directories
        discovered_files = self._discover_source_files()

        warnings = []
        if doc_count == 0:
            warnings.append("Knowledge collection is empty. Run ingestion to index manufacturing records.")
        if not llm_enabled:
            warnings.append("LLM_PROVIDER is 'none': running in deterministic retrieval-only mode with zero external API calls.")

        return {
            "status": "INITIALIZED" if doc_count > 0 else "EMPTY",
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "document_count": doc_count,
            "embedding_model": "all-MiniLM-L6-v2 (Chroma Local ONNX)",
            "embedding_type": "local_onnx",
            "llm_mode": llm_mode,
            "llm_enabled": llm_enabled,
            "available_source_files": [os.path.basename(f) for f in discovered_files],
            "last_ingestion": self.last_ingestion_info,
            "warnings": warnings
        }

    def _discover_source_files(self, custom_paths: Optional[List[str]] = None) -> List[str]:
        """Discovers candidates from configured data directories and files."""
        if custom_paths:
            resolved = []
            for p in custom_paths:
                p_abs = os.path.abspath(p)
                if os.path.isfile(p_abs):
                    resolved.append(p_abs)
                elif os.path.isdir(p_abs):
                    for root, _, files in os.walk(p_abs):
                        for f in files:
                            resolved.append(os.path.join(root, f))
            return sorted(list(set(resolved)))

        # Default directories to search
        search_dirs = [
            self.docs_directory,
            os.path.join(settings.BASE_DIR, "data"),
            os.path.join(settings.BASE_DIR, "backend", "data"),
            os.path.join(settings.BASE_DIR, "backend", "data", "kb")
        ]
        
        found = []
        valid_exts = {".csv", ".json", ".txt", ".md", ".pdf"}

        for d in search_dirs:
            if os.path.exists(d):
                for item in os.listdir(d):
                    full_p = os.path.join(d, item)
                    if os.path.isfile(full_p):
                        _, ext = os.path.splitext(item)
                        if ext.lower() in valid_exts:
                            found.append(os.path.abspath(full_p))

        # Deduplicate by basename to avoid duplicate ingestion of mirrored files
        unique_by_name = {}
        for f in found:
            bname = os.path.basename(f)
            if bname not in unique_by_name:
                unique_by_name[bname] = f
        return sorted(list(unique_by_name.values()))

    def ingest_documents(
        self,
        source_paths: Optional[List[str]] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Extracts, chunks, validates, and stores documents in persistent ChromaDB.
        Preserves entire CSV rows as single cohesive records.
        """
        files = self._discover_source_files(source_paths)
        if force_reindex:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )

        summary = {
            "status": "SUCCESS",
            "files_discovered": len(files),
            "files_processed": 0,
            "files_updated": 0,
            "files_skipped": 0,
            "chunks_added": 0,
            "chunks_updated": 0,
            "chunks_deleted": 0,
            "per_file_status": {},
            "warnings": [],
            "errors": []
        }

        # Fetch existing IDs and content hashes to ensure idempotency
        existing_data = self.collection.get(include=["metadatas"])
        existing_hashes = {}
        if existing_data and existing_data["ids"]:
            for doc_id, meta in zip(existing_data["ids"], existing_data["metadatas"]):
                if meta and "content_hash" in meta:
                    existing_hashes[doc_id] = meta["content_hash"]

        now_iso = datetime.now(timezone.utc).isoformat()

        for fpath in files:
            fname = os.path.basename(fpath)
            _, ext = os.path.splitext(fname)
            ext = ext.lower()

            try:
                records, file_warnings = self._extract_records_from_file(fpath, ext)
                if file_warnings:
                    summary["warnings"].extend(file_warnings)

                if not records:
                    summary["files_skipped"] += 1
                    summary["per_file_status"][fname] = {"status": "SKIPPED_EMPTY", "chunks": 0}
                    continue

                chunks_to_upsert = []
                ids_to_upsert = []
                metas_to_upsert = []
                file_updated = False

                for rec in records:
                    cid = rec["id"]
                    text = rec["text"]
                    chash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    
                    # Check idempotency
                    if not force_reindex and cid in existing_hashes and existing_hashes[cid] == chash:
                        continue  # Already up to date

                    meta = rec["metadata"]
                    meta["content_hash"] = chash
                    meta["ingestion_timestamp"] = now_iso
                    # Ensure ChromaDB-compatible types (str, int, float, bool)
                    sanitized_meta = {k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}

                    ids_to_upsert.append(cid)
                    chunks_to_upsert.append(text)
                    metas_to_upsert.append(sanitized_meta)
                    file_updated = True

                if chunks_to_upsert:
                    self.collection.upsert(
                        ids=ids_to_upsert,
                        documents=chunks_to_upsert,
                        metadatas=metas_to_upsert
                    )
                    summary["chunks_added"] += len(chunks_to_upsert)
                    summary["files_updated"] += 1
                    summary["per_file_status"][fname] = {
                        "status": "UPSERTED",
                        "chunks_added_or_updated": len(chunks_to_upsert)
                    }
                else:
                    summary["files_skipped"] += 1
                    summary["per_file_status"][fname] = {
                        "status": "UNCHANGED_IDEMPOTENT",
                        "chunks": len(records)
                    }

                summary["files_processed"] += 1

            except Exception as e:
                err_msg = f"Failed processing {fname}: {str(e)}"
                summary["errors"].append(err_msg)
                summary["per_file_status"][fname] = {"status": "ERROR", "error": str(e)}

        self.last_ingestion_info = {
            "timestamp": now_iso,
            "total_chunks_in_collection": self.collection.count(),
            "summary": summary
        }
        return summary

    def _extract_records_from_file(self, fpath: str, ext: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parses source file and extracts records with source metadata."""
        return extract_records_from_file(fpath, ext)

    def _infer_category(self, fname: str, row_dict: Optional[dict] = None) -> str:
        """Determines semantic category based on filename or contents."""
        return infer_document_category(fname, row_dict)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs semantic retrieval with metadata filtering, accurate distance reporting,
        and deterministic or grounded LLM answer generation.
        """
        q_clean = query_text.strip() if query_text else ""
        if not q_clean:
            raise ValueError("Query string cannot be empty or whitespace.")

        top_k = max(1, min(50, top_k))
        warnings = []

        if self.collection.count() == 0:
            return {
                "query": q_clean,
                "answer": "Knowledge collection is currently empty. Please run document ingestion.",
                "answer_mode": "empty_database",
                "llm_enabled": False,
                "results_count": 0,
                "matches": [],
                "sources": [],
                "distance_metric": "cosine_distance",
                "warnings": ["Vector database contains 0 indexed documents."]
            }

        # Build ChromaDB where filter
        where_filter = {}
        if filters:
            valid_keys = {
                "category", "doc_type", "source_file", "batch_id", "machine_id", "machine",
                "part_number", "record_id", "defect_type", "defect_family", "proxy_category", "provenance"
            }
            for k, v in filters.items():
                if k in valid_keys and v is not None and str(v).strip():
                    where_filter[k] = str(v).strip()

        # Chroma query
        query_params = {
            "query_texts": [q_clean],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            if len(where_filter) == 1:
                query_params["where"] = where_filter
            else:
                query_params["where"] = {"$and": [{k: v} for k, v in where_filter.items()]}

        try:
            res = self.collection.query(**query_params)
        except Exception as e:
            # Fallback without where filter if filter was invalid or returned empty
            warnings.append(f"Query filter exception: {str(e)}. Falling back to unfiltered search.")
            query_params.pop("where", None)
            res = self.collection.query(**query_params)

        matches: List[Dict[str, Any]] = []
        sources: List[str] = []

        if res and res["documents"] and res["documents"][0]:
            docs = res["documents"][0]
            metas = res["metadatas"][0] if res["metadatas"] else [{}] * len(docs)
            dists = res["distances"][0] if res["distances"] else [0.0] * len(docs)
            ids = res["ids"][0] if res["ids"] else [f"doc-{i}" for i in range(len(docs))]

            for rank, (doc_id, text, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
                # In cosine space, distance d in [0, 2]. Similarity is 1 - d/2.
                dist_val = float(dist)
                sim_score = max(0.0, round(1.0 - (dist_val / 2.0), 4))
                
                src_file = meta.get("file_name", "unknown")
                rec_id = meta.get("record_id")
                category = meta.get("category", "general")

                citation_name = f"{src_file}:{rec_id}" if rec_id else src_file
                if citation_name not in sources:
                    sources.append(citation_name)

                matches.append({
                    "id": doc_id,
                    "text": text,
                    "source_file": src_file,
                    "record_id": rec_id,
                    "category": category,
                    "metadata": meta,
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": round(dist_val, 4),
                    "similarity_score": sim_score,
                    "distance_metric": "cosine_distance",
                    "rank": rank
                })

        # Generate Grounded Answer based on LLM configuration mode
        llm_mode = getattr(settings, "LLM_PROVIDER", "none").lower()
        llm_active = universal_llm.is_enabled() if hasattr(universal_llm, "is_enabled") else (llm_mode != "none")

        if not matches:
            return {
                "query": q_clean,
                "answer": "No relevant manufacturing quality documents or records were found matching the query.",
                "answer_mode": "no_matches",
                "llm_enabled": llm_active,
                "results_count": 0,
                "matches": [],
                "sources": [],
                "distance_metric": "cosine_distance",
                "warnings": warnings
            }

        if not llm_active or llm_mode in ["none", ""]:
            # Mode 1: Deterministic retrieval only (Zero LLM calls)
            deterministic_answer = self._generate_deterministic_summary(q_clean, matches)
            return {
                "query": q_clean,
                "answer": deterministic_answer,
                "answer_mode": "deterministic_retrieval_only",
                "llm_enabled": False,
                "results_count": len(matches),
                "matches": matches,
                "sources": sources,
                "distance_metric": "cosine_distance",
                "warnings": warnings
            }
        else:
            # Mode 2: Grounded LLM generation via Universal LLM Client
            llm_answer = self._generate_grounded_llm_answer(q_clean, matches, sources)
            return {
                "query": q_clean,
                "answer": llm_answer,
                "answer_mode": "grounded_llm_generation",
                "llm_enabled": True,
                "results_count": len(matches),
                "matches": matches,
                "sources": sources,
                "distance_metric": "cosine_distance",
                "warnings": warnings
            }

    def _generate_deterministic_summary(self, query: str, matches: List[Dict[str, Any]]) -> str:
        """Produces a deterministic, hallucination-free evidence summary linking to citations."""
        lines = [
            f"[Deterministic Evidence Summary] Retrieved {len(matches)} matching quality record(s) for query: '{query}'",
            "--------------------------------------------------------------------------------"
        ]
        for m in matches[:3]:
            rec_str = f"Record: {m['record_id']} | " if m.get("record_id") else ""
            lines.append(f"• [Rank {m['rank']}] Source: {m['source_file']} ({rec_str}Similarity: {m['similarity_score']})")
            
            # Extract first 2-3 lines of content for summary
            snippet_lines = [l.strip() for l in m["text"].split("\n") if l.strip()]
            for s in snippet_lines[1:4]:
                lines.append(f"    - {s}")
            lines.append("")

        lines.append("Note: Running in offline deterministic mode (LLM_PROVIDER='none'). Zero LLM tokens generated.")
        return "\n".join(lines)

    def _generate_grounded_llm_answer(self, query: str, matches: List[Dict[str, Any]], sources: List[str]) -> str:
        """Instructs the configured LLM to answer strictly from retrieved context with citations."""
        context_blocks = []
        for m in matches:
            citation = f"[{m['source_file']} | Record: {m.get('record_id', 'N/A')}]"
            context_blocks.append(f"--- Context Block {citation} ---\n{m['text']}")

        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are the Quality Knowledge Retrieval Assistant for QualityMind. "
            "Your role is to answer manufacturing engineering questions strictly using the provided context blocks.\n"
            "Strict Guidelines:\n"
            "1. Ground all statements in the retrieved context. Cite specific Record IDs (e.g., NCR-019, MNT-2026-041) or file names.\n"
            "2. Distinguish confirmed historical facts from potential hypotheses or current part measurements.\n"
            "3. If the context does not provide sufficient information, state clearly: 'The retrieved records provide insufficient evidence to answer this question.'\n"
            "4. Never present historical correlation as confirmed causation of a new incident.\n"
            "5. Do NOT perform authoritative dimensional tolerance compliance checks (that is reserved for Agent 3)."
        )

        user_content = f"User Question: {query}\n\nRetrieved Knowledge Context:\n{context_str}\n\nPlease provide a clear, source-cited summary:"

        try:
            resp = universal_llm.chat(
                agent_id="agent_6",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            if resp and resp.get("content"):
                return resp["content"].strip()
        except Exception as e:
            pass

        # Fallback to deterministic summary if LLM call fails
        return self._generate_deterministic_summary(query, matches)

# Global singleton instance
quality_knowledge_agent = QualityKnowledgeAgent()
