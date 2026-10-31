# NSW2 research: FC27-shaped stress replay and fake NSP

This is a research-only workload based on the 415 anonymized five-second
telemetry windows from the 14 October PS5 FC27 session (source 2efd8b3c).
The source fixture has 60,955 compositor callbacks, 858 gaps >50ms,
10 gaps >500ms, and maximum 1,288.129ms. These are HISTORICAL data.

- At synthetic x1/x4/x8 load, repeatedly mutate HUD/pitch/kit versions,
  remap/evict cache descriptors, and fail if a fresh HUD draw is black or stale.
- Intentionally broken variants must be caught (missing invalidation and
  dropped black HUD image). A 750ms guest pause with 30Hz compositor must be
  recognized as repeating content, not smooth guest progress.
- A counterfactual 32-slot/60-unit-per-second queue reports pressure under
  x4/x8. This is not RADV throughput or real FC27 queue behavior.
- Native source-extracted C++ tests exercise the actual selected Encore
  Vulkan texture feedback, DMA/remap upload, blit pipeline state, HUD TIC
  freshness and frame-cache lock ownership with mock GPU objects.

The generated fc27-synthetic.nsp is a structurally valid PFS0 archive with
a lawful source-verified AArch64 HOS main, an unsigned synthetic main.npdm,
procedural HUD/pitch/kit bytes, and a small explanatory manifest.
It contains NO NCA, licensed game code, game art, title keys or Nintendo
firmware. Thus it is deliberately NOT BOOTABLE with Encore's NSP loader.
For real KProcess launch research, use the separate paired ExeFS/main file.
CI publishes the fixture and stress-report.json for seven days.

Passing CI means only that the model and source-extracted host regressions
pass. It DOES NOT establish actual PS5 GPU pixels, HUD correctness, or a
performance improvement on FC27. Genuine hardware validation still needs
guest progress counters + input-to-image + texture content ID/CRC + Vulkan
present timestamps, with logs and original game files kept private.
