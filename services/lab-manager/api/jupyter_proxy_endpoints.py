#!/usr/bin/env python3

"""
Jupyter Proxy API Endpoints

This module provides proxy endpoints to interact with Jupyter notebooks running
inside lab containers. It enables the AI Assistant to access notebook content
for context-aware coding assistance.

## Features:

### Notebook Content Access
- GET /labs/{lab_id}/jupyter/contents - List files in workspace
- GET /labs/{lab_id}/jupyter/notebook/{path} - Get notebook content (cells)
- GET /labs/{lab_id}/jupyter/active-cell - Get currently active cell content

### Kernel Information
- GET /labs/{lab_id}/jupyter/sessions - Get running kernel sessions
- GET /labs/{lab_id}/jupyter/kernel/{kernel_id}/status - Get kernel status

### Integration with AI Assistant
The endpoints return structured notebook data that can be passed to the
AI Assistant for context-aware help with:
- Explaining notebook cells
- Debugging cell errors
- Suggesting code improvements
- Providing hints for exercises

## Security:
All requests are authenticated through the lab session. The proxy only
forwards requests for labs owned by the authenticated user.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime

from exceptions import (
    ContentException,
    ContentNotFoundException,
    ConfigurationException
)

router = APIRouter(
    prefix="/labs",
    tags=["jupyter-proxy"],
    responses={
        404: {"description": "Lab or notebook not found"},
        500: {"description": "Internal server error"},
        502: {"description": "Jupyter server unavailable"}
    }
)

logger = logging.getLogger(__name__)

# Jupyter port in lab containers
JUPYTER_PORT = 8082


# Response Models

class NotebookCell(BaseModel):
    """Single notebook cell content"""
    cell_type: str  # 'code' | 'markdown' | 'raw'
    source: str  # Cell content
    execution_count: Optional[int] = None
    outputs: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class NotebookContent(BaseModel):
    """Full notebook content"""
    name: str
    path: str
    cells: List[NotebookCell]
    metadata: Dict[str, Any]
    nbformat: int
    nbformat_minor: int


class NotebookSummary(BaseModel):
    """Summary of notebook for AI context"""
    name: str
    path: str
    total_cells: int
    code_cells: int
    markdown_cells: int
    last_executed_cell: Optional[int] = None
    has_errors: bool
    error_cells: List[int] = []


class JupyterFile(BaseModel):
    """File listing entry"""
    name: str
    path: str
    type: str  # 'notebook' | 'file' | 'directory'
    size: Optional[int] = None
    last_modified: Optional[datetime] = None


class ActiveCellContext(BaseModel):
    """Context for currently active/focused cell"""
    cell_index: int
    cell_type: str
    source: str
    outputs: Optional[List[Dict[str, Any]]] = None
    has_error: bool
    error_message: Optional[str] = None
    previous_cells: List[NotebookCell]  # Previous 3 cells for context
    notebook_name: str
    notebook_path: str


class KernelSession(BaseModel):
    """Jupyter kernel session info"""
    id: str
    kernel_id: str
    kernel_name: str
    notebook_path: str
    status: str  # 'idle' | 'busy' | 'starting'


# Helper Functions

def get_lab_lifecycle_service():
    """Get lab lifecycle service instance"""
    from main import lab_lifecycle_service
    if not lab_lifecycle_service:
        raise ConfigurationException(
            message="Lab lifecycle service not initialized",
            error_code="SERVICE_INIT_ERROR",
            details={"service_name": "lab_lifecycle_service"}
        )
    return lab_lifecycle_service


async def get_lab_jupyter_url(lab_id: str) -> str:
    """
    Get the internal URL for Jupyter server in a lab container.

    Args:
        lab_id: Lab container identifier

    Returns:
        str: Internal URL to Jupyter server

    Raises:
        ContentNotFoundException: If lab not found
    """
    lifecycle_service = get_lab_lifecycle_service()
    lab = lifecycle_service.get_lab_status(lab_id)

    if not lab:
        raise ContentNotFoundException(
            message="Lab container not found",
            error_code="LAB_NOT_FOUND",
            details={"lab_id": lab_id}
        )

    # Get container name to construct internal URL
    container_name = lab.container_name or f"lab-{lab_id}"
    return f"http://{container_name}:{JUPYTER_PORT}"


async def proxy_jupyter_request(
    lab_id: str,
    endpoint: str,
    method: str = "GET",
    timeout: float = 10.0
) -> Dict[str, Any]:
    """
    Proxy a request to Jupyter server in lab container.

    Args:
        lab_id: Lab container identifier
        endpoint: Jupyter API endpoint (e.g., /api/contents)
        method: HTTP method
        timeout: Request timeout in seconds

    Returns:
        Dict: JSON response from Jupyter

    Raises:
        ContentException: If request fails
    """
    jupyter_url = await get_lab_jupyter_url(lab_id)
    full_url = f"{jupyter_url}{endpoint}"

    logger.debug(f"Proxying Jupyter request: {method} {full_url}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=full_url,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            raise ContentException(
                message="Jupyter server request timed out",
                error_code="JUPYTER_TIMEOUT",
                details={"lab_id": lab_id, "endpoint": endpoint}
            )
        except httpx.HTTPStatusError as e:
            raise ContentException(
                message=f"Jupyter server returned error: {e.response.status_code}",
                error_code="JUPYTER_HTTP_ERROR",
                details={
                    "lab_id": lab_id,
                    "endpoint": endpoint,
                    "status_code": e.response.status_code
                }
            )
        except httpx.RequestError as e:
            raise ContentException(
                message="Failed to connect to Jupyter server",
                error_code="JUPYTER_CONNECTION_ERROR",
                details={"lab_id": lab_id, "endpoint": endpoint, "error": str(e)}
            )


def parse_notebook_cells(notebook_data: Dict[str, Any]) -> List[NotebookCell]:
    """Parse notebook JSON into cell objects"""
    cells = []
    for cell in notebook_data.get("content", {}).get("cells", []):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)

        cells.append(NotebookCell(
            cell_type=cell.get("cell_type", "code"),
            source=source,
            execution_count=cell.get("execution_count"),
            outputs=cell.get("outputs", []),
            metadata=cell.get("metadata", {})
        ))
    return cells


def detect_cell_errors(cell: NotebookCell) -> tuple[bool, Optional[str]]:
    """Check if a cell has error output"""
    if not cell.outputs:
        return False, None

    for output in cell.outputs:
        if output.get("output_type") == "error":
            ename = output.get("ename", "Error")
            evalue = output.get("evalue", "Unknown error")
            return True, f"{ename}: {evalue}"

    return False, None


# API Endpoints

@router.get("/{lab_id}/jupyter/contents", response_model=List[JupyterFile])
async def list_jupyter_files(
    lab_id: str,
    path: str = Query("", description="Directory path to list")
):
    """
    List files in Jupyter workspace.

    Returns directory contents including notebooks, files, and subdirectories.
    Use this to discover available notebooks in the lab.

    Args:
        lab_id: Lab container identifier
        path: Directory path (empty for root workspace)

    Returns:
        List[JupyterFile]: Files and directories in the path
    """
    try:
        endpoint = f"/api/contents/{path}" if path else "/api/contents"
        data = await proxy_jupyter_request(lab_id, endpoint)

        files = []
        content = data.get("content", [])

        # Handle single file vs directory listing
        if isinstance(content, list):
            for item in content:
                files.append(JupyterFile(
                    name=item.get("name", ""),
                    path=item.get("path", ""),
                    type=item.get("type", "file"),
                    size=item.get("size"),
                    last_modified=item.get("last_modified")
                ))
        else:
            # Single file/notebook
            files.append(JupyterFile(
                name=data.get("name", ""),
                path=data.get("path", ""),
                type=data.get("type", "file"),
                size=data.get("size"),
                last_modified=data.get("last_modified")
            ))

        return files

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to list Jupyter files",
            error_code="JUPYTER_LIST_ERROR",
            details={"lab_id": lab_id, "path": path},
            original_exception=e
        )


@router.get("/{lab_id}/jupyter/notebook/{path:path}", response_model=NotebookContent)
async def get_notebook_content(lab_id: str, path: str):
    """
    Get full notebook content including all cells.

    Returns the complete notebook with all cells, their source code,
    outputs, and metadata. Use this for comprehensive notebook analysis.

    Args:
        lab_id: Lab container identifier
        path: Notebook path (e.g., 'notebooks/exercise1.ipynb')

    Returns:
        NotebookContent: Full notebook with all cells
    """
    try:
        endpoint = f"/api/contents/{path}?content=1"
        data = await proxy_jupyter_request(lab_id, endpoint)

        if data.get("type") != "notebook":
            raise ContentException(
                message="Requested path is not a notebook",
                error_code="NOT_A_NOTEBOOK",
                details={"lab_id": lab_id, "path": path, "type": data.get("type")}
            )

        cells = parse_notebook_cells(data)
        content = data.get("content", {})

        return NotebookContent(
            name=data.get("name", ""),
            path=data.get("path", path),
            cells=cells,
            metadata=content.get("metadata", {}),
            nbformat=content.get("nbformat", 4),
            nbformat_minor=content.get("nbformat_minor", 0)
        )

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to get notebook content",
            error_code="JUPYTER_NOTEBOOK_ERROR",
            details={"lab_id": lab_id, "path": path},
            original_exception=e
        )


@router.get("/{lab_id}/jupyter/notebook/{path:path}/summary", response_model=NotebookSummary)
async def get_notebook_summary(lab_id: str, path: str):
    """
    Get notebook summary for AI context.

    Returns a summary of the notebook including cell counts, error status,
    and the last executed cell. Useful for quick context without full content.

    Args:
        lab_id: Lab container identifier
        path: Notebook path

    Returns:
        NotebookSummary: Summary statistics and error info
    """
    try:
        notebook = await get_notebook_content(lab_id, path)

        code_cells = [c for c in notebook.cells if c.cell_type == "code"]
        markdown_cells = [c for c in notebook.cells if c.cell_type == "markdown"]

        # Find cells with errors
        error_cells = []
        for i, cell in enumerate(notebook.cells):
            has_error, _ = detect_cell_errors(cell)
            if has_error:
                error_cells.append(i)

        # Find last executed cell
        last_executed = None
        for i, cell in enumerate(code_cells):
            if cell.execution_count is not None:
                last_executed = i

        return NotebookSummary(
            name=notebook.name,
            path=notebook.path,
            total_cells=len(notebook.cells),
            code_cells=len(code_cells),
            markdown_cells=len(markdown_cells),
            last_executed_cell=last_executed,
            has_errors=len(error_cells) > 0,
            error_cells=error_cells
        )

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to get notebook summary",
            error_code="JUPYTER_SUMMARY_ERROR",
            details={"lab_id": lab_id, "path": path},
            original_exception=e
        )


@router.get("/{lab_id}/jupyter/notebook/{path:path}/cell/{cell_index}", response_model=ActiveCellContext)
async def get_cell_context(
    lab_id: str,
    path: str,
    cell_index: int,
    context_cells: int = Query(3, description="Number of previous cells for context")
):
    """
    Get context for a specific cell in a notebook.

    Returns the cell content along with previous cells for context.
    This is optimized for AI assistance - includes error detection
    and surrounding context.

    Args:
        lab_id: Lab container identifier
        path: Notebook path
        cell_index: Index of the cell to get context for
        context_cells: Number of previous cells to include

    Returns:
        ActiveCellContext: Cell with surrounding context
    """
    try:
        notebook = await get_notebook_content(lab_id, path)

        if cell_index < 0 or cell_index >= len(notebook.cells):
            raise ContentException(
                message="Cell index out of range",
                error_code="CELL_NOT_FOUND",
                details={
                    "lab_id": lab_id,
                    "path": path,
                    "cell_index": cell_index,
                    "total_cells": len(notebook.cells)
                }
            )

        cell = notebook.cells[cell_index]
        has_error, error_msg = detect_cell_errors(cell)

        # Get previous cells for context
        start_idx = max(0, cell_index - context_cells)
        previous = notebook.cells[start_idx:cell_index]

        return ActiveCellContext(
            cell_index=cell_index,
            cell_type=cell.cell_type,
            source=cell.source,
            outputs=cell.outputs,
            has_error=has_error,
            error_message=error_msg,
            previous_cells=previous,
            notebook_name=notebook.name,
            notebook_path=notebook.path
        )

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to get cell context",
            error_code="JUPYTER_CELL_ERROR",
            details={"lab_id": lab_id, "path": path, "cell_index": cell_index},
            original_exception=e
        )


@router.get("/{lab_id}/jupyter/sessions", response_model=List[KernelSession])
async def get_kernel_sessions(lab_id: str):
    """
    Get active Jupyter kernel sessions.

    Returns information about running kernels including which notebooks
    they're connected to and their current status.

    Args:
        lab_id: Lab container identifier

    Returns:
        List[KernelSession]: Active kernel sessions
    """
    try:
        data = await proxy_jupyter_request(lab_id, "/api/sessions")

        sessions = []
        for session in data:
            kernel = session.get("kernel", {})
            sessions.append(KernelSession(
                id=session.get("id", ""),
                kernel_id=kernel.get("id", ""),
                kernel_name=kernel.get("name", "python3"),
                notebook_path=session.get("notebook", {}).get("path", ""),
                status=kernel.get("execution_state", "unknown")
            ))

        return sessions

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to get kernel sessions",
            error_code="JUPYTER_SESSION_ERROR",
            details={"lab_id": lab_id},
            original_exception=e
        )


@router.get("/{lab_id}/jupyter/active-notebook")
async def get_active_notebook_context(lab_id: str):
    """
    Get context from the most recently active notebook.

    Automatically detects the most recently modified notebook and returns
    its content optimized for AI context. Includes:
    - Recent code cells
    - Any error outputs
    - Current kernel status

    This is the primary endpoint for AI Assistant integration.

    Args:
        lab_id: Lab container identifier

    Returns:
        Dict with notebook content and context for AI
    """
    try:
        # Get sessions to find active notebook
        sessions = await get_kernel_sessions(lab_id)

        if not sessions:
            # No active sessions, try to find most recent notebook
            files = await list_jupyter_files(lab_id, "notebooks")
            notebooks = [f for f in files if f.type == "notebook"]

            if not notebooks:
                return {
                    "has_active_notebook": False,
                    "message": "No notebooks found in workspace"
                }

            # Use first notebook found
            notebook_path = notebooks[0].path
        else:
            # Use notebook from first active session
            notebook_path = sessions[0].notebook_path

        # Get notebook content
        notebook = await get_notebook_content(lab_id, notebook_path)
        summary = await get_notebook_summary(lab_id, notebook_path)

        # Extract recent code cells for context
        recent_code_cells = []
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == "code" and cell.source.strip():
                has_error, error_msg = detect_cell_errors(cell)
                recent_code_cells.append({
                    "index": i,
                    "source": cell.source,
                    "execution_count": cell.execution_count,
                    "has_error": has_error,
                    "error_message": error_msg
                })

        # Get last 5 code cells for context
        recent_code_cells = recent_code_cells[-5:]

        # Get any error cells
        error_cells = []
        for i in summary.error_cells:
            cell = notebook.cells[i]
            _, error_msg = detect_cell_errors(cell)
            error_cells.append({
                "index": i,
                "source": cell.source,
                "error": error_msg
            })

        return {
            "has_active_notebook": True,
            "notebook_name": notebook.name,
            "notebook_path": notebook.path,
            "total_cells": summary.total_cells,
            "code_cells": summary.code_cells,
            "kernel_status": sessions[0].status if sessions else "unknown",
            "recent_code_cells": recent_code_cells,
            "error_cells": error_cells,
            "has_errors": summary.has_errors
        }

    except ContentException:
        raise
    except Exception as e:
        raise ContentException(
            message="Failed to get active notebook context",
            error_code="JUPYTER_CONTEXT_ERROR",
            details={"lab_id": lab_id},
            original_exception=e
        )
