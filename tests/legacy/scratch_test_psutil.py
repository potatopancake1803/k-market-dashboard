import psutil

_lms_procs = {}

def get_hardware():
    mem_bytes = 0
    cpu_pct = 0.0
    try:
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = p.info.get('name') or ""
                cmdline = p.info.get('cmdline') or []
                full_cmd = " ".join(cmdline).lower()
                name_lower = name.lower()
                if "lm studio" in name_lower or "lmstudio" in full_cmd or "lmlink" in full_cmd or "llama-server" in full_cmd:
                    pid = p.info['pid']
                    if pid not in _lms_procs:
                        _lms_procs[pid] = p
                        p.cpu_percent(interval=None) # Prime it
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        dead_pids = []
        for pid, p in _lms_procs.items():
            try:
                mem_bytes += p.memory_info().rss
                cpu_pct += p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                dead_pids.append(pid)
        for pid in dead_pids:
            del _lms_procs[pid]
    except Exception:
        pass
        
    try:
        ncpu = psutil.cpu_count() or 1
        cpu_pct = cpu_pct / ncpu
    except Exception:
        pass
        
    return {"ram_gb": round(mem_bytes / (1024**3), 1), "cpu_pct": round(cpu_pct, 1)}

# Run twice to see cpu
print("Run 1:", get_hardware())
import time
time.sleep(1)
print("Run 2:", get_hardware())
