# Eden Encore R457 — two PS5 real-console boot blockers (2026-11-11)

## Evidence boundary

- **Actual native release source:** `ec8b519182532d3864c5a67dd27aa41aa9d43ff3`, pinned vendor `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`, R457 native workflow [#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990). Source identification is not proof that a runtime package was installed correctly; the crash code size matches the associated `llvm-pie.elf`.
- **Actual user console testing, cache cleared:** two crash files for NS1 FC27 and a normal failed launch log for NS2. Never upload the entire user log archives (which may expose paths/identifiers) as a PR asset. The minimal observations below are sufficient to reproduce forensic analyses.
- **Exact artifact recovered from GitHub:** `build/symbols/Prospero.Eden-Encore-R457.elf`, `199322632` bytes from the recovered R457 bundle, symbols trace to `memory_native_a32.cpp`; `crash-provenance.json` says `native_ps5_execution_verified=false`. Tests of this ELF alone do not qualify emulation on the console.

## P0-NS1 — FC27: ABI KProcess 4/6 cœurs confirmé par ELF R457

### Preuves de crash

Les deux crashes à 10:06:47 et 10:07:14 ont le même signal `SIGSEGV`, la même adresse fautive `0x10`, le même thread `audio` et le même offset `eboot+0x39152f` (image PS5 à `0x400000`, ELF de symboles `.text` à zéro).

Dans **l'ELF non dépouillé du même build R457** :
- `Core::Memory::Memory::Impl::GetSpan` à `0x39152f` exécute `mov 0x10(%rdi), %r8` avec **`rdi=0`**, d'où le SIGSEGV.
- Le constructeur réel de `Kernel::KProcess` (vers `0x2aa150`) prépare **`m_memory` à `KProcess+0x1b0`** ; l'instruction `lea 0x1b0(%rbx), %rdi` se trouve à `0x2aa1ff`, avant l'appel du constructeur de `Core::Memory::Memory` vers `0x2aa20c`.
- Le code compilé de `AudioCore::DeviceSession::AppendBuffers` (vers `0xfe7a50`) lit `handle` puis fabrique l'adresse de **`m_memory` à `KProcess+0x160`** (immédiat `0x160` vers `0xfe7b22`), avant d'appeler `CpuGuestMemory<short, UnsafeRead>::Read`.
- **Différence exacte : `0x1b0 - 0x160 = 0x50 = 80 octets`.** Le `KProcess` épinglé contient cinq tableaux `std::array` à huit octets par entrée **avant `m_memory`**. `Core::Hardware::NUM_CPU_CORES` vaut 4 dans l'en-tête source Eden d'origine, mais 6 dans `vendor/encore-active/ns2-runtime/cpu6/core/hardware_properties.h`. Deux entrées de plus dans cinq tableaux expliquent **exactement** les 80 octets.
- Le moteur PS5 sélectionne déjà l'en-tête CPU6 pour `core`, `dynarmic` et `eden-headless` dans `headless/CMakeLists.txt`, mais **pas en priorité explicite pour `audio_core` et `video_core`**. C'est une **incohérence ABI/ODR entre unités de compilation**, pas une démonstration d'un constructeur `Memory` intrinsèquement défaillant.

**Conclusion prouvée** : le binaire utilise au moins deux dispositions de `KProcess` incompatibles ; l'audio lit une adresse d'objet qui n'est pas `m_memory`. Ce diagnostic explique l'accès nul à `GetSpan` et oriente une correction du contrat des en-têtes de compilation. Il reste à confirmer que **toutes** les unités natives utilisent le même layout et qu'aucun second problème ne survient après.

### Correctif ciblé sur la PR #50 (sans changer vendor)

- Le bloc conditionnel PS5 CPU6 du **vrai** `headless/CMakeLists.txt` force `target_include_directories(audio_core BEFORE PRIVATE "${EDEN_NS2_CPU6_ROOT}")` et le même contrat sur `video_core`, en conservant ceux de `core`, `dynarmic` et de l'exécutable.
- `headless/ps5_cpu6_abi_probe.cpp` est inscrit comme unité compilée dans **`core`, `audio_core`, `video_core`** : l'assertion C++ `NUM_CPU_CORES == 6` refuse une compilation qui verrait le mauvais en-tête et vérifie l'accès réel à `KProcess::GetMemory`.
- [Contrôle host ABI #43016026480](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43016026480) : **SUCCESS** sur `e5437841`. Le script compile le véritable témoin contre un jeu synthétique d'en-têtes `4 cœurs` (échec attendu) et `6 cœurs` (succès). **Il ne constitue pas une compilation réelle des trois unités PS5**.
- [PR vendor #41](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/41), ancien essai de silence temporaire en cas de mémoire « non prête », est **supplantée et ne doit pas être fusionnée** : elle masque le défaut ABI et risquerait d'occulter d'autres champs mal adressés. Aucun changement de pointeur vendor.

### Portes de sortie

1. Confirmer sur **vrai graphe CMake PS5** les lignes de compilation et priorités des includes pour les trois cibles, puis passer leurs assertions C++ sans erreur (aucun refactor large ni masquage de warning).
2. Vérifier l'identité ABI de tous les consommateurs de `KProcess`, particulièrement les autres services audio et GPU ; ne pas se limiter au symptôme FC27.
3. Valider sur **un vrai build PS5 identifié et testé sur la console** : FC27 dépasse `AudioOut::Start`, affiche sa première image de jeu, l'audio reste fonctionnel et le crash `0x39152f` ne revient pas.
4. Si un autre crash survient, symboliser son **nouvel ELF** ; ne pas assimiler les CI vertes à une validation du jeu.

## P0-NS2 — physically impossible monolithic 12 GiB guest backing on PS5

Two launches of NS2 titles fail *before* game boot with the same exception:
- `Direct allocation failed: rc=80020023 bytes=12886999040 limit=13019119616` → `Game load failed: Backing allocation: Cannot allocate memory`.
- The requested 12.00 GiB continuous allocation exceeds the largest single free direct-memory span measured at this point (~7.5 GiB); the overall direct-memory limit value is not the free contiguous capacity.
- Main `src/host_memory.cpp` `HostMemory::Impl(requested,...)` uses `AllocateMemoryPages(requested)` on `PS5_NATIVE` and throws `std::system_error(..., "Backing allocation")` on failure.
- Main `src/memory_pages.cpp` attempts a monolithic `sceKernelAllocateDirectMemory` for the full requested size. The existing sparse **JIT** reservations are not a replacement for the guest DRAM backing; logs show `EDEN_JIT_SPARSE_MEMORY phase=core_initialized reserved=0 committed=0` separately.
- In the same logs, the 3D-jacket snapshot was prepared before failure. No Vulkan/NS2 game frame was ever demonstrated. Do not infer that shader issues are fixed or still blocking until memory init succeeds.

Required architectural change: preserve the **full emulated NS2 guest DRAM address space** but reserve host virtual range independently of physically committed pages. Implement page/granule-level, owned, lazy direct-memory commit with synchronized read/write, GPU DMA/address-translation and Vulkan alias coherence, correct zero-fill on first touch, defined reuse and rollback; maintain alignment, exact ownership, use-after-free prevention, and peak physical memory budget. `std::memset` of a virtual hole, reduced declared NS2 DRAM, silent allocation retries, increasing swap on the console, or `malloc(12 GiB)` are NOT sufficient.

### Avancée du modèle d'ownership (recherche uniquement)

- `headless/ps5_ns2_guest_backing_plan.h` modélise 12 Gio de **capacité virtuelle** en 6144 blocs de 2 Mio, avec propriétaires physiques indépendants, budget explicite et transactions `Begin → Stage → Publish` ou `Abort → ReleaseAcknowledged → FinishAbort`.
- `tools/ns2/test_r457_ps5_guest_backing_plan.cpp` contrôle le premier et le dernier bloc, les budgets, l'absence de double propriétaire, le rollback partiel, la non-libération des résidents existants et la nécessité d'un accusé de libération.
- [CI NS2 #43016026399](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43016026399) : **SUCCESS** au commit `e5437841`. Elle interdit expressément l'inclusion du modèle dans `src/host_memory.cpp` : aucun raccordement PS5 dangereux n'est introduit.
- Ce modèle n'implémente **ni** `sceKernelReserveVirtualRange` + commit paresseux, **ni** mapping/zero-fill au premier accès, **ni** les alias GPU/CPU, **ni** les contraintes de `DirectMemoryStart`/fastmem. Il est **impossible de conclure que NS2 démarre** depuis cette CI.

Resolution / test gates:
1. Host mapping ownership state machine et **implémentation réelle** du commit/décommit sur granules natives 16K ou blocs 2M, accès à la première/dernière page, CPU read/write transverses, répétition, pas de double-free ; modèle logique seul insuffisant.
2. Exhaustion and fragmentation behavior, predictable error handling and rollback, plus consistent CPU→GPU and GPU→CPU views; protect source shared with NS1 and use only real compiled overrides.
3. Real PS5 CMake graph selects all modified sources and headers; run an isolated memory test before a full build.
4. PS5 startup gate: direct backing no longer asks for 12 GiB physical at once; both NS2 games reach **guest CPU service startup and first GPU frame handoff** before claiming success.

## Launcher regression distinct from the boot blockers

[Draft PR #49](https://github.com/niakw/ProsperoEden-Encore/pull/49) is reserved for visible launcher fixes and host checks (L1/R1 routing, R457 display, firmware/ns1/ns2 format/status, centered settings gear). It does **not** fix the NS1/NS2 memory crashes. Other texture/orientation/timing defects remain separately unqualified.

## Do not regress

- Keep `main` and the pinned `vendor` untouched while the current R457 console build is under diagnosis.
- Do not repeatedly build the native package until the new P0 host gates and actual CMake source selection pass.
- Distinguish proven binary fault location from a merely hypothesized ownership cause.
- Never mark a CI-green result as PS5 gameplay success.
