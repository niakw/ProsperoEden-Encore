# Comparatif différentiel du runtime actif — NS2 P0 / FC27 NS1 P1

**Photographie du 26 novembre 2026.** Demandé après l'échec console du build 68122b0b / 806252e9. Ni certificat de compatibilité, ni nouveau relevé des commandes NULL. Priorité : première soumission réelle, première image, fermeture, HUD/pause.

## Révisions

| Dépôt | Branche / licence | SHA examiné |
|---|---|---|
| Moteur | main / GPL-3.0 | `cbf54c0c7f464237b39320b1851494cb98568ec4` |
| Vendor, gitlink exact | main / GPL-3.0 | `465d7e9c82f364dcde05354d67ec1b5bf5e2682d` |
| Lichii | nx2 / GPL-3.0 | `0288882f36692a94b56fa85177abdad0ec8be59d` |
| EglantinePS5 | main / GPL-3.0 | `75a552ff945521eb31adf34f34ccb73a003809dc` |
| nxnative | main / MIT | `35fea5c2ee781689ff224e614a8da71867a571bf` |
| libounce | ISC | `03af07a739a9a3b48704500cffcd6155692cc194` |

Le moteur testé est antérieur aux corrections GSV/JIT/scheduler. Cette livraison est limitée aux fonctions P0/P1 ci-dessous, pas aux millions de lignes des dépôts. Les extraits conservent les licences respectives. Les comparaisons alignent les lignes après suppression des espaces de bordure et ne prouvent pas une équivalence sémantique. Les diffs ne sont pas des patches. **- = Encore ; + = upstream ; deux numéros = texte identique à l'indentation près.** Les fonctions non récupérables sont signalées. Lichii et Eglantine partagent des ancêtres : ne pas compter leurs accords comme deux preuves indépendantes.

