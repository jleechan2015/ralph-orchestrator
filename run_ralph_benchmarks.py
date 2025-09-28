#!/usr/bin/env python3
"""
Ralph Orchestrator Benchmark Suite
Executes all three benchmark projects and collects comprehensive metrics
"""

import time
import json
import subprocess
import psutil
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import shutil

class RalphBenchmarkRunner:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.benchmark_dir = Path("ralph_benchmarks")

        # Ensure benchmark directory exists
        self.benchmark_dir.mkdir(exist_ok=True)

        # Project configurations
        self.projects = [
            {
                "id": "project_1_cli",
                "name": "CLI Text Processor",
                "prompt_file": "PROMPT_project_1.md",
                "output_dir": self.benchmark_dir / "project_1_cli",
                "expected_loc": "150-300",
                "description": "Command-line text processing utility"
            },
            {
                "id": "project_2_api",
                "name": "FastAPI Task Management",
                "prompt_file": "PROMPT_project_2.md",
                "output_dir": self.benchmark_dir / "project_2_api",
                "expected_loc": "800-1500",
                "description": "RESTful Task Management API with JWT auth"
            },
            {
                "id": "project_3_finance",
                "name": "Full-Stack Finance Tracker",
                "prompt_file": "PROMPT_project_3.md",
                "output_dir": self.benchmark_dir / "project_3_finance",
                "expected_loc": "2000-4000",
                "description": "React + FastAPI + PostgreSQL finance tracker"
            }
        ]

    def get_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmark context"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": sys.version,
            "platform": sys.platform,
            "timestamp": datetime.now().isoformat()
        }

    def measure_resource_usage(self, process) -> Dict[str, Any]:
        """Monitor resource usage during execution"""
        try:
            proc = psutil.Process(process.pid)
            memory_info = proc.memory_info()
            return {
                "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
                "cpu_percent": proc.cpu_percent(),
                "status": proc.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"memory_mb": 0, "cpu_percent": 0, "status": "unknown"}

    def count_lines_of_code(self, directory: Path) -> Dict[str, Any]:
        """Count lines of code using simple file analysis"""
        if not directory.exists():
            return {"total_lines": 0, "file_count": 0, "extensions": {}}

        code_extensions = {'.py', '.js', '.ts', '.tsx', '.sql', '.md', '.json', '.yaml', '.yml'}
        total_lines = 0
        file_count = 0
        extensions = {}

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in code_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                        file_count += 1

                        ext = file_path.suffix
                        if ext not in extensions:
                            extensions[ext] = {"files": 0, "lines": 0}
                        extensions[ext]["files"] += 1
                        extensions[ext]["lines"] += lines
                except Exception:
                    continue

        return {
            "total_lines": total_lines,
            "file_count": file_count,
            "extensions": extensions
        }

    def run_ralph_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single Ralph project and collect metrics"""
        print(f"\n🚀 Starting Ralph benchmark: {project['name']}")
        print(f"   Prompt: {project['prompt_file']}")
        print(f"   Output: {project['output_dir']}")

        # Clean output directory
        if project['output_dir'].exists():
            shutil.rmtree(project['output_dir'])
        project['output_dir'].mkdir(parents=True, exist_ok=True)

        # Prepare Ralph command
        ralph_cmd = [
            sys.executable, "-m", "src.ralph_orchestrator.main",
            "--prompt", project['prompt_file'],
            "--verbose",
            "--max-iterations", "50",
            "--max-runtime", "1800",  # 30 minutes max
            "--agent", "claude"
        ]

        print(f"   Command: {' '.join(ralph_cmd)}")

        # Start timing
        start_time = time.time()

        # Execute Ralph
        try:
            # Change to output directory for Ralph execution
            original_cwd = os.getcwd()
            os.chdir(project['output_dir'])

            process = subprocess.Popen(
                ralph_cmd,
                cwd=original_cwd,  # Run from ralph-orchestrator root
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor execution
            stdout_lines = []
            stderr_lines = []

            while True:
                # Check if process is still running
                if process.poll() is not None:
                    break

                # Read output
                line = process.stdout.readline()
                if line:
                    stdout_lines.append(line.rstrip())
                    print(f"   📋 {line.rstrip()}")

                # Monitor resource usage periodically
                time.sleep(1)

            # Get remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_lines.extend(remaining_stdout.strip().split('\n'))
            if remaining_stderr:
                stderr_lines.extend(remaining_stderr.strip().split('\n'))

            end_time = time.time()
            execution_time = end_time - start_time

            # Change back to original directory
            os.chdir(original_cwd)

            # Analyze output
            loc_analysis = self.count_lines_of_code(project['output_dir'])

            # Calculate metrics
            velocity = loc_analysis['total_lines'] / (execution_time / 60) if execution_time > 0 else 0

            result = {
                "project_id": project['id'],
                "project_name": project['name'],
                "success": process.returncode == 0,
                "execution_time_seconds": round(execution_time, 2),
                "execution_time_minutes": round(execution_time / 60, 2),
                "return_code": process.returncode,
                "lines_of_code": loc_analysis['total_lines'],
                "file_count": loc_analysis['file_count'],
                "file_extensions": loc_analysis['extensions'],
                "implementation_velocity_loc_per_minute": round(velocity, 2),
                "expected_loc_range": project['expected_loc'],
                "stdout_lines": len(stdout_lines),
                "stderr_lines": len(stderr_lines),
                "output_directory": str(project['output_dir']),
                "prompt_file": project['prompt_file']
            }

            print(f"   ✅ Completed in {execution_time:.1f}s")
            print(f"   📊 Generated {loc_analysis['total_lines']} lines across {loc_analysis['file_count']} files")
            print(f"   ⚡ Velocity: {velocity:.1f} LOC/minute")

            return result

        except Exception as e:
            print(f"   ❌ Error executing Ralph: {e}")
            return {
                "project_id": project['id'],
                "project_name": project['name'],
                "success": False,
                "error": str(e),
                "execution_time_seconds": time.time() - start_time
            }

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all Ralph benchmarks and collect comprehensive results"""
        print("🎯 Ralph Orchestrator Benchmark Suite")
        print("=" * 50)

        self.start_time = time.time()
        system_info = self.get_system_info()

        print(f"📋 System: {system_info['cpu_count']} CPU cores, {system_info['memory_total_gb']}GB RAM")
        print(f"🐍 Python: {system_info['python_version']}")
        print(f"📅 Started: {system_info['timestamp']}")

        # Run each project
        project_results = []
        for project in self.projects:
            result = self.run_ralph_project(project)
            project_results.append(result)

        # Calculate overall metrics
        total_time = time.time() - self.start_time
        successful_projects = [r for r in project_results if r.get('success', False)]
        total_loc = sum(r.get('lines_of_code', 0) for r in successful_projects)
        total_files = sum(r.get('file_count', 0) for r in successful_projects)

        # Compile final results
        benchmark_results = {
            "benchmark_info": {
                "suite_name": "Ralph Orchestrator Benchmark",
                "total_execution_time_seconds": round(total_time, 2),
                "total_execution_time_minutes": round(total_time / 60, 2),
                "projects_attempted": len(project_results),
                "projects_successful": len(successful_projects),
                "success_rate": round(len(successful_projects) / len(project_results) * 100, 1)
            },
            "system_info": system_info,
            "aggregate_metrics": {
                "total_lines_of_code": total_loc,
                "total_files_generated": total_files,
                "average_velocity_loc_per_minute": round(total_loc / (total_time / 60), 2) if total_time > 0 else 0,
                "projects_completed": len(successful_projects),
                "projects_failed": len(project_results) - len(successful_projects)
            },
            "project_results": project_results,
            "comparison_baseline": {
                "cerebras_time_ms": 997,
                "cerebras_lines": 66,
                "cerebras_project": "Project 2 (Task Management API)"
            }
        }

        # Save results
        results_file = self.benchmark_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(benchmark_results, f, indent=2)

        # Generate summary report
        self.generate_summary_report(benchmark_results)

        print(f"\n🎉 Ralph benchmarks completed!")
        print(f"📊 Total time: {total_time/60:.1f} minutes")
        print(f"📝 Results saved to: {results_file}")

        return benchmark_results

    def generate_summary_report(self, results: Dict[str, Any]) -> None:
        """Generate a markdown summary report"""
        summary_file = self.benchmark_dir / "benchmark_summary.md"

        with open(summary_file, 'w') as f:
            f.write("# Ralph Orchestrator Benchmark Results\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

            # Overview
            f.write("## 📊 Overview\n\n")
            info = results['benchmark_info']
            f.write(f"- **Total Execution Time:** {info['total_execution_time_minutes']:.1f} minutes\n")
            f.write(f"- **Projects Attempted:** {info['projects_attempted']}\n")
            f.write(f"- **Success Rate:** {info['success_rate']:.1f}%\n")
            f.write(f"- **Total LOC Generated:** {results['aggregate_metrics']['total_lines_of_code']:,}\n")
            f.write(f"- **Average Velocity:** {results['aggregate_metrics']['average_velocity_loc_per_minute']:.1f} LOC/minute\n\n")

            # Individual project results
            f.write("## 🚀 Individual Project Results\n\n")
            for project in results['project_results']:
                f.write(f"### {project['project_name']}\n")
                if project.get('success', False):
                    f.write(f"- ✅ **Status:** Completed successfully\n")
                    f.write(f"- ⏱️ **Time:** {project['execution_time_minutes']:.1f} minutes\n")
                    f.write(f"- 📄 **Lines of Code:** {project['lines_of_code']:,}\n")
                    f.write(f"- 📁 **Files Generated:** {project['file_count']}\n")
                    f.write(f"- ⚡ **Velocity:** {project['implementation_velocity_loc_per_minute']:.1f} LOC/minute\n")
                    f.write(f"- 📋 **Expected Range:** {project['expected_loc_range']} lines\n")
                else:
                    f.write(f"- ❌ **Status:** Failed\n")
                    f.write(f"- ⏱️ **Time:** {project.get('execution_time_seconds', 0):.1f} seconds\n")
                    if 'error' in project:
                        f.write(f"- 🚨 **Error:** {project['error']}\n")
                f.write("\n")

            # Comparison with baseline
            f.write("## 🔄 Comparison with Cerebras Baseline\n\n")
            baseline = results['comparison_baseline']
            f.write(f"- **Cerebras (Baseline):** {baseline['cerebras_time_ms']}ms, {baseline['cerebras_lines']} lines\n")
            f.write(f"- **Ralph Average per Project:** {info['total_execution_time_seconds']/len(results['project_results']):.1f}s\n\n")

            # System info
            f.write("## 🖥️ System Information\n\n")
            sys_info = results['system_info']
            f.write(f"- **CPU Cores:** {sys_info['cpu_count']}\n")
            f.write(f"- **RAM:** {sys_info['memory_total_gb']} GB\n")
            f.write(f"- **Platform:** {sys_info['platform']}\n")
            f.write(f"- **Python:** {sys_info['python_version']}\n")

def main():
    """Main execution function"""
    runner = RalphBenchmarkRunner()
    results = runner.run_all_benchmarks()
    return results

if __name__ == "__main__":
    main()