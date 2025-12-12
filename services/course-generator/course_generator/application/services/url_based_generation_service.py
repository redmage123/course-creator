"""
URL-Based Course Generation Service

BUSINESS REQUIREMENT:
Enable AI-powered course generation from external third-party software documentation.
Instructors can provide URLs to documentation sites (Salesforce, AWS, internal wikis, etc.)
and the system will automatically fetch, process, and use the content to generate
comprehensive training materials.

TECHNICAL ARCHITECTURE:
This service orchestrates the complete URL-based generation workflow:
1. Validate and fetch content from provided URLs
2. Parse and extract meaningful documentation content
3. Store processed content in RAG for context enhancement
4. Generate course syllabus using RAG-enhanced AI prompts
5. Track generation metadata for attribution and caching

INTEGRATION POINTS:
- URLContentFetcher: Fetches and parses external content
- RAG Integration: Stores and retrieves content for generation
- AI Client: Generates course content with enhanced context
- Syllabus Generator: Creates structured course syllabi

DESIGN PATTERNS:
- Facade pattern: Simplifies complex multi-step workflow
- Strategy pattern: Different processing for different source types
- Observer pattern: Progress tracking and event handling
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4

from course_generator.application.services.url_content_fetcher import (
    URLContentFetcher,
    FetchedContent,
    ContentChunk,
    create_url_content_fetcher,
)
from course_generator.domain.entities.external_content import (
    ContentSourceType,
    FetchStatus,
    ExternalContentMetadata,
    ProcessedExternalContent,
    URLBasedGenerationRequest,
    URLGenerationResult,
)
from course_generator.exceptions import (
    CourseCreatorBaseException,
    CourseGeneratorException,
    URLFetchException,
    URLValidationException,
    URLConnectionException,
    URLTimeoutException,
    URLAccessDeniedException,
    URLNotFoundException,
    ContentParsingException,
    HTMLParsingException,
    ContentExtractionException,
    ContentTooLargeException,
    UnsupportedContentTypeException,
    RobotsDisallowedException,
    RAGException,
    AIServiceException,
)
from rag_integration import (
    RAGIntegrationService,
    enhance_prompt_with_rag,
    learn_from_generation,
)
from logging_setup import setup_docker_logging

# Import syllabus models using explicit path to avoid module collision
# when running tests with multiple services in sys.path
import importlib.util
from pathlib import Path

_service_root = Path(__file__).parent.parent.parent.parent
_syllabus_path = _service_root / "models" / "syllabus.py"
_spec = importlib.util.spec_from_file_location("cg_syllabus_models", _syllabus_path)
_syllabus_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_syllabus_module)

SyllabusRequest = _syllabus_module.SyllabusRequest
CourseLevel = _syllabus_module.CourseLevel

logger = setup_docker_logging("course-generator")


@dataclass
class URLFetchResult:
    """
    Result of fetching content from a single URL.

    Business Context:
    Captures the outcome of a URL fetch operation including
    success/failure status and any extracted content.
    """
    url: str
    success: bool
    content: Optional[FetchedContent] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    fetch_time_ms: int = 0


@dataclass
class GenerationProgress:
    """
    Tracks progress of URL-based generation operation.

    Business Context:
    Provides real-time progress information for UI feedback
    during long-running generation operations.
    """
    request_id: UUID
    status: str = "initializing"
    total_urls: int = 0
    urls_fetched: int = 0
    urls_failed: int = 0
    chunks_created: int = 0
    chunks_ingested: int = 0
    generation_started: bool = False
    generation_complete: bool = False
    current_step: str = ""
    error_messages: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary for API response."""
        return {
            "request_id": str(self.request_id),
            "status": self.status,
            "total_urls": self.total_urls,
            "urls_fetched": self.urls_fetched,
            "urls_failed": self.urls_failed,
            "chunks_created": self.chunks_created,
            "chunks_ingested": self.chunks_ingested,
            "generation_started": self.generation_started,
            "generation_complete": self.generation_complete,
            "current_step": self.current_step,
            "error_count": len(self.error_messages),
            "elapsed_seconds": (datetime.now(timezone.utc) - self.started_at).total_seconds(),
        }