Sélection CMake : [Dynarmic natif](https://github.com/niakw/ProsperoEden-Encore/blob/cbf54c0c7f464237b39320b1851494cb98568ec4/headless/CMakeLists.txt#L488-L505), [DMA/Puller](https://github.com/niakw/ProsperoEden-Encore/blob/cbf54c0c7f464237b39320b1851494cb98568ec4/headless/CMakeLists.txt#L2557-L2568), [déduplication Puller](https://github.com/niakw/ProsperoEden-Encore/blob/cbf54c0c7f464237b39320b1851494cb98568ec4/headless/CMakeLists.txt#L4016-L4025), [GSV](https://github.com/niakw/ProsperoEden-Encore/blob/cbf54c0c7f464237b39320b1851494cb98568ec4/headless/CMakeLists.txt#L4165-L4197). Propriétaires maintenus, pas copies historiques de sources/eden. Compilation complète du candidat non effectuée.

## Résultat console à expliquer

| Titre | Build 68122b0b — résultat | Priorité |
|---|---|---|
| MKW 0400C3F00006E000 | panic invité 0x1472 (2114-0010), pas de soumission observée | 429/315/1510, images/VI2 |
| DK 040074A01BF12000 | freeze, watchdog d'arrêt 10 s | cancellation, teardown GPU/IPC/JIT |
| Pokopia 0400A3A01EE4C000 | deux GPFIFO natives, attente syncpoint, fermeture forcée | producteur/retirement, sémaphores, scheduler |
| Z-A 0100F43008C44000 | SIGABRT hôte lors de l'init JIT après MKW | alias RX/RW, trim prelude, changement de titre |
| FC27 NS1 | 27,89 FPS présentation moyenne, 41 intervalles >100 ms, HUD tardif/pause lente ; pas d'A/B à scène identique | contention BufferCache/readback, cadence |

Ne pas interpréter un compteur GPU global par lots de 64 comme preuve qu'aucun paquet n'est entré : vérifier les traces GPFIFO individuelles.

## Comparaison ligne à ligne : homologues directs

### P0-01 · GSV 429 — création d'images

Écart avéré dans le build testé : un seul identifiant réservé même lorsque count > 1 ; bfb93d21 réserve base+i, ajoute des offsets et protège les références NVMap. La limite de formats de CalculateNativeImageRequirements reste à comparer avec les paramètres réels du panic MKW. Lien causal exact avec 0x1472 à valider console.

Encore : [graphics_supervisor.cpp:3466–3525](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L3466-L3525) (60 lignes).


<details>
<summary>Lichii — 4825–4842 : 1 alignées, 59 propres Encore, 17 propres upstream</summary>

Source : [nx2_gsv.h:4825–4842](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L4825-L4842). Numéros exacts dans chaque commit.

```diff
- 3466       | void IGraphicsSupervisor::CreateNativeImage(HLERequestContext& ctx) {
- 3467       |     const auto* packet = ctx.CommandBuffer();
- 3468       |     Result result = Kernel::ResultInvalidCombination;
- 3469       |     u32 id{};
- 3470       |     if (packet[0] == 0x1bd && packet[1] == 18) {
- 3471       |         result = Kernel::ResultInvalidState;
- 3472       |         if (m_bootstrap.GpuContextReady()) {
- 3473       |             const std::span<const u32> preferences{packet + 2, 16};
- 3474       |             const u32 count = packet[18];
- 3475       |             const auto requirements = ::Service::AM::CalculateNativeImageRequirements(preferences, count);
- 3476       |             result = Kernel::ResultNotImplemented;
- 3477       |             if (requirements) {
- 3478       |                 const std::scoped_lock lock{m_native_memory_mutex};
- 3479       |                 result = Kernel::ResultNotFound;
- 3480       |                 const u32 backing = packet[19];
- 3481       |                 const auto owned = m_native_memory.Get(backing);
- 3482       |                 if (owned && owned->bound && m_native_module) {
- 3483       |                     auto& nvmap = m_native_module->GetContainer().GetNvMapFile();
- 3484       |                     const auto handle = nvmap.GetHandle(backing);
- 3485       |                     result = Kernel::ResultInvalidSize;
- 3486       |                     if (handle && handle->allocated && handle->size >= requirements->size) {
- 3487       |                         result = Kernel::ResultOutOfResource;
- 3488       |                         if (count && count <= NativeImageLedger::MaxEntries - m_native_images.Count() &&
- 3489       |                             m_next_image_id && m_next_image_id + count - 1 <= std::numeric_limits<u32>::max()) {
- 3490       |                             // The SDK derives each image handle as base + i
- 3491       |                             // (Lichii 0288882f, NX2_NOTES). One backing ref
- 3492       |                             // per member keeps 430 and teardown symmetric.
- 3493       |                             u32 duplicated{};
- 3494       |                             for (; duplicated < count; ++duplicated)
- 3495       |                                 if (handle->Duplicate(true) != Nvidia::NvResult::Success) break;
- 3496       |                             if (duplicated == count) {
- 3497       |                                 try {
- 3498       |                                     if (const auto created = m_native_images.Create(
- 3499       |                                             backing, handle->size, *requirements, preferences,
- 3500       |                                             static_cast<u32>(m_next_image_id), count)) {
- 3501       |                                         id = *created;
- 3502       |                                         m_next_image_id += count;
- 3503       |                                         result = ResultSuccess;
- 3504       |                                     }
- 3505       |                                 } catch (const std::bad_alloc&) {
- 3506       |                                     result = Kernel::ResultOutOfResource;
- 3507       |                                 }
- 3508       |                             }
- 3509       |                             // The ledger rolls back partial publication on
- 3510       |                             // allocation failure; release ONLY our duplicates.
- 3511       |                             if (result.IsError())
- 3512       |                                 while (duplicated != 0) {
- 3513       |                                     --duplicated;
- 3514       |                                     nvmap.FreeHandle(backing, true);
- 3515       |                                 }
- 3516       |                         }
- 3517       |                     }
- 3518       |                 }
- 3519       |             }
- 3520       |         }
- 3521       |     }
- 3522       |     IPC::ResponseBuilder rb{ctx, 3};
- 3523       |     rb.Push(result.raw);
- 3524       |     rb.Push(id);
+       4825 |     void CreateNativeImage(HLERequestContext& ctx) {
+       4826 |         const auto* w = ctx.CommandBuffer();
+       4827 |         std::scoped_lock lk{m_objects->mutex};
+       4828 |         const u32 id = m_objects->next_image;
+       4829 |         auto& image = m_objects->images[id];
+       4830 |         image.count = std::max<u32>(w[18], 1);
+       4831 |         // nn::gs::sdk::CalculateNativeImageHandle(pool, i) is pool + i, so keep those free.
+       4832 |         m_objects->next_image += image.count;
+       4833 |         image.memory = w[19];
+       4834 |         std::copy_n(w + 2, image.preference.size(), image.preference.begin());
+       4835 |         image.size = Nx2CalculateImageLayout(w + 2).size;
+       4836 |         LOG_INFO(Service,
+       4837 |                  "nx2:gsv {} CreateNativeImage memory={} count={} size={:#x} format={} "
+       4838 |                  "word7={:#x} -> id {}",
+       4839 |                  ctx.GetCommand(), w[19], w[18], image.size, image.preference[6],
+       4840 |                  image.preference[7], id);
+       4841 |         TipcReplyWords(ctx, {id});
  3525  4842 | }
```

</details>


<details>
<summary>EglantinePS5 — 3958–3972 : 1 alignées, 59 propres Encore, 14 propres upstream</summary>

Source : [nx2_gsv.h:3958–3972](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L3958-L3972). Numéros exacts dans chaque commit.

```diff
- 3466       | void IGraphicsSupervisor::CreateNativeImage(HLERequestContext& ctx) {
- 3467       |     const auto* packet = ctx.CommandBuffer();
- 3468       |     Result result = Kernel::ResultInvalidCombination;
- 3469       |     u32 id{};
- 3470       |     if (packet[0] == 0x1bd && packet[1] == 18) {
- 3471       |         result = Kernel::ResultInvalidState;
- 3472       |         if (m_bootstrap.GpuContextReady()) {
- 3473       |             const std::span<const u32> preferences{packet + 2, 16};
- 3474       |             const u32 count = packet[18];
- 3475       |             const auto requirements = ::Service::AM::CalculateNativeImageRequirements(preferences, count);
- 3476       |             result = Kernel::ResultNotImplemented;
- 3477       |             if (requirements) {
- 3478       |                 const std::scoped_lock lock{m_native_memory_mutex};
- 3479       |                 result = Kernel::ResultNotFound;
- 3480       |                 const u32 backing = packet[19];
- 3481       |                 const auto owned = m_native_memory.Get(backing);
- 3482       |                 if (owned && owned->bound && m_native_module) {
- 3483       |                     auto& nvmap = m_native_module->GetContainer().GetNvMapFile();
- 3484       |                     const auto handle = nvmap.GetHandle(backing);
- 3485       |                     result = Kernel::ResultInvalidSize;
- 3486       |                     if (handle && handle->allocated && handle->size >= requirements->size) {
- 3487       |                         result = Kernel::ResultOutOfResource;
- 3488       |                         if (count && count <= NativeImageLedger::MaxEntries - m_native_images.Count() &&
- 3489       |                             m_next_image_id && m_next_image_id + count - 1 <= std::numeric_limits<u32>::max()) {
- 3490       |                             // The SDK derives each image handle as base + i
- 3491       |                             // (Lichii 0288882f, NX2_NOTES). One backing ref
- 3492       |                             // per member keeps 430 and teardown symmetric.
- 3493       |                             u32 duplicated{};
- 3494       |                             for (; duplicated < count; ++duplicated)
- 3495       |                                 if (handle->Duplicate(true) != Nvidia::NvResult::Success) break;
- 3496       |                             if (duplicated == count) {
- 3497       |                                 try {
- 3498       |                                     if (const auto created = m_native_images.Create(
- 3499       |                                             backing, handle->size, *requirements, preferences,
- 3500       |                                             static_cast<u32>(m_next_image_id), count)) {
- 3501       |                                         id = *created;
- 3502       |                                         m_next_image_id += count;
- 3503       |                                         result = ResultSuccess;
- 3504       |                                     }
- 3505       |                                 } catch (const std::bad_alloc&) {
- 3506       |                                     result = Kernel::ResultOutOfResource;
- 3507       |                                 }
- 3508       |                             }
- 3509       |                             // The ledger rolls back partial publication on
- 3510       |                             // allocation failure; release ONLY our duplicates.
- 3511       |                             if (result.IsError())
- 3512       |                                 while (duplicated != 0) {
- 3513       |                                     --duplicated;
- 3514       |                                     nvmap.FreeHandle(backing, true);
- 3515       |                                 }
- 3516       |                         }
- 3517       |                     }
- 3518       |                 }
- 3519       |             }
- 3520       |         }
- 3521       |     }
- 3522       |     IPC::ResponseBuilder rb{ctx, 3};
- 3523       |     rb.Push(result.raw);
- 3524       |     rb.Push(id);
+       3958 |     void CreateNativeImage(HLERequestContext& ctx) {
+       3959 |         const auto* w = ctx.CommandBuffer();
+       3960 |         std::scoped_lock lk{m_objects->mutex};
+       3961 |         const u32 id = m_objects->next_image;
+       3962 |         auto& image = m_objects->images[id];
+       3963 |         image.count = std::max<u32>(w[18], 1);
+       3964 |         // nn::gs::sdk::CalculateNativeImageHandle(pool, i) is pool + i, so keep those free.
+       3965 |         m_objects->next_image += image.count;
+       3966 |         image.memory = w[19];
+       3967 |         std::copy_n(w + 2, image.preference.size(), image.preference.begin());
+       3968 |         image.size = Nx2CalculateImageLayout(w + 2).size;
+       3969 |         LOG_INFO(Service, "nx2:gsv 429 CreateNativeImage memory={} count={} size={:#x} -> id {}",
+       3970 |                  w[19], w[18], image.size, id);
+       3971 |         TipcReplyWords(ctx, {id});
  3525  3972 | }
```

</details>

### P0-02 · GSV 314/315 — alias de fenêtre

Encore exige le groupe complet et refuse les handles absents ; les forks mémorisent l'état du premier objet puis renvoient succès. Ne pas copier ce faux succès. Tester le groupe complet issu de 429, le retrait 314 et la présentation VI2.

Encore : [graphics_supervisor.cpp:3527–3543](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L3527-L3543) (17 lignes).


<details>
<summary>Lichii — 5120–5129 : 3 alignées, 14 propres Encore, 7 propres upstream</summary>

Source : [nx2_gsv.h:5120–5129](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L5120-L5129). Numéros exacts dans chaque commit.

```diff
- 3527       | void IGraphicsSupervisor::ConfigureNativeWindowImagePool(HLERequestContext& ctx) {
- 3528       |     const auto* packet = ctx.CommandBuffer();
+       5120 |     void ConfigureWindowImagePool(HLERequestContext& ctx) {
+       5121 |         const u32 id = ctx.CommandBuffer()[2];
  3529  5122 |     const bool create = ctx.GetCommand() == 315;
- 3530       |     Result result = Kernel::ResultInvalidCombination;
- 3531       |     if (packet[0] == (create ? 0x14bU : 0x14aU) &&
- 3532       |         packet[1] == (create ? 2U : 1U)) {
- 3533       |         const std::scoped_lock lock{m_native_memory_mutex};
- 3534       |         result = Kernel::ResultNotFound;
- 3535       |         if (m_native_images.Get(packet[2])) {
- 3536       |             const u32 count = create ? packet[3] : 0;
- 3537       |             result = m_native_images.ConfigureWindowPool(packet[2], count, create)
- 3538       |                 ? ResultSuccess : Kernel::ResultInvalidState;
- 3539       |         }
+       5123 |         std::scoped_lock lk{m_objects->mutex};
+       5124 |         if (auto it = m_objects->images.find(id); it != m_objects->images.end()) {
+       5125 |             it->second.window_pool = create;
  3540  5126 |     }
- 3541       |     IPC::ResponseBuilder rb{ctx, 2};
- 3542       |     rb.Push(result.raw);
+       5127 |         LOG_INFO(Service, "nx2:gsv {} window image pool image {}", ctx.GetCommand(), id);
+       5128 |         TipcReplyWords(ctx, {});
  3543  5129 | }
```

</details>


<details>
<summary>EglantinePS5 — 4250–4259 : 3 alignées, 14 propres Encore, 7 propres upstream</summary>

Source : [nx2_gsv.h:4250–4259](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L4250-L4259). Numéros exacts dans chaque commit.

```diff
- 3527       | void IGraphicsSupervisor::ConfigureNativeWindowImagePool(HLERequestContext& ctx) {
- 3528       |     const auto* packet = ctx.CommandBuffer();
+       4250 |     void ConfigureWindowImagePool(HLERequestContext& ctx) {
+       4251 |         const u32 id = ctx.CommandBuffer()[2];
  3529  4252 |     const bool create = ctx.GetCommand() == 315;
- 3530       |     Result result = Kernel::ResultInvalidCombination;
- 3531       |     if (packet[0] == (create ? 0x14bU : 0x14aU) &&
- 3532       |         packet[1] == (create ? 2U : 1U)) {
- 3533       |         const std::scoped_lock lock{m_native_memory_mutex};
- 3534       |         result = Kernel::ResultNotFound;
- 3535       |         if (m_native_images.Get(packet[2])) {
- 3536       |             const u32 count = create ? packet[3] : 0;
- 3537       |             result = m_native_images.ConfigureWindowPool(packet[2], count, create)
- 3538       |                 ? ResultSuccess : Kernel::ResultInvalidState;
- 3539       |         }
+       4253 |         std::scoped_lock lk{m_objects->mutex};
+       4254 |         if (auto it = m_objects->images.find(id); it != m_objects->images.end()) {
+       4255 |             it->second.window_pool = create;
  3540  4256 |     }
- 3541       |     IPC::ResponseBuilder rb{ctx, 2};
- 3542       |     rb.Push(result.raw);
+       4257 |         LOG_INFO(Service, "nx2:gsv {} window image pool image {}", ctx.GetCommand(), id);
+       4258 |         TipcReplyWords(ctx, {});
  3543  4259 | }
```

</details>

### P0-03 · GSV 430 — durée de vie des images

Comparer destruction individuelle, mapping GPU, références et retirement. Encore interdit la destruction d'une image toujours en alias de fenêtre : conservation justifiée tant que le contrat invité 314/430 est respecté.

Encore : [graphics_supervisor.cpp:3545–3562](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L3545-L3562) (18 lignes).


<details>
<summary>Lichii — 5097–5117 : 3 alignées, 15 propres Encore, 18 propres upstream</summary>

Source : [nx2_gsv.h:5097–5117](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L5097-L5117). Numéros exacts dans chaque commit.

```diff
- 3545       | void IGraphicsSupervisor::DestroyNativeImage(HLERequestContext& ctx) {
- 3546       |     const auto* packet = ctx.CommandBuffer();
- 3547       |     Result result = Kernel::ResultInvalidCombination;
- 3548       |     if (packet[0] == 0x1be && packet[1] == 1) {
- 3549       |         const std::scoped_lock lock{m_native_memory_mutex};
- 3550       |         result = Kernel::ResultNotFound;
- 3551       |         const auto image = m_native_images.Get(packet[2]);
- 3552       |         if (image && m_native_module && !image->window_pool) {
- 3553       |             const auto freed = m_native_module->GetContainer().GetNvMapFile().FreeHandle(
- 3554       |                 image->backing, true);
- 3555       |             result = Kernel::ResultInvalidState;
- 3556       |             if (freed && m_native_images.Destroy(packet[2]))
- 3557       |                 result = ResultSuccess;
+       5097 |     void DestroyNativeImage(HLERequestContext& ctx) {
+       5098 |         const u32 id = ctx.CommandBuffer()[2];
+       5099 |         if (Nx2VideoTraceEnabled()) {
+       5100 |             LOG_INFO(Service, "nx2:vdec trace destroy image={} command={}", id, ctx.GetCommand());
  3558  5101 |         }
+       5102 |         const auto image_mutex = m_objects->DecoderMutex(id);
+       5103 |         std::unique_lock<std::mutex> image_lock;
+       5104 |         if (image_mutex) {
+       5105 |             image_lock = std::unique_lock{*image_mutex};
  3559  5106 |     }
- 3560       |     IPC::ResponseBuilder rb{ctx, 2};
- 3561       |     rb.Push(result.raw);
+       5107 |         std::optional<std::pair<u64, u64>> unmap;
+       5108 |         {
+       5109 |             std::scoped_lock lk{m_objects->mutex};
+       5110 |             if (const auto image = m_objects->images.find(id); image != m_objects->images.end()) {
+       5111 |                 unmap = TakeDecoderMapping(image->second);
+       5112 |                 m_objects->images.erase(image);
  3562  5113 | }
+       5114 |         }
+       5115 |         DropDecoderMapping(unmap);
+       5116 |         TipcReplyWords(ctx, {});
+       5117 |     }
```

</details>


<details>
<summary>EglantinePS5 — 4227–4247 : 3 alignées, 15 propres Encore, 18 propres upstream</summary>

Source : [nx2_gsv.h:4227–4247](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L4227-L4247). Numéros exacts dans chaque commit.

```diff
- 3545       | void IGraphicsSupervisor::DestroyNativeImage(HLERequestContext& ctx) {
- 3546       |     const auto* packet = ctx.CommandBuffer();
- 3547       |     Result result = Kernel::ResultInvalidCombination;
- 3548       |     if (packet[0] == 0x1be && packet[1] == 1) {
- 3549       |         const std::scoped_lock lock{m_native_memory_mutex};
- 3550       |         result = Kernel::ResultNotFound;
- 3551       |         const auto image = m_native_images.Get(packet[2]);
- 3552       |         if (image && m_native_module && !image->window_pool) {
- 3553       |             const auto freed = m_native_module->GetContainer().GetNvMapFile().FreeHandle(
- 3554       |                 image->backing, true);
- 3555       |             result = Kernel::ResultInvalidState;
- 3556       |             if (freed && m_native_images.Destroy(packet[2]))
- 3557       |                 result = ResultSuccess;
+       4227 |     void DestroyNativeImage(HLERequestContext& ctx) {
+       4228 |         const u32 id = ctx.CommandBuffer()[2];
+       4229 |         if (Nx2VideoTraceEnabled()) {
+       4230 |             LOG_INFO(Service, "nx2:vdec trace destroy image={} command={}", id, ctx.GetCommand());
  3558  4231 |         }
+       4232 |         const auto image_mutex = m_objects->DecoderMutex(id);
+       4233 |         std::unique_lock<std::mutex> image_lock;
+       4234 |         if (image_mutex) {
+       4235 |             image_lock = std::unique_lock{*image_mutex};
  3559  4236 |     }
- 3560       |     IPC::ResponseBuilder rb{ctx, 2};
- 3561       |     rb.Push(result.raw);
+       4237 |         std::optional<std::pair<u64, u64>> unmap;
+       4238 |         {
+       4239 |             std::scoped_lock lk{m_objects->mutex};
+       4240 |             if (const auto image = m_objects->images.find(id); image != m_objects->images.end()) {
+       4241 |                 unmap = TakeDecoderMapping(image->second);
+       4242 |                 m_objects->images.erase(image);
  3562  4243 | }
+       4244 |         }
+       4245 |         DropDecoderMapping(unmap);
+       4246 |         TipcReplyWords(ctx, {});
+       4247 |     }
```

</details>

### P0-04 · syncpt 103 — lecture du compteur

Encore lit le compteur natif 64 bits après retirement GPU ; Lichii/Eglantine lisent GetGuestSyncpointValue (progression au parseur). Libounce confirme UINT64_MAX pour producteur invalide. Ne pas signaler avant les écritures GPU : vérifier le producteur et la publication.

Encore : [graphics_supervisor.cpp:298–312](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L298-L312) (15 lignes).


<details>
<summary>Lichii — 236–243 : 3 alignées, 12 propres Encore, 5 propres upstream</summary>

Source : [nx2_gsv.h:236–243](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L236-L243). Numéros exacts dans chaque commit.

```diff
   298   236 |     void QueryCounter(HLERequestContext& ctx) {
-  299       |         const auto* packet = ctx.CommandBuffer();
-  300       |         if (packet[0] != 16 + 103 || packet[1] != 1) {
-  301       |             IPC::ResponseBuilder rb{ctx, 2};
-  302       |             rb.Push(Kernel::ResultInvalidCombination.raw);
-  303       |             return;
-  304       |         }
-  305       |         const u32 syncpoint = ~packet[2];
-  306       |         // libounce gsvSyncCheckNative treats UINT64_MAX as an invalid
-  307       |         // producer (already reached). Returning zero can strand a waiter.
+        237 |         const u32 syncpoint = ~ctx.CommandBuffer()[2];
   308   238 |         const u64 value = syncpoint < HostSyncpoints
-  309       |             ? system.Host1x().GetSyncpointManager().GetNativeGuestSyncpointValue(syncpoint)
-  310       |             : std::numeric_limits<u64>::max();
-  311       |         NativeTipcReplyWords(ctx, {static_cast<u32>(value), static_cast<u32>(value >> 32), 0});
+        239 |                               ? system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(syncpoint)
+        240 |                               : 0;
+        241 |         LOG_DEBUG(Service, "nx2:syncpt 103 syncpoint={} value={:#x}", syncpoint, value);
+        242 |         TipcReplyWords(ctx, {static_cast<u32>(value), static_cast<u32>(value >> 32), 0});
   312   243 |     }
```

</details>


<details>
<summary>EglantinePS5 — 220–227 : 3 alignées, 12 propres Encore, 5 propres upstream</summary>

Source : [nx2_gsv.h:220–227](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L220-L227). Numéros exacts dans chaque commit.

```diff
   298   220 |     void QueryCounter(HLERequestContext& ctx) {
-  299       |         const auto* packet = ctx.CommandBuffer();
-  300       |         if (packet[0] != 16 + 103 || packet[1] != 1) {
-  301       |             IPC::ResponseBuilder rb{ctx, 2};
-  302       |             rb.Push(Kernel::ResultInvalidCombination.raw);
-  303       |             return;
-  304       |         }
-  305       |         const u32 syncpoint = ~packet[2];
-  306       |         // libounce gsvSyncCheckNative treats UINT64_MAX as an invalid
-  307       |         // producer (already reached). Returning zero can strand a waiter.
+        221 |         const u32 syncpoint = ~ctx.CommandBuffer()[2];
   308   222 |         const u64 value = syncpoint < HostSyncpoints
-  309       |             ? system.Host1x().GetSyncpointManager().GetNativeGuestSyncpointValue(syncpoint)
-  310       |             : std::numeric_limits<u64>::max();
-  311       |         NativeTipcReplyWords(ctx, {static_cast<u32>(value), static_cast<u32>(value >> 32), 0});
+        223 |                               ? system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(syncpoint)
+        224 |                               : 0;
+        225 |         LOG_DEBUG(Service, "nx2:syncpt 103 syncpoint={} value={:#x}", syncpoint, value);
+        226 |         TipcReplyWords(ctx, {static_cast<u32>(value), static_cast<u32>(value >> 32), 0});
   312   227 |     }
```

</details>

### P0-05 · syncpt 201 — armement

Comparer largeur du seuil, retrait de l'ancien callback et signalement. Le mode 64 bits d'Encore préserve les seuils que le cast u32 upstream perd ; la boucle Pokopia exige de vérifier la livraison du signal après le fence.

Encore : [graphics_supervisor.cpp:342–381](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L342-L381) (40 lignes).


<details>
<summary>Lichii — 271–312 : 13 alignées, 27 propres Encore, 29 propres upstream</summary>

Source : [nx2_gsv.h:271–312](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L271-L312). Numéros exacts dans chaque commit.

```diff
   342   271 |     void RequestSlotEvent(HLERequestContext& ctx) {
-  343       |         const auto* w = ctx.CommandBuffer();
-  344       |         const auto wait = GraphicsSupervisorProtocol::DecodeSyncpointWait(
-  345       |             std::span<const u32>{w, IPC::COMMAND_BUFFER_LENGTH});
-  346       |         if (!wait) {
-  347       |             IPC::ResponseBuilder rb{ctx, 2};
-  348       |             rb.Push(Kernel::ResultInvalidCombination.raw);
-  349       |             return;
+        272 |         const auto* cmd_buf = ctx.CommandBuffer();
+        273 |         const u32 slot = cmd_buf[2];
+        274 |         const u32 syncpoint = ~cmd_buf[3];
+        275 |         const u64 value = u64{cmd_buf[4]} | (u64{cmd_buf[5]} << 32);
+        276 |         const u32 mode = cmd_buf[6];
+        277 |         LOG_DEBUG(Service, "nx2:syncpt TIPC 201 slot={:#x} syncpoint={} value={:#x} mode={}", slot,
+        278 |                   syncpoint, value, mode);
+        279 |         auto*& event = m_events[slot];
+        280 |         if (event == nullptr) {
+        281 |             event = m_context.CreateEvent(fmt::format("nx2:syncpt:Slot{:x}", slot));
   350   282 |         }
-  351       |         const u32 slot = wait->slot;
-  352       |         const u32 syncpoint = wait->id;
-  353       |         const u64 value = wait->threshold;
-  354       |         auto* event = EventFor(slot);
-  355       |         if (!event) {
-  356       |             IPC::ResponseBuilder rb{ctx, 2};
-  357       |             rb.Push(slot >= m_configured_slots ? Kernel::ResultInvalidArgument.raw
-  358       |                                                : Kernel::ResultOutOfResource.raw);
+        283 |         if (syncpoint >= HostSyncpoints) {
+        284 |             LOG_WARNING(Service, "nx2:syncpt TIPC 201 syncpoint {} out of range, signalling",
+        285 |                         syncpoint);
+        286 |             event->Signal(system.Kernel());
+        287 |             TipcReplyWords(ctx, {});
   359   288 |             return;
   360   289 |         }
   361   290 |         auto& request = m_requests[slot];
   362   291 |         Cancel(request);
+        292 |         // A new request starts unsignalled. Slots are reused by different client objects: title 1's
+        293 |         // movie player got slot 0 after NVN's fence waits had left it signalled, took that as a
+        294 |         // decoded frame and aborted when the decoder had none.
   363   295 |         event->Clear(system.Kernel());
-  364       |         if (syncpoint >= HostSyncpoints) {
-  365       |             event->Signal(system.Kernel());
-  366       |             NativeTipcReplyWords(ctx, {});
-  367       |             return;
-  368       |         }
   369   296 |         request.syncpoint = syncpoint;
-  370       |         request.pending.store(true, std::memory_order_release);
+        297 |         request.pending = true;
   371   298 |         auto& manager = system.Host1x().GetSyncpointManager();
-  372       |         request.handle = manager.RegisterNativeGuestAction(
-  373       |             syncpoint, value, wait->wide,
-  374       |             [shared=m_shared, &kernel=system.Kernel(), request=&request, event] {
+        299 |         // The action runs on the thread that reaches the value, or inline if it is already
+        300 |         // reached.
+        301 |         request.handle = manager.RegisterGuestAction(
+        302 |             syncpoint, static_cast<u32>(value),
+        303 |             [shared = m_shared, &kernel = system.Kernel(), &request, event] {
   375   304 |                 std::scoped_lock lk{shared->mutex};
-  376       |                 if (!shared->alive) return;
-  377       |                 request->pending.store(false, std::memory_order_release);
+        305 |                 if (!shared->alive) {
+        306 |                     return;
+        307 |                 }
+        308 |                 request.pending = false;
   378   309 |                 event->Signal(kernel);
   379   310 |             });
-  380       |         NativeTipcReplyWords(ctx, {});
+        311 |         TipcReplyWords(ctx, {});
   381   312 |     }
```

</details>


<details>
<summary>EglantinePS5 — 255–296 : 13 alignées, 27 propres Encore, 29 propres upstream</summary>

Source : [nx2_gsv.h:255–296](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L255-L296). Numéros exacts dans chaque commit.

```diff
   342   255 |     void RequestSlotEvent(HLERequestContext& ctx) {
-  343       |         const auto* w = ctx.CommandBuffer();
-  344       |         const auto wait = GraphicsSupervisorProtocol::DecodeSyncpointWait(
-  345       |             std::span<const u32>{w, IPC::COMMAND_BUFFER_LENGTH});
-  346       |         if (!wait) {
-  347       |             IPC::ResponseBuilder rb{ctx, 2};
-  348       |             rb.Push(Kernel::ResultInvalidCombination.raw);
-  349       |             return;
+        256 |         const auto* cmd_buf = ctx.CommandBuffer();
+        257 |         const u32 slot = cmd_buf[2];
+        258 |         const u32 syncpoint = ~cmd_buf[3];
+        259 |         const u64 value = u64{cmd_buf[4]} | (u64{cmd_buf[5]} << 32);
+        260 |         const u32 mode = cmd_buf[6];
+        261 |         LOG_DEBUG(Service, "nx2:syncpt TIPC 201 slot={:#x} syncpoint={} value={:#x} mode={}", slot,
+        262 |                   syncpoint, value, mode);
+        263 |         auto*& event = m_events[slot];
+        264 |         if (event == nullptr) {
+        265 |             event = m_context.CreateEvent(fmt::format("nx2:syncpt:Slot{:x}", slot));
   350   266 |         }
-  351       |         const u32 slot = wait->slot;
-  352       |         const u32 syncpoint = wait->id;
-  353       |         const u64 value = wait->threshold;
-  354       |         auto* event = EventFor(slot);
-  355       |         if (!event) {
-  356       |             IPC::ResponseBuilder rb{ctx, 2};
-  357       |             rb.Push(slot >= m_configured_slots ? Kernel::ResultInvalidArgument.raw
-  358       |                                                : Kernel::ResultOutOfResource.raw);
+        267 |         if (syncpoint >= HostSyncpoints) {
+        268 |             LOG_WARNING(Service, "nx2:syncpt TIPC 201 syncpoint {} out of range, signalling",
+        269 |                         syncpoint);
+        270 |             event->Signal(system.Kernel());
+        271 |             TipcReplyWords(ctx, {});
   359   272 |             return;
   360   273 |         }
   361   274 |         auto& request = m_requests[slot];
   362   275 |         Cancel(request);
+        276 |         // A new request starts unsignalled. Slots are reused by different client objects: title 1's
+        277 |         // movie player got slot 0 after NVN's fence waits had left it signalled, took that as a
+        278 |         // decoded frame and aborted when the decoder had none.
   363   279 |         event->Clear(system.Kernel());
-  364       |         if (syncpoint >= HostSyncpoints) {
-  365       |             event->Signal(system.Kernel());
-  366       |             NativeTipcReplyWords(ctx, {});
-  367       |             return;
-  368       |         }
   369   280 |         request.syncpoint = syncpoint;
-  370       |         request.pending.store(true, std::memory_order_release);
+        281 |         request.pending = true;
   371   282 |         auto& manager = system.Host1x().GetSyncpointManager();
-  372       |         request.handle = manager.RegisterNativeGuestAction(
-  373       |             syncpoint, value, wait->wide,
-  374       |             [shared=m_shared, &kernel=system.Kernel(), request=&request, event] {
+        283 |         // The action runs on the GPU thread under the manager's lock, or inline if the value is
+        284 |         // already reached.
+        285 |         request.handle = manager.RegisterGuestAction(
+        286 |             syncpoint, static_cast<u32>(value),
+        287 |             [shared = m_shared, &kernel = system.Kernel(), &request, event] {
   375   288 |                 std::scoped_lock lk{shared->mutex};
-  376       |                 if (!shared->alive) return;
-  377       |                 request->pending.store(false, std::memory_order_release);
+        289 |                 if (!shared->alive) {
+        290 |                     return;
+        291 |                 }
+        292 |                 request.pending = false;
   378   293 |                 event->Signal(kernel);
   379   294 |             });
-  380       |         NativeTipcReplyWords(ctx, {});
+        295 |         TipcReplyWords(ctx, {});
   381   296 |     }
```

</details>

### P0-06 · syncpt 202 — annulation

Les trois chemins signalent l'événement lors de l'annulation même sans attente active pour les slots admissibles. La divergence n'est pas l'absence générale de signal 202. Examiner les slots et les compteurs demandés.

Encore : [graphics_supervisor.cpp:382–398](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L382-L398) (17 lignes).


<details>
<summary>Lichii — 314–332 : 6 alignées, 11 propres Encore, 13 propres upstream</summary>

Source : [nx2_gsv.h:314–332](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L314-L332). Numéros exacts dans chaque commit.

```diff
   382   314 |     void CancelSlotEvent(HLERequestContext& ctx) {
   383   315 |         const u32 slot = ctx.CommandBuffer()[2];
-  384       |         if (slot >= m_configured_slots) {
-  385       |             IPC::ResponseBuilder rb{ctx, 2};
-  386       |             rb.Push(Kernel::ResultInvalidArgument.raw);
-  387       |             return;
+        316 |         LOG_DEBUG(Service, "nx2:syncpt TIPC 202 slot={:#x}", slot);
+        317 |         if (auto it = m_requests.find(slot); it != m_requests.end()) {
+        318 |             Cancel(it->second);
   388   319 |         }
-  389       |         Cancel(m_requests[slot]);
-  390       |         auto* event = EventFor(slot);
-  391       |         if (!event) {
-  392       |             IPC::ResponseBuilder rb{ctx, 2};
-  393       |             rb.Push(Kernel::ResultOutOfResource.raw);
-  394       |             return;
+        320 |         // nn::syncpt::sdk's cancel always waits on the slot's event after this reply, so a cancel
+        321 |         // signals it like a completion, also when nothing was pending; the client rechecks the
+        322 |         // counter (TIPC 103) itself. Title 1 hung forever there when the GPU thread ran a frame
+        323 |         // behind (EDEN_NX2_FRAMES_AHEAD) and a mid-frame wait outlasted NvOsEventPool's 100 ms,
+        324 |         // and its movie player cancels each slot before its first request: signalled only for
+        325 |         // pending requests, the player never got to start a movie.
+        326 |         auto*& event = m_events[slot];
+        327 |         if (event == nullptr) {
+        328 |             event = m_context.CreateEvent(fmt::format("nx2:syncpt:Slot{:x}", slot));
   395   329 |         }
   396   330 |         event->Signal(system.Kernel());
-  397       |         NativeTipcReplyWords(ctx, {});
+        331 |         TipcReplyWords(ctx, {});
   398   332 |     }
```

</details>


<details>
<summary>EglantinePS5 — 298–316 : 6 alignées, 11 propres Encore, 13 propres upstream</summary>

Source : [nx2_gsv.h:298–316](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L298-L316). Numéros exacts dans chaque commit.

```diff
   382   298 |     void CancelSlotEvent(HLERequestContext& ctx) {
   383   299 |         const u32 slot = ctx.CommandBuffer()[2];
-  384       |         if (slot >= m_configured_slots) {
-  385       |             IPC::ResponseBuilder rb{ctx, 2};
-  386       |             rb.Push(Kernel::ResultInvalidArgument.raw);
-  387       |             return;
+        300 |         LOG_DEBUG(Service, "nx2:syncpt TIPC 202 slot={:#x}", slot);
+        301 |         if (auto it = m_requests.find(slot); it != m_requests.end()) {
+        302 |             Cancel(it->second);
   388   303 |         }
-  389       |         Cancel(m_requests[slot]);
-  390       |         auto* event = EventFor(slot);
-  391       |         if (!event) {
-  392       |             IPC::ResponseBuilder rb{ctx, 2};
-  393       |             rb.Push(Kernel::ResultOutOfResource.raw);
-  394       |             return;
+        304 |         // nn::syncpt::sdk's cancel always waits on the slot's event after this reply, so a cancel
+        305 |         // signals it like a completion, also when nothing was pending; the client rechecks the
+        306 |         // counter (TIPC 103) itself. Title 1 hung forever there when the GPU thread ran a frame
+        307 |         // behind (EDEN_NX2_FRAMES_AHEAD) and a mid-frame wait outlasted NvOsEventPool's 100 ms,
+        308 |         // and its movie player cancels each slot before its first request: signalled only for
+        309 |         // pending requests, the player never got to start a movie.
+        310 |         auto*& event = m_events[slot];
+        311 |         if (event == nullptr) {
+        312 |             event = m_context.CreateEvent(fmt::format("nx2:syncpt:Slot{:x}", slot));
   395   313 |         }
   396   314 |         event->Signal(system.Kernel());
-  397       |         NativeTipcReplyWords(ctx, {});
+        315 |         TipcReplyWords(ctx, {});
   398   316 |     }
```

</details>

### P0-07 · NVDRV — GPFIFO admission et completion

Lichii capture les mots de pushbuffer au submit avec gestion des mappings en attente. Encore lit les mots live avec validation GMMU et cohérence. Écart avéré, pas preuve de la panne actuelle. Un snapshot aveugle casserait les listes produites par le GPU. Le count natif 0x100 utilise un WFI conditionnel côté Encore, Lichii utilise BuildIncrementCountCommandList. Vérifier retirement et cohérence du marqueur sans anticiper les fences.

Encore : [nvhost_gpu.cpp:977–1241](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp#L977-L1241) (265 lignes).


<details>
<summary>Lichii — 450–606 : 44 alignées, 221 propres Encore, 113 propres upstream</summary>

Source : [nvhost_gpu.cpp:450–606](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_gpu.cpp#L450-L606). Numéros exacts dans chaque commit.

```diff
-  977       | NvResult nvhost_gpu::SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries, DeviceFD fd) {
+        450 | NvResult nvhost_gpu::SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries) {
   978   451 |     LOG_TRACE(Service_NVDRV, "called, gpfifo={:X}, num_entries={:X}, flags={:X}", params.address,
   979   452 |               params.num_entries, params.flags.raw);
   980   453 | 
   981   454 |     auto& gpu = system.GPU();
   982   455 | 
-  983       |     std::scoped_lock lock(channel_mutex);
+        456 |     std::unique_lock lock(channel_mutex);
   984   457 | 
-  985       |     // Reject malformed native submits BEFORE InitChannel, GPU channel
-  986       |     // registry mutations or syncpoint reservations. Invalid guest flags
-  987       |     // used to initialise a channel and bind an owner despite returning
-  988       |     // BadParameter later. Maxwell/NS1 retains its original admission.
-  989       |     const bool native = UsesNativeAbi(fd);
-  990       |     auto& flags = params.flags;
-  991       | #ifdef PS5_NATIVE
-  992       |     unsigned impl_trace_ticket{};
-  993       |     const bool trace_impl = NextDetailedGpfifoTrace(g_gpfifo_impl_trace, impl_trace_ticket);
-  994       |     if (trace_impl)
-  995       |         std::fprintf(stderr,
-  996       |                      "EDEN_NS2_GPFIFO_IMPL ticket=%u stage=enter native=%u initialized=%u gmmu=%u entries=%u flags=%08x fence_id=%u fence_value=%u\n",
-  997       |                      impl_trace_ticket, static_cast<unsigned>(native),
-  998       |                      static_cast<unsigned>(channel_state->initialized),
-  999       |                      static_cast<unsigned>(channel_state->memory_manager != nullptr),
- 1000       |                      static_cast<unsigned>(params.num_entries),
- 1001       |                      static_cast<unsigned>(flags.raw),
- 1002       |                      static_cast<unsigned>(params.fence.id),
- 1003       |                      static_cast<unsigned>(params.fence.value));
- 1004       | #endif
- 1005       |     const auto native_plan = native
- 1006       |         ? PlanNativeSubmission(static_cast<u32>(flags.raw),
- 1007       |                                static_cast<u32>(params.fence.value), true)
- 1008       |         : std::optional<NativeSubmissionPlan>{};
- 1009       |     if (native && !native_plan) {
- 1010       | #ifdef PS5_NATIVE
- 1011       |         if (trace_impl)
- 1012       |             std::fprintf(stderr,
- 1013       |                          "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=native-plan flags=%08x fence_value=%u\n",
- 1014       |                          impl_trace_ticket, static_cast<unsigned>(flags.raw),
- 1015       |                          static_cast<unsigned>(params.fence.value));
- 1016       | #endif
- 1017       |         return NvResult::BadParameter;
+        458 |     // Lazily initialize channel when address space is available
+        459 |     if (!channel_state->initialized && channel_state->memory_manager) {
+        460 |         system.GPU().InitChannel(*channel_state, channel_state->program_id);
  1018   461 |     }
  1019   462 | 
- 1020       |     // A native GPU device may expose multiple FDs. A rejected or foreign
- 1021       |     // process must not cause InitChannel on another guest's address space.
- 1022       |     const Kernel::KProcess* native_owner = nullptr;
- 1023       |     std::shared_ptr<const std::atomic_bool> native_submission_lease;
- 1024       |     if (native) {
- 1025       |         const auto it = sessions.find(fd);
- 1026       |         const auto* owner = it == sessions.end() ? nullptr : core.GetSession(it->second);
- 1027       |         if (!owner || !owner->process) {
- 1028       | #ifdef PS5_NATIVE
- 1029       |             if (trace_impl)
- 1030       |                 std::fprintf(stderr,
- 1031       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=owner-session\n",
- 1032       |                              impl_trace_ticket);
- 1033       | #endif
- 1034       |             return NvResult::InvalidState;
- 1035       |         }
- 1036       |         native_owner = owner->process;
- 1037       |         // BindChannel is the sole publisher of this type-erased AS lease.
- 1038       |         // A surviving scheduler lease must not revive a revoked GSV VM.
- 1039       |         const auto as_owner = std::static_pointer_cast<nvhost_as_gpu>(
- 1040       |             channel_state->address_space_owner);
- 1041       |         if (!NativeEpochCurrent(fd) || !as_owner)
- 1042       |             return NvResult::InvalidState;
- 1043       |         native_submission_lease = as_owner->CaptureNativeSubmissionLease();
- 1044       |         if (!native_submission_lease)
- 1045       |             return NvResult::InvalidState;
- 1046       |         if (!native_channel_enabled) {
- 1047       | #ifdef PS5_NATIVE
- 1048       |             if (trace_impl)
- 1049       |                 std::fprintf(stderr,
- 1050       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-disabled\n",
- 1051       |                              impl_trace_ticket);
- 1052       | #endif
- 1053       |             return NvResult::InvalidState;
- 1054       |         }
- 1055       |         // An ENABLE/TSG ENABLE ioctl changes scheduling state only; it must
- 1056       |         // never bypass the GPFIFO setup contract or create a channel on an
- 1057       |         // unallocated ring at first submission.
- 1058       |         if (!native_gpfifo_configured)
- 1059       |             return NvResult::InvalidState;
- 1060       |         for (const auto& [other_fd, session_id] : sessions) {
- 1061       |             const auto* opened = core.GetSession(session_id);
- 1062       |             if (!opened || opened->process != native_owner) {
- 1063       | #ifdef PS5_NATIVE
- 1064       |                 if (trace_impl)
- 1065       |                     std::fprintf(stderr,
- 1066       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=mixed-owner\n",
- 1067       |                                  impl_trace_ticket);
- 1068       | #endif
- 1069       |                 return NvResult::InvalidState;
- 1070       |             }
- 1071       |         }
- 1072       |     }
+        463 |     const auto bind_id = channel_state->bind_id;
  1073   464 | 
- 1074       |     // Capture the exact source reservation before any channel mutation,
- 1075       |     // rather than asking the legacy cached min/max fence predicate twice.
- 1076       |     // The wait belongs to the command list and will be polled by the
- 1077       |     // existing native channel scheduler before executing its first word.
- 1078       |     if (native && flags.fence_wait.Value()) {
- 1079       |         try {
- 1080       |             auto lease = syncpoint_manager.CaptureNativeSyncpointLease(
- 1081       |                 static_cast<u32>(params.fence.id));
- 1082       |             if (!lease) {
- 1083       | #ifdef PS5_NATIVE
- 1084       |                 if (trace_impl)
- 1085       |                     std::fprintf(stderr,
- 1086       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=invalid-native-wait fence_id=%u fence_value=%u\n",
- 1087       |                                  impl_trace_ticket, static_cast<unsigned>(params.fence.id),
- 1088       |                                  static_cast<unsigned>(params.fence.value));
- 1089       | #endif
- 1090       |                 return NvResult::BadParameter;
- 1091       |             }
- 1092       |             entries.native_syncpoint_wait.emplace(Tegra::NativeSyncpointWait{
- 1093       |                 static_cast<u32>(params.fence.id), static_cast<u32>(params.fence.value),
- 1094       |                 std::move(lease)});
- 1095       |         } catch (const std::bad_alloc&) {
- 1096       |             return NvResult::InsufficientMemory;
- 1097       |         }
+        465 |     if (g_nx2_driver) {
+        466 |         for ([[maybe_unused]] const auto& entry : entries.command_lists) {
+        467 |             LOG_TRACE(Service_NVDRV, "nx2 GPFIFO entry raw={:#018x} addr={:#x} size={:#x}", entry.raw,
+        468 |                      entry.addr.Value(), entry.size.Value());
  1098   469 |     }
- 1099       | 
- 1100       |     // P2.7: every native GPFIFO entry must refer to a fully mapped GMMU
- 1101       |     // command span BEFORE InitChannel, owner binding or fence reservation.
- 1102       |     // A valid guest ioctl pointer only proves that the *list of headers*
- 1103       |     // was readable, not the GPU virtual addresses inside its entries.
- 1104       |     // Otherwise an unmapped command buffer can be read back as zero words
- 1105       |     // and falsely acknowledged as work submitted. Maxwell retains its
- 1106       |     // original command admission; the native mapper is synchronous here.
- 1107       |     if (native && channel_state->memory_manager) {
- 1108       |         for (const auto& command : entries.command_lists) {
- 1109       |             if (command.size == 0) continue;
- 1110       |             const u64 address = command.addr;
- 1111       |             const u64 bytes = static_cast<u64>(command.size) * sizeof(Tegra::CommandHeader);
- 1112       |             if (!channel_state->memory_manager->IsFullyMappedRange(address, bytes)) {
- 1113       |                 LOG_ERROR(Service_NVDRV,
- 1114       |                           "Native GPFIFO rejected unmapped command span address={:#x} bytes={:#x}",
- 1115       |                           address, bytes);
- 1116       | #ifdef PS5_NATIVE
- 1117       |                 if (trace_impl)
- 1118       |                     std::fprintf(stderr,
- 1119       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=unmapped-command address=%016llx bytes=%llu\n",
- 1120       |                                  impl_trace_ticket, static_cast<unsigned long long>(address),
- 1121       |                                  static_cast<unsigned long long>(bytes));
- 1122       | #endif
- 1123       |                 return NvResult::InvalidSize;
+        470 |         static const bool check = std::getenv("EDEN_NX2_PB_CHECK") != nullptr;
+        471 |         if (check) {
+        472 |             std::vector<u32> words;
+        473 |             for (const auto& entry : entries.command_lists) {
+        474 |                 words.resize(entry.size);
+        475 |                 system.ApplicationMemory().ReadBlock(entry.addr.Value(), words.data(),
+        476 |                                                      words.size() * sizeof(u32));
+        477 |                 entries.submit_hashes.push_back(Tegra::HashPushbufferWords(words));
  1124   478 |             }
  1125   479 |         }
+        480 |         // The present returns before the GPU thread reaches this frame's work (nx2_gsv.h,
+        481 |         // frames ahead), and Mario Kart World then refills command memory it already
+        482 |         // submitted: the end of a frame ran with the next frame's present image as its render
+        483 |         // target, leaving an image three frames old to be shown. Keep the words as submitted.
+        484 |         // EDEN_NX2_PB_SNAPSHOT=0: execute from memory.
+        485 |         static const bool snapshot = [] {
+        486 |             const char* value = std::getenv("EDEN_NX2_PB_SNAPSHOT");
+        487 |             return value == nullptr || value[0] != '0';
+        488 |         }();
+        489 |         if (snapshot && channel_state->memory_manager && channel_state->payload) {
+        490 |             // Before the copy: a suspension during it must count as one after it.
+        491 |             entries.snapshot_suspensions =
+        492 |                 channel_state->payload->dma_pusher.suspensions.load(std::memory_order_acquire);
+        493 |             size_t words = 0;
+        494 |             for (const auto& entry : entries.command_lists) {
+        495 |                 words += entry.size;
  1126   496 |     }
- 1127       | 
- 1128       |     // Lazily initialize channel when address space is available
- 1129       |     if (!channel_state->initialized && channel_state->memory_manager) {
- 1130       |         system.GPU().InitChannel(*channel_state, channel_state->program_id);
+        497 |             entries.submitted_words.resize(words);
+        498 |             entries.submitted_offsets.reserve(entries.command_lists.size());
+        499 |             size_t offset = 0;
+        500 |             for (u32 i = 0; i < entries.command_lists.size(); ++i) {
+        501 |                 const auto& entry = entries.command_lists[i];
+        502 |                 entries.submitted_offsets.push_back(static_cast<u32>(offset));
+        503 |                 // GMMU maps run on the GPU thread (GPU::MapInOrder): an entry on addresses a
+        504 |                 // queued map changes would copy as zeros (Pokopia's first lists). DmaPusher::Push
+        505 |                 // copies it after the map instead.
+        506 |                 const u64 bytes = static_cast<u64>(entry.size) * sizeof(u32);
+        507 |                 if (system.GPU().IsMapPending(entry.addr, bytes)) {
+        508 |                     entries.deferred_entries.push_back(i);
+        509 |                 } else {
+        510 |                     channel_state->memory_manager->ReadBlockUnsafe(
+        511 |                         entry.addr, entries.submitted_words.data() + offset,
+        512 |                         entry.size * sizeof(u32));
  1131   513 |     }
- 1132       | 
- 1133       |     // A real native GPU channel requires a bound GMMU and initialized
- 1134       |     // command scheduler. Never acknowledge 2nd-gen submissions before those
- 1135       |     // resources exist, and never change the existing Switch 1 path.
- 1136       | #ifdef PS5_NATIVE
- 1137       |     // Capture the actual NVDRV -> GPFIFO boundary, including cases where a
- 1138       |     // guest submission is incorrectly treated as legacy. Bounded: quiet in
- 1139       |     // the rest of gameplay, and never prints guest memory contents.
- 1140       |     static std::atomic<unsigned> submissions{0};
- 1141       |     const auto n = submissions.fetch_add(1, std::memory_order_relaxed) + 1;
- 1142       |     if (n <= 24 || (n & (n - 1)) == 0)
- 1143       |         std::fprintf(stderr,
- 1144       |                      "EDEN_NS2_GPFIFO submit=%u native=%u initialized=%u gmmu=%u entries=%u flags=%08x\n",
- 1145       |                      n, static_cast<unsigned>(native),
- 1146       |                      static_cast<unsigned>(channel_state->initialized),
- 1147       |                      static_cast<unsigned>(channel_state->memory_manager != nullptr),
- 1148       |                      static_cast<unsigned>(params.num_entries),
- 1149       |                      static_cast<unsigned>(params.flags.raw));
- 1150       | #endif
- 1151       |     if (native && (!channel_state->initialized || !channel_state->memory_manager)) {
- 1152       | #ifdef PS5_NATIVE
- 1153       |         if (trace_impl)
- 1154       |             std::fprintf(stderr,
- 1155       |                          "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-not-ready initialized=%u gmmu=%u\n",
- 1156       |                          impl_trace_ticket, static_cast<unsigned>(channel_state->initialized),
- 1157       |                          static_cast<unsigned>(channel_state->memory_manager != nullptr));
- 1158       | #endif
- 1159       |         return NvResult::InvalidState;
+        514 |                 offset += entry.size;
  1160   515 |     }
- 1161       |     // Bind only a validated process, after the channel has a real GMMU
- 1162       |     // and the complete native fence plan has already passed admission.
- 1163       |     // Only an authenticated Switch 2 channel may switch its address-space
- 1164       |     // texture layout. NS1 never enters this branch and keeps Maxwell tiling.
- 1165       |     if (native) {
- 1166       |         auto& native_channel_registry = NativeGpuChannelRegistry::Instance();
- 1167       |         if (!native_channel_registry.Bind(
- 1168       |                 channel_state.get(), native_owner)) {
- 1169       | #ifdef PS5_NATIVE
- 1170       |             if (trace_impl)
- 1171       |                 std::fprintf(stderr,
- 1172       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-bind\n",
- 1173       |                              impl_trace_ticket);
- 1174       | #endif
- 1175       |             return NvResult::InvalidState;
  1176   516 |         }
- 1177       |         if (!native_channel_registry.AttachFaultNotifier(
- 1178       |                 channel_state.get(), this, &nvhost_gpu::SignalNativeChannelFault))
- 1179       |             return NvResult::InvalidState;
- 1180       |         channel_state->memory_manager->EnableNativeTiling();
  1181   517 |     }
  1182   518 | 
- 1183       |     const auto bind_id = channel_state->bind_id;
- 1184       |     const u32 native_completion = native_plan ? native_plan->completion_count : 0;
- 1185       |     const auto push_gpu_entries = [&](Tegra::CommandList&& list) {
- 1186       |         if (native)
- 1187       |             list.native_submission_lease = native_submission_lease;
- 1188       |         gpu.PushGPUEntries(bind_id, std::move(list));
- 1189       |     };
+        519 |     auto& flags = params.flags;
  1190   520 | 
- 1191       |     // The native wait is attached to entries, not a legacy FENCE_ACTION
- 1192       |     // packet. This leaves the historical Maxwell submission path intact.
- 1193       |     if (!native && flags.fence_wait.Value()) {
+        521 |     if (flags.fence_wait.Value()) {
  1194   522 |         if (flags.increment_value.Value()) {
  1195   523 |             return NvResult::BadParameter;
  1196   524 |         }
  1197   525 | 
  1198   526 |         if (!syncpoint_manager.IsFenceSignalled(params.fence)) {
- 1199       |             push_gpu_entries(Tegra::CommandList{BuildWaitCommandList(params.fence)});
+        527 |             gpu.PushGPUEntries(bind_id, Tegra::CommandList{BuildWaitCommandList(params.fence)});
  1200   528 |         }
  1201   529 |     }
  1202   530 | 
  1203   531 |     params.fence.id = channel_syncpoint;
  1204   532 | 
- 1205       |     // Use the SAME reviewed native envelope that determined how many
- 1206       |     // completion commands the GPU queue will issue. Never reserve a fence
- 1207       |     // using a second, independently computed native increment count.
- 1208       |     const u32 increment = native
- 1209       |         ? native_plan->increment_total
- 1210       |         : (flags.fence_increment.Value() != 0 ? 2U : 0U) +
- 1211       |           (flags.increment_value.Value() != 0 ? u32{params.fence.value} : 0U);
+        533 |     u32 increment{(flags.fence_increment.Value() != 0 ? 2 : 0) +
+        534 |                   (flags.increment_value.Value() != 0 ? params.fence.value : 0)};
  1212   535 |     params.fence.value = syncpoint_manager.IncrementSyncpointMaxExt(channel_syncpoint, increment);
- 1213       |     push_gpu_entries(std::move(entries));
+        536 |     gpu.PushGPUEntries(bind_id, std::move(entries));
  1214   537 | 
+        538 |     if (g_nx2_driver && !flags.fence_increment.Value() && increment > 0) {
+        539 |         gpu.PushGPUEntries(bind_id,
+        540 |                            Tegra::CommandList{BuildIncrementCountCommandList(params.fence, increment)});
+        541 |     }
+        542 | 
  1215   543 |     if (flags.fence_increment.Value()) {
  1216   544 |         if (flags.suppress_wfi.Value()) {
- 1217       |             push_gpu_entries(
+        545 |             gpu.PushGPUEntries(bind_id,
  1218   546 |                 Tegra::CommandList{BuildIncrementCommandList(params.fence)});
  1219   547 |         } else {
- 1220       |             push_gpu_entries(
+        548 |             gpu.PushGPUEntries(bind_id,
  1221   549 |                 Tegra::CommandList{BuildIncrementWithWfiCommandList(params.fence)});
  1222   550 |         }
  1223   551 |     }
  1224   552 | 
- 1225       |     // The completed pushbuffer precedes its counter increment on the same
- 1226       |     // ordered GPU queue. Do not signal before work has been submitted.
- 1227       |     if (native_completion != 0) {
- 1228       |         push_gpu_entries(Tegra::CommandList{
- 1229       |             flags.suppress_wfi.Value()
- 1230       |                 ? BuildIncrementCommandList(params.fence, native_completion)
- 1231       |                 : BuildIncrementWithWfiCommandList(params.fence, native_completion)});
+        553 |     if (g_nx2_driver) {
+        554 |         LOG_TRACE(Service_NVDRV,
+        555 |                  "nx2 SubmitGPFIFO entries={} flags={:#x} fence_out=({}, {}) guest_value={}",
+        556 |                  params.num_entries, flags.raw, params.fence.id, params.fence.value,
+        557 |                  system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(params.fence.id));
  1232   558 |     }
- 1233       | 
- 1234       |     // Switch's submit struct defines flags as input. Preserve the accepted
- 1235       |     // value on native Ioctl2 H:0x1B replies; OunceVK verifies it byte-for-byte.
- 1236       |     // Maxwell/NS1 keeps Eden's historical zero-on-return behaviour.
- 1237       |     if (!native)
  1238   559 |         flags.raw = 0;
  1239   560 | 
+        561 |     static const bool sync_submit = [] {
+        562 |         const char* value = std::getenv("EDEN_NX2_SYNC_SUBMIT");
+        563 |         return value != nullptr && value[0] != '0';
+        564 |     }();
+        565 |     if (g_nx2_driver && sync_submit && increment > 0) {
+        566 |         lock.unlock();
+        567 |         auto& syncpoints = system.Host1x().GetSyncpointManager();
+        568 |         if (!syncpoints.IsReadyGuest(params.fence.id, params.fence.value)) {
+        569 |             struct Wake {
+        570 |                 std::mutex mutex;
+        571 |                 std::condition_variable cv;
+        572 |                 bool done{};
+        573 |             };
+        574 |             auto wake = std::make_shared<Wake>();
+        575 |             syncpoints.RegisterGuestAction(params.fence.id, params.fence.value, [wake] {
+        576 |                 {
+        577 |                     std::scoped_lock lk{wake->mutex};
+        578 |                     wake->done = true;
+        579 |                 }
+        580 |                 wake->cv.notify_all();
+        581 |             });
+        582 |             const auto deadline =
+        583 |                 std::chrono::steady_clock::now() + std::chrono::milliseconds{2000};
+        584 |             std::unique_lock lk{wake->mutex};
+        585 |             while (!wake->done && system.IsPoweredOn()) {
+        586 |                 const auto now = std::chrono::steady_clock::now();
+        587 |                 if (now >= deadline) {
+        588 |                     break;
+        589 |                 }
+        590 |                 wake->cv.wait_for(
+        591 |                     lk, std::min(std::chrono::duration_cast<std::chrono::milliseconds>(deadline - now),
+        592 |                                  std::chrono::milliseconds{50}));
+        593 |             }
+        594 |         }
+        595 |         static std::atomic<u32> timeouts{};
+        596 |         if (!syncpoints.IsReadyGuest(params.fence.id, params.fence.value) &&
+        597 |             (timeouts.fetch_add(1, std::memory_order_relaxed) % 64) == 0) {
+        598 |             LOG_WARNING(Service_NVDRV,
+        599 |                         "nx2 sync submit timed out waiting for fence ({}, {}), current value={}",
+        600 |                         params.fence.id, params.fence.value,
+        601 |                         syncpoints.GetGuestSyncpointValue(params.fence.id));
+        602 |         }
+        603 |     }
+        604 | 
  1240   605 |     return NvResult::Success;
  1241   606 | }
```

</details>


<details>
<summary>EglantinePS5 — 413–569 : 44 alignées, 221 propres Encore, 113 propres upstream</summary>

Source : [nvhost_gpu.cpp:413–569](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_gpu.cpp#L413-L569). Numéros exacts dans chaque commit.

```diff
-  977       | NvResult nvhost_gpu::SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries, DeviceFD fd) {
+        413 | NvResult nvhost_gpu::SubmitGPFIFOImpl(IoctlSubmitGpfifo& params, Tegra::CommandList&& entries) {
   978   414 |     LOG_TRACE(Service_NVDRV, "called, gpfifo={:X}, num_entries={:X}, flags={:X}", params.address,
   979   415 |               params.num_entries, params.flags.raw);
   980   416 | 
   981   417 |     auto& gpu = system.GPU();
   982   418 | 
-  983       |     std::scoped_lock lock(channel_mutex);
+        419 |     std::unique_lock lock(channel_mutex);
   984   420 | 
-  985       |     // Reject malformed native submits BEFORE InitChannel, GPU channel
-  986       |     // registry mutations or syncpoint reservations. Invalid guest flags
-  987       |     // used to initialise a channel and bind an owner despite returning
-  988       |     // BadParameter later. Maxwell/NS1 retains its original admission.
-  989       |     const bool native = UsesNativeAbi(fd);
-  990       |     auto& flags = params.flags;
-  991       | #ifdef PS5_NATIVE
-  992       |     unsigned impl_trace_ticket{};
-  993       |     const bool trace_impl = NextDetailedGpfifoTrace(g_gpfifo_impl_trace, impl_trace_ticket);
-  994       |     if (trace_impl)
-  995       |         std::fprintf(stderr,
-  996       |                      "EDEN_NS2_GPFIFO_IMPL ticket=%u stage=enter native=%u initialized=%u gmmu=%u entries=%u flags=%08x fence_id=%u fence_value=%u\n",
-  997       |                      impl_trace_ticket, static_cast<unsigned>(native),
-  998       |                      static_cast<unsigned>(channel_state->initialized),
-  999       |                      static_cast<unsigned>(channel_state->memory_manager != nullptr),
- 1000       |                      static_cast<unsigned>(params.num_entries),
- 1001       |                      static_cast<unsigned>(flags.raw),
- 1002       |                      static_cast<unsigned>(params.fence.id),
- 1003       |                      static_cast<unsigned>(params.fence.value));
- 1004       | #endif
- 1005       |     const auto native_plan = native
- 1006       |         ? PlanNativeSubmission(static_cast<u32>(flags.raw),
- 1007       |                                static_cast<u32>(params.fence.value), true)
- 1008       |         : std::optional<NativeSubmissionPlan>{};
- 1009       |     if (native && !native_plan) {
- 1010       | #ifdef PS5_NATIVE
- 1011       |         if (trace_impl)
- 1012       |             std::fprintf(stderr,
- 1013       |                          "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=native-plan flags=%08x fence_value=%u\n",
- 1014       |                          impl_trace_ticket, static_cast<unsigned>(flags.raw),
- 1015       |                          static_cast<unsigned>(params.fence.value));
- 1016       | #endif
- 1017       |         return NvResult::BadParameter;
+        421 |     // Lazily initialize channel when address space is available
+        422 |     if (!channel_state->initialized && channel_state->memory_manager) {
+        423 |         system.GPU().InitChannel(*channel_state, channel_state->program_id);
  1018   424 |     }
  1019   425 | 
- 1020       |     // A native GPU device may expose multiple FDs. A rejected or foreign
- 1021       |     // process must not cause InitChannel on another guest's address space.
- 1022       |     const Kernel::KProcess* native_owner = nullptr;
- 1023       |     std::shared_ptr<const std::atomic_bool> native_submission_lease;
- 1024       |     if (native) {
- 1025       |         const auto it = sessions.find(fd);
- 1026       |         const auto* owner = it == sessions.end() ? nullptr : core.GetSession(it->second);
- 1027       |         if (!owner || !owner->process) {
- 1028       | #ifdef PS5_NATIVE
- 1029       |             if (trace_impl)
- 1030       |                 std::fprintf(stderr,
- 1031       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=owner-session\n",
- 1032       |                              impl_trace_ticket);
- 1033       | #endif
- 1034       |             return NvResult::InvalidState;
- 1035       |         }
- 1036       |         native_owner = owner->process;
- 1037       |         // BindChannel is the sole publisher of this type-erased AS lease.
- 1038       |         // A surviving scheduler lease must not revive a revoked GSV VM.
- 1039       |         const auto as_owner = std::static_pointer_cast<nvhost_as_gpu>(
- 1040       |             channel_state->address_space_owner);
- 1041       |         if (!NativeEpochCurrent(fd) || !as_owner)
- 1042       |             return NvResult::InvalidState;
- 1043       |         native_submission_lease = as_owner->CaptureNativeSubmissionLease();
- 1044       |         if (!native_submission_lease)
- 1045       |             return NvResult::InvalidState;
- 1046       |         if (!native_channel_enabled) {
- 1047       | #ifdef PS5_NATIVE
- 1048       |             if (trace_impl)
- 1049       |                 std::fprintf(stderr,
- 1050       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-disabled\n",
- 1051       |                              impl_trace_ticket);
- 1052       | #endif
- 1053       |             return NvResult::InvalidState;
- 1054       |         }
- 1055       |         // An ENABLE/TSG ENABLE ioctl changes scheduling state only; it must
- 1056       |         // never bypass the GPFIFO setup contract or create a channel on an
- 1057       |         // unallocated ring at first submission.
- 1058       |         if (!native_gpfifo_configured)
- 1059       |             return NvResult::InvalidState;
- 1060       |         for (const auto& [other_fd, session_id] : sessions) {
- 1061       |             const auto* opened = core.GetSession(session_id);
- 1062       |             if (!opened || opened->process != native_owner) {
- 1063       | #ifdef PS5_NATIVE
- 1064       |                 if (trace_impl)
- 1065       |                     std::fprintf(stderr,
- 1066       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=mixed-owner\n",
- 1067       |                                  impl_trace_ticket);
- 1068       | #endif
- 1069       |                 return NvResult::InvalidState;
- 1070       |             }
- 1071       |         }
- 1072       |     }
+        426 |     const auto bind_id = channel_state->bind_id;
  1073   427 | 
- 1074       |     // Capture the exact source reservation before any channel mutation,
- 1075       |     // rather than asking the legacy cached min/max fence predicate twice.
- 1076       |     // The wait belongs to the command list and will be polled by the
- 1077       |     // existing native channel scheduler before executing its first word.
- 1078       |     if (native && flags.fence_wait.Value()) {
- 1079       |         try {
- 1080       |             auto lease = syncpoint_manager.CaptureNativeSyncpointLease(
- 1081       |                 static_cast<u32>(params.fence.id));
- 1082       |             if (!lease) {
- 1083       | #ifdef PS5_NATIVE
- 1084       |                 if (trace_impl)
- 1085       |                     std::fprintf(stderr,
- 1086       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=invalid-native-wait fence_id=%u fence_value=%u\n",
- 1087       |                                  impl_trace_ticket, static_cast<unsigned>(params.fence.id),
- 1088       |                                  static_cast<unsigned>(params.fence.value));
- 1089       | #endif
- 1090       |                 return NvResult::BadParameter;
- 1091       |             }
- 1092       |             entries.native_syncpoint_wait.emplace(Tegra::NativeSyncpointWait{
- 1093       |                 static_cast<u32>(params.fence.id), static_cast<u32>(params.fence.value),
- 1094       |                 std::move(lease)});
- 1095       |         } catch (const std::bad_alloc&) {
- 1096       |             return NvResult::InsufficientMemory;
- 1097       |         }
+        428 |     if (g_nx2_driver) {
+        429 |         for ([[maybe_unused]] const auto& entry : entries.command_lists) {
+        430 |             LOG_TRACE(Service_NVDRV, "nx2 GPFIFO entry raw={:#018x} addr={:#x} size={:#x}", entry.raw,
+        431 |                      entry.addr.Value(), entry.size.Value());
  1098   432 |     }
- 1099       | 
- 1100       |     // P2.7: every native GPFIFO entry must refer to a fully mapped GMMU
- 1101       |     // command span BEFORE InitChannel, owner binding or fence reservation.
- 1102       |     // A valid guest ioctl pointer only proves that the *list of headers*
- 1103       |     // was readable, not the GPU virtual addresses inside its entries.
- 1104       |     // Otherwise an unmapped command buffer can be read back as zero words
- 1105       |     // and falsely acknowledged as work submitted. Maxwell retains its
- 1106       |     // original command admission; the native mapper is synchronous here.
- 1107       |     if (native && channel_state->memory_manager) {
- 1108       |         for (const auto& command : entries.command_lists) {
- 1109       |             if (command.size == 0) continue;
- 1110       |             const u64 address = command.addr;
- 1111       |             const u64 bytes = static_cast<u64>(command.size) * sizeof(Tegra::CommandHeader);
- 1112       |             if (!channel_state->memory_manager->IsFullyMappedRange(address, bytes)) {
- 1113       |                 LOG_ERROR(Service_NVDRV,
- 1114       |                           "Native GPFIFO rejected unmapped command span address={:#x} bytes={:#x}",
- 1115       |                           address, bytes);
- 1116       | #ifdef PS5_NATIVE
- 1117       |                 if (trace_impl)
- 1118       |                     std::fprintf(stderr,
- 1119       |                                  "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=unmapped-command address=%016llx bytes=%llu\n",
- 1120       |                                  impl_trace_ticket, static_cast<unsigned long long>(address),
- 1121       |                                  static_cast<unsigned long long>(bytes));
- 1122       | #endif
- 1123       |                 return NvResult::InvalidSize;
+        433 |         static const bool check = std::getenv("EDEN_NX2_PB_CHECK") != nullptr;
+        434 |         if (check) {
+        435 |             std::vector<u32> words;
+        436 |             for (const auto& entry : entries.command_lists) {
+        437 |                 words.resize(entry.size);
+        438 |                 system.ApplicationMemory().ReadBlock(entry.addr.Value(), words.data(),
+        439 |                                                      words.size() * sizeof(u32));
+        440 |                 entries.submit_hashes.push_back(Tegra::HashPushbufferWords(words));
  1124   441 |             }
  1125   442 |         }
+        443 |         // The present returns before the GPU thread reaches this frame's work (nx2_gsv.h,
+        444 |         // frames ahead), and Mario Kart World then refills command memory it already
+        445 |         // submitted: the end of a frame ran with the next frame's present image as its render
+        446 |         // target, leaving an image three frames old to be shown. Keep the words as submitted.
+        447 |         // EDEN_NX2_PB_SNAPSHOT=0: execute from memory.
+        448 |         static const bool snapshot = [] {
+        449 |             const char* value = std::getenv("EDEN_NX2_PB_SNAPSHOT");
+        450 |             return value == nullptr || value[0] != '0';
+        451 |         }();
+        452 |         if (snapshot && channel_state->memory_manager && channel_state->payload) {
+        453 |             // Before the copy: a suspension during it must count as one after it.
+        454 |             entries.snapshot_suspensions =
+        455 |                 channel_state->payload->dma_pusher.suspensions.load(std::memory_order_acquire);
+        456 |             size_t words = 0;
+        457 |             for (const auto& entry : entries.command_lists) {
+        458 |                 words += entry.size;
  1126   459 |     }
- 1127       | 
- 1128       |     // Lazily initialize channel when address space is available
- 1129       |     if (!channel_state->initialized && channel_state->memory_manager) {
- 1130       |         system.GPU().InitChannel(*channel_state, channel_state->program_id);
+        460 |             entries.submitted_words.resize(words);
+        461 |             entries.submitted_offsets.reserve(entries.command_lists.size());
+        462 |             size_t offset = 0;
+        463 |             for (u32 i = 0; i < entries.command_lists.size(); ++i) {
+        464 |                 const auto& entry = entries.command_lists[i];
+        465 |                 entries.submitted_offsets.push_back(static_cast<u32>(offset));
+        466 |                 // GMMU maps run on the GPU thread (GPU::MapInOrder): an entry on addresses a
+        467 |                 // queued map changes would copy as zeros (Pokopia's first lists). DmaPusher::Push
+        468 |                 // copies it after the map instead.
+        469 |                 const u64 bytes = static_cast<u64>(entry.size) * sizeof(u32);
+        470 |                 if (system.GPU().IsMapPending(entry.addr, bytes)) {
+        471 |                     entries.deferred_entries.push_back(i);
+        472 |                 } else {
+        473 |                     channel_state->memory_manager->ReadBlockUnsafe(
+        474 |                         entry.addr, entries.submitted_words.data() + offset,
+        475 |                         entry.size * sizeof(u32));
  1131   476 |     }
- 1132       | 
- 1133       |     // A real native GPU channel requires a bound GMMU and initialized
- 1134       |     // command scheduler. Never acknowledge 2nd-gen submissions before those
- 1135       |     // resources exist, and never change the existing Switch 1 path.
- 1136       | #ifdef PS5_NATIVE
- 1137       |     // Capture the actual NVDRV -> GPFIFO boundary, including cases where a
- 1138       |     // guest submission is incorrectly treated as legacy. Bounded: quiet in
- 1139       |     // the rest of gameplay, and never prints guest memory contents.
- 1140       |     static std::atomic<unsigned> submissions{0};
- 1141       |     const auto n = submissions.fetch_add(1, std::memory_order_relaxed) + 1;
- 1142       |     if (n <= 24 || (n & (n - 1)) == 0)
- 1143       |         std::fprintf(stderr,
- 1144       |                      "EDEN_NS2_GPFIFO submit=%u native=%u initialized=%u gmmu=%u entries=%u flags=%08x\n",
- 1145       |                      n, static_cast<unsigned>(native),
- 1146       |                      static_cast<unsigned>(channel_state->initialized),
- 1147       |                      static_cast<unsigned>(channel_state->memory_manager != nullptr),
- 1148       |                      static_cast<unsigned>(params.num_entries),
- 1149       |                      static_cast<unsigned>(params.flags.raw));
- 1150       | #endif
- 1151       |     if (native && (!channel_state->initialized || !channel_state->memory_manager)) {
- 1152       | #ifdef PS5_NATIVE
- 1153       |         if (trace_impl)
- 1154       |             std::fprintf(stderr,
- 1155       |                          "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-not-ready initialized=%u gmmu=%u\n",
- 1156       |                          impl_trace_ticket, static_cast<unsigned>(channel_state->initialized),
- 1157       |                          static_cast<unsigned>(channel_state->memory_manager != nullptr));
- 1158       | #endif
- 1159       |         return NvResult::InvalidState;
+        477 |                 offset += entry.size;
  1160   478 |     }
- 1161       |     // Bind only a validated process, after the channel has a real GMMU
- 1162       |     // and the complete native fence plan has already passed admission.
- 1163       |     // Only an authenticated Switch 2 channel may switch its address-space
- 1164       |     // texture layout. NS1 never enters this branch and keeps Maxwell tiling.
- 1165       |     if (native) {
- 1166       |         auto& native_channel_registry = NativeGpuChannelRegistry::Instance();
- 1167       |         if (!native_channel_registry.Bind(
- 1168       |                 channel_state.get(), native_owner)) {
- 1169       | #ifdef PS5_NATIVE
- 1170       |             if (trace_impl)
- 1171       |                 std::fprintf(stderr,
- 1172       |                              "EDEN_NS2_GPFIFO_REJECT ticket=%u stage=impl reason=channel-bind\n",
- 1173       |                              impl_trace_ticket);
- 1174       | #endif
- 1175       |             return NvResult::InvalidState;
  1176   479 |         }
- 1177       |         if (!native_channel_registry.AttachFaultNotifier(
- 1178       |                 channel_state.get(), this, &nvhost_gpu::SignalNativeChannelFault))
- 1179       |             return NvResult::InvalidState;
- 1180       |         channel_state->memory_manager->EnableNativeTiling();
  1181   480 |     }
  1182   481 | 
- 1183       |     const auto bind_id = channel_state->bind_id;
- 1184       |     const u32 native_completion = native_plan ? native_plan->completion_count : 0;
- 1185       |     const auto push_gpu_entries = [&](Tegra::CommandList&& list) {
- 1186       |         if (native)
- 1187       |             list.native_submission_lease = native_submission_lease;
- 1188       |         gpu.PushGPUEntries(bind_id, std::move(list));
- 1189       |     };
+        482 |     auto& flags = params.flags;
  1190   483 | 
- 1191       |     // The native wait is attached to entries, not a legacy FENCE_ACTION
- 1192       |     // packet. This leaves the historical Maxwell submission path intact.
- 1193       |     if (!native && flags.fence_wait.Value()) {
+        484 |     if (flags.fence_wait.Value()) {
  1194   485 |         if (flags.increment_value.Value()) {
  1195   486 |             return NvResult::BadParameter;
  1196   487 |         }
  1197   488 | 
  1198   489 |         if (!syncpoint_manager.IsFenceSignalled(params.fence)) {
- 1199       |             push_gpu_entries(Tegra::CommandList{BuildWaitCommandList(params.fence)});
+        490 |             gpu.PushGPUEntries(bind_id, Tegra::CommandList{BuildWaitCommandList(params.fence)});
  1200   491 |         }
  1201   492 |     }
  1202   493 | 
  1203   494 |     params.fence.id = channel_syncpoint;
  1204   495 | 
- 1205       |     // Use the SAME reviewed native envelope that determined how many
- 1206       |     // completion commands the GPU queue will issue. Never reserve a fence
- 1207       |     // using a second, independently computed native increment count.
- 1208       |     const u32 increment = native
- 1209       |         ? native_plan->increment_total
- 1210       |         : (flags.fence_increment.Value() != 0 ? 2U : 0U) +
- 1211       |           (flags.increment_value.Value() != 0 ? u32{params.fence.value} : 0U);
+        496 |     u32 increment{(flags.fence_increment.Value() != 0 ? 2 : 0) +
+        497 |                   (flags.increment_value.Value() != 0 ? params.fence.value : 0)};
  1212   498 |     params.fence.value = syncpoint_manager.IncrementSyncpointMaxExt(channel_syncpoint, increment);
- 1213       |     push_gpu_entries(std::move(entries));
+        499 |     gpu.PushGPUEntries(bind_id, std::move(entries));
  1214   500 | 
+        501 |     if (g_nx2_driver && !flags.fence_increment.Value() && increment > 0) {
+        502 |         gpu.PushGPUEntries(bind_id,
+        503 |                            Tegra::CommandList{BuildIncrementCountCommandList(params.fence, increment)});
+        504 |     }
+        505 | 
  1215   506 |     if (flags.fence_increment.Value()) {
  1216   507 |         if (flags.suppress_wfi.Value()) {
- 1217       |             push_gpu_entries(
+        508 |             gpu.PushGPUEntries(bind_id,
  1218   509 |                 Tegra::CommandList{BuildIncrementCommandList(params.fence)});
  1219   510 |         } else {
- 1220       |             push_gpu_entries(
+        511 |             gpu.PushGPUEntries(bind_id,
  1221   512 |                 Tegra::CommandList{BuildIncrementWithWfiCommandList(params.fence)});
  1222   513 |         }
  1223   514 |     }
  1224   515 | 
- 1225       |     // The completed pushbuffer precedes its counter increment on the same
- 1226       |     // ordered GPU queue. Do not signal before work has been submitted.
- 1227       |     if (native_completion != 0) {
- 1228       |         push_gpu_entries(Tegra::CommandList{
- 1229       |             flags.suppress_wfi.Value()
- 1230       |                 ? BuildIncrementCommandList(params.fence, native_completion)
- 1231       |                 : BuildIncrementWithWfiCommandList(params.fence, native_completion)});
+        516 |     if (g_nx2_driver) {
+        517 |         LOG_TRACE(Service_NVDRV,
+        518 |                  "nx2 SubmitGPFIFO entries={} flags={:#x} fence_out=({}, {}) guest_value={}",
+        519 |                  params.num_entries, flags.raw, params.fence.id, params.fence.value,
+        520 |                  system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(params.fence.id));
  1232   521 |     }
- 1233       | 
- 1234       |     // Switch's submit struct defines flags as input. Preserve the accepted
- 1235       |     // value on native Ioctl2 H:0x1B replies; OunceVK verifies it byte-for-byte.
- 1236       |     // Maxwell/NS1 keeps Eden's historical zero-on-return behaviour.
- 1237       |     if (!native)
  1238   522 |         flags.raw = 0;
  1239   523 | 
+        524 |     static const bool sync_submit = [] {
+        525 |         const char* value = std::getenv("EDEN_NX2_SYNC_SUBMIT");
+        526 |         return value != nullptr && value[0] != '0';
+        527 |     }();
+        528 |     if (g_nx2_driver && sync_submit && increment > 0) {
+        529 |         lock.unlock();
+        530 |         auto& syncpoints = system.Host1x().GetSyncpointManager();
+        531 |         if (!syncpoints.IsReadyGuest(params.fence.id, params.fence.value)) {
+        532 |             struct Wake {
+        533 |                 std::mutex mutex;
+        534 |                 std::condition_variable cv;
+        535 |                 bool done{};
+        536 |             };
+        537 |             auto wake = std::make_shared<Wake>();
+        538 |             syncpoints.RegisterGuestAction(params.fence.id, params.fence.value, [wake] {
+        539 |                 {
+        540 |                     std::scoped_lock lk{wake->mutex};
+        541 |                     wake->done = true;
+        542 |                 }
+        543 |                 wake->cv.notify_all();
+        544 |             });
+        545 |             const auto deadline =
+        546 |                 std::chrono::steady_clock::now() + std::chrono::milliseconds{2000};
+        547 |             std::unique_lock lk{wake->mutex};
+        548 |             while (!wake->done && system.IsPoweredOn()) {
+        549 |                 const auto now = std::chrono::steady_clock::now();
+        550 |                 if (now >= deadline) {
+        551 |                     break;
+        552 |                 }
+        553 |                 wake->cv.wait_for(
+        554 |                     lk, std::min(std::chrono::duration_cast<std::chrono::milliseconds>(deadline - now),
+        555 |                                  std::chrono::milliseconds{50}));
+        556 |             }
+        557 |         }
+        558 |         static std::atomic<u32> timeouts{};
+        559 |         if (!syncpoints.IsReadyGuest(params.fence.id, params.fence.value) &&
+        560 |             (timeouts.fetch_add(1, std::memory_order_relaxed) % 64) == 0) {
+        561 |             LOG_WARNING(Service_NVDRV,
+        562 |                         "nx2 sync submit timed out waiting for fence ({}, {}), current value={}",
+        563 |                         params.fence.id, params.fence.value,
+        564 |                         syncpoints.GetGuestSyncpointValue(params.fence.id));
+        565 |         }
+        566 |     }
+        567 | 
  1240   568 |     return NvResult::Success;
  1241   569 | }
```

</details>

### P1-01 · BufferCache — garbage collector

Seuils et batching différents. Encore a déjà reçu un batch de collecte ; les contentions mesurées n'établissent pas que ce GC domine. Comparer durée sous mutex et retire/copy avant d'adopter des seuils upstream.

Encore : [buffer_cache.h:77–231](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h#L77-L231) (155 lignes).


<details>
<summary>Lichii — 80–118 : 9 alignées, 146 propres Encore, 30 propres upstream</summary>

Source : [buffer_cache.h:80–118](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/buffer_cache/buffer_cache.h#L80-L118). Numéros exacts dans chaque commit.

```diff
-   77       | void BufferCache<P>::RunGarbageCollector() {
-   78       |     const bool aggressive_gc = total_used_memory >= critical_memory;
-   79       |     const u64 ticks_to_destroy = aggressive_gc ? 60 : 120;
-   80       | #ifdef PS5_NATIVE
-   81       |     // Before a buffer reaches the GC age, subtracting from this unsigned
-   82       |     // frame tick wraps to a huge LRU threshold. On startup/pressure bursts
-   83       |     // that wrongly evicts young buffers and can force guest downloads.
-   84       |     if (frame_tick < ticks_to_destroy) {
-   85       |         return;
+         80 | void BufferCache<P>::RunGarbageCollector(bool aggressive_gc, u64 idle_frames) {
+         81 |     const StutterTrace::SiteScope site{StutterTrace::Site::BufferCollect};
+         82 |     const u64 ticks_to_destroy = idle_frames != 0 ? idle_frames : aggressive_gc ? 60 : 120;
+         83 |     int num_iterations = aggressive_gc ? 64 : 32;
+         84 |     // Their GPU-written data is downloaded first, all with one wait for the GPU: one wait per
+         85 |     // buffer stalled the GPU thread every frame on title 1 (an 8 GB GPU near its budget, no
+         86 |     // per-fence downloads keeping the buffers clean), ~2.5% of its time.
+         87 |     boost::container::small_vector<BufferId, 64> evicted;
+         88 |     lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, [&](BufferId buffer_id) {
+         89 |         if (num_iterations == 0) {
+         90 |             return true;
    86    91 |     }
-   87       | #endif
-   88       | #ifdef PS5_NATIVE
-   89       |     if constexpr (USE_MEMORY_MAPS && !IS_OPENGL) {
-   90       |         // Lichii batches GC readbacks rather than finishing the GPU once
-   91       |         // per dirty eviction. Keep the existing LRU age and eviction count.
-   92       |         constexpr u64 staging_budget = 16ULL * 1024 * 1024;
-   93       |         constexpr size_t max_regions = 4096;
-   94       |         std::array<BufferId, 64> candidates{};
-   95       |         size_t candidate_count = 0;
-   96       |         const size_t limit = aggressive_gc ? 64 : 32;
-   97       |         lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, [&](BufferId id) {
-   98       |             if (candidate_count == limit) return true;
-   99       |             candidates[candidate_count++] = id;
+         92 |         --num_iterations;
+         93 |         // Below the critical threshold, buffers holding GPU-written data stay: evicting one
+         94 |         // means downloading it first. The thresholds compare the whole device's use (mostly
+         95 |         // textures) with fixed headroom, so on an 8 GB GPU the collector ran every frame once a
+         96 |         // title 1 course was loaded, and the downloads were ~2.7% of the GPU thread.
+         97 |         const Buffer& buffer = slot_buffers[buffer_id];
+         98 |         if (!aggressive_gc && gpu_modified_ranges.Intersects(buffer.CpuAddr(), buffer.SizeBytes())) {
   100    99 |             return false;
-  101       |         });
-  102       |         struct Download {
-  103       |             BufferId id;
-  104       |             BufferCopy copy;
-  105       |         };
-  106       |         const auto download_batch = [&](std::span<const BufferId> ids) {
-  107       |             boost::container::small_vector<Download, 16> downloads;
-  108       |             u64 total = 0;
-  109       |             bool oversized = false;
-  110       |             for (const BufferId id : ids) {
-  111       |                 const auto& buffer = slot_buffers[id];
-  112       |                 // Plan without clearing GPU ownership. A staging allocation
-  113       |                 // failure must leave the original buffers readable.
-  114       |                 memory_tracker.ForEachDownloadRange(
-  115       |                     buffer.CpuAddr(), buffer.SizeBytes(), false,
-  116       |                     [&](u64 start, u64 bytes) {
-  117       |                         if (oversized) return;
-  118       |                         gpu_modified_ranges.ForEachInRange(start, bytes,
-  119       |                             [&](DAddr first, DAddr end) {
-  120       |                                 if (oversized) return;
-  121       |                                 const u64 size = end - first;
-  122       |                                 if (size > staging_budget ||
-  123       |                                     downloads.size() == max_regions) {
-  124       |                                     oversized = true;
-  125       |                                     return;
   126   100 |                                 }
-  127       |                                 const u64 aligned = (size + 63) & ~u64{63};
-  128       |                                 if (aligned > staging_budget - total) {
-  129       |                                     oversized = true;
-  130       |                                     return;
-  131       |                                 }
-  132       |                                 downloads.push_back({id, BufferCopy{
-  133       |                                     .src_offset = first - buffer.CpuAddr(),
-  134       |                                     .dst_offset = total,
-  135       |                                     .size = size,
-  136       |                                 }});
-  137       |                                 total += aligned;
-  138       |                             });
-  139       |                     });
-  140       |                 if (oversized) break;
-  141       |             }
-  142       |             if (oversized) {
-  143       |                 // Do not grow the new batch's staging or metadata without
-  144       |                 // bound. The existing single-buffer path handles rare large
-  145       |                 // or highly fragmented evictions with its original contract.
-  146       |                 for (const BufferId id : ids) {
-  147       |                     DownloadBufferMemory(slot_buffers[id]);
-  148       |                     DeleteBuffer(id);
-  149       |                 }
-  150       |                 return;
-  151       |             }
-  152       |             if (total) {
-  153       |                 // Catch only allocation failure, before recording GPU copies.
-  154       |                 // A failed retirement is not a recoverable allocation error.
-  155       |                 std::optional<decltype(runtime.DownloadStagingBuffer(total))> staging;
-  156       |                 try {
-  157       |                     staging.emplace(runtime.DownloadStagingBuffer(total));
-  158       |                 } catch (const std::bad_alloc&) {
-  159       |                     return;
-  160       |                 }
-  161       |                 runtime.PreCopyBarrier();
-  162       |                 for (size_t first = 0; first < downloads.size();) {
-  163       |                     const BufferId id = downloads[first].id;
-  164       |                     auto& buffer = slot_buffers[id];
-  165       |                     std::array<BufferCopy, 8> copies{};
-  166       |                     size_t count = 0;
-  167       |                     do {
-  168       |                         auto copy = downloads[first++].copy;
-  169       |                         copy.dst_offset += staging->offset;
-  170       |                         buffer.MarkUsage(copy.src_offset, copy.size);
-  171       |                         copies[count++] = copy;
-  172       |                     } while (first < downloads.size() && count < copies.size() &&
-  173       |                              downloads[first].id == id);
-  174       |                     runtime.CopyBuffer(staging->buffer, buffer,
-  175       |                         std::span<const BufferCopy>{copies.data(), count}, false);
-  176       |                 }
-  177       |                 runtime.PostCopyBarrier();
-  178       |                 runtime.Finish();
-  179       |                 // Keep the established pending CPU-write protection. Sample
-  180       |                 // after retirement so writes queued during the wait are visible.
-  181       |                 const auto cpu_written = PendingCpuWriteRanges();
-  182       |                 for (const auto& download : downloads) {
-  183       |                     const auto& copy = download.copy;
-  184       |                     const auto& buffer = slot_buffers[download.id];
-  185       |                     WriteDownloadedMemory(cpu_written, buffer.CpuAddr() + copy.src_offset,
-  186       |                         staging->mapped_span.data() + copy.dst_offset, copy.size);
-  187       |                 }
-  188       |             }
-  189       |             // Publish ownership only after every readback in this batch
-  190       |             // completed. Buffer allocations are page-aligned and disjoint.
-  191       |             for (const BufferId id : ids) {
-  192       |                 auto& buffer = slot_buffers[id];
-  193       |                 memory_tracker.ForEachDownloadRangeAndClear(
-  194       |                     buffer.CpuAddr(), buffer.SizeBytes(), [&](u64 start, u64 bytes) {
-  195       |                         ClearDownload(start, bytes);
-  196       |                         gpu_modified_ranges.Subtract(start, bytes);
+        101 |         evicted.push_back(buffer_id);
+        102 |         return false;
   197   103 |                     });
-  198       |                 DeleteBuffer(id);
-  199       |             }
-  200       |         };
-  201       |         // Bound the nominal batch by the owners' sizes; the planner above
-  202       |         // independently caps the actual aligned readback size and region count.
-  203       |         for (size_t first = 0; first < candidate_count;) {
-  204       |             size_t end = first;
-  205       |             u64 bytes = 0;
-  206       |             do {
-  207       |                 const u64 size = slot_buffers[candidates[end]].SizeBytes();
-  208       |                 if (end != first && (bytes >= staging_budget ||
-  209       |                                      size > staging_budget - bytes)) break;
-  210       |                 bytes += size;
-  211       |                 ++end;
-  212       |             } while (end < candidate_count);
-  213       |             download_batch(std::span<const BufferId>{candidates.data() + first, end - first});
-  214       |             first = end;
+        104 |     if constexpr (USE_MEMORY_MAPS) {
+        105 |         DownloadBuffersMemory(evicted);
+        106 |     } else {
+        107 |         for (const BufferId buffer_id : evicted) {
+        108 |             DownloadBufferMemory(slot_buffers[buffer_id]);
   215   109 |         }
-  216       |         return;
   217   110 |     }
-  218       | #endif
-  219       |     int num_iterations = aggressive_gc ? 64 : 32;
-  220       |     const auto clean_up = [this, &num_iterations](BufferId buffer_id) {
-  221       |         if (num_iterations == 0) {
-  222       |             return true;
+        111 |     for (const BufferId buffer_id : evicted) {
+        112 |         if (create_trace.enabled) {
+        113 |             ++create_trace.collected;
+        114 |             create_trace.collected_bytes += slot_buffers[buffer_id].SizeBytes();
   223   115 |         }
-  224       |         --num_iterations;
-  225       |         auto& buffer = slot_buffers[buffer_id];
-  226       |         DownloadBufferMemory(buffer);
   227   116 |         DeleteBuffer(buffer_id);
-  228       |         return false;
-  229       |     };
-  230       |     lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, clean_up);
   231   117 | }
+        118 | }
```

</details>


<details>
<summary>EglantinePS5 — 83–117 : 9 alignées, 146 propres Encore, 26 propres upstream</summary>

Source : [buffer_cache.h:83–117](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/buffer_cache/buffer_cache.h#L83-L117). Numéros exacts dans chaque commit.

```diff
-   77       | void BufferCache<P>::RunGarbageCollector() {
-   78       |     const bool aggressive_gc = total_used_memory >= critical_memory;
+         83 | void BufferCache<P>::RunGarbageCollector(bool aggressive_gc) {
+         84 |     const StutterTrace::SiteScope site{StutterTrace::Site::BufferCollect};
    79    85 |     const u64 ticks_to_destroy = aggressive_gc ? 60 : 120;
-   80       | #ifdef PS5_NATIVE
-   81       |     // Before a buffer reaches the GC age, subtracting from this unsigned
-   82       |     // frame tick wraps to a huge LRU threshold. On startup/pressure bursts
-   83       |     // that wrongly evicts young buffers and can force guest downloads.
-   84       |     if (frame_tick < ticks_to_destroy) {
-   85       |         return;
+         86 |     int num_iterations = aggressive_gc ? 64 : 32;
+         87 |     // Their GPU-written data is downloaded first, all with one wait for the GPU: one wait per
+         88 |     // buffer stalled the GPU thread every frame on title 1 (an 8 GB GPU near its budget, no
+         89 |     // per-fence downloads keeping the buffers clean), ~2.5% of its time.
+         90 |     boost::container::small_vector<BufferId, 64> evicted;
+         91 |     lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, [&](BufferId buffer_id) {
+         92 |         if (num_iterations == 0) {
+         93 |             return true;
    86    94 |     }
-   87       | #endif
-   88       | #ifdef PS5_NATIVE
-   89       |     if constexpr (USE_MEMORY_MAPS && !IS_OPENGL) {
-   90       |         // Lichii batches GC readbacks rather than finishing the GPU once
-   91       |         // per dirty eviction. Keep the existing LRU age and eviction count.
-   92       |         constexpr u64 staging_budget = 16ULL * 1024 * 1024;
-   93       |         constexpr size_t max_regions = 4096;
-   94       |         std::array<BufferId, 64> candidates{};
-   95       |         size_t candidate_count = 0;
-   96       |         const size_t limit = aggressive_gc ? 64 : 32;
-   97       |         lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, [&](BufferId id) {
-   98       |             if (candidate_count == limit) return true;
-   99       |             candidates[candidate_count++] = id;
+         95 |         --num_iterations;
+         96 |         // Below the critical threshold, buffers holding GPU-written data stay: evicting one
+         97 |         // means downloading it first. The thresholds compare the whole device's use (mostly
+         98 |         // textures) with fixed headroom, so on an 8 GB GPU the collector ran every frame once a
+         99 |         // title 1 course was loaded, and the downloads were ~2.7% of the GPU thread.
+        100 |         const Buffer& buffer = slot_buffers[buffer_id];
+        101 |         if (!aggressive_gc && gpu_modified_ranges.Intersects(buffer.CpuAddr(), buffer.SizeBytes())) {
   100   102 |             return false;
-  101       |         });
-  102       |         struct Download {
-  103       |             BufferId id;
-  104       |             BufferCopy copy;
-  105       |         };
-  106       |         const auto download_batch = [&](std::span<const BufferId> ids) {
-  107       |             boost::container::small_vector<Download, 16> downloads;
-  108       |             u64 total = 0;
-  109       |             bool oversized = false;
-  110       |             for (const BufferId id : ids) {
-  111       |                 const auto& buffer = slot_buffers[id];
-  112       |                 // Plan without clearing GPU ownership. A staging allocation
-  113       |                 // failure must leave the original buffers readable.
-  114       |                 memory_tracker.ForEachDownloadRange(
-  115       |                     buffer.CpuAddr(), buffer.SizeBytes(), false,
-  116       |                     [&](u64 start, u64 bytes) {
-  117       |                         if (oversized) return;
-  118       |                         gpu_modified_ranges.ForEachInRange(start, bytes,
-  119       |                             [&](DAddr first, DAddr end) {
-  120       |                                 if (oversized) return;
-  121       |                                 const u64 size = end - first;
-  122       |                                 if (size > staging_budget ||
-  123       |                                     downloads.size() == max_regions) {
-  124       |                                     oversized = true;
-  125       |                                     return;
   126   103 |                                 }
-  127       |                                 const u64 aligned = (size + 63) & ~u64{63};
-  128       |                                 if (aligned > staging_budget - total) {
-  129       |                                     oversized = true;
-  130       |                                     return;
-  131       |                                 }
-  132       |                                 downloads.push_back({id, BufferCopy{
-  133       |                                     .src_offset = first - buffer.CpuAddr(),
-  134       |                                     .dst_offset = total,
-  135       |                                     .size = size,
-  136       |                                 }});
-  137       |                                 total += aligned;
-  138       |                             });
-  139       |                     });
-  140       |                 if (oversized) break;
-  141       |             }
-  142       |             if (oversized) {
-  143       |                 // Do not grow the new batch's staging or metadata without
-  144       |                 // bound. The existing single-buffer path handles rare large
-  145       |                 // or highly fragmented evictions with its original contract.
-  146       |                 for (const BufferId id : ids) {
-  147       |                     DownloadBufferMemory(slot_buffers[id]);
-  148       |                     DeleteBuffer(id);
-  149       |                 }
-  150       |                 return;
-  151       |             }
-  152       |             if (total) {
-  153       |                 // Catch only allocation failure, before recording GPU copies.
-  154       |                 // A failed retirement is not a recoverable allocation error.
-  155       |                 std::optional<decltype(runtime.DownloadStagingBuffer(total))> staging;
-  156       |                 try {
-  157       |                     staging.emplace(runtime.DownloadStagingBuffer(total));
-  158       |                 } catch (const std::bad_alloc&) {
-  159       |                     return;
-  160       |                 }
-  161       |                 runtime.PreCopyBarrier();
-  162       |                 for (size_t first = 0; first < downloads.size();) {
-  163       |                     const BufferId id = downloads[first].id;
-  164       |                     auto& buffer = slot_buffers[id];
-  165       |                     std::array<BufferCopy, 8> copies{};
-  166       |                     size_t count = 0;
-  167       |                     do {
-  168       |                         auto copy = downloads[first++].copy;
-  169       |                         copy.dst_offset += staging->offset;
-  170       |                         buffer.MarkUsage(copy.src_offset, copy.size);
-  171       |                         copies[count++] = copy;
-  172       |                     } while (first < downloads.size() && count < copies.size() &&
-  173       |                              downloads[first].id == id);
-  174       |                     runtime.CopyBuffer(staging->buffer, buffer,
-  175       |                         std::span<const BufferCopy>{copies.data(), count}, false);
-  176       |                 }
-  177       |                 runtime.PostCopyBarrier();
-  178       |                 runtime.Finish();
-  179       |                 // Keep the established pending CPU-write protection. Sample
-  180       |                 // after retirement so writes queued during the wait are visible.
-  181       |                 const auto cpu_written = PendingCpuWriteRanges();
-  182       |                 for (const auto& download : downloads) {
-  183       |                     const auto& copy = download.copy;
-  184       |                     const auto& buffer = slot_buffers[download.id];
-  185       |                     WriteDownloadedMemory(cpu_written, buffer.CpuAddr() + copy.src_offset,
-  186       |                         staging->mapped_span.data() + copy.dst_offset, copy.size);
-  187       |                 }
-  188       |             }
-  189       |             // Publish ownership only after every readback in this batch
-  190       |             // completed. Buffer allocations are page-aligned and disjoint.
-  191       |             for (const BufferId id : ids) {
-  192       |                 auto& buffer = slot_buffers[id];
-  193       |                 memory_tracker.ForEachDownloadRangeAndClear(
-  194       |                     buffer.CpuAddr(), buffer.SizeBytes(), [&](u64 start, u64 bytes) {
-  195       |                         ClearDownload(start, bytes);
-  196       |                         gpu_modified_ranges.Subtract(start, bytes);
+        104 |         evicted.push_back(buffer_id);
+        105 |         return false;
   197   106 |                     });
-  198       |                 DeleteBuffer(id);
-  199       |             }
-  200       |         };
-  201       |         // Bound the nominal batch by the owners' sizes; the planner above
-  202       |         // independently caps the actual aligned readback size and region count.
-  203       |         for (size_t first = 0; first < candidate_count;) {
-  204       |             size_t end = first;
-  205       |             u64 bytes = 0;
-  206       |             do {
-  207       |                 const u64 size = slot_buffers[candidates[end]].SizeBytes();
-  208       |                 if (end != first && (bytes >= staging_budget ||
-  209       |                                      size > staging_budget - bytes)) break;
-  210       |                 bytes += size;
-  211       |                 ++end;
-  212       |             } while (end < candidate_count);
-  213       |             download_batch(std::span<const BufferId>{candidates.data() + first, end - first});
-  214       |             first = end;
-  215       |         }
-  216       |         return;
+        107 |     if constexpr (USE_MEMORY_MAPS) {
+        108 |         DownloadBuffersMemory(evicted);
+        109 |     } else {
+        110 |         for (const BufferId buffer_id : evicted) {
+        111 |             DownloadBufferMemory(slot_buffers[buffer_id]);
   217   112 |     }
-  218       | #endif
-  219       |     int num_iterations = aggressive_gc ? 64 : 32;
-  220       |     const auto clean_up = [this, &num_iterations](BufferId buffer_id) {
-  221       |         if (num_iterations == 0) {
-  222       |             return true;
   223   113 |         }
-  224       |         --num_iterations;
-  225       |         auto& buffer = slot_buffers[buffer_id];
-  226       |         DownloadBufferMemory(buffer);
+        114 |     for (const BufferId buffer_id : evicted) {
   227   115 |         DeleteBuffer(buffer_id);
-  228       |         return false;
-  229       |     };
-  230       |     lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, clean_up);
   231   116 | }
+        117 | }
```

</details>

### P1-02 · BufferCache — DownloadMemory

Lichii et Eglantine disposent en plus d'un DownloadMemoryForRead et d'une anticipation des plages CPU lues. Comparer données GPU modifiées, cohérence et verrouillage ; hypothèse pertinente HUD/pause, pas correctif prouvé.

Encore : [buffer_cache.h:414–431](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h#L414-L431) (18 lignes).


<details>
<summary>Lichii — 470–492 : 10 alignées, 8 propres Encore, 13 propres upstream</summary>

Source : [buffer_cache.h:470–492](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/buffer_cache/buffer_cache.h#L470-L492). Numéros exacts dans chaque commit.

```diff
   414   470 | void BufferCache<P>::DownloadMemory(DAddr device_addr, u64 size) {
-  415       |     // The cache page table covers 16 GiB of guest physical memory.
-  416       |     constexpr DAddr address_limit = DAddr{1} << 34;
-  417       |     if (!size || device_addr >= address_limit || size > address_limit - device_addr) {
+        471 |     if constexpr (USE_MEMORY_MAPS) {
+        472 |         if (download_cpu_read_ranges) {
+        473 |             download_cpu_read_ranges = false;
+        474 |             boost::container::small_vector<std::pair<DAddr, u64>, 16> ranges{{device_addr, size}};
+        475 |             cpu_read_ranges.ForEach([&](DAddr lower, DAddr upper) {
+        476 |                 gpu_modified_ranges.ForEachInRange(lower, upper - lower,
+        477 |                                                    [&](DAddr start, DAddr end) {
+        478 |                                                        ranges.emplace_back(start, end - start);
+        479 |                                                    });
+        480 |             });
+        481 |             DownloadRangesMemory(ranges);
   418   482 |         return;
   419   483 |     }
-  420       |     const DAddr end_addr = device_addr + size;
+        484 |     }
   421   485 |     ForEachBufferInRange(device_addr, size, [&](BufferId, Buffer& buffer) {
-  422       |         // The memory tracker is shared across buffers. Never clear or copy
-  423       |         // another buffer's GPU-written pages using this buffer's offsets.
-  424       |         // Match Lichii's per-owner intersection before the destructive readback.
   425   486 |         const DAddr start = (std::max)(device_addr, buffer.CpuAddr());
-  426       |         const DAddr end = (std::min)(end_addr, buffer.CpuAddr() + buffer.SizeBytes());
+        487 |         const DAddr end = (std::min)(device_addr + size, buffer.CpuAddr() + buffer.SizeBytes());
   427   488 |         if (start < end) {
   428   489 |             DownloadBufferMemory(buffer, start, end - start);
   429   490 |         }
   430   491 |     });
   431   492 | }
```

</details>


<details>
<summary>EglantinePS5 — 418–440 : 10 alignées, 8 propres Encore, 13 propres upstream</summary>

Source : [buffer_cache.h:418–440](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/buffer_cache/buffer_cache.h#L418-L440). Numéros exacts dans chaque commit.

```diff
   414   418 | void BufferCache<P>::DownloadMemory(DAddr device_addr, u64 size) {
-  415       |     // The cache page table covers 16 GiB of guest physical memory.
-  416       |     constexpr DAddr address_limit = DAddr{1} << 34;
-  417       |     if (!size || device_addr >= address_limit || size > address_limit - device_addr) {
+        419 |     if constexpr (USE_MEMORY_MAPS) {
+        420 |         if (download_cpu_read_ranges) {
+        421 |             download_cpu_read_ranges = false;
+        422 |             boost::container::small_vector<std::pair<DAddr, u64>, 16> ranges{{device_addr, size}};
+        423 |             cpu_read_ranges.ForEach([&](DAddr lower, DAddr upper) {
+        424 |                 gpu_modified_ranges.ForEachInRange(lower, upper - lower,
+        425 |                                                    [&](DAddr start, DAddr end) {
+        426 |                                                        ranges.emplace_back(start, end - start);
+        427 |                                                    });
+        428 |             });
+        429 |             DownloadRangesMemory(ranges);
   418   430 |         return;
   419   431 |     }
-  420       |     const DAddr end_addr = device_addr + size;
+        432 |     }
   421   433 |     ForEachBufferInRange(device_addr, size, [&](BufferId, Buffer& buffer) {
-  422       |         // The memory tracker is shared across buffers. Never clear or copy
-  423       |         // another buffer's GPU-written pages using this buffer's offsets.
-  424       |         // Match Lichii's per-owner intersection before the destructive readback.
   425   434 |         const DAddr start = (std::max)(device_addr, buffer.CpuAddr());
-  426       |         const DAddr end = (std::min)(end_addr, buffer.CpuAddr() + buffer.SizeBytes());
+        435 |         const DAddr end = (std::min)(device_addr + size, buffer.CpuAddr() + buffer.SizeBytes());
   427   436 |         if (start < end) {
   428   437 |             DownloadBufferMemory(buffer, start, end - start);
   429   438 |         }
   430   439 |     });
   431   440 | }
```

</details>

## Références complémentaires (contrats, pas homologues directs)

- [libounce, gsvSyncArmEvent / DisarmEvent / CheckNative](https://github.com/ouncebrew/libounce/blob/03af07a739a9a3b48704500cffcd6155692cc194/nx/source/switch2/services/gsv.c#L615-L677) : vérifier les mots, la largeur et le sentinel de producteur invalide. Ne prouve pas le retirement Vulkan.
- [nxnative, SetHeapSize](https://github.com/seedds/nxnative/blob/35fea5c2ee781689ff224e614a8da71867a571bf/dm/host/hle_svc.c#L1073-L1099) : comptabilise le heap par rapport au pool et protège les mappings utilisés. ARM/Metal et x86/Vulkan ne sont pas interchangeables.
- [MKW](https://github.com/seedds/nxnative/blob/35fea5c2ee781689ff224e614a8da71867a571bf/dm/games/0400C3F00006E000/README.md#L1-L15) : course à 60 fps rapportée sur Mac, heap demandé ~7,43 Go, conditions de rendu.
- [Bananza](https://github.com/seedds/nxnative/blob/35fea5c2ee781689ff224e614a8da71867a571bf/dm/games/040074A01BF12000/README.md#L1-L12) : début de partie testé Mac ; compilation initiale des pipelines, ne prouve pas la fermeture PS5.
- [Pokopia](https://github.com/seedds/nxnative/blob/35fea5c2ee781689ff224e614a8da71867a571bf/dm/games/0400A3A01EE4C000/README.md#L1-L20) : update v655360 identique au log Encore ; 31 min de gameplay rapportées Mac, depth zero, shaders précompilés sélectivement.
- [Dynarmic ClearCache](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/dynarmic/backend/x64/block_of_code_native.cpp#L228-L265) : bfb93d21 évite trim sans code invité abandonné. La cause SIGABRT exacte reste à prouver.
- [Scheduler replay](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp#L53-L88) : 465d7e9c lie le canal avant lecture cohérente. Console non validée.

## Priorité des écarts

| ID | Écart | Statut | Preuve attendue |
|---|---|---|---|
| P0-01 | 429 n'allouait qu'un ID pour un pool | corrigé source bfb93d21 | 429(count>1) + 315 + image |
| P0-08 | reprise du canal avec mauvais contexte | corrigé source 465d7e9c | Pokopia avance après deux listes |
| P0-JIT | ClearCache au prelude rendait des pages inutilement | corrigé source bfb93d21 | Z-A après MKW et à froid |
| P0-07 | snapshot pushbuffer upstream vs lecture cohérente live | ouvert | démontrer réécriture ou production GPU, préserver mappings |
| P0-04/05 | progression syncpoint et retirement | ouvert | completion réelle, marqueur visible, événement atteint |
| P0-02/03 | teardown images/canaux/syncpt | ouvert | DK/Pokopia ferment sans watchdog |
| P1-01/02 | contentions et lecture GPU par CPU | ouvert | même scène/cache, p50/p95/p99, pauses >100 ms, HUD/pause |

Ne pas reclasser un écart en bug sans preuve, ni marquer résolu avant console. [Bibliothèque NS1/NS2](../EDEN_ENCORE_BIBLIOTHEQUE_TECHNIQUE_NS1_NS2_2026-11-20.md), [gap analysis](EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md), [FC27 F07](../FC27_F07_MASTER_TRACKER.md).

**Couverture de cette section :** 9 fonctions homologues, 18 comparaisons, 1877 lignes-source parcourues (répétitions incluses), 184 alignées, 1026 propres Encore, 483 propres upstream. Reste hors périmètre : comparaison intégrale kernel, shader, VI2, loader, teardown et autres propriétaires. OunceVK reste à intégrer par signatures exactes.
