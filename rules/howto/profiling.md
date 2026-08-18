# HOWTO — Python CPU profiling with py-spy

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

## Profiling — Python CPU (py-spy)

Sampling profiler, attaches to a running process (`pip install py-spy`).

1. **Find the PID:**
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId, CommandLine | Format-List
   ```
2. **Live monitor:** `py-spy top --pid <PID> --rate 100` — wait for the state
   under investigation.
3. **Read:** `%Own` = time in the function itself; `%Total` = including callees;
   follow the chain bottom-up to the root caller.
4. **Flame graph:** `py-spy record --output profile.svg --pid <PID> --duration 30`.

`top` accumulates since process start — restart the app and measure a short,
focused window for clean results. Genuinely idle = all functions 0.00%.
