import json
import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from ..models.schemas import (
    RunReport, 
    ExportRequest, 
    ExportResponse,
    ReportSummary
)

router = APIRouter()

# In-memory storage for demo purposes
# In production, use a database
reports_storage: dict = {}

@router.get("/run/{run_id}", response_model=RunReport)
async def get_run_report(run_id: str):
    """Get a specific run report by ID."""
    if run_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Run report not found")
    
    return reports_storage[run_id]

@router.get("/runs", response_model=List[ReportSummary])
async def list_runs(limit: int = 50, offset: int = 0):
    """List all run reports with pagination."""
    reports = list(reports_storage.values())
    
    # Sort by start time (newest first)
    reports.sort(key=lambda x: x.start_time, reverse=True)
    
    # Apply pagination
    paginated_reports = reports[offset:offset + limit]
    
    # Convert to summary format
    summaries = []
    for report in paginated_reports:
        summaries.append(ReportSummary(
            id=report.id,
            start_time=report.start_time,
            end_time=report.end_time,
            profile=report.profile,
            total_items=report.stats.total,
            success_rate=report.kpis.success_rate,
            pages_per_hour=report.kpis.pages_per_hour
        ))
    
    return summaries

@router.post("/export", response_model=ExportResponse)
async def export_report(request: ExportRequest):
    """Export run report data to file."""
    try:
        if request.run_id and request.run_id not in reports_storage:
            raise HTTPException(status_code=404, detail="Run report not found")
        
        # Get data to export
        if request.run_id:
            reports = [reports_storage[request.run_id]]
        else:
            reports = list(reports_storage.values())
        
        # Ensure output path exists
        output_path = Path(request.path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if request.format == "json":
            # Export as JSON
            export_data = {
                "reports": [report.dict() for report in reports],
                "export_time": "2025-01-01T00:00:00Z",
                "total_reports": len(reports)
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
        elif request.format == "csv":
            # Export as CSV (flattened data)
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "run_id", "start_time", "end_time", "profile", "url", 
                    "status", "depth", "attempts", "formats", "outputs"
                ])
                
                # Write data
                for report in reports:
                    for item in report.items:
                        writer.writerow([
                            report.id,
                            report.start_time,
                            report.end_time or "",
                            report.profile,
                            item.url,
                            item.status,
                            item.depth,
                            item.attempts,
                            ",".join([k for k, v in item.formats.dict().items() if v]),
                            ",".join([k for k, v in (item.outputs.dict() if item.outputs else {}).items() if v])
                        ])
        
        return ExportResponse(
            ok=True,
            path=str(output_path),
            format=request.format,
            records_exported=sum(len(report.items) for report in reports)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

@router.post("/save")
async def save_report(report: RunReport):
    """Save a run report."""
    reports_storage[report.id] = report
    return {"ok": True, "message": f"Report {report.id} saved successfully"}

@router.delete("/run/{run_id}")
async def delete_report(run_id: str):
    """Delete a run report."""
    if run_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Run report not found")
    
    del reports_storage[run_id]
    return {"ok": True, "message": f"Report {run_id} deleted successfully"}
