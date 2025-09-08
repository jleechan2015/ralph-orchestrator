# ABOUTME: FastAPI web server for Ralph Orchestrator monitoring dashboard
# ABOUTME: Provides REST API endpoints and WebSocket connections for real-time updates

"""FastAPI web server for Ralph Orchestrator monitoring."""

import os
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil

from ..metrics import Metrics, CostTracker
from ..orchestrator import RalphOrchestrator

logger = logging.getLogger(__name__)


class OrchestratorMonitor:
    """Monitors and manages orchestrator instances."""
    
    def __init__(self):
        self.active_orchestrators: Dict[str, RalphOrchestrator] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.websocket_clients: List[WebSocket] = []
        self.metrics_cache: Dict[str, Any] = {}
        self.system_metrics_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if not self.system_metrics_task:
            self.system_metrics_task = asyncio.create_task(self._monitor_system_metrics())
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        if self.system_metrics_task:
            self.system_metrics_task.cancel()
            try:
                await self.system_metrics_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_system_metrics(self):
        """Monitor system metrics continuously."""
        while True:
            try:
                # Collect system metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "percent": psutil.virtual_memory().percent
                    },
                    "active_processes": len(psutil.pids()),
                    "orchestrators": len(self.active_orchestrators)
                }
                
                self.metrics_cache["system"] = metrics
                
                # Broadcast to WebSocket clients
                await self._broadcast_to_clients({
                    "type": "system_metrics",
                    "data": metrics
                })
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(5)
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        disconnected_clients = []
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.websocket_clients:
                self.websocket_clients.remove(client)
    
    def register_orchestrator(self, orchestrator_id: str, orchestrator: RalphOrchestrator):
        """Register an orchestrator instance."""
        self.active_orchestrators[orchestrator_id] = orchestrator
        asyncio.create_task(self._broadcast_to_clients({
            "type": "orchestrator_registered",
            "data": {"id": orchestrator_id, "timestamp": datetime.now().isoformat()}
        }))
    
    def unregister_orchestrator(self, orchestrator_id: str):
        """Unregister an orchestrator instance."""
        if orchestrator_id in self.active_orchestrators:
            del self.active_orchestrators[orchestrator_id]
            asyncio.create_task(self._broadcast_to_clients({
                "type": "orchestrator_unregistered",
                "data": {"id": orchestrator_id, "timestamp": datetime.now().isoformat()}
            }))
    
    def get_orchestrator_status(self, orchestrator_id: str) -> Dict[str, Any]:
        """Get status of a specific orchestrator."""
        if orchestrator_id not in self.active_orchestrators:
            return None
        
        orchestrator = self.active_orchestrators[orchestrator_id]
        
        # Try to use the new get_orchestrator_state method if it exists
        if hasattr(orchestrator, 'get_orchestrator_state'):
            state = orchestrator.get_orchestrator_state()
            state['id'] = orchestrator_id  # Override with our ID
            return state
        else:
            # Fallback to old method for compatibility
            return {
                "id": orchestrator_id,
                "status": "running" if not orchestrator.stop_requested else "stopping",
                "metrics": orchestrator.metrics.to_dict(),
                "cost": orchestrator.cost_tracker.get_summary() if orchestrator.cost_tracker else None,
                "config": {
                    "primary_tool": orchestrator.primary_tool,
                    "max_iterations": orchestrator.max_iterations,
                    "max_runtime": orchestrator.max_runtime,
                    "prompt_file": str(orchestrator.prompt_file)
                }
            }
    
    def get_all_orchestrators_status(self) -> List[Dict[str, Any]]:
        """Get status of all orchestrators."""
        return [
            self.get_orchestrator_status(orch_id)
            for orch_id in self.active_orchestrators
        ]


