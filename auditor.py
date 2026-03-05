import os
import sys
import time
from typing import List
import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.layout import Layout
from rich import box

console = Console()

HEADER = r"""
  MMMMMMMM               MMMMMMMM                                     db      th      
   | ____ \              | ____ \                                    | |     | |      
   | |_/ /   ___  _ __  | |_/ /   ___  _ __   ___  _ __  _   _  _ __ | | ___ | | __   
   |  __/   / _ \| '__| |  __/   / _ \| '__| / __|| '__|| | | || '__|| |/ _ \| |/ /   
   | |     |  __/| |    | |     |  __/| |    \__ \| |   | |_| || |   | |  __/|   <    
   \_|      \___|_|    \_|      \___|_|    |___/|_|    \__,_||_|   |_|\___||_|\_\ """

def display_dashboard():
    console.clear()
    console.print(Align.center(Text(HEADER, style="bold cyan")))
    console.print(Align.center(Panel(
        "[bold white]ZENITH SECURITY AUDITOR V5 (DASHBOARD MODE)[/]",
        style="cyan",
        box=box.DOUBLE
    )))

def scan_files(folder_path: str) -> List[str]:
    files_to_scan = []
    # Skip directories with many non-code files, large binaries, or build artifacts
    skip_dirs = {
        '.git', 'node_modules', '__pycache__', 'venv', '.venv', 
        '.next', 'dist', 'build', 'out', '.output', 'target', 
        '.pnpm-store', '.yarn', 'cache', '.cache'
    }
    # Targeted extensions
    extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.c', '.cpp', '.java', '.go', '.php', '.sql', '.rs'}

    for root, dirs, files in os.walk(folder_path):
        # Prevent walking into skipped directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                files_to_scan.append(os.path.join(root, file))
    
    return files_to_scan

def analyze_file(file_path: str, model):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        prompt = f"""
        Act as a senior security researcher. Conduct a "Deep Audit" on the following file content:
        
        FILE: {file_path}
        CONTENT:
        {content}
        
        Focus on:
        - Logic Flaws
        - Hardcoded Secrets
        - Broken Access Control
        - Micro-holes (info leaks, weak salts, missing else blocks)
        
        Format your response EXACTLY as a "Hole Report" with one or more blocks like this:
        [FILE] {file_path}
        [HOLE] Brief description of the vulnerability
        [EXPLOIT] How it can be exploited
        [FIX] How to patch it
        
        If no vulnerabilities are found, respond with "NO VULNERABILITIES DETECTED".
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[ERROR] Could not analyze {file_path}: {str(e)}"

def main():
    display_dashboard()
    api_key = ""
    
    while True:
        if not api_key:
            console.print("\n[bold cyan][1] PASTE GEMINI API KEY[/]")
            console.print("[dim italic](Text will be bright white for visibility. Press ENTER when done.)[/]")
            try:
                # Using rich's console.input for better color control
                api_key = console.input("[bold white]> [/]").strip()
            except EOFError:
                break
                
            if api_key.lower() == 'exit':
                break
            
            if not api_key:
                console.print("[red]Error: API Key cannot be empty.[/]")
                continue
            
            console.print(f"[bold green]✓ Key Received (Length: {len(api_key)})[/]")
            time.sleep(1)
        
        display_dashboard()
        console.print(f"[dim]API Key: {'*' * (len(api_key)-8)}{api_key[-8:]}[/]")
        
        folder_name = Prompt.ask("[bold cyan][2] TARGET FOLDER[/] (e.g., Code, or type 'back')", default=".")
        
        # Clean up input
        folder_name = folder_name.strip().strip('"').strip("'")

        if folder_name.lower() == 'back':
            api_key = ""
            display_dashboard()
            continue

        if folder_name.lower() == 'exit':
            break

        # Smart Path Resolution
        possible_paths = [
            os.path.abspath(folder_name), 
            os.path.join(os.path.dirname(os.getcwd()), folder_name), 
            folder_name 
        ]
        
        target_path = None
        for p in possible_paths:
            if os.path.exists(p) and os.path.isdir(p):
                target_path = os.path.abspath(p)
                break
        
        if not target_path:
            console.print(f"[red]Error: Could not find folder '{folder_name}'[/]")
            time.sleep(2)
            display_dashboard()
            continue

        folder_path = target_path

        try:
            genai.configure(api_key=api_key)
            
            # Try to find the best available model
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Prefer 1.5 flash, then 1.5 pro, then 1.0 pro
            preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
            model_name = None
            
            for p in preferred:
                if p in available_models:
                    model_name = p
                    break
            
            if not model_name:
                # Fallback to whatever is available if preferred aren't found
                if available_models:
                    model_name = available_models[0]
                else:
                    raise Exception("No generative models found for this API key.")
            
            console.print(f"[dim]Using model: {model_name}[/]")
            model = genai.GenerativeModel(model_name)
            
        except Exception as e:
            console.print(f"[bold red]CRITICAL ERROR: {str(e)}[/]")
            console.print("[yellow]Hint: Ensure your API key is a valid Google AI Studio key.[/]")
            api_key = "" 
            time.sleep(4)
            display_dashboard()
            continue

        console.print(f"\n[bold green][STATUS: CRAWLING {folder_path}...][/]")
        files = scan_files(folder_path)
        
        if not files:
            console.print("[yellow]No relevant source files found to scan. Returning to menu...[/]")
            time.sleep(2)
            display_dashboard()
            continue

        console.print(f"[bold green]Detected {len(files)} files. Starting Deep Audit...[/]\n")

        with Live(console=console, refresh_per_second=4) as live:
            for i, file_path in enumerate(files):
                rel_path = os.path.relpath(file_path, folder_path)
                live.update(Align.center(Panel(f"Scanning [{i+1}/{len(files)}]: {rel_path}...", style="yellow")))
                
                report = analyze_file(file_path, model)
                
                if "NO VULNERABILITIES DETECTED" not in report.upper():
                    console.print(Panel(report, style="red", box=box.ROUNDED, title="[bold red]HOLE REPORT[/]"))
                else:
                    console.print(f"[dim green][✓] {rel_path}: Clean[/]")

        console.print("\n[bold cyan]=================================================================================[/]")
        console.print("[bold cyan][ AUDIT COMPLETE ][/]")
        console.print("[bold cyan]=================================================================================[/]")
        
        if Prompt.ask("\nPerform another scan?", choices=["y", "n"], default="y") == "n":
            break
        display_dashboard()

    console.print("[bold cyan]Exiting Zenith Security Auditor. Goodbye![/]")

if __name__ == "__main__":
    main()