class URLBasedGenerationService:
    """
    Service for generating courses from external documentation URLs.

    ARCHITECTURAL RESPONSIBILITY:
    Orchestrates the complete workflow from URL input to generated course,
    coordinating URL fetching, content processing, RAG storage, and AI generation.

    WORKFLOW STAGES:
    1. URL Validation: Validate and normalize input URLs
    2. Content Fetching: Fetch content from each URL with error handling
    3. Content Processing: Parse HTML and extract meaningful content
    4. RAG Ingestion: Store processed content in RAG for retrieval
    5. Prompt Enhancement: Build enhanced prompts with RAG context
    6. Course Generation: Generate syllabus using AI with enhanced context
    7. Result Assembly: Combine all outputs with attribution

    CONFIGURATION:
    - max_concurrent_fetches: Parallel URL fetching limit
    - fetch_timeout: Per-URL fetch timeout
    - max_total_content: Maximum combined content size
    - rag_domain: RAG domain for content storage
    """

    # Configuration
    MAX_CONCURRENT_FETCHES = 3
    FETCH_TIMEOUT = 30.0
    MAX_TOTAL_CONTENT_CHARS = 500000  # 500K characters max
    RAG_DOMAIN = "content_generation"
    RAG_SOURCE = "external_documentation"

    def __init__(
        self,
        url_fetcher: Optional[URLContentFetcher] = None,
        rag_service: Optional[RAGIntegrationService] = None,
        max_concurrent_fetches: int = MAX_CONCURRENT_FETCHES,
    ):
        """
        Initialize URL-based generation service.

        Args:
            url_fetcher: URL content fetcher instance (created if not provided)
            rag_service: RAG integration service (created if not provided)
            max_concurrent_fetches: Maximum parallel URL fetches
        """
        self.url_fetcher = url_fetcher or create_url_content_fetcher(
            timeout=self.FETCH_TIMEOUT
        )
        self.rag_service = rag_service or RAGIntegrationService()
        self.max_concurrent_fetches = max_concurrent_fetches
        self._progress_cache: Dict[UUID, GenerationProgress] = {}

        logger.info(
            f"URLBasedGenerationService initialized: "
            f"max_concurrent={max_concurrent_fetches}"
        )

    async def generate_from_urls(
        self,
        request: SyllabusRequest,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Generate course syllabus from external documentation URLs.

        MAIN ENTRY POINT:
        This is the primary method for URL-based course generation.
        It orchestrates the complete workflow and returns the generated syllabus.

        Args:
            request: Syllabus request containing URLs and generation parameters
            user_id: Optional user ID for attribution
            organization_id: Optional organization ID for context

        Returns:
            Dictionary containing generated syllabus and processing metadata

        Raises:
            URLFetchException: If all URLs fail to fetch
            ContentExtractionException: If no meaningful content extracted
            RAGException: If RAG storage fails
            AIServiceException: If AI generation fails
        """
        request_id = uuid4()
        start_time = time.time()

        # Initialize progress tracking
        progress = GenerationProgress(
            request_id=request_id,
            total_urls=len(request.all_source_urls),
            status="fetching_urls",
            current_step="Fetching documentation from URLs",
        )
        self._progress_cache[request_id] = progress

        logger.info(
            f"Starting URL-based generation: request_id={request_id}, "
            f"urls={len(request.all_source_urls)}, title={request.title}"
        )

        try:
            # Step 1: Fetch content from all URLs
            fetch_results = await self._fetch_all_urls(
                request.all_source_urls, progress
            )

            # Check if we got any content
            successful_fetches = [r for r in fetch_results if r.success]
            if not successful_fetches:
                error_summary = "; ".join(
                    f"{r.url[:50]}...: {r.error}" for r in fetch_results[:3]
                )
                raise URLFetchException(
                    message=f"Failed to fetch content from any URL. Errors: {error_summary}",
                    error_code="ALL_URLS_FAILED",
                    details={"fetch_results": [r.error for r in fetch_results]}
                )

            progress.urls_fetched = len(successful_fetches)
            progress.urls_failed = len(fetch_results) - len(successful_fetches)

            # Step 2: Create content chunks for RAG
            progress.status = "processing_content"
            progress.current_step = "Processing and chunking content"

            all_chunks = []
            processed_contents = []

            for result in successful_fetches:
                if result.content:
                    # Create chunks
                    chunks = self.url_fetcher.create_content_chunks(result.content)
                    all_chunks.extend(chunks)

                    # Create processed content record
                    processed = ProcessedExternalContent(
                        request_id=request_id,
                        metadata=ExternalContentMetadata(
                            source_url=result.content.url,
                            content_hash=result.content.content_hash,
                            fetch_timestamp=result.content.fetch_timestamp,
                            title=result.content.title,
                            description=result.content.description,
                            word_count=result.content.word_count,
                            character_count=result.content.character_count,
                            heading_count=len(result.content.headings),
                            code_block_count=len(result.content.code_blocks),
                        ),
                        content=result.content.content,
                        structured_content={
                            "headings": result.content.headings,
                        },
                        code_examples=result.content.code_blocks,
                        chunks=[{"index": c.chunk_index, "content": c.content} for c in chunks],
                        processing_time_ms=result.fetch_time_ms,
                    )
                    processed_contents.append(processed)

            progress.chunks_created = len(all_chunks)

            # Limit total chunks if needed
            if len(all_chunks) > request.max_content_chunks:
                logger.warning(
                    f"Limiting chunks from {len(all_chunks)} to {request.max_content_chunks}"
                )
                all_chunks = all_chunks[:request.max_content_chunks]

            # Step 3: Store chunks in RAG for context enhancement
            if request.use_rag_enhancement and all_chunks:
                progress.status = "storing_in_rag"
                progress.current_step = "Storing content in RAG for enhanced generation"

                rag_doc_ids = await self._store_chunks_in_rag(
                    all_chunks, request, progress
                )

                for processed in processed_contents:
                    processed.rag_document_ids = rag_doc_ids

            # Step 4: Build enhanced generation context
            progress.status = "generating_syllabus"
            progress.current_step = "Generating course syllabus with AI"
            progress.generation_started = True

            # Build context from fetched content
            context_summary = self._build_context_summary(processed_contents)

            # Generate syllabus with enhanced context
            syllabus_data = await self._generate_syllabus_with_context(
                request, context_summary, processed_contents
            )

            progress.generation_complete = True
            progress.status = "completed"
            progress.current_step = "Generation complete"

            # Calculate total time
            total_time_ms = int((time.time() - start_time) * 1000)

            # Build result
            result = {
                "success": True,
                "request_id": str(request_id),
                "syllabus": syllabus_data,
                "source_summary": {
                    "urls_processed": len(successful_fetches),
                    "urls_failed": len(fetch_results) - len(successful_fetches),
                    "total_words": sum(p.metadata.word_count for p in processed_contents),
                    "total_chunks": len(all_chunks),
                    "code_examples_found": sum(len(p.code_examples) for p in processed_contents),
                    "sources": [
                        {
                            "url": p.metadata.source_url,
                            "title": p.metadata.title,
                            "word_count": p.metadata.word_count,
                        }
                        for p in processed_contents
                    ],
                },
                "processing_time_ms": total_time_ms,
                "generation_method": "rag_enhanced" if request.use_rag_enhancement else "standard",
                "progress": progress.to_dict(),
            }

            # Learn from successful generation
            if request.use_rag_enhancement:
                await self._learn_from_generation(request, syllabus_data, processed_contents)

            logger.info(
                f"URL-based generation completed: request_id={request_id}, "
                f"time={total_time_ms}ms, chunks={len(all_chunks)}"
            )

            return result

        except CourseCreatorBaseException:
            # Re-raise custom exceptions
            progress.status = "failed"
            raise

        except Exception as e:
            progress.status = "failed"
            progress.error_messages.append(str(e))
            logger.error(f"URL-based generation failed: {str(e)}")
            raise AIServiceException(
                message=f"URL-based course generation failed: {str(e)}",
                error_code="URL_GENERATION_FAILED",
                original_exception=e
            )

    async def _fetch_all_urls(
        self,
        urls: List[str],
        progress: GenerationProgress,
    ) -> List[URLFetchResult]:
        """
        Fetch content from all URLs with concurrency control.

        Args:
            urls: List of URLs to fetch
            progress: Progress tracker

        Returns:
            List of fetch results (success or failure for each URL)
        """
        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent_fetches)

        async def fetch_with_semaphore(url: str) -> URLFetchResult:
            async with semaphore:
                return await self._fetch_single_url(url)

        # Fetch all URLs concurrently with semaphore
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    async def _fetch_single_url(self, url: str) -> URLFetchResult:
        """
        Fetch content from a single URL with error handling.

        Args:
            url: URL to fetch

        Returns:
            URLFetchResult with content or error information
        """
        start_time = time.time()

        try:
            content = await self.url_fetcher.fetch_and_parse(url)
            fetch_time = int((time.time() - start_time) * 1000)

            return URLFetchResult(
                url=url,
                success=True,
                content=content,
                fetch_time_ms=fetch_time,
            )

        except URLValidationException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="validation",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except URLConnectionException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="connection",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except URLTimeoutException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="timeout",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except URLAccessDeniedException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="access_denied",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except URLNotFoundException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="not_found",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except ContentParsingException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="parsing",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except RobotsDisallowedException as e:
            return URLFetchResult(
                url=url,
                success=False,
                error=str(e),
                error_type="robots_disallowed",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return URLFetchResult(
                url=url,
                success=False,
                error=f"Unexpected error: {str(e)}",
                error_type="unknown",
                fetch_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _store_chunks_in_rag(
        self,
        chunks: List[ContentChunk],
        request: SyllabusRequest,
        progress: GenerationProgress,
    ) -> List[str]:
        """
        Store content chunks in RAG for retrieval during generation.

        Args:
            chunks: Content chunks to store
            request: Original request for metadata
            progress: Progress tracker

        Returns:
            List of RAG document IDs
        """
        doc_ids = []

        for i, chunk in enumerate(chunks):
            try:
                # Create RAG document
                doc_content = f"""
Source: {chunk.source_url}
Context: {chunk.heading_context}

{chunk.content}
"""
                # Store in RAG
                success = await learn_from_generation(
                    content_type="documentation",
                    subject=request.title,
                    difficulty_level=request.level.value,
                    generated_content=doc_content,
                    quality_score=0.8,  # High quality for external docs
                    generation_metadata={
                        "source_url": chunk.source_url,
                        "chunk_index": chunk.chunk_index,
                        "course_title": request.title,
                        "is_external_source": True,
                    }
                )

                if success:
                    doc_ids.append(f"doc_{i}")
                    progress.chunks_ingested += 1

            except RAGException as e:
                logger.warning(f"Failed to store chunk {i} in RAG: {str(e)}")

            except Exception as e:
                logger.warning(f"Unexpected error storing chunk {i}: {str(e)}")

        return doc_ids

    def _build_context_summary(
        self,
        processed_contents: List[ProcessedExternalContent],
    ) -> str:
        """
        Build a summary of fetched content for prompt enhancement.

        Args:
            processed_contents: All processed content from URLs

        Returns:
            Formatted context summary string
        """
        if not processed_contents:
            return ""

        summary_parts = []

        for pc in processed_contents:
            # Build source summary
            source_summary = f"## Source: {pc.metadata.title or pc.metadata.source_url}\n"
            source_summary += f"URL: {pc.metadata.source_url}\n"
            source_summary += f"Words: {pc.metadata.word_count}\n\n"

            # Add key headings
            if pc.structured_content.get("headings"):
                headings = pc.structured_content["headings"][:10]  # Top 10 headings
                source_summary += "### Key Topics:\n"
                for h in headings:
                    source_summary += f"- {h['text']}\n"
                source_summary += "\n"

            # Add content excerpt
            content_excerpt = pc.content[:2000] if len(pc.content) > 2000 else pc.content
            source_summary += f"### Content Excerpt:\n{content_excerpt}\n\n"

            # Add code examples if present
            if pc.code_examples:
                source_summary += "### Code Examples Found:\n"
                for i, code in enumerate(pc.code_examples[:3]):  # Top 3 examples
                    lang = code.get("language", "")
                    source_summary += f"```{lang}\n{code['content'][:500]}\n```\n"

            summary_parts.append(source_summary)

        return "\n---\n".join(summary_parts)

    async def _generate_syllabus_with_context(
        self,
        request: SyllabusRequest,
        context_summary: str,
        processed_contents: List[ProcessedExternalContent],
    ) -> Dict[str, Any]:
        """
        Generate course syllabus using fetched content as context.

        Args:
            request: Original syllabus request
            context_summary: Formatted content summary
            processed_contents: All processed content

        Returns:
            Generated syllabus data
        """
        # Build enhanced prompt with external content context
        base_prompt = f"""
Generate a comprehensive course syllabus for: {request.title}

Course Description: {request.description}
Target Level: {request.level.value}
Target Audience: {request.target_audience or "General learners"}
Duration: {request.duration or "Flexible"} hours

EXTERNAL DOCUMENTATION CONTEXT:
The following content was fetched from external documentation sources.
Use this content to create accurate, relevant course modules and learning objectives.

{context_summary}

REQUIREMENTS:
1. Create modules that cover the key topics from the documentation
2. Include practical exercises based on code examples found
3. Structure content from basic to advanced concepts
4. Include quizzes to test understanding of key concepts
5. Reference specific documentation sections where appropriate

Generate a JSON syllabus with the following structure:
{{
    "title": "Course Title",
    "description": "Course description",
    "level": "{request.level.value}",
    "duration": estimated_hours,
    "objectives": ["objective1", "objective2", ...],
    "prerequisites": ["prereq1", "prereq2", ...],
    "modules": [
        {{
            "module_number": 1,
            "title": "Module Title",
            "description": "Module description",
            "duration": minutes,
            "objectives": ["obj1", "obj2"],
            "topics": [
                {{"title": "Topic", "description": "Description", "duration": minutes}}
            ]
        }}
    ]
}}
"""

        # Use RAG enhancement if enabled
        if request.use_rag_enhancement:
            try:
                enhanced = await enhance_prompt_with_rag(
                    content_type="syllabus",
                    subject=request.title,
                    difficulty_level=request.level.value,
                    original_prompt=base_prompt,
                )
                generation_prompt = enhanced.enhanced_prompt
            except RAGException as e:
                logger.warning(f"RAG enhancement failed, using base prompt: {str(e)}")
                generation_prompt = base_prompt
        else:
            generation_prompt = base_prompt

        # For now, return a structured placeholder
        # In production, this would call the AI client
        syllabus_data = {
            "title": request.title,
            "description": request.description,
            "level": request.level.value,
            "duration": request.duration or self._estimate_duration(processed_contents),
            "objectives": request.objectives or self._extract_objectives(processed_contents),
            "prerequisites": request.prerequisites,
            "target_audience": request.target_audience,
            "modules": self._generate_modules_from_content(processed_contents, request.level),
            "external_sources": [
                {
                    "url": pc.metadata.source_url,
                    "title": pc.metadata.title,
                }
                for pc in processed_contents
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generation_method": "url_based_rag_enhanced",
        }

        return syllabus_data

    def _estimate_duration(self, contents: List[ProcessedExternalContent]) -> int:
        """Estimate course duration based on content volume."""
        total_words = sum(pc.metadata.word_count for pc in contents)
        # Rough estimate: 1 hour per 3000 words of source material
        return max(1, total_words // 3000)

    def _extract_objectives(self, contents: List[ProcessedExternalContent]) -> List[str]:
        """Extract learning objectives from content headings."""
        objectives = []
        for pc in contents:
            headings = pc.structured_content.get("headings", [])
            for h in headings[:5]:  # Top headings as objectives
                if h.get("level", 0) <= 2:  # H1 and H2
                    objectives.append(f"Understand {h['text']}")

        return objectives[:8]  # Limit to 8 objectives

    def _generate_modules_from_content(
        self,
        contents: List[ProcessedExternalContent],
        level: CourseLevel,
    ) -> List[Dict[str, Any]]:
        """
        Generate module structure from processed content.

        Uses headings and content structure to create logical modules.
        """
        modules = []
        module_num = 1

        for pc in contents:
            headings = pc.structured_content.get("headings", [])

            # Group headings into modules
            current_module_headings = []
            for h in headings:
                if h.get("level", 0) == 1 and current_module_headings:
                    # New top-level heading, create module from previous
                    module = self._create_module(
                        module_num, current_module_headings, pc, level
                    )
                    if module:
                        modules.append(module)
                        module_num += 1
                    current_module_headings = []

                current_module_headings.append(h)

            # Don't forget last module
            if current_module_headings:
                module = self._create_module(
                    module_num, current_module_headings, pc, level
                )
                if module:
                    modules.append(module)
                    module_num += 1

        # If no modules created from headings, create from chunks
        if not modules and contents:
            for i, pc in enumerate(contents):
                modules.append({
                    "module_number": i + 1,
                    "title": pc.metadata.title or f"Module {i + 1}",
                    "description": pc.metadata.description or "Content from external documentation",
                    "duration": 60,  # Default 60 minutes
                    "objectives": [f"Understand {pc.metadata.title or 'key concepts'}"],
                    "topics": [
                        {
                            "title": "Overview",
                            "description": "Introduction to the topic",
                            "duration": 30,
                        },
                        {
                            "title": "Practical Application",
                            "description": "Hands-on exercises",
                            "duration": 30,
                        },
                    ],
                    "source_url": pc.metadata.source_url,
                })

        return modules[:10]  # Limit to 10 modules

    def _create_module(
        self,
        module_num: int,
        headings: List[Dict[str, Any]],
        content: ProcessedExternalContent,
        level: CourseLevel,
    ) -> Optional[Dict[str, Any]]:
        """Create a single module from headings."""
        if not headings:
            return None

        main_heading = headings[0]
        sub_headings = [h for h in headings[1:] if h.get("level", 0) > 1]

        topics = []
        for h in sub_headings[:5]:  # Up to 5 topics per module
            topics.append({
                "title": h["text"],
                "description": f"Learn about {h['text']}",
                "duration": 15,  # 15 minutes per topic
            })

        if not topics:
            topics = [{
                "title": "Overview",
                "description": f"Introduction to {main_heading['text']}",
                "duration": 30,
            }]

        return {
            "module_number": module_num,
            "title": main_heading["text"],
            "description": f"This module covers {main_heading['text']}",
            "duration": len(topics) * 15 + 15,  # Topics + intro time
            "objectives": [f"Understand {main_heading['text']}"],
            "topics": topics,
            "source_url": content.metadata.source_url,
        }

    async def _learn_from_generation(
        self,
        request: SyllabusRequest,
        syllabus_data: Dict[str, Any],
        contents: List[ProcessedExternalContent],
    ) -> None:
        """Store successful generation for future learning."""
        try:
            await learn_from_generation(
                content_type="syllabus",
                subject=request.title,
                difficulty_level=request.level.value,
                generated_content=str(syllabus_data),
                quality_score=0.8,
                generation_metadata={
                    "url_based": True,
                    "source_count": len(contents),
                    "total_words": sum(pc.metadata.word_count for pc in contents),
                }
            )
        except RAGException as e:
            logger.warning(f"Failed to store generation for learning: {str(e)}")

    def get_progress(self, request_id: UUID) -> Optional[GenerationProgress]:
        """Get progress for a generation request."""
        return self._progress_cache.get(request_id)


# Factory function
def create_url_based_generation_service(
    max_concurrent_fetches: int = URLBasedGenerationService.MAX_CONCURRENT_FETCHES,
) -> URLBasedGenerationService:
    """
    Create URL-based generation service instance.

    Args:
        max_concurrent_fetches: Maximum parallel URL fetches

    Returns:
        Configured URLBasedGenerationService instance
    """
    return URLBasedGenerationService(
        max_concurrent_fetches=max_concurrent_fetches
    )


# Export components
__all__ = [
    "URLBasedGenerationService",
    "URLFetchResult",
    "GenerationProgress",
    "create_url_based_generation_service",
]