class WebMonitor:
    """Web monitoring server for Ralph Orchestrator."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.monitor = OrchestratorMonitor()
        self.app = None
        self._setup_app()
    
    def _setup_app(self):
        """Setup FastAPI application."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.monitor.start_monitoring()
            yield
            # Shutdown
            await self.monitor.stop_monitoring()
        
        self.app = FastAPI(
            title="Ralph Orchestrator Monitor",
            description="Real-time monitoring for Ralph AI Orchestrator",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files directory if it exists
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def index():
            """Serve the main dashboard."""
            html_file = Path(__file__).parent / "static" / "index.html"
            if html_file.exists():
                return FileResponse(html_file, media_type="text/html")
            else:
                # Return a basic HTML page if static file doesn't exist yet
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Ralph Orchestrator Monitor</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        .status { padding: 10px; margin: 10px 0; background: #f0f0f0; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <h1>Ralph Orchestrator Monitor</h1>
                    <div id="status" class="status">
                        <p>Web monitor is running. Dashboard file not found.</p>
                        <p>API Endpoints:</p>
                        <ul>
                            <li><a href="/api/status">/api/status</a> - System status</li>
                            <li><a href="/api/orchestrators">/api/orchestrators</a> - Active orchestrators</li>
                            <li><a href="/api/metrics">/api/metrics</a> - System metrics</li>
                            <li><a href="/docs">/docs</a> - API documentation</li>
                        </ul>
                    </div>
                </body>
                </html>
                """)
        
        @self.app.get("/api/status")
        async def get_status():
            """Get overall system status."""
            return {
                "status": "online",
                "timestamp": datetime.now().isoformat(),
                "active_orchestrators": len(self.monitor.active_orchestrators),
                "connected_clients": len(self.monitor.websocket_clients),
                "system_metrics": self.monitor.metrics_cache.get("system", {})
            }
        
        @self.app.get("/api/orchestrators")
        async def get_orchestrators():
            """Get all active orchestrators."""
            return {
                "orchestrators": self.monitor.get_all_orchestrators_status(),
                "count": len(self.monitor.active_orchestrators)
            }
        
        @self.app.get("/api/orchestrators/{orchestrator_id}")
        async def get_orchestrator(orchestrator_id: str):
            """Get specific orchestrator status."""
            status = self.monitor.get_orchestrator_status(orchestrator_id)
            if not status:
                raise HTTPException(status_code=404, detail="Orchestrator not found")
            return status
        
        @self.app.get("/api/orchestrators/{orchestrator_id}/tasks")
        async def get_orchestrator_tasks(orchestrator_id: str):
            """Get task queue status for an orchestrator."""
            if orchestrator_id not in self.monitor.active_orchestrators:
                raise HTTPException(status_code=404, detail="Orchestrator not found")
            
            orchestrator = self.monitor.active_orchestrators[orchestrator_id]
            task_status = orchestrator.get_task_status()
            
            return {
                "orchestrator_id": orchestrator_id,
                "tasks": task_status
            }
        
        @self.app.post("/api/orchestrators/{orchestrator_id}/pause")
        async def pause_orchestrator(orchestrator_id: str):
            """Pause an orchestrator."""
            if orchestrator_id not in self.monitor.active_orchestrators:
                raise HTTPException(status_code=404, detail="Orchestrator not found")
            
            orchestrator = self.monitor.active_orchestrators[orchestrator_id]
            orchestrator.stop_requested = True
            
            return {"status": "paused", "orchestrator_id": orchestrator_id}
        
        @self.app.post("/api/orchestrators/{orchestrator_id}/resume")
        async def resume_orchestrator(orchestrator_id: str):
            """Resume an orchestrator."""
            if orchestrator_id not in self.monitor.active_orchestrators:
                raise HTTPException(status_code=404, detail="Orchestrator not found")
            
            orchestrator = self.monitor.active_orchestrators[orchestrator_id]
            orchestrator.stop_requested = False
            
            return {"status": "resumed", "orchestrator_id": orchestrator_id}
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get system metrics."""
            return self.monitor.metrics_cache
        
        @self.app.get("/api/history")
        async def get_history():
            """Get execution history."""
            # Load history from metrics files
            metrics_dir = Path(".agent") / "metrics"
            history = []
            
            if metrics_dir.exists():
                for metrics_file in sorted(metrics_dir.glob("metrics_*.json")):
                    try:
                        data = json.loads(metrics_file.read_text())
                        data["filename"] = metrics_file.name
                        history.append(data)
                    except Exception as e:
                        logger.error(f"Error reading metrics file {metrics_file}: {e}")
            
            return {"history": history[-50:]}  # Return last 50 entries
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.monitor.websocket_clients.append(websocket)
            
            # Send initial state
            await websocket.send_json({
                "type": "initial_state",
                "data": {
                    "orchestrators": self.monitor.get_all_orchestrators_status(),
                    "system_metrics": self.monitor.metrics_cache.get("system", {})
                }
            })
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    # Handle ping/pong or other commands if needed
                    if data == "ping":
                        await websocket.send_text("pong")
            except WebSocketDisconnect:
                self.monitor.websocket_clients.remove(websocket)
                logger.info("WebSocket client disconnected")
    
    def run(self):
        """Run the web server."""
        logger.info(f"Starting web monitor on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    async def arun(self):
        """Run the web server asynchronously."""
        logger.info(f"Starting web monitor on {self.host}:{self.port}")
        config = uvicorn.Config(app=self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
    
    def register_orchestrator(self, orchestrator_id: str, orchestrator: RalphOrchestrator):
        """Register an orchestrator with the monitor."""
        self.monitor.register_orchestrator(orchestrator_id, orchestrator)
    
    def unregister_orchestrator(self, orchestrator_id: str):
        """Unregister an orchestrator from the monitor."""
        self.monitor.unregister_orchestrator(orchestrator_id)