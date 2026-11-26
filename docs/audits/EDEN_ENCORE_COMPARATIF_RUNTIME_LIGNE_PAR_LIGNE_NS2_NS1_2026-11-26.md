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

## Annexe II — ordonnancement GPU et chemin de lecture CPU

Même photographie de sources, mêmes règles d'alignement.

### P0-08 · Scheduler::Push

Encore protège l'epoch et le bind du contexte, et publie les canaux parqués sous le même verrou GPU depuis 465d7e9c. Les forks doivent être lus avec leur propre chemin de soumission et de snapshot ; pas de backport isolé.

Encore : [scheduler.cpp:19–52](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp#L19-L52).

<details>
<summary>Lichii — 38–60 : 6 alignées, 28 propres Encore, 17 propres upstream</summary>

Source : [scheduler.cpp:38–60](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/control/scheduler.cpp#L38-L60).

```diff
    19    38 | void Scheduler::Push(GPU& gpu, s32 channel, CommandList&& entries) {
-   20       |     {
-   21       |         // Hold a SHARED channel epoch lease through submission. Channel
-   22       |         // re-registration must not retire the old owner while a GPU worker
-   23       |         // is still dispatching its commands. Independent readers retain
-   24       |         // concurrency; only replacement needs the exclusive lease.
-   25       |         std::shared_lock epoch_lock(scheduling_guard);
-   26       |         const auto it = channels.find(channel);
-   27       |         if (it == channels.end() || !it->second || !it->second->payload)
-   28       |             throw std::runtime_error("Native GPFIFO: missing channel owner");
-   29       |         const auto channel_state = it->second;
-   30       |         auto& pusher = channel_state->payload->dma_pusher;
-   31       |         // GPU::BindChannel mutates a single shared GPU execution context.
-   32       |         // Concurrent native channel submissions and semaphore replay must
-   33       |         // not interleave a bind with another owner's DispatchCalls.
+         39 |     std::shared_ptr<ChannelState> channel_state;
    34    40 |         {
-   35       |             const std::scoped_lock gpu_lock(gpu_submit_guard);
-   36       |             gpu.BindChannel(channel_state->bind_id);
-   37       |             pusher.Push(std::move(entries));
-   38       |             pusher.DispatchCalls();
-   39       |             // Publish the parked state while the GPU execution lease still
-   40       |             // protects the pusher. A concurrent replay must not change it.
-   41       |             const std::scoped_lock pending_lock(pending_guard);
-   42       |             if (pusher.HasPendingNativeAcquire() &&
-   43       |                 std::find(pending_native_channels.begin(), pending_native_channels.end(),
-   44       |                           channel_state) == pending_native_channels.end()) {
-   45       |                 pending_native_channels.push_back(channel_state);
+         41 |         std::unique_lock lk(scheduling_guard);
+         42 |         auto it = channels.find(channel);
+         43 |         ASSERT(it != channels.end());
+         44 |         channel_state = it->second;
    46    45 |             }
+         46 |     BindChannel(gpu, channel_state->bind_id);
+         47 |     // Process commands outside the lock to reduce contention.
+         48 |     // Multiple channels can prepare their commands in parallel.
+         49 |     channel_state->payload->dma_pusher.Push(std::move(entries));
+         50 |     channel_state->payload->dma_pusher.DispatchCalls();
+         51 |     if (channel_state->payload->dma_pusher.HasPendingAcquire() &&
+         52 |         std::find(pending_channels.begin(), pending_channels.end(), channel_state) ==
+         53 |             pending_channels.end()) {
+         54 |         pending_channels.push_back(channel_state);
+         55 |         any_pending.store(true, std::memory_order_release);
    47    56 |         }
+         57 |     if (!pending_channels.empty()) {
+         58 |         ResumePending(gpu);
    48    59 |     }
-   49       |     // Do not hold the scheduling lease while replaying other channels.
-   50       |     if (HasPendingNativeChannels())
-   51       |         ResumePendingNative(gpu);
    52    60 | }
```

</details>

<details>
<summary>EglantinePS5 — 42–79 : 7 alignées, 27 propres Encore, 31 propres upstream</summary>

Source : [scheduler.cpp:42–79](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/control/scheduler.cpp#L42-L79).

```diff
    19    42 | void Scheduler::Push(GPU& gpu, s32 channel, CommandList&& entries) {
+         43 |     std::shared_ptr<ChannelState> channel_state;
    20    44 |     {
-   21       |         // Hold a SHARED channel epoch lease through submission. Channel
-   22       |         // re-registration must not retire the old owner while a GPU worker
-   23       |         // is still dispatching its commands. Independent readers retain
-   24       |         // concurrency; only replacement needs the exclusive lease.
-   25       |         std::shared_lock epoch_lock(scheduling_guard);
-   26       |         const auto it = channels.find(channel);
-   27       |         if (it == channels.end() || !it->second || !it->second->payload)
-   28       |             throw std::runtime_error("Native GPFIFO: missing channel owner");
-   29       |         const auto channel_state = it->second;
-   30       |         auto& pusher = channel_state->payload->dma_pusher;
-   31       |         // GPU::BindChannel mutates a single shared GPU execution context.
-   32       |         // Concurrent native channel submissions and semaphore replay must
-   33       |         // not interleave a bind with another owner's DispatchCalls.
+         45 | #if !defined(__PROSPERO__) // not PS5
+         46 | #else // PS5
+         47 |         const ::Eden::Performance::Timer sched_lock_timer(::Eden::Performance::gpu_sched_lock);
+         48 | #endif // PS5
+         49 |         std::unique_lock lk(scheduling_guard);
+         50 |         auto it = channels.find(channel);
+         51 |         ASSERT(it != channels.end());
+         52 |         channel_state = it->second;
+         53 |     }
+         54 |     BindChannel(gpu, channel_state->bind_id);
+         55 |     // Process commands outside the lock to reduce contention.
+         56 |     // Multiple channels can prepare their commands in parallel.
+         57 | #if !defined(__PROSPERO__) // not PS5
+         58 |     channel_state->payload->dma_pusher.Push(std::move(entries));
+         59 |     channel_state->payload->dma_pusher.DispatchCalls();
+         60 | #else // PS5
    34    61 |         {
-   35       |             const std::scoped_lock gpu_lock(gpu_submit_guard);
-   36       |             gpu.BindChannel(channel_state->bind_id);
-   37       |             pusher.Push(std::move(entries));
-   38       |             pusher.DispatchCalls();
-   39       |             // Publish the parked state while the GPU execution lease still
-   40       |             // protects the pusher. A concurrent replay must not change it.
-   41       |             const std::scoped_lock pending_lock(pending_guard);
-   42       |             if (pusher.HasPendingNativeAcquire() &&
-   43       |                 std::find(pending_native_channels.begin(), pending_native_channels.end(),
-   44       |                           channel_state) == pending_native_channels.end()) {
-   45       |                 pending_native_channels.push_back(channel_state);
+         62 |         const ::Eden::Performance::Timer dma_push_timer(::Eden::Performance::gpu_dma_push);
+         63 |         channel_state->payload->dma_pusher.Push(std::move(entries));
    46    64 |             }
+         65 |     {
+         66 |         const ::Eden::Performance::Timer dma_dispatch_timer(::Eden::Performance::gpu_dma_dispatch);
+         67 |         channel_state->payload->dma_pusher.DispatchCalls();
    47    68 |         }
+         69 | #endif // PS5
+         70 |     if (channel_state->payload->dma_pusher.HasPendingAcquire() &&
+         71 |         std::find(pending_channels.begin(), pending_channels.end(), channel_state) ==
+         72 |             pending_channels.end()) {
+         73 |         pending_channels.push_back(channel_state);
+         74 |         any_pending.store(true, std::memory_order_release);
    48    75 |     }
-   49       |     // Do not hold the scheduling lease while replaying other channels.
-   50       |     if (HasPendingNativeChannels())
-   51       |         ResumePendingNative(gpu);
+         76 |     if (!pending_channels.empty()) {
+         77 |         ResumePending(gpu);
    52    78 | }
+         79 | }
```

</details>

### P0-09 · Scheduler::DeclareChannel

Préserver le recyclage des bind IDs, l'identité du propriétaire et la disparition des canaux parqués retirés.

Encore : [scheduler.cpp:90–109](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp#L90-L109).

<details>
<summary>Lichii — 99–103 : 2 alignées, 18 propres Encore, 3 propres upstream</summary>

Source : [scheduler.cpp:99–103](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/control/scheduler.cpp#L99-L103).

```diff
    90    99 | void Scheduler::DeclareChannel(std::shared_ptr<ChannelState> new_channel) {
-   91       |     if (!new_channel || !new_channel->payload)
-   92       |         throw std::runtime_error("Native GPFIFO: invalid channel owner");
-   93       |     const s32 channel = new_channel->bind_id;
-   94       |     std::unique_lock epoch_lock(scheduling_guard);
-   95       |     const std::scoped_lock pending_lock(pending_guard);
-   96       |     const auto existing = channels.find(channel);
-   97       |     if (existing != channels.end()) {
-   98       |         if (existing->second == new_channel)
-   99       |             return; // Same live owner: never discard its pending wait.
-  100       |         // A driver can reuse the bind ID after process/channel teardown.
-  101       |         // The old generation must not resume a parked semaphore against
-  102       |         // the new owner's GPU binding, or publish an obsolete guest fence.
-  103       |         const auto retired = existing->second;
-  104       |         std::erase(pending_native_channels, retired);
-  105       |         existing->second = std::move(new_channel);
-  106       |     } else {
-  107       |         channels.emplace(channel, std::move(new_channel));
-  108       |     }
+        100 |     s32 channel = new_channel->bind_id;
+        101 |     std::unique_lock lk(scheduling_guard);
+        102 |     channels.emplace(channel, new_channel);
   109   103 | }
```

</details>

<details>
<summary>EglantinePS5 — 110–114 : 2 alignées, 18 propres Encore, 3 propres upstream</summary>

Source : [scheduler.cpp:110–114](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/control/scheduler.cpp#L110-L114).

```diff
    90   110 | void Scheduler::DeclareChannel(std::shared_ptr<ChannelState> new_channel) {
-   91       |     if (!new_channel || !new_channel->payload)
-   92       |         throw std::runtime_error("Native GPFIFO: invalid channel owner");
-   93       |     const s32 channel = new_channel->bind_id;
-   94       |     std::unique_lock epoch_lock(scheduling_guard);
-   95       |     const std::scoped_lock pending_lock(pending_guard);
-   96       |     const auto existing = channels.find(channel);
-   97       |     if (existing != channels.end()) {
-   98       |         if (existing->second == new_channel)
-   99       |             return; // Same live owner: never discard its pending wait.
-  100       |         // A driver can reuse the bind ID after process/channel teardown.
-  101       |         // The old generation must not resume a parked semaphore against
-  102       |         // the new owner's GPU binding, or publish an obsolete guest fence.
-  103       |         const auto retired = existing->second;
-  104       |         std::erase(pending_native_channels, retired);
-  105       |         existing->second = std::move(new_channel);
-  106       |     } else {
-  107       |         channels.emplace(channel, std::move(new_channel));
-  108       |     }
+        111 |     s32 channel = new_channel->bind_id;
+        112 |     std::unique_lock lk(scheduling_guard);
+        113 |     channels.emplace(channel, new_channel);
   109   114 | }
```

</details>

### P1-03 · Rasterizer::GetFlushArea

Encore vérifie texture et buffer séparément avec preuve négative de propriété, et contrôle toute la plage renvoyée. Examiner les raccourcis upstream et la latence du readback sans réintroduire une publication différée non sûre.

Encore : [vulkan_rasterizer.cpp:2427–2464](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2427-L2464).

<details>
<summary>Lichii — 4338–4387 : 12 alignées, 26 propres Encore, 38 propres upstream</summary>

Source : [vk_rasterizer.cpp:4338–4387](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L4338-L4387).

```diff
  2427  4338 | VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {
- 2428       |     ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);
- 2429       |     const VideoCore::RasterizerDownloadArea clean_area{
+       4339 |     RENDER_LEND_RESULT(GetFlushArea(addr, size))
+       4340 |     // Guest cores ask this on reads of cached pages, and the back holds both caches' locks through
+       4341 |     // each draw. Pages no image was ever registered on, and Switch 2 pages the GPU never wrote,
+       4342 |     // get the clean area the caches would return without a look under their locks (after
+       4343 |     // Stephen Jayakar's EDEN_NX2_READ_FASTPATH, eb3553bcb8).
+       4344 |     const VideoCore::RasterizerDownloadArea owed_area{
  2430  4345 |         .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),
  2431  4346 |         .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),
- 2432       |         .preemtive = true,
+       4347 |         .preemtive = false,
  2433  4348 |     };
- 2434       |     // A clean/never-held texture page does not prove that a GPU-written
- 2435       |     // storage buffer is current in guest memory. Query each cache independently:
- 2436       |     // never-owned pages remain lock-free, and no two cache locks are nested.
+       4349 |     // GPU-written list words owed on these pages land in guest memory first (FlushRegionForRead):
+       4350 |     // the core keeps the area it gets, so later reads in it would not ask again.
+       4351 |     if (buffer_cache_runtime.Nx2Slots().Owes(owed_area.start_address,
+       4352 |                                              owed_area.end_address - owed_area.start_address)) {
+       4353 |         std::scoped_lock lock{buffer_cache.mutex};
+       4354 |         buffer_cache.ForgetReadTraps(owed_area.start_address,
+       4355 |                                      owed_area.end_address - owed_area.start_address);
+       4356 |         return owed_area;
+       4357 |     }
  2437  4358 |     std::optional<VideoCore::RasterizerDownloadArea> texture_area;
- 2438       |     if (!::Eden::ImagePages::NeverHeld(addr, size)) {
- 2439       |         ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);
- 2440       |         std::lock_guard lock{texture_cache.mutex, std::adopt_lock};
+       4359 |     if (texture_cache.page_filter.Any(addr, size)) {
+       4360 |         std::scoped_lock lock{texture_cache.mutex};
  2441  4361 |         texture_area = texture_cache.GetFlushArea(addr, size);
  2442  4362 |     }
- 2443       |     if (texture_area && !texture_area->preemtive) {
- 2444       |         // The existing GPU sync flushes both cache domains.
+       4363 |     if (texture_area) {
+       4364 |         // The core disarmed the read's pages before asking, and skips later reads in this area,
+       4365 |         // even through another device alias of those pages. The buffer cache arms only pages it
+       4366 |         // doesn't count as armed, so it must forget the whole area.
+       4367 |         std::scoped_lock lock{buffer_cache.mutex};
+       4368 |         buffer_cache.ForgetReadTraps(texture_area->start_address,
+       4369 |                                      texture_area->end_address - texture_area->start_address);
  2445  4370 |         return *texture_area;
  2446  4371 |     }
- 2447       |     auto area = texture_area.value_or(clean_area);
- 2448       |     // Core::Memory caches the returned interval, not just the original
- 2449       |     // scalar read. A preemptive texture can extend over other GPU-written
- 2450       |     // buffers. Check EVERY byte the caller may subsequently read without
- 2451       |     // re-entering GetFlushArea. Keep the original texture extent when clean.
- 2452       |     const DAddr buffer_start = area.start_address;
- 2453       |     const u64 buffer_size = area.end_address - buffer_start;
- 2454       |     if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {
- 2455       |         ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);
- 2456       |         std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};
- 2457       |         if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {
- 2458       |             // Preserve the real GPU ownership and the existing ordered
- 2459       |             // FlushRegion on the GPU worker. Do not certify stale siblings.
- 2460       |             area.preemtive = false;
+       4372 |     if (buffer_cache.FlushesOnCpuRead() &&
+       4373 |         (!Tegra::g_nx2_ampere.load(std::memory_order_relaxed) ||
+       4374 |          Tegra::Nx2MayBeGpuWritten(addr, size))) {
+       4375 |         std::scoped_lock lock{buffer_cache.mutex};
+       4376 |         auto area = buffer_cache.GetFlushArea(addr, size);
+       4377 |         if (area) {
+       4378 |             return *area;
  2461  4379 |         }
  2462  4380 |     }
- 2463       |     return area;
+       4381 |     VideoCore::RasterizerDownloadArea new_area{
+       4382 |         .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),
+       4383 |         .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),
+       4384 |         .preemtive = true,
+       4385 |     };
+       4386 |     return new_area;
  2464  4387 | }
```

</details>

<details>
<summary>EglantinePS5 — 2776–2836 : 14 alignées, 24 propres Encore, 47 propres upstream</summary>

Source : [vk_rasterizer.cpp:2776–2836](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L2776-L2836).

```diff
  2427  2776 | VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {
- 2428       |     ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);
- 2429       |     const VideoCore::RasterizerDownloadArea clean_area{
+       2777 |     ::Eden::Performance::Timer guest_read_timer(::Eden::Performance::guest_cpu_read);
+       2778 |     const VideoCore::RasterizerDownloadArea owed_area{
  2430  2779 |         .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),
  2431  2780 |         .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),
- 2432       |         .preemtive = true,
+       2781 |         .preemtive = false,
  2433  2782 |     };
- 2434       |     // A clean/never-held texture page does not prove that a GPU-written
- 2435       |     // storage buffer is current in guest memory. Query each cache independently:
- 2436       |     // never-owned pages remain lock-free, and no two cache locks are nested.
+       2783 |     // GPU-written list words owed on these pages land in guest memory first (FlushRegionForRead):
+       2784 |     // the core keeps the area it gets, so later reads in it would not ask again.
+       2785 |     if (buffer_cache_runtime.Nx2Slots().Owes(owed_area.start_address,
+       2786 |                                              owed_area.end_address - owed_area.start_address)) {
+       2787 |         std::scoped_lock lock{buffer_cache.mutex};
+       2788 |         buffer_cache.ForgetReadTraps(owed_area.start_address,
+       2789 |                                      owed_area.end_address - owed_area.start_address);
+       2790 |         return owed_area;
+       2791 |     }
  2437  2792 |     std::optional<VideoCore::RasterizerDownloadArea> texture_area;
+       2793 | #if defined(__PROSPERO__) // PS5
+       2794 |     // Pages no image was ever registered in have nothing for the texture cache to flush: answered
+       2795 |     // without its lock, which the GPU thread holds through every draw (image_pages.h). Otherwise
+       2796 |     // the lock is spun for briefly before sleeping on it (performance.h, GuestCacheLock).
  2438  2797 |     if (!::Eden::ImagePages::NeverHeld(addr, size)) {
- 2439       |         ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);
+       2798 |         ::Eden::Performance::GuestCacheLock(texture_cache.mutex);
  2440  2799 |         std::lock_guard lock{texture_cache.mutex, std::adopt_lock};
  2441  2800 |         texture_area = texture_cache.GetFlushArea(addr, size);
  2442  2801 |     }
- 2443       |     if (texture_area && !texture_area->preemtive) {
- 2444       |         // The existing GPU sync flushes both cache domains.
+       2802 | #else // PS5
+       2803 |     // Guest cores ask this on reads of cached pages, and the back holds both caches' locks through
+       2804 |     // each draw. Pages no image was ever registered on, and Switch 2 pages the GPU never wrote,
+       2805 |     // get the clean area the caches would return without a look under their locks (after
+       2806 |     // Stephen Jayakar's EDEN_NX2_READ_FASTPATH, eb3553bcb8).
+       2807 |     if (texture_cache.page_filter.Any(addr, size)) {
+       2808 |         std::scoped_lock lock{texture_cache.mutex};
+       2809 |         texture_area = texture_cache.GetFlushArea(addr, size);
+       2810 |     }
+       2811 | #endif // PS5
+       2812 |     if (texture_area) {
+       2813 |         // The core disarmed the read's pages before asking, and skips later reads in this area,
+       2814 |         // even through another device alias of those pages. The buffer cache arms only pages it
+       2815 |         // doesn't count as armed, so it must forget the whole area.
+       2816 |         std::scoped_lock lock{buffer_cache.mutex};
+       2817 |         buffer_cache.ForgetReadTraps(texture_area->start_address,
+       2818 |                                      texture_area->end_address - texture_area->start_address);
  2445  2819 |         return *texture_area;
  2446  2820 |     }
- 2447       |     auto area = texture_area.value_or(clean_area);
- 2448       |     // Core::Memory caches the returned interval, not just the original
- 2449       |     // scalar read. A preemptive texture can extend over other GPU-written
- 2450       |     // buffers. Check EVERY byte the caller may subsequently read without
- 2451       |     // re-entering GetFlushArea. Keep the original texture extent when clean.
- 2452       |     const DAddr buffer_start = area.start_address;
- 2453       |     const u64 buffer_size = area.end_address - buffer_start;
- 2454       |     if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {
- 2455       |         ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);
- 2456       |         std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};
- 2457       |         if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {
- 2458       |             // Preserve the real GPU ownership and the existing ordered
- 2459       |             // FlushRegion on the GPU worker. Do not certify stale siblings.
- 2460       |             area.preemtive = false;
+       2821 |     if (buffer_cache.FlushesOnCpuRead() &&
+       2822 |         (!Tegra::g_nx2_ampere.load(std::memory_order_relaxed) ||
+       2823 |          Tegra::Nx2MayBeGpuWritten(addr, size))) {
+       2824 |         std::scoped_lock lock{buffer_cache.mutex};
+       2825 |         auto area = buffer_cache.GetFlushArea(addr, size);
+       2826 |         if (area) {
+       2827 |             return *area;
  2461  2828 |         }
  2462  2829 |     }
- 2463       |     return area;
+       2830 |     VideoCore::RasterizerDownloadArea new_area{
+       2831 |         .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),
+       2832 |         .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),
+       2833 |         .preemtive = true,
+       2834 |     };
+       2835 |     return new_area;
  2464  2836 | }
```

</details>

### P0/P1-04 · Rasterizer::ReleaseFences

Comparer la retraite du fence, le comportement force=false et le travail encore en attente. Le producteur NS2 ne peut pas être signalé avant la disponibilité de son marqueur GPU.

Encore : [vulkan_rasterizer.cpp:2705–2712](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2705-L2712).

<details>
<summary>Lichii — 4845–4862 : 3 alignées, 5 propres Encore, 15 propres upstream</summary>

Source : [vk_rasterizer.cpp:4845–4862](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L4845-L4862).

```diff
  2705  4845 | void RasterizerVulkan::ReleaseFences(bool force) {
- 2706       |     if (force) {
- 2707       |         ::Eden::Performance::DiagnosticTimer drain_timer(::Eden::Performance::gpu_fence_drain);
- 2708       |         fence_manager.WaitPendingFences(force);
- 2709       |     } else {
- 2710       |         fence_manager.WaitPendingFences(force);
+       4846 |     // EDEN_NX2_RENDER_SOFT_RELEASE_E: with the fencing thread an unforced release does nothing
+       4847 |     // (FenceManager::WaitPendingFences), so the back has nothing to lend (Fritchii 554125b40).
+       4848 |     static_assert(FenceManagerParams::HAS_ASYNC_CHECK);
+       4849 |     if (!force && VideoCommon::GpuSplit::SoftReleasesOnBack()) {
+       4850 |         VideoCommon::GpuSplit::Get().NoteSoftRelease();
+       4851 |         return;
  2711  4852 |     }
+       4853 |     // With immediate fences the forced release's wait ends inside SignalFence (Fritchii 440c984e7).
+       4854 |     if (force && PostFence([this] { fence_manager.WaitPendingFences(true); })) {
+       4855 |         return;
  2712  4856 | }
+       4857 |     if (VideoCommon::GpuSplit::LendsToRender() && force) {
+       4858 |         NoteSyncLent();
+       4859 |     }
+       4860 |     RENDER_LEND(ReleaseFences(force))
+       4861 |     fence_manager.WaitPendingFences(force);
+       4862 | }
```

</details>

<details>
<summary>EglantinePS5 — 3108–3115 : 7 alignées, 1 propres Encore, 1 propres upstream</summary>

Source : [vk_rasterizer.cpp:3108–3115](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L3108-L3115).

```diff
  2705  3108 | void RasterizerVulkan::ReleaseFences(bool force) {
  2706  3109 |     if (force) {
- 2707       |         ::Eden::Performance::DiagnosticTimer drain_timer(::Eden::Performance::gpu_fence_drain);
+       3110 |         ::Eden::Performance::Timer drain_timer(::Eden::Performance::gpu_fence_drain);
  2708  3111 |         fence_manager.WaitPendingFences(force);
  2709  3112 |     } else {
  2710  3113 |         fence_manager.WaitPendingFences(force);
  2711  3114 |     }
  2712  3115 | }
```

</details>

### P0/P1-05 · Rasterizer::WaitForIdle

Comparer barrières et flushes. Le WFI de la completion 0x100 constitue un coût potentiel, pas une preuve de deadlock. Ne pas supprimer les dépendances mémoire.

Encore : [vulkan_rasterizer.cpp:2722–2752](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2722-L2752).

<details>
<summary>Lichii — 4912–4978 : 27 alignées, 4 propres Encore, 40 propres upstream</summary>

Source : [vk_rasterizer.cpp:4912–4978](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L4912-L4978).

```diff
  2722  4912 | void RasterizerVulkan::WaitForIdle() {
+       4913 |     // EDEN_NX2_RENDER_POST_WFI: with no report since the last lent fence (whose commit synced
+       4914 |     // the queries), no streamer has a sync pending and NotifyWFI leaves the back's buffer cache
+       4915 |     // alone: the rest is GPURender's recording.
+       4916 |     // EDEN_NX2_RENDER_QUERY_SYNC_E: also with reports whose value syncs the back collects here.
+       4917 |     using VideoCommon::GpuSplit;
+       4918 |     if (GpuSplit::Get().Posts(GpuSplit::PostedOp::WaitForIdle) && maxwell3d != nullptr &&
+       4919 |         !QuerySyncOwed()) {
+       4920 |         QuerySyncPacket sync;
+       4921 |         if (GpuSplit::QuerySyncOnBack()) {
+       4922 |             CollectQuerySync(sync);
+       4923 |         } else if (!back_payload_sync.empty()) [[unlikely]] {
+       4924 |             GpuSplit::Get().NotePayloadSyncsLeft();
+       4925 |         }
+       4926 |         PostRenderOp(GpuSplit::PostedOp::WaitForIdle, [this, sync = std::move(sync)]() mutable {
+       4927 |             if (!sync.commands.Empty()) {
+       4928 |                 buffer_cache_runtime.Arena().PlayCollected(sync.commands, sync.stamp);
+       4929 |             }
+       4930 |             if (!GpuSplit::QuerySyncEnabled() && query_cache.HasPendingSync()) [[unlikely]] {
+       4931 |                 GpuSplit::Get().NotePostedWaitSynced();
+       4932 |             }
+       4933 |             t_query_sync_targets = &sync.targets;
+       4934 |             SCOPE_EXIT {
+       4935 |                 t_query_sync_targets = nullptr;
+       4936 |             };
+       4937 |             WaitForIdle();
+       4938 |         });
+       4939 |         return;
+       4940 |     }
+       4941 |     if (GpuSplit::QuerySyncOnBack()) {
+       4942 |         // Lent: NotifyWFI syncs everything pending, the back parked.
+       4943 |         query_sync_lent_only = false;
+       4944 |         samples_slots.clear();
+       4945 |     }
+       4946 |     RENDER_LEND(WaitForIdle())
  2723  4947 |     // Everything but wait pixel operations. This intentionally includes FRAGMENT_SHADER_BIT because
  2724  4948 |     // fragment shaders can still write storage buffers.
  2725  4949 |     VkPipelineStageFlags flags =
  2726  4950 |         VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT | VK_PIPELINE_STAGE_VERTEX_INPUT_BIT |
  2727  4951 |         VK_PIPELINE_STAGE_VERTEX_SHADER_BIT | VK_PIPELINE_STAGE_TESSELLATION_CONTROL_SHADER_BIT |
  2728  4952 |         VK_PIPELINE_STAGE_TESSELLATION_EVALUATION_SHADER_BIT |
  2729  4953 |         VK_PIPELINE_STAGE_GEOMETRY_SHADER_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |
  2730  4954 |         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_TRANSFER_BIT;
  2731  4955 |     if (device.IsExtTransformFeedbackSupported()) {
  2732  4956 |         flags |= VK_PIPELINE_STAGE_TRANSFORM_FEEDBACK_BIT_EXT;
  2733  4957 |     }
  2734  4958 | 
  2735  4959 |     query_cache.NotifyWFI();
  2736  4960 | 
+       4961 |     if (device.IsMoltenVK() && scheduler.IsRenderPassActive()) {
+       4962 |         scheduler.DeferFragmentBarrier();
+       4963 |         fence_manager.SignalOrdering();
+       4964 |         return;
+       4965 |     }
  2737  4966 |     scheduler.RequestOutsideRenderPassOperationContext();
  2738  4967 |     scheduler.Record([flags](vk::CommandBuffer cmdbuf) {
- 2739       |         // A reusable event that is never reset only orders its first signal and, without a
- 2740       |         // memory barrier, does not make earlier GPU writes visible to subsequent commands.
- 2741       |         // A pipeline barrier expresses both the execution dependency and the guest WFI memory
- 2742       |         // visibility on every invocation. Adapted from Lichii #295 / 73bcdc059d.
+       4968 |         // Later work waits for the earlier work and sees its writes.
  2743  4969 |         static constexpr VkMemoryBarrier WFI_BARRIER{
  2744  4970 |             .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
  2745  4971 |             .pNext = nullptr,
  2746  4972 |             .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,
  2747  4973 |             .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT,
  2748  4974 |         };
  2749  4975 |         cmdbuf.PipelineBarrier(flags, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, WFI_BARRIER);
  2750  4976 |     });
  2751  4977 |     fence_manager.SignalOrdering();
  2752  4978 | }
```

</details>

<details>
<summary>EglantinePS5 — 3146–3178 : 27 alignées, 4 propres Encore, 6 propres upstream</summary>

Source : [vk_rasterizer.cpp:3146–3178](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/video_core/renderer_vulkan/vk_rasterizer.cpp#L3146-L3178).

```diff
  2722  3146 | void RasterizerVulkan::WaitForIdle() {
  2723  3147 |     // Everything but wait pixel operations. This intentionally includes FRAGMENT_SHADER_BIT because
  2724  3148 |     // fragment shaders can still write storage buffers.
  2725  3149 |     VkPipelineStageFlags flags =
  2726  3150 |         VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT | VK_PIPELINE_STAGE_VERTEX_INPUT_BIT |
  2727  3151 |         VK_PIPELINE_STAGE_VERTEX_SHADER_BIT | VK_PIPELINE_STAGE_TESSELLATION_CONTROL_SHADER_BIT |
  2728  3152 |         VK_PIPELINE_STAGE_TESSELLATION_EVALUATION_SHADER_BIT |
  2729  3153 |         VK_PIPELINE_STAGE_GEOMETRY_SHADER_BIT | VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |
  2730  3154 |         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_TRANSFER_BIT;
  2731  3155 |     if (device.IsExtTransformFeedbackSupported()) {
  2732  3156 |         flags |= VK_PIPELINE_STAGE_TRANSFORM_FEEDBACK_BIT_EXT;
  2733  3157 |     }
  2734  3158 | 
  2735  3159 |     query_cache.NotifyWFI();
  2736  3160 | 
+       3161 |     if (device.IsMoltenVK() && scheduler.IsRenderPassActive()) {
+       3162 |         scheduler.DeferFragmentBarrier();
+       3163 |         fence_manager.SignalOrdering();
+       3164 |         return;
+       3165 |     }
  2737  3166 |     scheduler.RequestOutsideRenderPassOperationContext();
  2738  3167 |     scheduler.Record([flags](vk::CommandBuffer cmdbuf) {
- 2739       |         // A reusable event that is never reset only orders its first signal and, without a
- 2740       |         // memory barrier, does not make earlier GPU writes visible to subsequent commands.
- 2741       |         // A pipeline barrier expresses both the execution dependency and the guest WFI memory
- 2742       |         // visibility on every invocation. Adapted from Lichii #295 / 73bcdc059d.
+       3168 |         // Later work waits for the earlier work and sees its writes.
  2743  3169 |         static constexpr VkMemoryBarrier WFI_BARRIER{
  2744  3170 |             .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
  2745  3171 |             .pNext = nullptr,
  2746  3172 |             .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,
  2747  3173 |             .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT,
  2748  3174 |         };
  2749  3175 |         cmdbuf.PipelineBarrier(flags, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, WFI_BARRIER);
  2750  3176 |     });
  2751  3177 |     fence_manager.SignalOrdering();
  2752  3178 | }
```

</details>

**Couverture cumulée :** 14 fonctions, 28 comparaisons directes, 2447 lignes-source parcourues (répétitions incluses). Ni couverture exhaustive du GPU ni preuve console.

## Annexe III — GMMU / NVMap / mémoire physique et heap

Cette annexe compare le chemin **invité → NVDRV address space/NVMap → KPageTable/SVC**. Elle ne modifie aucun propriétaire runtime. Les lignes sont celles des SHAs figés en tête du document. Les fonctions Encore nettement plus longues contiennent des propriétaires PS5/sparse absents des forks : la métrique de diff sert à localiser les écarts, pas à recommander le code le plus court.

### P0-M01 · AS-GPU AllocateSpace

Comparer réservation VA, alignement, big-page et bookkeeping. Encore contient en plus les chemins natifs PS5 4K/sparse ; l'écart de taille est donc attendu et doit être lu par invariants plutôt que par similarité brute.

Encore : [nvhost_as_gpu.cpp:1445–1701](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L1445-L1701) — 257 lignes.

<details>
<summary>Lichii — 554–605 : 48 alignées, 209 propres Encore, 4 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:554–605](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L554-L605).

```diff
  1445   554 | NvResult nvhost_as_gpu::AllocateSpace(IoctlAllocSpace& params) {
  1446   555 |     LOG_DEBUG(Service_NVDRV, "called, pages={:X}, page_size={:X}, flags={:X}", params.pages,
  1447   556 |               params.page_size, params.flags);
  1448   557 | 
  1449   558 |     std::scoped_lock lock(mutex);
  1450   559 | 
- 1451       |     if (native_sparse_poisoned && m_native_process &&
- 1452       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 1453       |         return NvResult::InvalidState;
  1454   560 |     if (!vm.initialised) {
  1455   561 |         return NvResult::BadValue;
  1456   562 |     }
  1457   563 | 
- 1458       |     if (params.page_size != VM::YUZU_PAGESIZE && params.page_size != vm.big_page_size) {
- 1459       |         return NvResult::BadValue;
- 1460       |     }
- 1461       | 
- 1462       |     // Native GA10F can reserve sparse 4-KiB GPU VA without backing physical
- 1463       |     // pages. The original Maxwell ioctl below deliberately keeps its legacy
- 1464       |     // unsupported-small-sparse contract; never select this path by Title ID.
- 1465       |     const bool small_sparse =
- 1466       |         params.page_size == VM::YUZU_PAGESIZE &&
- 1467       |         ((params.flags & MappingFlags::Sparse) != MappingFlags::None);
- 1468       |     if (small_sparse && m_native_process &&
- 1469       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1470       |         if (!gmmu || !vm.small_page_allocator || params.pages == 0)
- 1471       |             return NvResult::BadValue;
- 1472       |         constexpr u32 allowed_flags =
- 1473       |             static_cast<u32>(MappingFlags::Fixed) | static_cast<u32>(MappingFlags::Sparse);
- 1474       |         if ((static_cast<u32>(params.flags) & ~allowed_flags) != 0)
- 1475       |             return NvResult::BadValue;
- 1476       | 
- 1477       |         // All VA arithmetic is 64-bit; the actual allocator stores 4K page
- 1478       |         // numbers in u32. A reservation never commits pages or pins NVMap.
- 1479       |         auto& allocator = *vm.small_page_allocator;
- 1480       |         const u64 first_va = static_cast<u64>(allocator.GetVAStart()) << VM::PAGE_SIZE_BITS;
- 1481       |         const u64 limit_va = static_cast<u64>(allocator.GetVALimit()) << VM::PAGE_SIZE_BITS;
- 1482       |         const u64 size = static_cast<u64>(params.pages) * VM::YUZU_PAGESIZE;
- 1483       |         if (size > limit_va - first_va)
- 1484       |             return NvResult::InsufficientMemory;
- 1485       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 1486       |         u64 address = fixed ? static_cast<u64>(params.offset) : 0;
- 1487       |         if (fixed) {
- 1488       |             if (address < first_va || address >= limit_va ||
- 1489       |                 (address & (VM::YUZU_PAGESIZE - 1)) != 0 ||
- 1490       |                 size > limit_va - address)
- 1491       |                 return NvResult::BadValue;
- 1492       |             // FlatAllocator::AllocateFixed does not reject an overlapping
- 1493       |             // reservation itself. An alias must not steal another guest VA,
- 1494       |             // including existing fixed maps from MapBufferEx.
- 1495       |             const auto reserved = allocation_map.lower_bound(address);
- 1496       |             if ((reserved != allocation_map.end() &&
- 1497       |                  reserved->first < address + size) ||
- 1498       |                 (reserved != allocation_map.begin() &&
- 1499       |                  std::prev(reserved)->second.size >
- 1500       |                      address - std::prev(reserved)->first))
- 1501       |                 return NvResult::BadValue;
- 1502       |             const auto mapped = mapping_map.lower_bound(address);
- 1503       |             if ((mapped != mapping_map.end() &&
- 1504       |                  mapped->first < address + size) ||
- 1505       |                 (mapped != mapping_map.begin() &&
- 1506       |                  std::prev(mapped)->second.size >
- 1507       |                      address - std::prev(mapped)->first))
- 1508       |                 return NvResult::BadValue;
- 1509       |         }
- 1510       | 
- 1511       |         u32 first_page{};
- 1512       |         bool reserved_pages = false;
- 1513       |         bool tracked = false;
- 1514       |         try {
- 1515       |             if (fixed) {
- 1516       |                 first_page = static_cast<u32>(address >> VM::PAGE_SIZE_BITS);
- 1517       |                 allocator.AllocateFixed(first_page, params.pages);
- 1518       |             } else {
- 1519       |                 first_page = allocator.Allocate(params.pages);
- 1520       |                 if (!first_page)
- 1521       |                     return NvResult::InsufficientMemory;
- 1522       |                 address = static_cast<u64>(first_page) << VM::PAGE_SIZE_BITS;
- 1523       |             }
- 1524       |             reserved_pages = true;
- 1525       |             const auto [it, inserted] = allocation_map.try_emplace(
- 1526       |                 address, Allocation{{}, size, VM::YUZU_PAGESIZE, true, false});
- 1527       |             if (!inserted) {
- 1528       |                 allocator.Free(first_page, params.pages);
- 1529       |                 return NvResult::BadValue;
- 1530       |             }
- 1531       |             tracked = true;
- 1532       |             // The last operation only marks GMMU pages Reserved, not
- 1533       |             // Mapped. A later fixed MapBufferEx/worker sparse remap is
- 1534       |             // responsible for real backing and the corresponding fence.
- 1535       |             try {
- 1536       |                 gmmu->MapSparse(address, size, false);
- 1537       |             } catch (const std::bad_alloc&) {
- 1538       |                 // The page-table operation may have partially reserved VA.
- 1539       |                 // Only release its ledger after undoing those GPU PTEs.
- 1540       |                 try {
- 1541       |                     gmmu->Unmap(address, size);
- 1542       |                 } catch (const std::bad_alloc&) {
- 1543       |                     // GMMU rollback failed after a partial MapSparse.
- 1544       |                     // Retain VA ownership and quarantine all further native
- 1545       |                     // mutations; an untracked live PTE must not be reused.
- 1546       |                     PoisonNativeAddressSpace();
- 1547       |                     return NvResult::InvalidState;
- 1548       |                 }
- 1549       |                 allocation_map.erase(address);
- 1550       |                 allocator.Free(first_page, params.pages);
- 1551       |                 return NvResult::InsufficientMemory;
- 1552       |             }
- 1553       |         } catch (const std::bad_alloc&) {
- 1554       |             if (tracked) allocation_map.erase(address);
- 1555       |             if (reserved_pages) allocator.Free(first_page, params.pages);
- 1556       |             return NvResult::InsufficientMemory;
- 1557       |         }
- 1558       |         params.offset = address;
- 1559       |         return NvResult::Success;
- 1560       |     }
- 1561       | 
- 1562       |     // NS2 regular 4K/big-page and big-page sparse reservations must not
- 1563       |     // publish a guest VA without a live owner in allocation_map. The
- 1564       |     // already-admitted native 4K sparse branch above is unchanged.
- 1565       |     // Legacy Maxwell follows its original path below.
- 1566       |     if (m_native_process &&
- 1567       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1568       |         constexpr u32 allowed_flags =
- 1569       |             static_cast<u32>(MappingFlags::Fixed) | static_cast<u32>(MappingFlags::Sparse);
- 1570       |         // The VA allocator counts 4K or negotiated big-page units.
- 1571       |         // An arbitrary page_size would reserve N small pages but publish
- 1572       |         // N*page_size bytes of GPU VA, aliasing an adjacent reservation.
- 1573       |         // Validate the exact page class BEFORE any allocator/GMMU change.
- 1574       |         if (!gmmu || !vm.small_page_allocator || !vm.big_page_allocator ||
- 1575       |             !params.pages ||
- 1576       |             (params.page_size != VM::YUZU_PAGESIZE &&
- 1577       |              params.page_size != vm.big_page_size) ||
- 1578       |             (static_cast<u32>(params.flags) & ~allowed_flags))
- 1579       |             return NvResult::BadValue;
- 1580       |         const bool big = params.page_size == vm.big_page_size;
- 1581       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 1582       |         const bool sparse = (params.flags & MappingFlags::Sparse) != MappingFlags::None;
- 1583       |         const u32 shift = big ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS;
- 1584       |         auto& allocator = big ? *vm.big_page_allocator : *vm.small_page_allocator;
- 1585       |         const u64 min_va = static_cast<u64>(allocator.GetVAStart()) << shift;
- 1586       |         const u64 max_va = static_cast<u64>(allocator.GetVALimit()) << shift;
- 1587       |         const u64 size = static_cast<u64>(params.pages) * params.page_size;
- 1588       |         if (min_va >= max_va || !size || size > max_va - min_va)
- 1589       |             return NvResult::InsufficientMemory;
- 1590       | 
- 1591       |         u64 address = fixed ? static_cast<u64>(params.offset) : 0;
- 1592       |         u32 start_page = 0;
- 1593       |         if (fixed) {
- 1594       |             if (address < min_va || address >= max_va ||
- 1595       |                 (address & (params.page_size - 1)) ||
- 1596       |                 size > max_va - address)
- 1597       |                 return NvResult::BadValue;
- 1598       |             const auto next_allocation = allocation_map.lower_bound(address);
- 1599       |             if ((next_allocation != allocation_map.end() &&
- 1600       |                  next_allocation->first < address + size) ||
- 1601       |                 (next_allocation != allocation_map.begin() &&
- 1602       |                  std::prev(next_allocation)->second.size >
- 1603       |                      address - std::prev(next_allocation)->first))
- 1604       |                 return NvResult::BadValue;
- 1605       |             const auto next_mapping = mapping_map.lower_bound(address);
- 1606       |             if ((next_mapping != mapping_map.end() &&
- 1607       |                  next_mapping->first < address + size) ||
- 1608       |                 (next_mapping != mapping_map.begin() &&
- 1609       |                  std::prev(next_mapping)->second.size >
- 1610       |                      address - std::prev(next_mapping)->first))
- 1611       |                 return NvResult::BadValue;
- 1612       |             start_page = static_cast<u32>(address >> shift);
- 1613       |         }
- 1614       | 
- 1615       |         bool reserved = false;
- 1616       |         try {
- 1617       |             if (fixed) {
- 1618       |                 allocator.AllocateFixed(start_page, params.pages);
- 1619       |             } else {
- 1620       |                 start_page = allocator.Allocate(params.pages);
- 1621       |                 if (!start_page) return NvResult::InsufficientMemory;
- 1622       |                 address = static_cast<u64>(start_page) << shift;
- 1623       |             }
- 1624       |             reserved = true;
- 1625       |             const auto [entry, inserted] = allocation_map.try_emplace(
- 1626       |                 address, Allocation{{}, size, params.page_size, sparse, big});
- 1627       |             (void)entry;
- 1628       |             if (!inserted) {
- 1629       |                 allocator.Free(start_page, params.pages);
+        564 |     if (params.page_size != VM::LICHII_PAGESIZE && params.page_size != vm.big_page_size) {
  1630   565 |                 return NvResult::BadValue;
  1631   566 |             }
- 1632       |         } catch (const std::bad_alloc&) {
- 1633       |             if (reserved) {
- 1634       |                 allocation_map.erase(address);
- 1635       |                 allocator.Free(start_page, params.pages);
- 1636       |             }
- 1637       |             return NvResult::InsufficientMemory;
- 1638       |         }
- 1639       |         if (sparse) {
- 1640       |             try {
- 1641       |                 gmmu->MapSparse(address, size, big);
- 1642       |             } catch (const std::bad_alloc&) {
- 1643       |                 // MapSparse may already have touched PTEs. Retain the
- 1644       |                 // reservation if the rollback itself cannot complete:
- 1645       |                 // freeing potentially live GPU VA would be unsafe.
- 1646       |                 try {
- 1647       |                     gmmu->Unmap(address, size);
- 1648       |                 } catch (const std::bad_alloc&) {
- 1649       |                     // The GMMU might still contain some reserved PTEs.
- 1650       |                     // Do not let a later ioctl overwrite these stale pages
- 1651       |                     // or release their owning VA on a second failed unwind.
- 1652       |                     PoisonNativeAddressSpace();
- 1653       |                     return NvResult::InvalidState;
- 1654       |                 }
- 1655       |                 allocation_map.erase(address);
- 1656       |                 allocator.Free(start_page, params.pages);
- 1657       |                 return NvResult::InsufficientMemory;
- 1658       |             }
- 1659       |         }
- 1660       |         params.offset = address;
- 1661       |         return NvResult::Success;
- 1662       |     }
  1663   567 | 
  1664   568 |     if (params.page_size != vm.big_page_size &&
  1665   569 |         ((params.flags & MappingFlags::Sparse) != MappingFlags::None)) {
  1666   570 |         UNIMPLEMENTED_MSG("Sparse small pages are not implemented!");
  1667   571 |         return NvResult::NotImplemented;
  1668   572 |     }
  1669   573 | 
- 1670       |     const u32 page_size_bits{params.page_size == VM::YUZU_PAGESIZE ? VM::PAGE_SIZE_BITS
+        574 |     const u32 page_size_bits{params.page_size == VM::LICHII_PAGESIZE ? VM::PAGE_SIZE_BITS
  1671   575 |                                                                    : vm.big_page_size_bits};
  1672   576 | 
- 1673       |     auto& allocator{params.page_size == VM::YUZU_PAGESIZE ? *vm.small_page_allocator
+        577 |     auto& allocator{params.page_size == VM::LICHII_PAGESIZE ? *vm.small_page_allocator
  1674   578 |                                                           : *vm.big_page_allocator};
  1675   579 | 
  1676   580 |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
  1677   581 |         allocator.AllocateFixed(static_cast<u32>(params.offset >> page_size_bits), params.pages);
  1678   582 |     } else {
  1679   583 |         params.offset = static_cast<u64>(allocator.Allocate(params.pages)) << page_size_bits;
  1680   584 |         if (!params.offset) {
  1681   585 |             ASSERT_MSG(false, "Failed to allocate free space in the GPU AS!");
  1682   586 |             return NvResult::InsufficientMemory;
  1683   587 |         }
  1684   588 |     }
  1685   589 | 
  1686   590 |     u64 size{static_cast<u64>(params.pages) * params.page_size};
  1687   591 | 
  1688   592 |     if ((params.flags & MappingFlags::Sparse) != MappingFlags::None) {
  1689   593 |         gmmu->MapSparse(params.offset, size);
  1690   594 |     }
  1691   595 | 
  1692   596 |     allocation_map[params.offset] = {
  1693   597 |         .mappings{},
  1694   598 |         .size = size,
  1695   599 |         .page_size = params.page_size,
  1696   600 |         .sparse = (params.flags & MappingFlags::Sparse) != MappingFlags::None,
- 1697       |         .big_pages = params.page_size != VM::YUZU_PAGESIZE,
+        601 |         .big_pages = params.page_size != VM::LICHII_PAGESIZE,
  1698   602 |     };
  1699   603 | 
  1700   604 |     return NvResult::Success;
  1701   605 | }
```

</details>

<details>
<summary>EglantinePS5 — 483–534 : 52 alignées, 205 propres Encore, 0 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:483–534](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L483-L534).

```diff
  1445   483 | NvResult nvhost_as_gpu::AllocateSpace(IoctlAllocSpace& params) {
  1446   484 |     LOG_DEBUG(Service_NVDRV, "called, pages={:X}, page_size={:X}, flags={:X}", params.pages,
  1447   485 |               params.page_size, params.flags);
  1448   486 | 
  1449   487 |     std::scoped_lock lock(mutex);
  1450   488 | 
- 1451       |     if (native_sparse_poisoned && m_native_process &&
- 1452       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 1453       |         return NvResult::InvalidState;
  1454   489 |     if (!vm.initialised) {
  1455   490 |         return NvResult::BadValue;
  1456   491 |     }
  1457   492 | 
  1458   493 |     if (params.page_size != VM::YUZU_PAGESIZE && params.page_size != vm.big_page_size) {
  1459   494 |         return NvResult::BadValue;
  1460   495 |     }
  1461   496 | 
- 1462       |     // Native GA10F can reserve sparse 4-KiB GPU VA without backing physical
- 1463       |     // pages. The original Maxwell ioctl below deliberately keeps its legacy
- 1464       |     // unsupported-small-sparse contract; never select this path by Title ID.
- 1465       |     const bool small_sparse =
- 1466       |         params.page_size == VM::YUZU_PAGESIZE &&
- 1467       |         ((params.flags & MappingFlags::Sparse) != MappingFlags::None);
- 1468       |     if (small_sparse && m_native_process &&
- 1469       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1470       |         if (!gmmu || !vm.small_page_allocator || params.pages == 0)
- 1471       |             return NvResult::BadValue;
- 1472       |         constexpr u32 allowed_flags =
- 1473       |             static_cast<u32>(MappingFlags::Fixed) | static_cast<u32>(MappingFlags::Sparse);
- 1474       |         if ((static_cast<u32>(params.flags) & ~allowed_flags) != 0)
- 1475       |             return NvResult::BadValue;
- 1476       | 
- 1477       |         // All VA arithmetic is 64-bit; the actual allocator stores 4K page
- 1478       |         // numbers in u32. A reservation never commits pages or pins NVMap.
- 1479       |         auto& allocator = *vm.small_page_allocator;
- 1480       |         const u64 first_va = static_cast<u64>(allocator.GetVAStart()) << VM::PAGE_SIZE_BITS;
- 1481       |         const u64 limit_va = static_cast<u64>(allocator.GetVALimit()) << VM::PAGE_SIZE_BITS;
- 1482       |         const u64 size = static_cast<u64>(params.pages) * VM::YUZU_PAGESIZE;
- 1483       |         if (size > limit_va - first_va)
- 1484       |             return NvResult::InsufficientMemory;
- 1485       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 1486       |         u64 address = fixed ? static_cast<u64>(params.offset) : 0;
- 1487       |         if (fixed) {
- 1488       |             if (address < first_va || address >= limit_va ||
- 1489       |                 (address & (VM::YUZU_PAGESIZE - 1)) != 0 ||
- 1490       |                 size > limit_va - address)
- 1491       |                 return NvResult::BadValue;
- 1492       |             // FlatAllocator::AllocateFixed does not reject an overlapping
- 1493       |             // reservation itself. An alias must not steal another guest VA,
- 1494       |             // including existing fixed maps from MapBufferEx.
- 1495       |             const auto reserved = allocation_map.lower_bound(address);
- 1496       |             if ((reserved != allocation_map.end() &&
- 1497       |                  reserved->first < address + size) ||
- 1498       |                 (reserved != allocation_map.begin() &&
- 1499       |                  std::prev(reserved)->second.size >
- 1500       |                      address - std::prev(reserved)->first))
- 1501       |                 return NvResult::BadValue;
- 1502       |             const auto mapped = mapping_map.lower_bound(address);
- 1503       |             if ((mapped != mapping_map.end() &&
- 1504       |                  mapped->first < address + size) ||
- 1505       |                 (mapped != mapping_map.begin() &&
- 1506       |                  std::prev(mapped)->second.size >
- 1507       |                      address - std::prev(mapped)->first))
- 1508       |                 return NvResult::BadValue;
- 1509       |         }
- 1510       | 
- 1511       |         u32 first_page{};
- 1512       |         bool reserved_pages = false;
- 1513       |         bool tracked = false;
- 1514       |         try {
- 1515       |             if (fixed) {
- 1516       |                 first_page = static_cast<u32>(address >> VM::PAGE_SIZE_BITS);
- 1517       |                 allocator.AllocateFixed(first_page, params.pages);
- 1518       |             } else {
- 1519       |                 first_page = allocator.Allocate(params.pages);
- 1520       |                 if (!first_page)
- 1521       |                     return NvResult::InsufficientMemory;
- 1522       |                 address = static_cast<u64>(first_page) << VM::PAGE_SIZE_BITS;
- 1523       |             }
- 1524       |             reserved_pages = true;
- 1525       |             const auto [it, inserted] = allocation_map.try_emplace(
- 1526       |                 address, Allocation{{}, size, VM::YUZU_PAGESIZE, true, false});
- 1527       |             if (!inserted) {
- 1528       |                 allocator.Free(first_page, params.pages);
- 1529       |                 return NvResult::BadValue;
- 1530       |             }
- 1531       |             tracked = true;
- 1532       |             // The last operation only marks GMMU pages Reserved, not
- 1533       |             // Mapped. A later fixed MapBufferEx/worker sparse remap is
- 1534       |             // responsible for real backing and the corresponding fence.
- 1535       |             try {
- 1536       |                 gmmu->MapSparse(address, size, false);
- 1537       |             } catch (const std::bad_alloc&) {
- 1538       |                 // The page-table operation may have partially reserved VA.
- 1539       |                 // Only release its ledger after undoing those GPU PTEs.
- 1540       |                 try {
- 1541       |                     gmmu->Unmap(address, size);
- 1542       |                 } catch (const std::bad_alloc&) {
- 1543       |                     // GMMU rollback failed after a partial MapSparse.
- 1544       |                     // Retain VA ownership and quarantine all further native
- 1545       |                     // mutations; an untracked live PTE must not be reused.
- 1546       |                     PoisonNativeAddressSpace();
- 1547       |                     return NvResult::InvalidState;
- 1548       |                 }
- 1549       |                 allocation_map.erase(address);
- 1550       |                 allocator.Free(first_page, params.pages);
- 1551       |                 return NvResult::InsufficientMemory;
- 1552       |             }
- 1553       |         } catch (const std::bad_alloc&) {
- 1554       |             if (tracked) allocation_map.erase(address);
- 1555       |             if (reserved_pages) allocator.Free(first_page, params.pages);
- 1556       |             return NvResult::InsufficientMemory;
- 1557       |         }
- 1558       |         params.offset = address;
- 1559       |         return NvResult::Success;
- 1560       |     }
- 1561       | 
- 1562       |     // NS2 regular 4K/big-page and big-page sparse reservations must not
- 1563       |     // publish a guest VA without a live owner in allocation_map. The
- 1564       |     // already-admitted native 4K sparse branch above is unchanged.
- 1565       |     // Legacy Maxwell follows its original path below.
- 1566       |     if (m_native_process &&
- 1567       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1568       |         constexpr u32 allowed_flags =
- 1569       |             static_cast<u32>(MappingFlags::Fixed) | static_cast<u32>(MappingFlags::Sparse);
- 1570       |         // The VA allocator counts 4K or negotiated big-page units.
- 1571       |         // An arbitrary page_size would reserve N small pages but publish
- 1572       |         // N*page_size bytes of GPU VA, aliasing an adjacent reservation.
- 1573       |         // Validate the exact page class BEFORE any allocator/GMMU change.
- 1574       |         if (!gmmu || !vm.small_page_allocator || !vm.big_page_allocator ||
- 1575       |             !params.pages ||
- 1576       |             (params.page_size != VM::YUZU_PAGESIZE &&
- 1577       |              params.page_size != vm.big_page_size) ||
- 1578       |             (static_cast<u32>(params.flags) & ~allowed_flags))
- 1579       |             return NvResult::BadValue;
- 1580       |         const bool big = params.page_size == vm.big_page_size;
- 1581       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 1582       |         const bool sparse = (params.flags & MappingFlags::Sparse) != MappingFlags::None;
- 1583       |         const u32 shift = big ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS;
- 1584       |         auto& allocator = big ? *vm.big_page_allocator : *vm.small_page_allocator;
- 1585       |         const u64 min_va = static_cast<u64>(allocator.GetVAStart()) << shift;
- 1586       |         const u64 max_va = static_cast<u64>(allocator.GetVALimit()) << shift;
- 1587       |         const u64 size = static_cast<u64>(params.pages) * params.page_size;
- 1588       |         if (min_va >= max_va || !size || size > max_va - min_va)
- 1589       |             return NvResult::InsufficientMemory;
- 1590       | 
- 1591       |         u64 address = fixed ? static_cast<u64>(params.offset) : 0;
- 1592       |         u32 start_page = 0;
- 1593       |         if (fixed) {
- 1594       |             if (address < min_va || address >= max_va ||
- 1595       |                 (address & (params.page_size - 1)) ||
- 1596       |                 size > max_va - address)
- 1597       |                 return NvResult::BadValue;
- 1598       |             const auto next_allocation = allocation_map.lower_bound(address);
- 1599       |             if ((next_allocation != allocation_map.end() &&
- 1600       |                  next_allocation->first < address + size) ||
- 1601       |                 (next_allocation != allocation_map.begin() &&
- 1602       |                  std::prev(next_allocation)->second.size >
- 1603       |                      address - std::prev(next_allocation)->first))
- 1604       |                 return NvResult::BadValue;
- 1605       |             const auto next_mapping = mapping_map.lower_bound(address);
- 1606       |             if ((next_mapping != mapping_map.end() &&
- 1607       |                  next_mapping->first < address + size) ||
- 1608       |                 (next_mapping != mapping_map.begin() &&
- 1609       |                  std::prev(next_mapping)->second.size >
- 1610       |                      address - std::prev(next_mapping)->first))
- 1611       |                 return NvResult::BadValue;
- 1612       |             start_page = static_cast<u32>(address >> shift);
- 1613       |         }
- 1614       | 
- 1615       |         bool reserved = false;
- 1616       |         try {
- 1617       |             if (fixed) {
- 1618       |                 allocator.AllocateFixed(start_page, params.pages);
- 1619       |             } else {
- 1620       |                 start_page = allocator.Allocate(params.pages);
- 1621       |                 if (!start_page) return NvResult::InsufficientMemory;
- 1622       |                 address = static_cast<u64>(start_page) << shift;
- 1623       |             }
- 1624       |             reserved = true;
- 1625       |             const auto [entry, inserted] = allocation_map.try_emplace(
- 1626       |                 address, Allocation{{}, size, params.page_size, sparse, big});
- 1627       |             (void)entry;
- 1628       |             if (!inserted) {
- 1629       |                 allocator.Free(start_page, params.pages);
- 1630       |                 return NvResult::BadValue;
- 1631       |             }
- 1632       |         } catch (const std::bad_alloc&) {
- 1633       |             if (reserved) {
- 1634       |                 allocation_map.erase(address);
- 1635       |                 allocator.Free(start_page, params.pages);
- 1636       |             }
- 1637       |             return NvResult::InsufficientMemory;
- 1638       |         }
- 1639       |         if (sparse) {
- 1640       |             try {
- 1641       |                 gmmu->MapSparse(address, size, big);
- 1642       |             } catch (const std::bad_alloc&) {
- 1643       |                 // MapSparse may already have touched PTEs. Retain the
- 1644       |                 // reservation if the rollback itself cannot complete:
- 1645       |                 // freeing potentially live GPU VA would be unsafe.
- 1646       |                 try {
- 1647       |                     gmmu->Unmap(address, size);
- 1648       |                 } catch (const std::bad_alloc&) {
- 1649       |                     // The GMMU might still contain some reserved PTEs.
- 1650       |                     // Do not let a later ioctl overwrite these stale pages
- 1651       |                     // or release their owning VA on a second failed unwind.
- 1652       |                     PoisonNativeAddressSpace();
- 1653       |                     return NvResult::InvalidState;
- 1654       |                 }
- 1655       |                 allocation_map.erase(address);
- 1656       |                 allocator.Free(start_page, params.pages);
- 1657       |                 return NvResult::InsufficientMemory;
- 1658       |             }
- 1659       |         }
- 1660       |         params.offset = address;
- 1661       |         return NvResult::Success;
- 1662       |     }
- 1663       | 
  1664   497 |     if (params.page_size != vm.big_page_size &&
  1665   498 |         ((params.flags & MappingFlags::Sparse) != MappingFlags::None)) {
  1666   499 |         UNIMPLEMENTED_MSG("Sparse small pages are not implemented!");
  1667   500 |         return NvResult::NotImplemented;
  1668   501 |     }
  1669   502 | 
  1670   503 |     const u32 page_size_bits{params.page_size == VM::YUZU_PAGESIZE ? VM::PAGE_SIZE_BITS
  1671   504 |                                                                    : vm.big_page_size_bits};
  1672   505 | 
  1673   506 |     auto& allocator{params.page_size == VM::YUZU_PAGESIZE ? *vm.small_page_allocator
  1674   507 |                                                           : *vm.big_page_allocator};
  1675   508 | 
  1676   509 |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
  1677   510 |         allocator.AllocateFixed(static_cast<u32>(params.offset >> page_size_bits), params.pages);
  1678   511 |     } else {
  1679   512 |         params.offset = static_cast<u64>(allocator.Allocate(params.pages)) << page_size_bits;
  1680   513 |         if (!params.offset) {
  1681   514 |             ASSERT_MSG(false, "Failed to allocate free space in the GPU AS!");
  1682   515 |             return NvResult::InsufficientMemory;
  1683   516 |         }
  1684   517 |     }
  1685   518 | 
  1686   519 |     u64 size{static_cast<u64>(params.pages) * params.page_size};
  1687   520 | 
  1688   521 |     if ((params.flags & MappingFlags::Sparse) != MappingFlags::None) {
  1689   522 |         gmmu->MapSparse(params.offset, size);
  1690   523 |     }
  1691   524 | 
  1692   525 |     allocation_map[params.offset] = {
  1693   526 |         .mappings{},
  1694   527 |         .size = size,
  1695   528 |         .page_size = params.page_size,
  1696   529 |         .sparse = (params.flags & MappingFlags::Sparse) != MappingFlags::None,
  1697   530 |         .big_pages = params.page_size != VM::YUZU_PAGESIZE,
  1698   531 |     };
  1699   532 | 
  1700   533 |     return NvResult::Success;
  1701   534 | }
```

</details>

### P0-M02 · AS-GPU FreeSpace

Point critique de durée de vie : retrait de mapping, désenregistrement et libération VA. Une différence n'est un bug que si elle laisse une traduction ou une référence survivre à la libération.

Encore : [nvhost_as_gpu.cpp:1765–1844](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L1765-L1844) — 80 lignes.

<details>
<summary>Lichii — 631–658 : 21 alignées, 59 propres Encore, 7 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:631–658](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L631-L658).

```diff
  1765   631 | NvResult nvhost_as_gpu::FreeSpace(IoctlFreeSpace& params) {
  1766   632 |     LOG_DEBUG(Service_NVDRV, "called, offset={:X}, pages={:X}, page_size={:X}", params.offset, params.pages, params.page_size);
- 1767       |     // A native GPU free retires GMMU PTEs and may drop the last NVMap
- 1768       |     // physical pin. A queued GPU command could still dereference that PA.
- 1769       |     // Drain BEFORE taking the AS mutex: GPU command processing can query
- 1770       |     // these page tables while WaitForIdle() runs. NS1 stays unchanged.
- 1771       |     if (m_native_process &&
- 1772       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 1773       |         system.IsPoweredOn() && !system.IsShuttingDown())
- 1774       |         system.GPU().WaitForIdle();
  1775   633 |     std::scoped_lock lock(mutex);
  1776   634 |     if (!vm.initialised) {
  1777   635 |         return NvResult::BadValue;
  1778   636 |     }
- 1779       |     if (native_sparse_regions.contains(params.offset))
- 1780       |         return NvResult::BadParameter;
- 1781       |     if (native_sparse_poisoned && m_native_process &&
- 1782       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 1783       |         return NvResult::InvalidState;
  1784   637 |     if (auto const it = allocation_map.find(params.offset); it != allocation_map.end()) {
- 1785       |         // FreeSpace holds the AS mutex throughout retirement; no other
- 1786       |         // caller may mutate this allocation vector. Avoid copying the
- 1787       |         // entire owner ledger on a P0 memory-pressure exit path.
- 1788       |         const auto& allocation = it->second;
+        638 |         auto const allocation = it->second;
  1789   639 |         if (allocation.page_size != params.page_size || allocation.size != (u64(params.pages) * params.page_size))
  1790   640 |             return NvResult::BadValue;
  1791   641 | 
- 1792       |         // Native A:14 and GSV 216 share the sparse range/pin registry.
- 1793       |         // Reserve all needed host nodes before unmapping any guest PTE.
- 1794       |         NativeSparseMappingTable updated_sparse;
- 1795       |         std::set<u32> retained_handles;
- 1796       |         const bool native_sparse = allocation.sparse && m_native_process &&
- 1797       |                                    NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 1798       |         if (native_sparse) {
- 1799       |             try {
- 1800       |                 updated_sparse = native_sparse_mappings;
- 1801       |                 updated_sparse.Replace(NativeSparseRange{
- 1802       |                     static_cast<u64>(params.offset), allocation.size, 0, 0});
- 1803       |                 retained_handles = updated_sparse.ReferencedHandles();
- 1804       |             } catch (const std::bad_alloc&) {
- 1805       |                 return NvResult::InsufficientMemory;
- 1806       |             }
+        642 |         for (const auto mapping_offset : allocation.mappings) {
+        643 |             void(FreeMappingLocked(mapping_offset));
  1807   644 |         }
  1808   645 | 
- 1809       |         for (const auto mapping_offset : allocation.mappings)
- 1810       |             if (!FreeMappingLocked(mapping_offset))
- 1811       |                 return NvResult::BadValue;
- 1812       | 
- 1813       |         // Always retire GPU PTEs BEFORE dropping their pinned NVMap memory.
- 1814       |         if (allocation.sparse) {
- 1815       |             if (native_sparse) {
- 1816       |                 try {
- 1817       |                     gmmu->Unmap(params.offset, allocation.size);
- 1818       |                 } catch (const std::bad_alloc&) {
- 1819       |                     // Retain the ledger and pins on an incomplete unmap.
- 1820       |                     PoisonNativeAddressSpace();
- 1821       |                     return NvResult::InvalidState;
- 1822       |                 }
- 1823       |             } else {
+        646 |         // Unset sparse flag if required
+        647 |         if (allocation.sparse)
  1824   648 |                 gmmu->Unmap(params.offset, allocation.size);
- 1825       |             }
- 1826       |         }
- 1827       |         if (native_sparse) {
- 1828       |             native_sparse_mappings = std::move(updated_sparse);
- 1829       |             for (auto pin = native_sparse_pins.begin(); pin != native_sparse_pins.end();) {
- 1830       |                 if (retained_handles.contains(pin->first)) { ++pin; continue; }
- 1831       |                 nvmap.UnpinHandle(pin->first);
- 1832       |                 pin = native_sparse_pins.erase(pin);
- 1833       |             }
- 1834       |         }
  1835   649 | 
- 1836       |         auto& allocator{params.page_size == VM::YUZU_PAGESIZE ? *vm.small_page_allocator : *vm.big_page_allocator};
- 1837       |         u32 page_size_bits{params.page_size == VM::YUZU_PAGESIZE ? VM::PAGE_SIZE_BITS : vm.big_page_size_bits};
+        650 |         auto& allocator{params.page_size == VM::LICHII_PAGESIZE ? *vm.small_page_allocator : *vm.big_page_allocator};
+        651 |         u32 page_size_bits{params.page_size == VM::LICHII_PAGESIZE ? VM::PAGE_SIZE_BITS : vm.big_page_size_bits};
  1838   652 | 
  1839   653 |         allocator.Free(u32(params.offset >> page_size_bits), u32(allocation.size >> page_size_bits));
  1840   654 |         allocation_map.erase(params.offset);
  1841   655 |         return NvResult::Success;
  1842   656 |     }
  1843   657 |     return NvResult::BadValue;
  1844   658 | }
```

</details>

<details>
<summary>EglantinePS5 — 560–587 : 25 alignées, 55 propres Encore, 3 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:560–587](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L560-L587).

```diff
  1765   560 | NvResult nvhost_as_gpu::FreeSpace(IoctlFreeSpace& params) {
  1766   561 |     LOG_DEBUG(Service_NVDRV, "called, offset={:X}, pages={:X}, page_size={:X}", params.offset, params.pages, params.page_size);
- 1767       |     // A native GPU free retires GMMU PTEs and may drop the last NVMap
- 1768       |     // physical pin. A queued GPU command could still dereference that PA.
- 1769       |     // Drain BEFORE taking the AS mutex: GPU command processing can query
- 1770       |     // these page tables while WaitForIdle() runs. NS1 stays unchanged.
- 1771       |     if (m_native_process &&
- 1772       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 1773       |         system.IsPoweredOn() && !system.IsShuttingDown())
- 1774       |         system.GPU().WaitForIdle();
  1775   562 |     std::scoped_lock lock(mutex);
  1776   563 |     if (!vm.initialised) {
  1777   564 |         return NvResult::BadValue;
  1778   565 |     }
- 1779       |     if (native_sparse_regions.contains(params.offset))
- 1780       |         return NvResult::BadParameter;
- 1781       |     if (native_sparse_poisoned && m_native_process &&
- 1782       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 1783       |         return NvResult::InvalidState;
  1784   566 |     if (auto const it = allocation_map.find(params.offset); it != allocation_map.end()) {
- 1785       |         // FreeSpace holds the AS mutex throughout retirement; no other
- 1786       |         // caller may mutate this allocation vector. Avoid copying the
- 1787       |         // entire owner ledger on a P0 memory-pressure exit path.
- 1788       |         const auto& allocation = it->second;
+        567 |         auto const allocation = it->second;
  1789   568 |         if (allocation.page_size != params.page_size || allocation.size != (u64(params.pages) * params.page_size))
  1790   569 |             return NvResult::BadValue;
  1791   570 | 
- 1792       |         // Native A:14 and GSV 216 share the sparse range/pin registry.
- 1793       |         // Reserve all needed host nodes before unmapping any guest PTE.
- 1794       |         NativeSparseMappingTable updated_sparse;
- 1795       |         std::set<u32> retained_handles;
- 1796       |         const bool native_sparse = allocation.sparse && m_native_process &&
- 1797       |                                    NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 1798       |         if (native_sparse) {
- 1799       |             try {
- 1800       |                 updated_sparse = native_sparse_mappings;
- 1801       |                 updated_sparse.Replace(NativeSparseRange{
- 1802       |                     static_cast<u64>(params.offset), allocation.size, 0, 0});
- 1803       |                 retained_handles = updated_sparse.ReferencedHandles();
- 1804       |             } catch (const std::bad_alloc&) {
- 1805       |                 return NvResult::InsufficientMemory;
- 1806       |             }
- 1807       |         }
- 1808       | 
  1809   571 |         for (const auto mapping_offset : allocation.mappings)
  1810   572 |             if (!FreeMappingLocked(mapping_offset))
  1811   573 |                 return NvResult::BadValue;
  1812   574 | 
- 1813       |         // Always retire GPU PTEs BEFORE dropping their pinned NVMap memory.
- 1814       |         if (allocation.sparse) {
- 1815       |             if (native_sparse) {
- 1816       |                 try {
- 1817       |                     gmmu->Unmap(params.offset, allocation.size);
- 1818       |                 } catch (const std::bad_alloc&) {
- 1819       |                     // Retain the ledger and pins on an incomplete unmap.
- 1820       |                     PoisonNativeAddressSpace();
- 1821       |                     return NvResult::InvalidState;
- 1822       |                 }
- 1823       |             } else {
+        575 |         // Unset sparse flag if required
+        576 |         if (allocation.sparse)
  1824   577 |                 gmmu->Unmap(params.offset, allocation.size);
- 1825       |             }
- 1826       |         }
- 1827       |         if (native_sparse) {
- 1828       |             native_sparse_mappings = std::move(updated_sparse);
- 1829       |             for (auto pin = native_sparse_pins.begin(); pin != native_sparse_pins.end();) {
- 1830       |                 if (retained_handles.contains(pin->first)) { ++pin; continue; }
- 1831       |                 nvmap.UnpinHandle(pin->first);
- 1832       |                 pin = native_sparse_pins.erase(pin);
- 1833       |             }
- 1834       |         }
  1835   578 | 
  1836   579 |         auto& allocator{params.page_size == VM::YUZU_PAGESIZE ? *vm.small_page_allocator : *vm.big_page_allocator};
  1837   580 |         u32 page_size_bits{params.page_size == VM::YUZU_PAGESIZE ? VM::PAGE_SIZE_BITS : vm.big_page_size_bits};
  1838   581 | 
  1839   582 |         allocator.Free(u32(params.offset >> page_size_bits), u32(allocation.size >> page_size_bits));
  1840   583 |         allocation_map.erase(params.offset);
  1841   584 |         return NvResult::Success;
  1842   585 |     }
  1843   586 |     return NvResult::BadValue;
  1844   587 | }
```

</details>

### P0-M03 · AS-GPU Remap

Le remap est directement pertinent aux mappings sparse NS2. Relever séparément validation des entrées, kind, source offset, batch et ordre map/unmap ; ne pas déduire une équivalence d'un simple ResultSuccess.

Encore : [nvhost_as_gpu.cpp:1846–1934](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L1846-L1934) — 89 lignes.

<details>
<summary>Lichii — 660–704 : 38 alignées, 51 propres Encore, 7 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:660–704](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L660-L704).

```diff
  1846   660 | NvResult nvhost_as_gpu::Remap(std::span<IoctlRemapEntry> entries) {
  1847   661 |     LOG_DEBUG(Service_NVDRV, "called, num_entries={:#x}", entries.size());
  1848   662 | 
- 1849       |     if (m_native_process &&
- 1850       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1851       |         // Native NVDRV A:14 shares the same transactional pin and mapping
- 1852       |         // table with GSV 216. Legacy A:14 pinned on every remap but never
- 1853       |         // recorded enough ownership to retire the backing.
- 1854       |         if (entries.empty()) return NvResult::Success;
- 1855       |         if (entries.size() > 256) return NvResult::BadParameter;
- 1856       |         if (!vm.initialised) return NvResult::InvalidState;
- 1857       |         std::vector<NativeSparseRemapEntry> transaction;
- 1858       |         try {
- 1859       |             transaction.reserve(entries.size());
- 1860       |             for (const auto& entry : entries) {
- 1861       |                 // SwitchBrew A:14 remap_op flags bit2 controls
- 1862       |                 // cacheability. Accept it without mistaking it for a
- 1863       |                 // page-size selector or an unknown command bit.
- 1864       |                 if ((u32{entry.flags} & ~0x4U) || !entry.big_pages ||
- 1865       |                     entry.kind > std::numeric_limits<u8>::max())
- 1866       |                     return NvResult::BadParameter;
- 1867       |                 NativeSparseRemapEntry item{};
- 1868       |                 item.flags = (vm.big_page_size_bits == 16 ? 0x2000U : 0x4000U) |
- 1869       |                              (u32{entry.flags} & 0x4U);
- 1870       |                 item.kind = entry.kind;
- 1871       |                 item.fallback_kind = entry.kind;
- 1872       |                 item.handle = entry.handle;
- 1873       |                 item.source_pages = entry.handle ? u64{entry.handle_offset_big_pages} : u64{0};
- 1874       |                 item.destination_pages = entry.as_offset_big_pages;
- 1875       |                 item.pages = entry.big_pages;
- 1876       |                 transaction.push_back(item);
- 1877       |             }
- 1878       |         } catch (const std::bad_alloc&) {
- 1879       |             return NvResult::InsufficientMemory;
- 1880       |         }
- 1881       |         // The guest can have already queued reads of the old big-page
- 1882       |         // backing. Retire those commands before changing their GMMU PTEs.
- 1883       |         // GSV 216 has the same wait-before-remap contract; no NS1 wait.
- 1884       |         if (system.IsPoweredOn() && !system.IsShuttingDown())
- 1885       |             system.GPU().WaitForIdle();
- 1886       |         return RemapNativeSparse(transaction);
- 1887       |     }
- 1888       | 
  1889   663 |     if (!vm.initialised) {
  1890   664 |         return NvResult::BadValue;
  1891   665 |     }
  1892   666 | 
  1893   667 |     for (const auto& entry : entries) {
  1894   668 |         GPUVAddr virtual_address{static_cast<u64>(entry.as_offset_big_pages)
  1895   669 |                                  << vm.big_page_size_bits};
  1896   670 |         u64 size{static_cast<u64>(entry.big_pages) << vm.big_page_size_bits};
  1897   671 | 
- 1898       |         const auto alloc = NativeGpuAllocation::FindContaining(
- 1899       |             allocation_map, virtual_address, size);
- 1900       |         if (alloc == allocation_map.end()) {
+        672 |         auto alloc{allocation_map.upper_bound(virtual_address)};
+        673 | 
+        674 |         if (alloc-- == allocation_map.begin() ||
+        675 |             (virtual_address - alloc->first) + size > alloc->second.size) {
  1901   676 |             LOG_WARNING(Service_NVDRV, "Cannot remap into an unallocated region!");
  1902   677 |             return NvResult::BadValue;
  1903   678 |         }
  1904   679 | 
  1905   680 |         if (!alloc->second.sparse) {
  1906   681 |             LOG_WARNING(Service_NVDRV, "Cannot remap a non-sparse mapping!");
  1907   682 |             return NvResult::BadValue;
  1908   683 |         }
  1909   684 | 
  1910   685 |         const bool use_big_pages = alloc->second.big_pages;
  1911   686 |         if (!entry.handle) {
  1912   687 |             gmmu->MapSparse(virtual_address, size, use_big_pages);
  1913   688 |         } else {
  1914   689 |             auto handle{nvmap.GetHandle(entry.handle)};
  1915   690 |             if (!handle) {
  1916   691 |                 return NvResult::BadValue;
  1917   692 |             }
  1918   693 | 
- 1919       |             const DAddr base = nvmap.PinHandle(entry.handle, false);
- 1920       |             const u64 source = static_cast<u64>(entry.handle_offset_big_pages)
- 1921       |                                << vm.big_page_size_bits;
- 1922       |             if (!NativePinnedPhysicalSpan(base, source, size)) {
- 1923       |                 if (base) nvmap.UnpinHandle(entry.handle);
- 1924       |                 return NvResult::InsufficientMemory;
- 1925       |             }
- 1926       |             const DAddr device_address = base + source;
+        694 |             DAddr base = nvmap.PinHandle(entry.handle, false);
+        695 |             DAddr device_address{static_cast<DAddr>(
+        696 |                 base + (static_cast<u64>(entry.handle_offset_big_pages) << vm.big_page_size_bits))};
  1927   697 | 
  1928   698 |             gmmu->Map(virtual_address, device_address, size,
  1929   699 |                       static_cast<Tegra::PTEKind>(entry.kind), use_big_pages);
  1930   700 |         }
  1931   701 |     }
  1932   702 | 
  1933   703 |     return NvResult::Success;
  1934   704 | }
```

</details>

<details>
<summary>EglantinePS5 — 589–633 : 38 alignées, 51 propres Encore, 7 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:589–633](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L589-L633).

```diff
  1846   589 | NvResult nvhost_as_gpu::Remap(std::span<IoctlRemapEntry> entries) {
  1847   590 |     LOG_DEBUG(Service_NVDRV, "called, num_entries={:#x}", entries.size());
  1848   591 | 
- 1849       |     if (m_native_process &&
- 1850       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process)) {
- 1851       |         // Native NVDRV A:14 shares the same transactional pin and mapping
- 1852       |         // table with GSV 216. Legacy A:14 pinned on every remap but never
- 1853       |         // recorded enough ownership to retire the backing.
- 1854       |         if (entries.empty()) return NvResult::Success;
- 1855       |         if (entries.size() > 256) return NvResult::BadParameter;
- 1856       |         if (!vm.initialised) return NvResult::InvalidState;
- 1857       |         std::vector<NativeSparseRemapEntry> transaction;
- 1858       |         try {
- 1859       |             transaction.reserve(entries.size());
- 1860       |             for (const auto& entry : entries) {
- 1861       |                 // SwitchBrew A:14 remap_op flags bit2 controls
- 1862       |                 // cacheability. Accept it without mistaking it for a
- 1863       |                 // page-size selector or an unknown command bit.
- 1864       |                 if ((u32{entry.flags} & ~0x4U) || !entry.big_pages ||
- 1865       |                     entry.kind > std::numeric_limits<u8>::max())
- 1866       |                     return NvResult::BadParameter;
- 1867       |                 NativeSparseRemapEntry item{};
- 1868       |                 item.flags = (vm.big_page_size_bits == 16 ? 0x2000U : 0x4000U) |
- 1869       |                              (u32{entry.flags} & 0x4U);
- 1870       |                 item.kind = entry.kind;
- 1871       |                 item.fallback_kind = entry.kind;
- 1872       |                 item.handle = entry.handle;
- 1873       |                 item.source_pages = entry.handle ? u64{entry.handle_offset_big_pages} : u64{0};
- 1874       |                 item.destination_pages = entry.as_offset_big_pages;
- 1875       |                 item.pages = entry.big_pages;
- 1876       |                 transaction.push_back(item);
- 1877       |             }
- 1878       |         } catch (const std::bad_alloc&) {
- 1879       |             return NvResult::InsufficientMemory;
- 1880       |         }
- 1881       |         // The guest can have already queued reads of the old big-page
- 1882       |         // backing. Retire those commands before changing their GMMU PTEs.
- 1883       |         // GSV 216 has the same wait-before-remap contract; no NS1 wait.
- 1884       |         if (system.IsPoweredOn() && !system.IsShuttingDown())
- 1885       |             system.GPU().WaitForIdle();
- 1886       |         return RemapNativeSparse(transaction);
- 1887       |     }
- 1888       | 
  1889   592 |     if (!vm.initialised) {
  1890   593 |         return NvResult::BadValue;
  1891   594 |     }
  1892   595 | 
  1893   596 |     for (const auto& entry : entries) {
  1894   597 |         GPUVAddr virtual_address{static_cast<u64>(entry.as_offset_big_pages)
  1895   598 |                                  << vm.big_page_size_bits};
  1896   599 |         u64 size{static_cast<u64>(entry.big_pages) << vm.big_page_size_bits};
  1897   600 | 
- 1898       |         const auto alloc = NativeGpuAllocation::FindContaining(
- 1899       |             allocation_map, virtual_address, size);
- 1900       |         if (alloc == allocation_map.end()) {
+        601 |         auto alloc{allocation_map.upper_bound(virtual_address)};
+        602 | 
+        603 |         if (alloc-- == allocation_map.begin() ||
+        604 |             (virtual_address - alloc->first) + size > alloc->second.size) {
  1901   605 |             LOG_WARNING(Service_NVDRV, "Cannot remap into an unallocated region!");
  1902   606 |             return NvResult::BadValue;
  1903   607 |         }
  1904   608 | 
  1905   609 |         if (!alloc->second.sparse) {
  1906   610 |             LOG_WARNING(Service_NVDRV, "Cannot remap a non-sparse mapping!");
  1907   611 |             return NvResult::BadValue;
  1908   612 |         }
  1909   613 | 
  1910   614 |         const bool use_big_pages = alloc->second.big_pages;
  1911   615 |         if (!entry.handle) {
  1912   616 |             gmmu->MapSparse(virtual_address, size, use_big_pages);
  1913   617 |         } else {
  1914   618 |             auto handle{nvmap.GetHandle(entry.handle)};
  1915   619 |             if (!handle) {
  1916   620 |                 return NvResult::BadValue;
  1917   621 |             }
  1918   622 | 
- 1919       |             const DAddr base = nvmap.PinHandle(entry.handle, false);
- 1920       |             const u64 source = static_cast<u64>(entry.handle_offset_big_pages)
- 1921       |                                << vm.big_page_size_bits;
- 1922       |             if (!NativePinnedPhysicalSpan(base, source, size)) {
- 1923       |                 if (base) nvmap.UnpinHandle(entry.handle);
- 1924       |                 return NvResult::InsufficientMemory;
- 1925       |             }
- 1926       |             const DAddr device_address = base + source;
+        623 |             DAddr base = nvmap.PinHandle(entry.handle, false);
+        624 |             DAddr device_address{static_cast<DAddr>(
+        625 |                 base + (static_cast<u64>(entry.handle_offset_big_pages) << vm.big_page_size_bits))};
  1927   626 | 
  1928   627 |             gmmu->Map(virtual_address, device_address, size,
  1929   628 |                       static_cast<Tegra::PTEKind>(entry.kind), use_big_pages);
  1930   629 |         }
  1931   630 |     }
  1932   631 | 
  1933   632 |     return NvResult::Success;
  1934   633 | }
```

</details>

### P0-M04 · AS-GPU MapBufferEx

Fonction centrale pour la traduction NVMap→GPU VA. Encore ajoute des contrats de session/processus, des mappings natifs 4K et de la quarantaine ; les forks ont un chemin Nx2Map plus direct. À corréler avec les adresses des deux GPFIFO Pokopia, pas à simplifier aveuglément.

Encore : [nvhost_as_gpu.cpp:1936–2317](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L1936-L2317) — 382 lignes.

<details>
<summary>Lichii — 706–797 : 64 alignées, 318 propres Encore, 28 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:706–797](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L706-L797).

```diff
  1936   706 | NvResult nvhost_as_gpu::MapBufferEx(IoctlMapBufferEx& params) {
  1937   707 |     LOG_DEBUG(Service_NVDRV,
  1938   708 |               "called, flags={:X}, nvmap_handle={:X}, buffer_offset={}, mapping_size={}"
  1939   709 |               ", offset={:#x}",
  1940   710 |               params.flags, params.handle, params.buffer_offset, params.mapping_size,
  1941   711 |               params.offset);
  1942   712 | 
- 1943       |     // A native PTE-kind remap must drain prior GPU work BEFORE entering the
- 1944       |     // address-space critical section. The GPU worker may still query these
- 1945       |     // page tables while WaitForIdle drains the queue.
- 1946       |     const bool native_remap_requested =
- 1947       |         m_native_process &&
- 1948       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 1949       |         (params.flags & MappingFlags::Remap) != MappingFlags::None;
- 1950       |     if (native_remap_requested && system.IsPoweredOn() && !system.IsShuttingDown())
- 1951       |         system.GPU().WaitForIdle();
- 1952       | 
  1953   713 |     std::scoped_lock lock(mutex);
  1954   714 | 
  1955   715 |     if (!vm.initialised) {
  1956   716 |         return NvResult::BadValue;
  1957   717 |     }
  1958   718 | 
- 1959       |     // A partially committed native sparse transaction has quarantined
- 1960       |     // physical owners. Do not let an unrelated ioctl overwrite its PTEs.
- 1961       |     const bool remap_native = m_native_process &&
- 1962       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 1963       |     if (remap_native && native_sparse_poisoned)
- 1964       |         return NvResult::InvalidState;
- 1965       |     if (remap_native) {
- 1966       |         // Switch 2 allows FIXED bit0, CACHEABLE bit2 and the legacy
- 1967       |         // subrange REMAP bit8 only. Unknown bits cannot be acknowledged
- 1968       |         // as a successful mapping with silently different PTE ownership.
- 1969       |         constexpr u32 valid_flags = 0x105U;
- 1970       |         if ((static_cast<u32>(params.flags) & ~valid_flags) != 0)
- 1971       |             return NvResult::NotSupported;
- 1972       |         // The fourth u32 in MAP_BUFFER_EX/EX2 is documented as
- 1973       |         // reserved/inout, not a requested page size. Preserve it.
- 1974       |     }
- 1975       | 
  1976   719 |     // Remaps a subregion of an existing mapping to a different PA
  1977   720 |     if ((params.flags & MappingFlags::Remap) != MappingFlags::None) {
- 1978       |         // These two ioctl fields are SIGNED; reject negative input before
- 1979       |         // conversion, address arithmetic or locating an existing mapping.
- 1980       |         if (params.offset < 0 || params.buffer_offset < 0) {
- 1981       |             return NvResult::BadValue;
- 1982       |         }
- 1983       |         const u64 gpu_base = static_cast<u64>(params.offset);
- 1984       |         const u64 buffer_offset = static_cast<u64>(params.buffer_offset);
- 1985       |         if (auto const it = mapping_map.find(gpu_base); it != mapping_map.end()) {
+        721 |         if (auto const it = mapping_map.find(params.offset); it != mapping_map.end()) {
  1986   722 |             auto const mapping = it->second;
- 1987       |             // A remap into an existing buffer must fit its original offset
- 1988       |             // and size. Reject wrapped GPU VAs before any page-table change.
- 1989       |             constexpr u64 gpu_limit = u64{1} << 49;
- 1990       |             if (!NativeGpuAllocation::ContainsSubrange(
- 1991       |                     mapping.size, buffer_offset, params.mapping_size) ||
- 1992       |                 gpu_base >= gpu_limit ||
- 1993       |                 buffer_offset >= gpu_limit - gpu_base ||
- 1994       |                 params.mapping_size > gpu_limit - gpu_base - buffer_offset ||
- 1995       |                 mapping.ptr > std::numeric_limits<VAddr>::max() - buffer_offset) {
+        723 |             if (mapping.size < params.mapping_size) {
  1996   724 |                 LOG_WARNING(Service_NVDRV, "Cannot remap a partially mapped GPU address space region: {:#x}", params.offset);
  1997   725 |                 return NvResult::BadValue;
  1998   726 |             }
- 1999       |             const u64 gpu_address = gpu_base + buffer_offset;
- 2000       |             const VAddr device_address{mapping.ptr + buffer_offset};
- 2001       |             if (remap_native) {
- 2002       |                 // Native remap only changes the PTE kind/view of the
- 2003       |                 // original NvMap owner. A different handle requires the
- 2004       |                 // explicit sparse-remap transaction; silently ignoring it
- 2005       |                 // would acknowledge a map to the WRONG physical memory.
- 2006       |                 if (params.handle != 0 && params.handle != mapping.handle)
- 2007       |                     return NvResult::NotSupported;
- 2008       |                 const u64 page = mapping.big_page ? vm.big_page_size
- 2009       |                                                   : VM::YUZU_PAGESIZE;
- 2010       |                 if ((gpu_address | buffer_offset | params.mapping_size) & (page - 1))
- 2011       |                     return NvResult::BadValue;
- 2012       |                 const auto backing = nvmap.GetHandle(mapping.handle);
- 2013       |                 const auto* session = backing
- 2014       |                     ? container.GetSession(backing->session_id) : nullptr;
- 2015       |                 if (!backing || !backing->allocated || !session ||
- 2016       |                     session->process != m_native_process)
- 2017       |                     return NvResult::BadValue;
- 2018       |                 const u32 requested = params.kind == std::numeric_limits<u32>::max()
- 2019       |                                           ? u32{backing->kind} : u32{params.kind};
- 2020       |                 if (requested > std::numeric_limits<u8>::max())
- 2021       |                     return NvResult::NotSupported;
- 2022       |                 const u8 candidate = static_cast<u8>(requested);
- 2023       |                 auto native_kind = SelectNativeMemoryKind(candidate, candidate);
- 2024       |                 if (!native_kind && candidate != backing->kind)
- 2025       |                     native_kind = SelectNativeMemoryKind(candidate, backing->kind);
- 2026       |                 if (!native_kind &&
- 2027       |                     candidate == static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2))
- 2028       |                     native_kind = NativeMemoryKind{
- 2029       |                         static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2), candidate};
- 2030       |                 if (!native_kind) return NvResult::NotSupported;
- 2031       |                 try {
- 2032       |                     gmmu->Map(gpu_address, device_address, params.mapping_size,
- 2033       |                               static_cast<Tegra::PTEKind>(native_kind->backend),
- 2034       |                               mapping.big_page);
- 2035       |                 } catch (const std::bad_alloc&) {
- 2036       |                     // The original NVMap owner and pin remain valid even if
- 2037       |                     // this PTE edit was only partially completed.
- 2038       |                     PoisonNativeAddressSpace();
- 2039       |                     return NvResult::InsufficientMemory;
- 2040       |                 }
- 2041       |                 params.kind = native_kind->selected;
- 2042       |                 return NvResult::Success;
- 2043       |             }
+        727 |             u64 gpu_address = u64(params.offset + params.buffer_offset);
+        728 |             VAddr device_address{mapping.ptr + params.buffer_offset};
  2044   729 |             gmmu->Map(gpu_address, device_address, params.mapping_size, Tegra::PTEKind(params.kind), mapping.big_page);
  2045   730 |             return NvResult::Success;
  2046   731 |         } else {
  2047   732 |             LOG_WARNING(Service_NVDRV, "Cannot remap an unmapped GPU address space region: {:#x}", params.offset);
  2048   733 |             return NvResult::BadValue;
  2049   734 |         }
  2050   735 |     }
  2051   736 | 
  2052   737 |     auto handle{nvmap.GetHandle(params.handle)};
  2053   738 |     if (!handle) {
  2054   739 |         return NvResult::BadValue;
  2055   740 |     }
- 2056       |     // An authenticated NS2 GPU AS may only bind actually allocated NVMap
- 2057       |     // backing from its KProcess. An unrelated FD may expose a numeric
- 2058       |     // handle with the same value, but must not create an alias into it.
- 2059       |     const bool native =
- 2060       |         m_native_process && NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2061       |     std::optional<NativeMemoryKind> native_kind;
- 2062       |     if (native) {
- 2063       |         const auto* owner = container.GetSession(handle->session_id);
- 2064       |         if (!handle->allocated || !owner || owner->process != m_native_process)
- 2065       |             return NvResult::BadValue;
  2066   741 | 
- 2067       |         // In the native ioctl the kind is a GA10F MMU kind, not an Eden
- 2068       |         // Maxwell PTEKind ordinal. For example native generic kind 6 is
- 2069       |         // NOT backend PTE kind 6 (Z16 MS16). The same translation already
- 2070       |         // governs GSV GPU 210/216 sparse mappings. -1 selects the
- 2071       |         // allocated NvMap handle's kind, as specified by NVGPU_AS ioctl.
- 2072       |         const u32 requested = params.kind == std::numeric_limits<u32>::max()
- 2073       |                                   ? u32{handle->kind} : u32{params.kind};
- 2074       |         if (requested > std::numeric_limits<u8>::max())
- 2075       |             return NvResult::NotSupported;
- 2076       |         const u8 candidate = static_cast<u8>(requested);
- 2077       |         native_kind = SelectNativeMemoryKind(candidate, candidate);
- 2078       |         if (!native_kind && candidate != handle->kind)
- 2079       |             native_kind = SelectNativeMemoryKind(candidate, handle->kind);
- 2080       |         // The legacy generic backend kind is still used by imported
- 2081       |         // NvMap allocations, and has an exact 1:1 backend representation.
- 2082       |         if (!native_kind && candidate == static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2))
- 2083       |             native_kind = NativeMemoryKind{
- 2084       |                 static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2), candidate};
- 2085       |         if (!native_kind) return NvResult::NotSupported;
- 2086       |     }
- 2087       | 
- 2088       |     const u64 size{params.mapping_size ? params.mapping_size : handle->orig_size};
- 2089       |     if (!NativeGpuAllocation::ContainsSubrange(handle->orig_size,
- 2090       |                                                params.buffer_offset, size))
- 2091       |         return NvResult::BadValue;
- 2092       |     // Validate the fixed GPU allocation BEFORE pinning NvMap. Refusing
- 2093       |     // an invalid ioctl after PinHandle leaked its underlying GPU pin.
- 2094       |     auto fixed_alloc = allocation_map.end();
- 2095       |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
- 2096       |         fixed_alloc = NativeGpuAllocation::FindContaining(
- 2097       |             allocation_map, params.offset, size);
- 2098       |         if (fixed_alloc == allocation_map.end()) {
- 2099       |             LOG_WARNING(Service_NVDRV, "Fixed GPU map outside allocation: {:#x}", params.offset);
- 2100       |             return NvResult::BadValue;
- 2101       |         }
- 2102       |         if (native) {
- 2103       |             // A fixed map without the Remap flag may not replace a live GPU
- 2104       |             // view. insert_or_assign would forget its NVMap pin and leave
- 2105       |             // queued texture/compute work pointing at re-used pages.
- 2106       |             const u64 address = static_cast<u64>(params.offset);
- 2107       |             const auto next = mapping_map.lower_bound(address);
- 2108       |             if ((next != mapping_map.end() && next->first < address + size) ||
- 2109       |                 (next != mapping_map.begin() &&
- 2110       |                  std::prev(next)->second.size > address - std::prev(next)->first))
- 2111       |                 return NvResult::BadValue;
- 2112       |         }
- 2113       |     }
- 2114       |     const DAddr pinned = nvmap.PinHandle(params.handle, false);
- 2115       |     if (!NativePinnedPhysicalSpan(pinned, params.buffer_offset, size)) {
- 2116       |         if (pinned) nvmap.UnpinHandle(params.handle);
- 2117       |         return NvResult::InsufficientMemory;
- 2118       |     }
- 2119       |     const DAddr device_address = pinned + params.buffer_offset;
+        742 |     DAddr device_address = DAddr(nvmap.PinHandle(params.handle, false) + params.buffer_offset);
+        743 |     u64 size{params.mapping_size ? params.mapping_size : handle->orig_size};
  2120   744 | 
  2121   745 |     bool big_page{[&]() {
  2122   746 |         if (Common::IsAligned(handle->align, vm.big_page_size)) {
  2123   747 |             return true;
- 2124       |         } else if (Common::IsAligned(handle->align, VM::YUZU_PAGESIZE)) {
+        748 |         } else if (Common::IsAligned(handle->align, VM::LICHII_PAGESIZE)) {
  2125   749 |             return false;
  2126   750 |         } else {
  2127   751 |             ASSERT(false);
  2128   752 |             return false;
  2129   753 |         }
  2130   754 |     }()};
- 2131       |     if (native) {
- 2132       |         if (vm.big_page_allocator &&
- 2133       |             vm.big_page_allocator->GetVAStart() == vm.big_page_allocator->GetVALimit())
- 2134       |             // A native small-page-only address-space view cannot use a big
- 2135       |             // PTE merely because its physical NvMap handle is aligned.
- 2136       |             big_page = false;
- 2137       |         if (big_page && !Common::IsAligned(handle->align, vm.big_page_size)) {
- 2138       |             nvmap.UnpinHandle(params.handle);
- 2139       |             return NvResult::BadValue;
- 2140       |         }
- 2141       |     }
  2142   755 | 
- 2143       |     // Native NS2: all fallible owner and lookup allocations must complete
- 2144       |     // BEFORE publishing GPU PTEs. The legacy NVDRV path below stays intact.
- 2145       |     // Otherwise a failed map/offset-vector allocation can orphan an NVMap
- 2146       |     // pin or publish backing that can no longer be retired.
- 2147       |     if (native) {
- 2148       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 2149       |         // The allocated VA determines which GMMU table can resolve this
- 2150       |         // fixed map. Mapping a 4K physical view into a big-page-only VA
- 2151       |         // would succeed at ioctl level but remain invisible to the guest
- 2152       |         // (GetEntry selects the big table above the split).
- 2153       |         if (fixed && fixed_alloc->second.big_pages && !big_page) {
- 2154       |             nvmap.UnpinHandle(params.handle);
- 2155       |             return NvResult::BadValue;
- 2156       |         }
- 2157       |         const bool use_big_pages = fixed ? fixed_alloc->second.big_pages : big_page;
- 2158       |         const u32 page_size = use_big_pages ? vm.big_page_size : VM::YUZU_PAGESIZE;
- 2159       |         const u32 page_bits = use_big_pages ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS;
- 2160       |         if (!size || size > std::numeric_limits<u64>::max() - (page_size - 1)) {
- 2161       |             nvmap.UnpinHandle(params.handle);
- 2162       |             return NvResult::BadValue;
- 2163       |         }
- 2164       |         const u64 mapped_size = Common::AlignUp(size, u64{page_size});
- 2165       |         const u64 source_offset = static_cast<u64>(params.buffer_offset);
- 2166       |         // MemoryManager::Map walks whole PTEs even if the requested size
- 2167       |         // ends mid-page. Validate the full physical range and alignment.
- 2168       |         if ((source_offset & (page_size - 1)) ||
- 2169       |             source_offset > handle->aligned_size ||
- 2170       |             mapped_size > handle->aligned_size - source_offset ||
- 2171       |             !NativePinnedPhysicalSpan(pinned, source_offset, mapped_size) ||
- 2172       |             ((pinned + source_offset) & (page_size - 1)) != 0) {
- 2173       |             nvmap.UnpinHandle(params.handle);
- 2174       |             return NvResult::BadValue;
- 2175       |         }
- 2176       | 
- 2177       |         u64 address{};
- 2178       |         u32 allocated_page{};
- 2179       |         u32 allocated_pages{};
- 2180       |         bool owns_va = false;
- 2181       |         auto* allocator = use_big_pages ? &*vm.big_page_allocator : &*vm.small_page_allocator;
- 2182       |         if (fixed) {
- 2183       |             address = static_cast<u64>(params.offset);
- 2184       |             const auto& allocation = fixed_alloc->second;
- 2185       |             if (address < fixed_alloc->first ||
- 2186       |                 ((address | mapped_size) & (page_size - 1)) ||
- 2187       |                 mapped_size > allocation.size - (address - fixed_alloc->first)) {
- 2188       |                 nvmap.UnpinHandle(params.handle);
- 2189       |                 return NvResult::BadValue;
- 2190       |             }
- 2191       |         } else {
- 2192       |             const u64 page_count = mapped_size >> page_bits;
- 2193       |             if (!page_count || page_count > std::numeric_limits<u32>::max()) {
- 2194       |                 nvmap.UnpinHandle(params.handle);
- 2195       |                 return NvResult::BadValue;
- 2196       |             }
- 2197       |             allocated_pages = static_cast<u32>(page_count);
- 2198       |             try {
- 2199       |                 allocated_page = allocator->Allocate(allocated_pages);
- 2200       |             } catch (const std::bad_alloc&) {
- 2201       |                 nvmap.UnpinHandle(params.handle);
- 2202       |                 return NvResult::InsufficientMemory;
- 2203       |             }
- 2204       |             if (!allocated_page) {
- 2205       |                 nvmap.UnpinHandle(params.handle);
- 2206       |                 return NvResult::InsufficientMemory;
- 2207       |             }
- 2208       |             owns_va = true;
- 2209       |             address = static_cast<u64>(allocated_page) << page_bits;
- 2210       |         }
- 2211       | 
- 2212       |         bool owner_inserted = false;
- 2213       |         bool token_inserted = false;
- 2214       |         bool allocation_indexed = false;
- 2215       |         const auto rollback = [&] {
- 2216       |             if (allocation_indexed) fixed_alloc->second.mappings.pop_back();
- 2217       |             if (token_inserted) map_buffer_offsets.erase(static_cast<s64>(address));
- 2218       |             if (owner_inserted) mapping_map.erase(address);
- 2219       |             if (owns_va) allocator->Free(allocated_page, allocated_pages);
- 2220       |             nvmap.UnpinHandle(params.handle);
- 2221       |         };
- 2222       | 
- 2223       |         // The sparse batch table is a distinct physical owner from
- 2224       |         // MapBufferEx. Never silently override its live PTE/pin by a fixed
- 2225       |         // mapping which would survive the sparse table's later release.
- 2226       |         const auto sparse = native_sparse_mappings.Ranges().lower_bound(address);
- 2227       |         if ((sparse != native_sparse_mappings.Ranges().end() &&
- 2228       |              sparse->first < address + mapped_size) ||
- 2229       |             (sparse != native_sparse_mappings.Ranges().begin() &&
- 2230       |              std::prev(sparse)->second.size >
- 2231       |                  address - std::prev(sparse)->first)) {
- 2232       |             rollback();
- 2233       |             return NvResult::BadValue;
- 2234       |         }
+        756 |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
+        757 |         auto alloc{allocation_map.upper_bound(params.offset)};
  2235   758 | 
- 2236       |         try {
- 2237       |             if (fixed)
- 2238       |                 fixed_alloc->second.mappings.reserve(fixed_alloc->second.mappings.size() + 1);
- 2239       |             const auto [it, inserted] = mapping_map.try_emplace(
- 2240       |                 address, Mapping(params.handle, device_address, address,
- 2241       |                                  mapped_size, fixed, use_big_pages,
- 2242       |                                  fixed && fixed_alloc->second.sparse));
- 2243       |             if (!inserted) {
- 2244       |                 rollback();
- 2245       |                 return NvResult::BadValue;
- 2246       |             }
- 2247       |             owner_inserted = true;
- 2248       |             const auto [token, new_token] =
- 2249       |                 map_buffer_offsets.insert(static_cast<s64>(address));
- 2250       |             (void)token;
- 2251       |             if (!new_token) {
- 2252       |                 rollback();
+        759 |         if (alloc-- == allocation_map.begin() ||
+        760 |             (params.offset - alloc->first) + size > alloc->second.size) {
+        761 |             ASSERT_MSG(false, "Cannot perform a fixed mapping into an unallocated region!");
  2253   762 |                 return NvResult::BadValue;
  2254   763 |             }
- 2255       |             token_inserted = true;
- 2256       |             if (fixed) {
- 2257       |                 fixed_alloc->second.mappings.push_back(address);
- 2258       |                 allocation_indexed = true;
- 2259       |             }
- 2260       |         } catch (const std::bad_alloc&) {
- 2261       |             rollback();
- 2262       |             return NvResult::InsufficientMemory;
- 2263       |         }
  2264   764 | 
- 2265       |         try {
- 2266       |             // No unowned GMMU page can become visible: every mapping has a
- 2267       |             // complete ledger and pin before this transaction commits.
- 2268       |             gmmu->Map(address, device_address, mapped_size,
- 2269       |                       static_cast<Tegra::PTEKind>(native_kind->backend), use_big_pages);
- 2270       |         } catch (const std::bad_alloc&) {
- 2271       |             // A GMMU allocation may have modified some PTEs before OOM.
- 2272       |             // Do not unpin live backing unless the page-table rollback
- 2273       |             // succeeds. A retained ledger is safer than a GPU UAF.
- 2274       |             try {
- 2275       |                 if (fixed && fixed_alloc->second.sparse)
- 2276       |                     gmmu->MapSparse(address, mapped_size, use_big_pages);
- 2277       |                 else
- 2278       |                     gmmu->Unmap(address, mapped_size);
- 2279       |             } catch (const std::bad_alloc&) {
- 2280       |                 PoisonNativeAddressSpace();
- 2281       |                 return NvResult::InvalidState;
- 2282       |             }
- 2283       |             rollback();
- 2284       |             return NvResult::InsufficientMemory;
- 2285       |         }
- 2286       |         params.offset = address;
- 2287       |         params.kind = native_kind->selected; // Native selected/fallback kind, never backend ordinal.
- 2288       |         // The caller's reserved/inout word is not the selected page size.
- 2289       |         return NvResult::Success;
- 2290       |     }
- 2291       | 
- 2292       |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
- 2293       |         const auto alloc = fixed_alloc; // Validated before NvMap pin.
  2294   765 |         const bool use_big_pages = alloc->second.big_pages && big_page;
  2295   766 |         gmmu->Map(params.offset, device_address, size, static_cast<Tegra::PTEKind>(params.kind), use_big_pages);
  2296   767 | 
  2297   768 |         alloc->second.mappings.push_back(params.offset);
  2298   769 |         mapping_map.insert_or_assign(params.offset, Mapping(params.handle, device_address, params.offset, size, true, use_big_pages, alloc->second.sparse));
  2299   770 |     } else {
  2300   771 |         auto& allocator{big_page ? *vm.big_page_allocator : *vm.small_page_allocator};
- 2301       |         u32 page_size{big_page ? vm.big_page_size : VM::YUZU_PAGESIZE};
+        772 |         u32 page_size{big_page ? vm.big_page_size : VM::LICHII_PAGESIZE};
  2302   773 |         u32 page_size_bits{big_page ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS};
  2303   774 | 
- 2304       |         params.offset = u64(allocator.Allocate(u32(Common::AlignUp(size, page_size) >> page_size_bits))) << page_size_bits;
+        775 |         const u64 aligned_size{Common::AlignUp(size, page_size)};
+        776 |         params.offset = u64(allocator.Allocate(u32(aligned_size >> page_size_bits))) << page_size_bits;
  2305   777 |         if (!params.offset) {
- 2306       |             nvmap.UnpinHandle(params.handle); // Allocation failed after NvMap pin.
+        778 |             u64 buffers{};
+        779 |             u64 buffer_bytes{};
+        780 |             for (const auto& [offset, mapping] : mapping_map) {
+        781 |                 if (!mapping.fixed && mapping.big_page == big_page) {
+        782 |                     ++buffers;
+        783 |                     buffer_bytes += mapping.size;
+        784 |                 }
+        785 |             }
+        786 |             LOG_ERROR(Service_NVDRV,
+        787 |                       "No free {} page range of {:#x} bytes; {} buffers hold {} MiB of it",
+        788 |                       big_page ? "big" : "small", aligned_size, buffers, buffer_bytes >> 20);
  2307   789 |             ASSERT_MSG(false, "Failed to allocate free space in the GPU AS!");
  2308   790 |             return NvResult::InsufficientMemory;
  2309   791 |         }
- 2310       |         gmmu->Map(params.offset, device_address, Common::AlignUp(size, page_size), Tegra::PTEKind(params.kind), big_page);
- 2311       |         mapping_map.insert_or_assign(params.offset, Mapping(params.handle, device_address, params.offset, size, false, big_page, false));
+        792 |         gmmu->Map(params.offset, device_address, aligned_size, Tegra::PTEKind(params.kind), big_page);
+        793 |         mapping_map.insert_or_assign(params.offset, Mapping(params.handle, device_address, params.offset, aligned_size, false, big_page, false));
  2312   794 |     }
  2313   795 | 
- 2314       |     map_buffer_offsets.insert(params.offset);
- 2315       | 
  2316   796 |     return NvResult::Success;
  2317   797 | }
```

</details>

<details>
<summary>EglantinePS5 — 635–716 : 71 alignées, 311 propres Encore, 11 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:635–716](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L635-L716).

```diff
  1936   635 | NvResult nvhost_as_gpu::MapBufferEx(IoctlMapBufferEx& params) {
  1937   636 |     LOG_DEBUG(Service_NVDRV,
  1938   637 |               "called, flags={:X}, nvmap_handle={:X}, buffer_offset={}, mapping_size={}"
  1939   638 |               ", offset={:#x}",
  1940   639 |               params.flags, params.handle, params.buffer_offset, params.mapping_size,
  1941   640 |               params.offset);
  1942   641 | 
- 1943       |     // A native PTE-kind remap must drain prior GPU work BEFORE entering the
- 1944       |     // address-space critical section. The GPU worker may still query these
- 1945       |     // page tables while WaitForIdle drains the queue.
- 1946       |     const bool native_remap_requested =
- 1947       |         m_native_process &&
- 1948       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 1949       |         (params.flags & MappingFlags::Remap) != MappingFlags::None;
- 1950       |     if (native_remap_requested && system.IsPoweredOn() && !system.IsShuttingDown())
- 1951       |         system.GPU().WaitForIdle();
- 1952       | 
  1953   642 |     std::scoped_lock lock(mutex);
  1954   643 | 
  1955   644 |     if (!vm.initialised) {
  1956   645 |         return NvResult::BadValue;
  1957   646 |     }
  1958   647 | 
- 1959       |     // A partially committed native sparse transaction has quarantined
- 1960       |     // physical owners. Do not let an unrelated ioctl overwrite its PTEs.
- 1961       |     const bool remap_native = m_native_process &&
- 1962       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 1963       |     if (remap_native && native_sparse_poisoned)
- 1964       |         return NvResult::InvalidState;
- 1965       |     if (remap_native) {
- 1966       |         // Switch 2 allows FIXED bit0, CACHEABLE bit2 and the legacy
- 1967       |         // subrange REMAP bit8 only. Unknown bits cannot be acknowledged
- 1968       |         // as a successful mapping with silently different PTE ownership.
- 1969       |         constexpr u32 valid_flags = 0x105U;
- 1970       |         if ((static_cast<u32>(params.flags) & ~valid_flags) != 0)
- 1971       |             return NvResult::NotSupported;
- 1972       |         // The fourth u32 in MAP_BUFFER_EX/EX2 is documented as
- 1973       |         // reserved/inout, not a requested page size. Preserve it.
- 1974       |     }
- 1975       | 
  1976   648 |     // Remaps a subregion of an existing mapping to a different PA
  1977   649 |     if ((params.flags & MappingFlags::Remap) != MappingFlags::None) {
- 1978       |         // These two ioctl fields are SIGNED; reject negative input before
- 1979       |         // conversion, address arithmetic or locating an existing mapping.
- 1980       |         if (params.offset < 0 || params.buffer_offset < 0) {
- 1981       |             return NvResult::BadValue;
- 1982       |         }
- 1983       |         const u64 gpu_base = static_cast<u64>(params.offset);
- 1984       |         const u64 buffer_offset = static_cast<u64>(params.buffer_offset);
- 1985       |         if (auto const it = mapping_map.find(gpu_base); it != mapping_map.end()) {
+        650 |         if (auto const it = mapping_map.find(params.offset); it != mapping_map.end()) {
  1986   651 |             auto const mapping = it->second;
- 1987       |             // A remap into an existing buffer must fit its original offset
- 1988       |             // and size. Reject wrapped GPU VAs before any page-table change.
- 1989       |             constexpr u64 gpu_limit = u64{1} << 49;
- 1990       |             if (!NativeGpuAllocation::ContainsSubrange(
- 1991       |                     mapping.size, buffer_offset, params.mapping_size) ||
- 1992       |                 gpu_base >= gpu_limit ||
- 1993       |                 buffer_offset >= gpu_limit - gpu_base ||
- 1994       |                 params.mapping_size > gpu_limit - gpu_base - buffer_offset ||
- 1995       |                 mapping.ptr > std::numeric_limits<VAddr>::max() - buffer_offset) {
+        652 |             if (mapping.size < params.mapping_size) {
  1996   653 |                 LOG_WARNING(Service_NVDRV, "Cannot remap a partially mapped GPU address space region: {:#x}", params.offset);
  1997   654 |                 return NvResult::BadValue;
  1998   655 |             }
- 1999       |             const u64 gpu_address = gpu_base + buffer_offset;
- 2000       |             const VAddr device_address{mapping.ptr + buffer_offset};
- 2001       |             if (remap_native) {
- 2002       |                 // Native remap only changes the PTE kind/view of the
- 2003       |                 // original NvMap owner. A different handle requires the
- 2004       |                 // explicit sparse-remap transaction; silently ignoring it
- 2005       |                 // would acknowledge a map to the WRONG physical memory.
- 2006       |                 if (params.handle != 0 && params.handle != mapping.handle)
- 2007       |                     return NvResult::NotSupported;
- 2008       |                 const u64 page = mapping.big_page ? vm.big_page_size
- 2009       |                                                   : VM::YUZU_PAGESIZE;
- 2010       |                 if ((gpu_address | buffer_offset | params.mapping_size) & (page - 1))
- 2011       |                     return NvResult::BadValue;
- 2012       |                 const auto backing = nvmap.GetHandle(mapping.handle);
- 2013       |                 const auto* session = backing
- 2014       |                     ? container.GetSession(backing->session_id) : nullptr;
- 2015       |                 if (!backing || !backing->allocated || !session ||
- 2016       |                     session->process != m_native_process)
- 2017       |                     return NvResult::BadValue;
- 2018       |                 const u32 requested = params.kind == std::numeric_limits<u32>::max()
- 2019       |                                           ? u32{backing->kind} : u32{params.kind};
- 2020       |                 if (requested > std::numeric_limits<u8>::max())
- 2021       |                     return NvResult::NotSupported;
- 2022       |                 const u8 candidate = static_cast<u8>(requested);
- 2023       |                 auto native_kind = SelectNativeMemoryKind(candidate, candidate);
- 2024       |                 if (!native_kind && candidate != backing->kind)
- 2025       |                     native_kind = SelectNativeMemoryKind(candidate, backing->kind);
- 2026       |                 if (!native_kind &&
- 2027       |                     candidate == static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2))
- 2028       |                     native_kind = NativeMemoryKind{
- 2029       |                         static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2), candidate};
- 2030       |                 if (!native_kind) return NvResult::NotSupported;
- 2031       |                 try {
- 2032       |                     gmmu->Map(gpu_address, device_address, params.mapping_size,
- 2033       |                               static_cast<Tegra::PTEKind>(native_kind->backend),
- 2034       |                               mapping.big_page);
- 2035       |                 } catch (const std::bad_alloc&) {
- 2036       |                     // The original NVMap owner and pin remain valid even if
- 2037       |                     // this PTE edit was only partially completed.
- 2038       |                     PoisonNativeAddressSpace();
- 2039       |                     return NvResult::InsufficientMemory;
- 2040       |                 }
- 2041       |                 params.kind = native_kind->selected;
- 2042       |                 return NvResult::Success;
- 2043       |             }
+        656 |             u64 gpu_address = u64(params.offset + params.buffer_offset);
+        657 |             VAddr device_address{mapping.ptr + params.buffer_offset};
  2044   658 |             gmmu->Map(gpu_address, device_address, params.mapping_size, Tegra::PTEKind(params.kind), mapping.big_page);
  2045   659 |             return NvResult::Success;
  2046   660 |         } else {
  2047   661 |             LOG_WARNING(Service_NVDRV, "Cannot remap an unmapped GPU address space region: {:#x}", params.offset);
  2048   662 |             return NvResult::BadValue;
  2049   663 |         }
  2050   664 |     }
  2051   665 | 
  2052   666 |     auto handle{nvmap.GetHandle(params.handle)};
  2053   667 |     if (!handle) {
  2054   668 |         return NvResult::BadValue;
  2055   669 |     }
- 2056       |     // An authenticated NS2 GPU AS may only bind actually allocated NVMap
- 2057       |     // backing from its KProcess. An unrelated FD may expose a numeric
- 2058       |     // handle with the same value, but must not create an alias into it.
- 2059       |     const bool native =
- 2060       |         m_native_process && NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2061       |     std::optional<NativeMemoryKind> native_kind;
- 2062       |     if (native) {
- 2063       |         const auto* owner = container.GetSession(handle->session_id);
- 2064       |         if (!handle->allocated || !owner || owner->process != m_native_process)
- 2065       |             return NvResult::BadValue;
  2066   670 | 
- 2067       |         // In the native ioctl the kind is a GA10F MMU kind, not an Eden
- 2068       |         // Maxwell PTEKind ordinal. For example native generic kind 6 is
- 2069       |         // NOT backend PTE kind 6 (Z16 MS16). The same translation already
- 2070       |         // governs GSV GPU 210/216 sparse mappings. -1 selects the
- 2071       |         // allocated NvMap handle's kind, as specified by NVGPU_AS ioctl.
- 2072       |         const u32 requested = params.kind == std::numeric_limits<u32>::max()
- 2073       |                                   ? u32{handle->kind} : u32{params.kind};
- 2074       |         if (requested > std::numeric_limits<u8>::max())
- 2075       |             return NvResult::NotSupported;
- 2076       |         const u8 candidate = static_cast<u8>(requested);
- 2077       |         native_kind = SelectNativeMemoryKind(candidate, candidate);
- 2078       |         if (!native_kind && candidate != handle->kind)
- 2079       |             native_kind = SelectNativeMemoryKind(candidate, handle->kind);
- 2080       |         // The legacy generic backend kind is still used by imported
- 2081       |         // NvMap allocations, and has an exact 1:1 backend representation.
- 2082       |         if (!native_kind && candidate == static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2))
- 2083       |             native_kind = NativeMemoryKind{
- 2084       |                 static_cast<u8>(Tegra::PTEKind::GENERIC_16BX2), candidate};
- 2085       |         if (!native_kind) return NvResult::NotSupported;
- 2086       |     }
- 2087       | 
- 2088       |     const u64 size{params.mapping_size ? params.mapping_size : handle->orig_size};
- 2089       |     if (!NativeGpuAllocation::ContainsSubrange(handle->orig_size,
- 2090       |                                                params.buffer_offset, size))
- 2091       |         return NvResult::BadValue;
- 2092       |     // Validate the fixed GPU allocation BEFORE pinning NvMap. Refusing
- 2093       |     // an invalid ioctl after PinHandle leaked its underlying GPU pin.
- 2094       |     auto fixed_alloc = allocation_map.end();
- 2095       |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
- 2096       |         fixed_alloc = NativeGpuAllocation::FindContaining(
- 2097       |             allocation_map, params.offset, size);
- 2098       |         if (fixed_alloc == allocation_map.end()) {
- 2099       |             LOG_WARNING(Service_NVDRV, "Fixed GPU map outside allocation: {:#x}", params.offset);
- 2100       |             return NvResult::BadValue;
- 2101       |         }
- 2102       |         if (native) {
- 2103       |             // A fixed map without the Remap flag may not replace a live GPU
- 2104       |             // view. insert_or_assign would forget its NVMap pin and leave
- 2105       |             // queued texture/compute work pointing at re-used pages.
- 2106       |             const u64 address = static_cast<u64>(params.offset);
- 2107       |             const auto next = mapping_map.lower_bound(address);
- 2108       |             if ((next != mapping_map.end() && next->first < address + size) ||
- 2109       |                 (next != mapping_map.begin() &&
- 2110       |                  std::prev(next)->second.size > address - std::prev(next)->first))
- 2111       |                 return NvResult::BadValue;
- 2112       |         }
- 2113       |     }
- 2114       |     const DAddr pinned = nvmap.PinHandle(params.handle, false);
- 2115       |     if (!NativePinnedPhysicalSpan(pinned, params.buffer_offset, size)) {
- 2116       |         if (pinned) nvmap.UnpinHandle(params.handle);
- 2117       |         return NvResult::InsufficientMemory;
- 2118       |     }
- 2119       |     const DAddr device_address = pinned + params.buffer_offset;
+        671 |     DAddr device_address = DAddr(nvmap.PinHandle(params.handle, false) + params.buffer_offset);
+        672 |     u64 size{params.mapping_size ? params.mapping_size : handle->orig_size};
  2120   673 | 
  2121   674 |     bool big_page{[&]() {
  2122   675 |         if (Common::IsAligned(handle->align, vm.big_page_size)) {
  2123   676 |             return true;
  2124   677 |         } else if (Common::IsAligned(handle->align, VM::YUZU_PAGESIZE)) {
  2125   678 |             return false;
  2126   679 |         } else {
  2127   680 |             ASSERT(false);
  2128   681 |             return false;
  2129   682 |         }
  2130   683 |     }()};
- 2131       |     if (native) {
- 2132       |         if (vm.big_page_allocator &&
- 2133       |             vm.big_page_allocator->GetVAStart() == vm.big_page_allocator->GetVALimit())
- 2134       |             // A native small-page-only address-space view cannot use a big
- 2135       |             // PTE merely because its physical NvMap handle is aligned.
- 2136       |             big_page = false;
- 2137       |         if (big_page && !Common::IsAligned(handle->align, vm.big_page_size)) {
- 2138       |             nvmap.UnpinHandle(params.handle);
- 2139       |             return NvResult::BadValue;
- 2140       |         }
- 2141       |     }
  2142   684 | 
- 2143       |     // Native NS2: all fallible owner and lookup allocations must complete
- 2144       |     // BEFORE publishing GPU PTEs. The legacy NVDRV path below stays intact.
- 2145       |     // Otherwise a failed map/offset-vector allocation can orphan an NVMap
- 2146       |     // pin or publish backing that can no longer be retired.
- 2147       |     if (native) {
- 2148       |         const bool fixed = (params.flags & MappingFlags::Fixed) != MappingFlags::None;
- 2149       |         // The allocated VA determines which GMMU table can resolve this
- 2150       |         // fixed map. Mapping a 4K physical view into a big-page-only VA
- 2151       |         // would succeed at ioctl level but remain invisible to the guest
- 2152       |         // (GetEntry selects the big table above the split).
- 2153       |         if (fixed && fixed_alloc->second.big_pages && !big_page) {
- 2154       |             nvmap.UnpinHandle(params.handle);
- 2155       |             return NvResult::BadValue;
- 2156       |         }
- 2157       |         const bool use_big_pages = fixed ? fixed_alloc->second.big_pages : big_page;
- 2158       |         const u32 page_size = use_big_pages ? vm.big_page_size : VM::YUZU_PAGESIZE;
- 2159       |         const u32 page_bits = use_big_pages ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS;
- 2160       |         if (!size || size > std::numeric_limits<u64>::max() - (page_size - 1)) {
- 2161       |             nvmap.UnpinHandle(params.handle);
- 2162       |             return NvResult::BadValue;
- 2163       |         }
- 2164       |         const u64 mapped_size = Common::AlignUp(size, u64{page_size});
- 2165       |         const u64 source_offset = static_cast<u64>(params.buffer_offset);
- 2166       |         // MemoryManager::Map walks whole PTEs even if the requested size
- 2167       |         // ends mid-page. Validate the full physical range and alignment.
- 2168       |         if ((source_offset & (page_size - 1)) ||
- 2169       |             source_offset > handle->aligned_size ||
- 2170       |             mapped_size > handle->aligned_size - source_offset ||
- 2171       |             !NativePinnedPhysicalSpan(pinned, source_offset, mapped_size) ||
- 2172       |             ((pinned + source_offset) & (page_size - 1)) != 0) {
- 2173       |             nvmap.UnpinHandle(params.handle);
- 2174       |             return NvResult::BadValue;
- 2175       |         }
- 2176       | 
- 2177       |         u64 address{};
- 2178       |         u32 allocated_page{};
- 2179       |         u32 allocated_pages{};
- 2180       |         bool owns_va = false;
- 2181       |         auto* allocator = use_big_pages ? &*vm.big_page_allocator : &*vm.small_page_allocator;
- 2182       |         if (fixed) {
- 2183       |             address = static_cast<u64>(params.offset);
- 2184       |             const auto& allocation = fixed_alloc->second;
- 2185       |             if (address < fixed_alloc->first ||
- 2186       |                 ((address | mapped_size) & (page_size - 1)) ||
- 2187       |                 mapped_size > allocation.size - (address - fixed_alloc->first)) {
- 2188       |                 nvmap.UnpinHandle(params.handle);
- 2189       |                 return NvResult::BadValue;
- 2190       |             }
- 2191       |         } else {
- 2192       |             const u64 page_count = mapped_size >> page_bits;
- 2193       |             if (!page_count || page_count > std::numeric_limits<u32>::max()) {
- 2194       |                 nvmap.UnpinHandle(params.handle);
- 2195       |                 return NvResult::BadValue;
- 2196       |             }
- 2197       |             allocated_pages = static_cast<u32>(page_count);
- 2198       |             try {
- 2199       |                 allocated_page = allocator->Allocate(allocated_pages);
- 2200       |             } catch (const std::bad_alloc&) {
- 2201       |                 nvmap.UnpinHandle(params.handle);
- 2202       |                 return NvResult::InsufficientMemory;
- 2203       |             }
- 2204       |             if (!allocated_page) {
- 2205       |                 nvmap.UnpinHandle(params.handle);
- 2206       |                 return NvResult::InsufficientMemory;
- 2207       |             }
- 2208       |             owns_va = true;
- 2209       |             address = static_cast<u64>(allocated_page) << page_bits;
- 2210       |         }
- 2211       | 
- 2212       |         bool owner_inserted = false;
- 2213       |         bool token_inserted = false;
- 2214       |         bool allocation_indexed = false;
- 2215       |         const auto rollback = [&] {
- 2216       |             if (allocation_indexed) fixed_alloc->second.mappings.pop_back();
- 2217       |             if (token_inserted) map_buffer_offsets.erase(static_cast<s64>(address));
- 2218       |             if (owner_inserted) mapping_map.erase(address);
- 2219       |             if (owns_va) allocator->Free(allocated_page, allocated_pages);
- 2220       |             nvmap.UnpinHandle(params.handle);
- 2221       |         };
- 2222       | 
- 2223       |         // The sparse batch table is a distinct physical owner from
- 2224       |         // MapBufferEx. Never silently override its live PTE/pin by a fixed
- 2225       |         // mapping which would survive the sparse table's later release.
- 2226       |         const auto sparse = native_sparse_mappings.Ranges().lower_bound(address);
- 2227       |         if ((sparse != native_sparse_mappings.Ranges().end() &&
- 2228       |              sparse->first < address + mapped_size) ||
- 2229       |             (sparse != native_sparse_mappings.Ranges().begin() &&
- 2230       |              std::prev(sparse)->second.size >
- 2231       |                  address - std::prev(sparse)->first)) {
- 2232       |             rollback();
- 2233       |             return NvResult::BadValue;
- 2234       |         }
+        685 |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
+        686 |         auto alloc{allocation_map.upper_bound(params.offset)};
  2235   687 | 
- 2236       |         try {
- 2237       |             if (fixed)
- 2238       |                 fixed_alloc->second.mappings.reserve(fixed_alloc->second.mappings.size() + 1);
- 2239       |             const auto [it, inserted] = mapping_map.try_emplace(
- 2240       |                 address, Mapping(params.handle, device_address, address,
- 2241       |                                  mapped_size, fixed, use_big_pages,
- 2242       |                                  fixed && fixed_alloc->second.sparse));
- 2243       |             if (!inserted) {
- 2244       |                 rollback();
- 2245       |                 return NvResult::BadValue;
- 2246       |             }
- 2247       |             owner_inserted = true;
- 2248       |             const auto [token, new_token] =
- 2249       |                 map_buffer_offsets.insert(static_cast<s64>(address));
- 2250       |             (void)token;
- 2251       |             if (!new_token) {
- 2252       |                 rollback();
+        688 |         if (alloc-- == allocation_map.begin() ||
+        689 |             (params.offset - alloc->first) + size > alloc->second.size) {
+        690 |             ASSERT_MSG(false, "Cannot perform a fixed mapping into an unallocated region!");
  2253   691 |                 return NvResult::BadValue;
  2254   692 |             }
- 2255       |             token_inserted = true;
- 2256       |             if (fixed) {
- 2257       |                 fixed_alloc->second.mappings.push_back(address);
- 2258       |                 allocation_indexed = true;
- 2259       |             }
- 2260       |         } catch (const std::bad_alloc&) {
- 2261       |             rollback();
- 2262       |             return NvResult::InsufficientMemory;
- 2263       |         }
  2264   693 | 
- 2265       |         try {
- 2266       |             // No unowned GMMU page can become visible: every mapping has a
- 2267       |             // complete ledger and pin before this transaction commits.
- 2268       |             gmmu->Map(address, device_address, mapped_size,
- 2269       |                       static_cast<Tegra::PTEKind>(native_kind->backend), use_big_pages);
- 2270       |         } catch (const std::bad_alloc&) {
- 2271       |             // A GMMU allocation may have modified some PTEs before OOM.
- 2272       |             // Do not unpin live backing unless the page-table rollback
- 2273       |             // succeeds. A retained ledger is safer than a GPU UAF.
- 2274       |             try {
- 2275       |                 if (fixed && fixed_alloc->second.sparse)
- 2276       |                     gmmu->MapSparse(address, mapped_size, use_big_pages);
- 2277       |                 else
- 2278       |                     gmmu->Unmap(address, mapped_size);
- 2279       |             } catch (const std::bad_alloc&) {
- 2280       |                 PoisonNativeAddressSpace();
- 2281       |                 return NvResult::InvalidState;
- 2282       |             }
- 2283       |             rollback();
- 2284       |             return NvResult::InsufficientMemory;
- 2285       |         }
- 2286       |         params.offset = address;
- 2287       |         params.kind = native_kind->selected; // Native selected/fallback kind, never backend ordinal.
- 2288       |         // The caller's reserved/inout word is not the selected page size.
- 2289       |         return NvResult::Success;
- 2290       |     }
- 2291       | 
- 2292       |     if ((params.flags & MappingFlags::Fixed) != MappingFlags::None) {
- 2293       |         const auto alloc = fixed_alloc; // Validated before NvMap pin.
  2294   694 |         const bool use_big_pages = alloc->second.big_pages && big_page;
  2295   695 |         gmmu->Map(params.offset, device_address, size, static_cast<Tegra::PTEKind>(params.kind), use_big_pages);
  2296   696 | 
  2297   697 |         alloc->second.mappings.push_back(params.offset);
  2298   698 |         mapping_map.insert_or_assign(params.offset, Mapping(params.handle, device_address, params.offset, size, true, use_big_pages, alloc->second.sparse));
  2299   699 |     } else {
  2300   700 |         auto& allocator{big_page ? *vm.big_page_allocator : *vm.small_page_allocator};
  2301   701 |         u32 page_size{big_page ? vm.big_page_size : VM::YUZU_PAGESIZE};
  2302   702 |         u32 page_size_bits{big_page ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS};
  2303   703 | 
  2304   704 |         params.offset = u64(allocator.Allocate(u32(Common::AlignUp(size, page_size) >> page_size_bits))) << page_size_bits;
  2305   705 |         if (!params.offset) {
- 2306       |             nvmap.UnpinHandle(params.handle); // Allocation failed after NvMap pin.
  2307   706 |             ASSERT_MSG(false, "Failed to allocate free space in the GPU AS!");
  2308   707 |             return NvResult::InsufficientMemory;
  2309   708 |         }
  2310   709 |         gmmu->Map(params.offset, device_address, Common::AlignUp(size, page_size), Tegra::PTEKind(params.kind), big_page);
  2311   710 |         mapping_map.insert_or_assign(params.offset, Mapping(params.handle, device_address, params.offset, size, false, big_page, false));
  2312   711 |     }
  2313   712 | 
  2314   713 |     map_buffer_offsets.insert(params.offset);
  2315   714 | 
  2316   715 |     return NvResult::Success;
  2317   716 | }
```

</details>

### P0-M05 · AS-GPU UnmapBuffer

Comparer symétrie exacte avec MapBufferEx : taille, page size, aliases et invalidation. C'est aussi un candidat pour les fermetures DK/Pokopia si une traduction reste vivante après le propriétaire.

Encore : [nvhost_as_gpu.cpp:2319–2433](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L2319-L2433) — 115 lignes.

<details>
<summary>Lichii — 799–804 : 4 alignées, 111 propres Encore, 2 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:799–804](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L799-L804).

```diff
  2319   799 | NvResult nvhost_as_gpu::UnmapBuffer(IoctlUnmapBuffer& params) {
- 2320       |     // Native unmap also invalidates the GMMU and unpins NvMap memory.
- 2321       |     // Never let the producer retire backing ahead of an already queued
- 2322       |     // consumer. Do NOT wait with mutex held (GPU worker may read its PTEs).
- 2323       |     if (m_native_process &&
- 2324       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 2325       |         system.IsPoweredOn() && !system.IsShuttingDown())
- 2326       |         system.GPU().WaitForIdle();
- 2327       |     std::scoped_lock lock(mutex);
- 2328       |     if (native_sparse_poisoned && m_native_process &&
- 2329       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 2330       |         return NvResult::InvalidState;
- 2331       |     if (auto const offset_it = map_buffer_offsets.find(params.offset); offset_it != map_buffer_offsets.end()) {
  2332   800 |         LOG_DEBUG(Service_NVDRV, "called, offset={:#x}", params.offset);
- 2333       |         if (!vm.initialised) {
- 2334       |             return NvResult::BadValue;
- 2335       |         }
- 2336       | 
- 2337       |         auto const it = mapping_map.find(params.offset);
- 2338       |         // A stale unmap token is never a valid mapping. In particular a
- 2339       |         // FreeSpace/UnmapBuffer race must not dereference end() or free a
- 2340       |         // different allocation whose VA was re-used.
- 2341       |         if (it == mapping_map.end()) {
- 2342       |             map_buffer_offsets.erase(offset_it);
- 2343       |             return NvResult::BadValue;
- 2344       |         }
- 2345       |         auto const mapping = it->second;
- 2346       |         const bool native = m_native_process &&
- 2347       |                             NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2348       |         if (native) {
- 2349       |             // The GPU must relinquish its PTE/cache reference before VA or
- 2350       |             // NVMap backing can be released. On host OOM retain the ledger
- 2351       |             // and its physical pin, even if the unmap partially progressed.
- 2352       |             try {
- 2353       |                 if (mapping.sparse_alloc)
- 2354       |                     gmmu->MapSparse(params.offset, mapping.size, mapping.big_page);
- 2355       |                 else
- 2356       |                     gmmu->Unmap(params.offset, mapping.size);
- 2357       |                 if (!mapping.fixed) {
- 2358       |                     auto& allocator = mapping.big_page ? *vm.big_page_allocator
- 2359       |                                                        : *vm.small_page_allocator;
- 2360       |                     const u32 page_size = mapping.big_page ? vm.big_page_size
- 2361       |                                                              : VM::YUZU_PAGESIZE;
- 2362       |                     const u32 page_bits = mapping.big_page ? vm.big_page_size_bits
- 2363       |                                                              : VM::PAGE_SIZE_BITS;
- 2364       |                     const u64 rounded = Common::AlignUp(mapping.size, u64{page_size});
- 2365       |                     allocator.Free(u32(mapping.offset >> page_bits),
- 2366       |                                    u32(rounded >> page_bits));
- 2367       |                 }
- 2368       |             } catch (const std::bad_alloc&) {
- 2369       |                 PoisonNativeAddressSpace();
- 2370       |                 return NvResult::InsufficientMemory;
- 2371       |             }
- 2372       | 
- 2373       |             if (mapping.fixed) {
- 2374       |                 const auto owner = NativeGpuAllocation::FindContaining(
- 2375       |                     allocation_map, static_cast<u64>(params.offset), mapping.size);
- 2376       |                 if (owner != allocation_map.end()) {
- 2377       |                     auto& entries = owner->second.mappings;
- 2378       |                     entries.erase(std::remove(entries.begin(), entries.end(),
- 2379       |                                               static_cast<u64>(params.offset)), entries.end());
- 2380       |                 }
- 2381       |             }
- 2382       |             nvmap.UnpinHandle(mapping.handle);
- 2383       |             mapping_map.erase(params.offset);
- 2384       |             map_buffer_offsets.erase(params.offset);
- 2385       |             return NvResult::Success;
- 2386       |         }
- 2387       |         if (!mapping.fixed) {
- 2388       |             auto& allocator{mapping.big_page ? *vm.big_page_allocator : *vm.small_page_allocator};
- 2389       |             u32 page_size_bits{mapping.big_page ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS};
- 2390       |             // Allocate() reserved CEIL(size/page_size) pages, not the floor.
- 2391       |             // On native NS2 a partial final page must be returned too, or
- 2392       |             // repeated GPU texture/buffer streaming leaks virtual space.
- 2393       |             // Keep Maxwell's original release behavior untouched.
- 2394       |             const bool native =
- 2395       |                 m_native_process &&
- 2396       |                 NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2397       |             const u64 rounded_size = native
- 2398       |                 ? Common::AlignUp(mapping.size,
- 2399       |                                   mapping.big_page ? vm.big_page_size : VM::YUZU_PAGESIZE)
- 2400       |                 : mapping.size;
- 2401       |             allocator.Free(u32(mapping.offset >> page_size_bits),
- 2402       |                            u32(rounded_size >> page_size_bits));
- 2403       |         }
- 2404       | 
- 2405       |         // Sparse mappings shouldn't be fully unmapped, just returned to their sparse state
- 2406       |         // Only FreeSpace can unmap them fully
- 2407       |         if (mapping.sparse_alloc) {
- 2408       |             gmmu->MapSparse(params.offset, mapping.size, mapping.big_page);
- 2409       |         } else {
- 2410       |             gmmu->Unmap(params.offset, mapping.size);
- 2411       |         }
- 2412       | 
- 2413       |         // A fixed mapping may have been explicitly UnmapBuffer'd before
- 2414       |         // FreeSpace. Retire its allocation ledger reference now so the
- 2415       |         // later FreeSpace cannot try to unpin an already retired mapping.
- 2416       |         if (m_native_process &&
- 2417       |             NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 2418       |             mapping.fixed) {
- 2419       |             auto owner = NativeGpuAllocation::FindContaining(
- 2420       |                 allocation_map, static_cast<u64>(params.offset), mapping.size);
- 2421       |             if (owner != allocation_map.end()) {
- 2422       |                 auto& mappings = owner->second.mappings;
- 2423       |                 mappings.erase(std::remove(mappings.begin(), mappings.end(),
- 2424       |                                            static_cast<u64>(params.offset)),
- 2425       |                                mappings.end());
- 2426       |             }
- 2427       |         }
- 2428       |         nvmap.UnpinHandle(mapping.handle);
- 2429       |         mapping_map.erase(params.offset);
- 2430       |         map_buffer_offsets.erase(params.offset);
- 2431       |     }
+        801 |     std::scoped_lock lock(mutex);
+        802 |     void(FreeMappingLocked(params.offset));
  2432   803 |     return NvResult::Success;
  2433   804 | }
```

</details>

<details>
<summary>EglantinePS5 — 718–747 : 29 alignées, 86 propres Encore, 1 propres upstream</summary>

Source : [nvhost_as_gpu.cpp:718–747](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp#L718-L747).

```diff
  2319   718 | NvResult nvhost_as_gpu::UnmapBuffer(IoctlUnmapBuffer& params) {
- 2320       |     // Native unmap also invalidates the GMMU and unpins NvMap memory.
- 2321       |     // Never let the producer retire backing ahead of an already queued
- 2322       |     // consumer. Do NOT wait with mutex held (GPU worker may read its PTEs).
- 2323       |     if (m_native_process &&
- 2324       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 2325       |         system.IsPoweredOn() && !system.IsShuttingDown())
- 2326       |         system.GPU().WaitForIdle();
  2327   719 |     std::scoped_lock lock(mutex);
- 2328       |     if (native_sparse_poisoned && m_native_process &&
- 2329       |         NativeGpuProcessRegistry::Instance().Contains(m_native_process))
- 2330       |         return NvResult::InvalidState;
  2331   720 |     if (auto const offset_it = map_buffer_offsets.find(params.offset); offset_it != map_buffer_offsets.end()) {
  2332   721 |         LOG_DEBUG(Service_NVDRV, "called, offset={:#x}", params.offset);
  2333   722 |         if (!vm.initialised) {
  2334   723 |             return NvResult::BadValue;
  2335   724 |         }
  2336   725 | 
  2337   726 |         auto const it = mapping_map.find(params.offset);
- 2338       |         // A stale unmap token is never a valid mapping. In particular a
- 2339       |         // FreeSpace/UnmapBuffer race must not dereference end() or free a
- 2340       |         // different allocation whose VA was re-used.
- 2341       |         if (it == mapping_map.end()) {
- 2342       |             map_buffer_offsets.erase(offset_it);
- 2343       |             return NvResult::BadValue;
- 2344       |         }
  2345   727 |         auto const mapping = it->second;
- 2346       |         const bool native = m_native_process &&
- 2347       |                             NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2348       |         if (native) {
- 2349       |             // The GPU must relinquish its PTE/cache reference before VA or
- 2350       |             // NVMap backing can be released. On host OOM retain the ledger
- 2351       |             // and its physical pin, even if the unmap partially progressed.
- 2352       |             try {
- 2353       |                 if (mapping.sparse_alloc)
- 2354       |                     gmmu->MapSparse(params.offset, mapping.size, mapping.big_page);
- 2355       |                 else
- 2356       |                     gmmu->Unmap(params.offset, mapping.size);
  2357   728 |                 if (!mapping.fixed) {
- 2358       |                     auto& allocator = mapping.big_page ? *vm.big_page_allocator
- 2359       |                                                        : *vm.small_page_allocator;
- 2360       |                     const u32 page_size = mapping.big_page ? vm.big_page_size
- 2361       |                                                              : VM::YUZU_PAGESIZE;
- 2362       |                     const u32 page_bits = mapping.big_page ? vm.big_page_size_bits
- 2363       |                                                              : VM::PAGE_SIZE_BITS;
- 2364       |                     const u64 rounded = Common::AlignUp(mapping.size, u64{page_size});
- 2365       |                     allocator.Free(u32(mapping.offset >> page_bits),
- 2366       |                                    u32(rounded >> page_bits));
- 2367       |                 }
- 2368       |             } catch (const std::bad_alloc&) {
- 2369       |                 PoisonNativeAddressSpace();
- 2370       |                 return NvResult::InsufficientMemory;
- 2371       |             }
- 2372       | 
- 2373       |             if (mapping.fixed) {
- 2374       |                 const auto owner = NativeGpuAllocation::FindContaining(
- 2375       |                     allocation_map, static_cast<u64>(params.offset), mapping.size);
- 2376       |                 if (owner != allocation_map.end()) {
- 2377       |                     auto& entries = owner->second.mappings;
- 2378       |                     entries.erase(std::remove(entries.begin(), entries.end(),
- 2379       |                                               static_cast<u64>(params.offset)), entries.end());
- 2380       |                 }
- 2381       |             }
- 2382       |             nvmap.UnpinHandle(mapping.handle);
- 2383       |             mapping_map.erase(params.offset);
- 2384       |             map_buffer_offsets.erase(params.offset);
- 2385       |             return NvResult::Success;
- 2386       |         }
- 2387       |         if (!mapping.fixed) {
  2388   729 |             auto& allocator{mapping.big_page ? *vm.big_page_allocator : *vm.small_page_allocator};
  2389   730 |             u32 page_size_bits{mapping.big_page ? vm.big_page_size_bits : VM::PAGE_SIZE_BITS};
- 2390       |             // Allocate() reserved CEIL(size/page_size) pages, not the floor.
- 2391       |             // On native NS2 a partial final page must be returned too, or
- 2392       |             // repeated GPU texture/buffer streaming leaks virtual space.
- 2393       |             // Keep Maxwell's original release behavior untouched.
- 2394       |             const bool native =
- 2395       |                 m_native_process &&
- 2396       |                 NativeGpuProcessRegistry::Instance().Contains(m_native_process);
- 2397       |             const u64 rounded_size = native
- 2398       |                 ? Common::AlignUp(mapping.size,
- 2399       |                                   mapping.big_page ? vm.big_page_size : VM::YUZU_PAGESIZE)
- 2400       |                 : mapping.size;
- 2401       |             allocator.Free(u32(mapping.offset >> page_size_bits),
- 2402       |                            u32(rounded_size >> page_size_bits));
+        731 |             allocator.Free(u32(mapping.offset >> page_size_bits), u32(mapping.size >> page_size_bits));
  2403   732 |         }
  2404   733 | 
  2405   734 |         // Sparse mappings shouldn't be fully unmapped, just returned to their sparse state
  2406   735 |         // Only FreeSpace can unmap them fully
  2407   736 |         if (mapping.sparse_alloc) {
  2408   737 |             gmmu->MapSparse(params.offset, mapping.size, mapping.big_page);
  2409   738 |         } else {
  2410   739 |             gmmu->Unmap(params.offset, mapping.size);
  2411   740 |         }
  2412   741 | 
- 2413       |         // A fixed mapping may have been explicitly UnmapBuffer'd before
- 2414       |         // FreeSpace. Retire its allocation ledger reference now so the
- 2415       |         // later FreeSpace cannot try to unpin an already retired mapping.
- 2416       |         if (m_native_process &&
- 2417       |             NativeGpuProcessRegistry::Instance().Contains(m_native_process) &&
- 2418       |             mapping.fixed) {
- 2419       |             auto owner = NativeGpuAllocation::FindContaining(
- 2420       |                 allocation_map, static_cast<u64>(params.offset), mapping.size);
- 2421       |             if (owner != allocation_map.end()) {
- 2422       |                 auto& mappings = owner->second.mappings;
- 2423       |                 mappings.erase(std::remove(mappings.begin(), mappings.end(),
- 2424       |                                            static_cast<u64>(params.offset)),
- 2425       |                                mappings.end());
- 2426       |             }
- 2427       |         }
  2428   742 |         nvmap.UnpinHandle(mapping.handle);
  2429   743 |         mapping_map.erase(params.offset);
  2430   744 |         map_buffer_offsets.erase(params.offset);
  2431   745 |     }
  2432   746 |     return NvResult::Success;
  2433   747 | }
```

</details>

### P0-M06 · NVMap IocAlloc

Comparer alignement, kind, adresse, taille et état allocated. Encore est plus long que les forks : la comparaison ligne par ligne montre précisément les contrôles supplémentaires au lieu de traiter la longueur comme un écart fonctionnel.

Encore : [nvmap.cpp:100–184](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp#L100-L184) — 85 lignes.

<details>
<summary>Lichii — 99–142 : 40 alignées, 45 propres Encore, 4 propres upstream</summary>

Source : [nvmap.cpp:99–142](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvmap.cpp#L99-L142).

```diff
   100    99 | NvResult nvmap::IocAlloc(IocAllocParams& params, DeviceFD fd) {
   101   100 |     LOG_DEBUG(Service_NVDRV, "called, addr={:X}", params.address);
   102   101 | 
   103   102 |     if (!params.handle) {
   104   103 |         LOG_CRITICAL(Service_NVDRV, "Handle is 0");
   105   104 |         return NvResult::BadValue;
   106   105 |     }
   107   106 | 
   108   107 |     if ((params.align - 1) & params.align) {
   109   108 |         LOG_CRITICAL(Service_NVDRV, "Incorrect alignment used, alignment={:08X}", params.align);
   110   109 |         return NvResult::BadValue;
   111   110 |     }
   112   111 | 
   113   112 |     // Force page size alignment at a minimum
-  114       |     if (params.align < YUZU_PAGESIZE) {
-  115       |         params.align = YUZU_PAGESIZE;
+        113 |     if (params.align < LICHII_PAGESIZE) {
+        114 |         params.align = LICHII_PAGESIZE;
   116   115 |     }
   117   116 | 
   118   117 |     auto handle_description{file.GetHandle(params.handle)};
   119   118 |     if (!handle_description) {
   120   119 |         LOG_CRITICAL(Service_NVDRV, "Object does not exist, handle={:08X}", params.handle);
   121   120 |         return NvResult::BadValue;
   122   121 |     }
   123   122 | 
   124   123 |     if (handle_description->allocated) {
   125   124 |         LOG_CRITICAL(Service_NVDRV, "Object is already allocated, handle={:08X}", params.handle);
   126   125 |         return NvResult::InsufficientMemory;
   127   126 |     }
   128   127 | 
-  129       | #ifdef PS5_NATIVE
-  130       |     // A zero CPU backing cannot be pinned into the guest process address space.
-  131       |     // Do not report success with a handle whose pages do not exist: FC27's
-  132       |     // observed failure otherwise cascades into writes to address 0.
-  133       |     if (!params.address) {
-  134       |         LOG_ERROR(Service_NVDRV, "EDEN_NVMAP_REJECT_ZERO_ADDRESS handle={:08X} size={:X}",
-  135       |                   params.handle, handle_description->size);
-  136       |         return NvResult::BadValue;
-  137       |     }
-  138       | #endif
-  139       | 
-  140       |     // Never manufacture an NVDRV session when the caller supplies a stale FD.
-  141       |     // Verify ownership before Handle::Alloc mutates its allocated state.
-  142       |     const auto session_it = sessions.find(fd);
-  143       |     if (session_it == sessions.end()) {
-  144       |         return NvResult::BadValue;
-  145       |     }
-  146       |     auto* const session = container.GetSession(session_it->second);
-  147       |     if (!session || !session->process) {
-  148       |         return NvResult::BadValue;
-  149       |     }
   150   128 |     const auto result = handle_description->Alloc(params.flags, params.align, params.kind,
-  151       |                                                   params.address, session_it->second);
+        129 |                                                   params.address, sessions[fd]);
   152   130 |     if (result != NvResult::Success) {
   153   131 |         LOG_CRITICAL(Service_NVDRV, "Object failed to allocate, handle={:08X}", params.handle);
   154   132 |         return result;
   155   133 |     }
   156   134 |     bool is_out_io{};
-  157       |     auto* const process = session->process;
-  158       | #ifdef PS5_NATIVE
-  159       |     const auto map_result = process->GetPageTable().LockForMapDeviceAddressSpace(
-  160       |         &is_out_io, handle_description->address, handle_description->size,
-  161       |         Kernel::KMemoryPermission::None, true, false);
-  162       |     if (!map_result.IsSuccess()) {
-  163       |         // Handle::Alloc has already set allocated=true; without rollback,
-  164       |         // the guest receives a successful nvmap allocation for unmapped pages.
-  165       |         // No device lock was acquired on this failure path, so NEVER unlock.
-  166       |         LOG_ERROR(Service_NVDRV,
-  167       |                   "EDEN_NVMAP_MAP_FAILED handle={:08X} addr={:X} size={:X}",
-  168       |                   params.handle, handle_description->address, handle_description->size);
-  169       |         {
-  170       |             std::scoped_lock lock(handle_description->mutex);
-  171       |             handle_description->allocated = false;
-  172       |             handle_description->address = 0;
-  173       |         }
-  174       |         return NvResult::BadValue;
-  175       |     }
-  176       | #else
+        135 |     auto process = container.GetSession(sessions[fd])->process;
   177   136 |     ASSERT(process->GetPageTable()
   178   137 |                .LockForMapDeviceAddressSpace(&is_out_io, handle_description->address,
   179   138 |                                              handle_description->size,
   180   139 |                                              Kernel::KMemoryPermission::None, true, false)
   181   140 |                .IsSuccess());
-  182       | #endif
   183   141 |     return result;
   184   142 | }
```

</details>

<details>
<summary>EglantinePS5 — 100–143 : 42 alignées, 43 propres Encore, 2 propres upstream</summary>

Source : [nvmap.cpp:100–143](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvmap.cpp#L100-L143).

```diff
   100   100 | NvResult nvmap::IocAlloc(IocAllocParams& params, DeviceFD fd) {
   101   101 |     LOG_DEBUG(Service_NVDRV, "called, addr={:X}", params.address);
   102   102 | 
   103   103 |     if (!params.handle) {
   104   104 |         LOG_CRITICAL(Service_NVDRV, "Handle is 0");
   105   105 |         return NvResult::BadValue;
   106   106 |     }
   107   107 | 
   108   108 |     if ((params.align - 1) & params.align) {
   109   109 |         LOG_CRITICAL(Service_NVDRV, "Incorrect alignment used, alignment={:08X}", params.align);
   110   110 |         return NvResult::BadValue;
   111   111 |     }
   112   112 | 
   113   113 |     // Force page size alignment at a minimum
   114   114 |     if (params.align < YUZU_PAGESIZE) {
   115   115 |         params.align = YUZU_PAGESIZE;
   116   116 |     }
   117   117 | 
   118   118 |     auto handle_description{file.GetHandle(params.handle)};
   119   119 |     if (!handle_description) {
   120   120 |         LOG_CRITICAL(Service_NVDRV, "Object does not exist, handle={:08X}", params.handle);
   121   121 |         return NvResult::BadValue;
   122   122 |     }
   123   123 | 
   124   124 |     if (handle_description->allocated) {
   125   125 |         LOG_CRITICAL(Service_NVDRV, "Object is already allocated, handle={:08X}", params.handle);
   126   126 |         return NvResult::InsufficientMemory;
   127   127 |     }
   128   128 | 
-  129       | #ifdef PS5_NATIVE
-  130       |     // A zero CPU backing cannot be pinned into the guest process address space.
-  131       |     // Do not report success with a handle whose pages do not exist: FC27's
-  132       |     // observed failure otherwise cascades into writes to address 0.
-  133       |     if (!params.address) {
-  134       |         LOG_ERROR(Service_NVDRV, "EDEN_NVMAP_REJECT_ZERO_ADDRESS handle={:08X} size={:X}",
-  135       |                   params.handle, handle_description->size);
-  136       |         return NvResult::BadValue;
-  137       |     }
-  138       | #endif
-  139       | 
-  140       |     // Never manufacture an NVDRV session when the caller supplies a stale FD.
-  141       |     // Verify ownership before Handle::Alloc mutates its allocated state.
-  142       |     const auto session_it = sessions.find(fd);
-  143       |     if (session_it == sessions.end()) {
-  144       |         return NvResult::BadValue;
-  145       |     }
-  146       |     auto* const session = container.GetSession(session_it->second);
-  147       |     if (!session || !session->process) {
-  148       |         return NvResult::BadValue;
-  149       |     }
   150   129 |     const auto result = handle_description->Alloc(params.flags, params.align, params.kind,
-  151       |                                                   params.address, session_it->second);
+        130 |                                                   params.address, sessions[fd]);
   152   131 |     if (result != NvResult::Success) {
   153   132 |         LOG_CRITICAL(Service_NVDRV, "Object failed to allocate, handle={:08X}", params.handle);
   154   133 |         return result;
   155   134 |     }
   156   135 |     bool is_out_io{};
-  157       |     auto* const process = session->process;
-  158       | #ifdef PS5_NATIVE
-  159       |     const auto map_result = process->GetPageTable().LockForMapDeviceAddressSpace(
-  160       |         &is_out_io, handle_description->address, handle_description->size,
-  161       |         Kernel::KMemoryPermission::None, true, false);
-  162       |     if (!map_result.IsSuccess()) {
-  163       |         // Handle::Alloc has already set allocated=true; without rollback,
-  164       |         // the guest receives a successful nvmap allocation for unmapped pages.
-  165       |         // No device lock was acquired on this failure path, so NEVER unlock.
-  166       |         LOG_ERROR(Service_NVDRV,
-  167       |                   "EDEN_NVMAP_MAP_FAILED handle={:08X} addr={:X} size={:X}",
-  168       |                   params.handle, handle_description->address, handle_description->size);
-  169       |         {
-  170       |             std::scoped_lock lock(handle_description->mutex);
-  171       |             handle_description->allocated = false;
-  172       |             handle_description->address = 0;
-  173       |         }
-  174       |         return NvResult::BadValue;
-  175       |     }
-  176       | #else
+        136 |     auto process = container.GetSession(sessions[fd])->process;
   177   137 |     ASSERT(process->GetPageTable()
   178   138 |                .LockForMapDeviceAddressSpace(&is_out_io, handle_description->address,
   179   139 |                                              handle_description->size,
   180   140 |                                              Kernel::KMemoryPermission::None, true, false)
   181   141 |                .IsSuccess());
-  182       | #endif
   183   142 |     return result;
   184   143 | }
```

</details>

### P0-M07 · NVMap IocFromId

Contrat de duplication/référence d'un handle partagé. Pertinent aux images GSV : une référence supplémentaire doit être libérée exactement une fois.

Encore : [nvmap.cpp:206–231](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp#L206-L231) — 26 lignes.

<details>
<summary>Lichii — 164–189 : 26 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nvmap.cpp:164–189](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvmap.cpp#L164-L189).

```diff
   206   164 | NvResult nvmap::IocFromId(IocFromIdParams& params) {
   207   165 |     LOG_DEBUG(Service_NVDRV, "called, id:{}", params.id);
   208   166 | 
   209   167 |     // Handles and IDs are always the same value in nvmap however IDs can be used globally given the
   210   168 |     // right permissions.
   211   169 |     // Since we don't plan on ever supporting multiprocess we can skip implementing handle refs and
   212   170 |     // so this function just does simple validation and passes through the handle id.
   213   171 |     if (!params.id) {
   214   172 |         LOG_CRITICAL(Service_NVDRV, "Zero Id is invalid!");
   215   173 |         return NvResult::BadValue;
   216   174 |     }
   217   175 | 
   218   176 |     auto handle_description{file.GetHandle(params.id)};
   219   177 |     if (!handle_description) {
   220   178 |         LOG_CRITICAL(Service_NVDRV, "Unregistered handle!");
   221   179 |         return NvResult::BadValue;
   222   180 |     }
   223   181 | 
   224   182 |     auto result = handle_description->Duplicate(false);
   225   183 |     if (result != NvResult::Success) {
   226   184 |         LOG_CRITICAL(Service_NVDRV, "Could not duplicate handle!");
   227   185 |         return result;
   228   186 |     }
   229   187 |     params.handle = handle_description->id;
   230   188 |     return NvResult::Success;
   231   189 | }
```

</details>

<details>
<summary>EglantinePS5 — 165–190 : 26 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nvmap.cpp:165–190](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvmap.cpp#L165-L190).

```diff
   206   165 | NvResult nvmap::IocFromId(IocFromIdParams& params) {
   207   166 |     LOG_DEBUG(Service_NVDRV, "called, id:{}", params.id);
   208   167 | 
   209   168 |     // Handles and IDs are always the same value in nvmap however IDs can be used globally given the
   210   169 |     // right permissions.
   211   170 |     // Since we don't plan on ever supporting multiprocess we can skip implementing handle refs and
   212   171 |     // so this function just does simple validation and passes through the handle id.
   213   172 |     if (!params.id) {
   214   173 |         LOG_CRITICAL(Service_NVDRV, "Zero Id is invalid!");
   215   174 |         return NvResult::BadValue;
   216   175 |     }
   217   176 | 
   218   177 |     auto handle_description{file.GetHandle(params.id)};
   219   178 |     if (!handle_description) {
   220   179 |         LOG_CRITICAL(Service_NVDRV, "Unregistered handle!");
   221   180 |         return NvResult::BadValue;
   222   181 |     }
   223   182 | 
   224   183 |     auto result = handle_description->Duplicate(false);
   225   184 |     if (result != NvResult::Success) {
   226   185 |         LOG_CRITICAL(Service_NVDRV, "Could not duplicate handle!");
   227   186 |         return result;
   228   187 |     }
   229   188 |     params.handle = handle_description->id;
   230   189 |     return NvResult::Success;
   231   190 | }
```

</details>

### P0-M08 · NVMap IocFree

Comparer decrement de références, destruction et retour d'adresse/taille. À relier au nouveau pool GSV base+i, qui duplique une référence par image.

Encore : [nvmap.cpp:278–310](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp#L278-L310) — 33 lignes.

<details>
<summary>Lichii — 236–260 : 24 alignées, 9 propres Encore, 1 propres upstream</summary>

Source : [nvmap.cpp:236–260](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nvdrv/devices/nvmap.cpp#L236-L260).

```diff
   278   236 | NvResult nvmap::IocFree(IocFreeParams& params, DeviceFD fd) {
   279   237 |     LOG_DEBUG(Service_NVDRV, "called");
   280   238 | 
   281   239 |     if (!params.handle) {
   282   240 |         LOG_CRITICAL(Service_NVDRV, "Handle null freed?");
   283   241 |         return NvResult::Success;
   284   242 |     }
   285   243 | 
-  286       |     const auto session_it = sessions.find(fd);
-  287       |     if (session_it == sessions.end()) {
-  288       |         return NvResult::BadValue;
-  289       |     }
-  290       |     auto* const session = container.GetSession(session_it->second);
-  291       |     if (!session || !session->process) {
-  292       |         return NvResult::BadValue;
-  293       |     }
   294   244 |     if (auto freeInfo{file.FreeHandle(params.handle, false)}) {
-  295       |         auto* const process = session->process;
+        245 |         auto process = container.GetSession(sessions[fd])->process;
   296   246 |         if (freeInfo->can_unlock) {
   297   247 |             ASSERT(process->GetPageTable()
   298   248 |                        .UnlockForDeviceAddressSpace(freeInfo->address, freeInfo->size)
   299   249 |                        .IsSuccess());
   300   250 |         }
   301   251 |         params.address = freeInfo->address;
   302   252 |         params.size = static_cast<u32>(freeInfo->size);
   303   253 |         params.flags.raw = 0;
   304   254 |         params.flags.map_uncached.Assign(freeInfo->was_uncached);
   305   255 |     } else {
   306   256 |         // This is possible when there's internal dups or other duplicates.
   307   257 |     }
   308   258 | 
   309   259 |     return NvResult::Success;
   310   260 | }
```

</details>

<details>
<summary>EglantinePS5 — 237–261 : 24 alignées, 9 propres Encore, 1 propres upstream</summary>

Source : [nvmap.cpp:237–261](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nvdrv/devices/nvmap.cpp#L237-L261).

```diff
   278   237 | NvResult nvmap::IocFree(IocFreeParams& params, DeviceFD fd) {
   279   238 |     LOG_DEBUG(Service_NVDRV, "called");
   280   239 | 
   281   240 |     if (!params.handle) {
   282   241 |         LOG_CRITICAL(Service_NVDRV, "Handle null freed?");
   283   242 |         return NvResult::Success;
   284   243 |     }
   285   244 | 
-  286       |     const auto session_it = sessions.find(fd);
-  287       |     if (session_it == sessions.end()) {
-  288       |         return NvResult::BadValue;
-  289       |     }
-  290       |     auto* const session = container.GetSession(session_it->second);
-  291       |     if (!session || !session->process) {
-  292       |         return NvResult::BadValue;
-  293       |     }
   294   245 |     if (auto freeInfo{file.FreeHandle(params.handle, false)}) {
-  295       |         auto* const process = session->process;
+        246 |         auto process = container.GetSession(sessions[fd])->process;
   296   247 |         if (freeInfo->can_unlock) {
   297   248 |             ASSERT(process->GetPageTable()
   298   249 |                        .UnlockForDeviceAddressSpace(freeInfo->address, freeInfo->size)
   299   250 |                        .IsSuccess());
   300   251 |         }
   301   252 |         params.address = freeInfo->address;
   302   253 |         params.size = static_cast<u32>(freeInfo->size);
   303   254 |         params.flags.raw = 0;
   304   255 |         params.flags.map_uncached.Assign(freeInfo->was_uncached);
   305   256 |     } else {
   306   257 |         // This is possible when there's internal dups or other duplicates.
   307   258 |     }
   308   259 | 
   309   260 |     return NvResult::Success;
   310   261 | }
```

</details>

### P0-K01 · KPageTableBase::SetHeapSize

Le cœur KPageTable est presque ancestralement commun, mais Eglantine contient des adaptations PS5 supplémentaires. Pour MKW/Pokopia, la question utile est la réservation physique réelle et le rollback en cas d'échec, pas seulement la valeur retournée au SVC.

Encore : [k_page_table_base.cpp:2150–2299](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp#L2150-L2299) — 150 lignes.

<details>
<summary>Lichii — 2181–2330 : 150 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [k_page_table_base.cpp:2181–2330](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/kernel/k_page_table_base.cpp#L2181-L2330).

```diff
  2150  2181 | Result KPageTableBase::SetHeapSize(KProcessAddress* out, size_t size) {
  2151  2182 |     // Lock the physical memory mutex.
  2152  2183 |     KScopedLightLock map_phys_mem_lk(m_map_physical_memory_lock);
  2153  2184 | 
  2154  2185 |     // Try to perform a reduction in heap, instead of an extension.
  2155  2186 |     KProcessAddress cur_address;
  2156  2187 |     size_t allocation_size;
  2157  2188 |     {
  2158  2189 |         // Lock the table.
  2159  2190 |         KScopedLightLock lk(m_general_lock);
  2160  2191 | 
  2161  2192 |         // Validate that setting heap size is possible at all.
  2162  2193 |         R_UNLESS(!m_is_kernel, ResultOutOfMemory);
  2163  2194 |         R_UNLESS(size <= static_cast<size_t>(m_heap_region_end - m_heap_region_start),
  2164  2195 |                  ResultOutOfMemory);
  2165  2196 |         R_UNLESS(size <= m_max_heap_size, ResultOutOfMemory);
  2166  2197 | 
  2167  2198 |         if (size < static_cast<size_t>(m_current_heap_end - m_heap_region_start)) {
  2168  2199 |             // The size being requested is less than the current size, so we need to free the end of
  2169  2200 |             // the heap.
  2170  2201 | 
  2171  2202 |             // Validate memory state.
  2172  2203 |             size_t num_allocator_blocks;
  2173  2204 |             R_TRY(this->CheckMemoryState(
  2174  2205 |                 std::addressof(num_allocator_blocks), m_heap_region_start + size,
  2175  2206 |                 (m_current_heap_end - m_heap_region_start) - size, KMemoryState::All,
  2176  2207 |                 KMemoryState::Normal, KMemoryPermission::All, KMemoryPermission::UserReadWrite,
  2177  2208 |                 KMemoryAttribute::All, KMemoryAttribute::None));
  2178  2209 | 
  2179  2210 |             // Create an update allocator.
  2180  2211 |             Result allocator_result;
  2181  2212 |             KMemoryBlockManagerUpdateAllocator allocator(std::addressof(allocator_result),
  2182  2213 |                                                          m_memory_block_slab_manager,
  2183  2214 |                                                          num_allocator_blocks);
  2184  2215 |             R_TRY(allocator_result);
  2185  2216 | 
  2186  2217 |             // We're going to perform an update, so create a helper.
  2187  2218 |             KScopedPageTableUpdater updater(this);
  2188  2219 | 
  2189  2220 |             // Unmap the end of the heap.
  2190  2221 |             const size_t num_pages = ((m_current_heap_end - m_heap_region_start) - size) / PageSize;
  2191  2222 |             const KPageProperties unmap_properties = {KMemoryPermission::None, false, false,
  2192  2223 |                                                       DisableMergeAttribute::None};
  2193  2224 |             R_TRY(this->Operate(updater.GetPageList(), m_heap_region_start + size, num_pages, 0,
  2194  2225 |                                 false, unmap_properties, OperationType::Unmap, false));
  2195  2226 | 
  2196  2227 |             // Release the memory from the resource limit.
  2197  2228 |             m_resource_limit->Release(m_system.Kernel(), Svc::LimitableResource::PhysicalMemoryMax,
  2198  2229 |                                       num_pages * PageSize);
  2199  2230 | 
  2200  2231 |             // Apply the memory block update.
  2201  2232 |             m_memory_block_manager.Update(std::addressof(allocator), m_heap_region_start + size,
  2202  2233 |                                           num_pages, KMemoryState::Free, KMemoryPermission::None,
  2203  2234 |                                           KMemoryAttribute::None,
  2204  2235 |                                           KMemoryBlockDisableMergeAttribute::None,
  2205  2236 |                                           size == 0 ? KMemoryBlockDisableMergeAttribute::Normal
  2206  2237 |                                                     : KMemoryBlockDisableMergeAttribute::None);
  2207  2238 | 
  2208  2239 |             // Update the current heap end.
  2209  2240 |             m_current_heap_end = m_heap_region_start + size;
  2210  2241 | 
  2211  2242 |             // Set the output.
  2212  2243 |             *out = m_heap_region_start;
  2213  2244 |             R_SUCCEED();
  2214  2245 |         } else if (size == static_cast<size_t>(m_current_heap_end - m_heap_region_start)) {
  2215  2246 |             // The size requested is exactly the current size.
  2216  2247 |             *out = m_heap_region_start;
  2217  2248 |             R_SUCCEED();
  2218  2249 |         } else {
  2219  2250 |             // We have to allocate memory. Determine how much to allocate and where while the table
  2220  2251 |             // is locked.
  2221  2252 |             cur_address = m_current_heap_end;
  2222  2253 |             allocation_size = size - (m_current_heap_end - m_heap_region_start);
  2223  2254 |         }
  2224  2255 |     }
  2225  2256 | 
  2226  2257 |     // Reserve memory for the heap extension.
  2227  2258 |     KScopedResourceReservation memory_reservation(m_system.Kernel(),
  2228  2259 |         m_resource_limit, Svc::LimitableResource::PhysicalMemoryMax, allocation_size);
  2229  2260 |     R_UNLESS(memory_reservation.Succeeded(), ResultLimitReached);
  2230  2261 | 
  2231  2262 |     // Allocate pages for the heap extension.
  2232  2263 |     KPageGroup pg(m_system.Kernel(), m_block_info_manager);
  2233  2264 |     R_TRY(m_system.Kernel().MemoryManager().AllocateAndOpen(std::addressof(pg), allocation_size / PageSize,
  2234  2265 |                                                    m_allocate_option));
  2235  2266 | 
  2236  2267 |     // Close the opened pages when we're done with them.
  2237  2268 |     // If the mapping succeeds, each page will gain an extra reference, otherwise they will be freed
  2238  2269 |     // automatically.
  2239  2270 |     SCOPE_EXIT {
  2240  2271 |         pg.Close(m_system.Kernel());
  2241  2272 |     };
  2242  2273 | 
  2243  2274 |     // Clear all the newly allocated pages.
  2244  2275 |     for (const auto& it : pg) {
  2245  2276 |         ClearBackingRegion(m_system, it.GetAddress(), it.GetSize(), m_heap_fill_value);
  2246  2277 |     }
  2247  2278 | 
  2248  2279 |     // Map the pages.
  2249  2280 |     {
  2250  2281 |         // Lock the table.
  2251  2282 |         KScopedLightLock lk(m_general_lock);
  2252  2283 | 
  2253  2284 |         // Ensure that the heap hasn't changed since we began executing.
  2254  2285 |         ASSERT(cur_address == m_current_heap_end);
  2255  2286 | 
  2256  2287 |         // Check the memory state.
  2257  2288 |         size_t num_allocator_blocks;
  2258  2289 |         R_TRY(this->CheckMemoryState(std::addressof(num_allocator_blocks), m_current_heap_end,
  2259  2290 |                                      allocation_size, KMemoryState::All, KMemoryState::Free,
  2260  2291 |                                      KMemoryPermission::None, KMemoryPermission::None,
  2261  2292 |                                      KMemoryAttribute::None, KMemoryAttribute::None));
  2262  2293 | 
  2263  2294 |         // Create an update allocator.
  2264  2295 |         Result allocator_result;
  2265  2296 |         KMemoryBlockManagerUpdateAllocator allocator(
  2266  2297 |             std::addressof(allocator_result), m_memory_block_slab_manager, num_allocator_blocks);
  2267  2298 |         R_TRY(allocator_result);
  2268  2299 | 
  2269  2300 |         // We're going to perform an update, so create a helper.
  2270  2301 |         KScopedPageTableUpdater updater(this);
  2271  2302 | 
  2272  2303 |         // Map the pages.
  2273  2304 |         const size_t num_pages = allocation_size / PageSize;
  2274  2305 |         const KPageProperties map_properties = {KMemoryPermission::UserReadWrite, false, false,
  2275  2306 |                                                 (m_current_heap_end == m_heap_region_start)
  2276  2307 |                                                     ? DisableMergeAttribute::DisableHead
  2277  2308 |                                                     : DisableMergeAttribute::None};
  2278  2309 |         R_TRY(this->Operate(updater.GetPageList(), m_current_heap_end, num_pages, pg,
  2279  2310 |                             map_properties, OperationType::MapGroup, false));
  2280  2311 | 
  2281  2312 |         // We succeeded, so commit our memory reservation.
  2282  2313 |         memory_reservation.Commit();
  2283  2314 | 
  2284  2315 |         // Apply the memory block update.
  2285  2316 |         m_memory_block_manager.Update(
  2286  2317 |             std::addressof(allocator), m_current_heap_end, num_pages, KMemoryState::Normal,
  2287  2318 |             KMemoryPermission::UserReadWrite, KMemoryAttribute::None,
  2288  2319 |             m_heap_region_start == m_current_heap_end ? KMemoryBlockDisableMergeAttribute::Normal
  2289  2320 |                                                       : KMemoryBlockDisableMergeAttribute::None,
  2290  2321 |             KMemoryBlockDisableMergeAttribute::None);
  2291  2322 | 
  2292  2323 |         // Update the current heap end.
  2293  2324 |         m_current_heap_end = m_heap_region_start + size;
  2294  2325 | 
  2295  2326 |         // Set the output.
  2296  2327 |         *out = m_heap_region_start;
  2297  2328 |         R_SUCCEED();
  2298  2329 |     }
  2299  2330 | }
```

</details>

<details>
<summary>EglantinePS5 — 2249–2398 : 150 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [k_page_table_base.cpp:2249–2398](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/kernel/k_page_table_base.cpp#L2249-L2398).

```diff
  2150  2249 | Result KPageTableBase::SetHeapSize(KProcessAddress* out, size_t size) {
  2151  2250 |     // Lock the physical memory mutex.
  2152  2251 |     KScopedLightLock map_phys_mem_lk(m_map_physical_memory_lock);
  2153  2252 | 
  2154  2253 |     // Try to perform a reduction in heap, instead of an extension.
  2155  2254 |     KProcessAddress cur_address;
  2156  2255 |     size_t allocation_size;
  2157  2256 |     {
  2158  2257 |         // Lock the table.
  2159  2258 |         KScopedLightLock lk(m_general_lock);
  2160  2259 | 
  2161  2260 |         // Validate that setting heap size is possible at all.
  2162  2261 |         R_UNLESS(!m_is_kernel, ResultOutOfMemory);
  2163  2262 |         R_UNLESS(size <= static_cast<size_t>(m_heap_region_end - m_heap_region_start),
  2164  2263 |                  ResultOutOfMemory);
  2165  2264 |         R_UNLESS(size <= m_max_heap_size, ResultOutOfMemory);
  2166  2265 | 
  2167  2266 |         if (size < static_cast<size_t>(m_current_heap_end - m_heap_region_start)) {
  2168  2267 |             // The size being requested is less than the current size, so we need to free the end of
  2169  2268 |             // the heap.
  2170  2269 | 
  2171  2270 |             // Validate memory state.
  2172  2271 |             size_t num_allocator_blocks;
  2173  2272 |             R_TRY(this->CheckMemoryState(
  2174  2273 |                 std::addressof(num_allocator_blocks), m_heap_region_start + size,
  2175  2274 |                 (m_current_heap_end - m_heap_region_start) - size, KMemoryState::All,
  2176  2275 |                 KMemoryState::Normal, KMemoryPermission::All, KMemoryPermission::UserReadWrite,
  2177  2276 |                 KMemoryAttribute::All, KMemoryAttribute::None));
  2178  2277 | 
  2179  2278 |             // Create an update allocator.
  2180  2279 |             Result allocator_result;
  2181  2280 |             KMemoryBlockManagerUpdateAllocator allocator(std::addressof(allocator_result),
  2182  2281 |                                                          m_memory_block_slab_manager,
  2183  2282 |                                                          num_allocator_blocks);
  2184  2283 |             R_TRY(allocator_result);
  2185  2284 | 
  2186  2285 |             // We're going to perform an update, so create a helper.
  2187  2286 |             KScopedPageTableUpdater updater(this);
  2188  2287 | 
  2189  2288 |             // Unmap the end of the heap.
  2190  2289 |             const size_t num_pages = ((m_current_heap_end - m_heap_region_start) - size) / PageSize;
  2191  2290 |             const KPageProperties unmap_properties = {KMemoryPermission::None, false, false,
  2192  2291 |                                                       DisableMergeAttribute::None};
  2193  2292 |             R_TRY(this->Operate(updater.GetPageList(), m_heap_region_start + size, num_pages, 0,
  2194  2293 |                                 false, unmap_properties, OperationType::Unmap, false));
  2195  2294 | 
  2196  2295 |             // Release the memory from the resource limit.
  2197  2296 |             m_resource_limit->Release(m_system.Kernel(), Svc::LimitableResource::PhysicalMemoryMax,
  2198  2297 |                                       num_pages * PageSize);
  2199  2298 | 
  2200  2299 |             // Apply the memory block update.
  2201  2300 |             m_memory_block_manager.Update(std::addressof(allocator), m_heap_region_start + size,
  2202  2301 |                                           num_pages, KMemoryState::Free, KMemoryPermission::None,
  2203  2302 |                                           KMemoryAttribute::None,
  2204  2303 |                                           KMemoryBlockDisableMergeAttribute::None,
  2205  2304 |                                           size == 0 ? KMemoryBlockDisableMergeAttribute::Normal
  2206  2305 |                                                     : KMemoryBlockDisableMergeAttribute::None);
  2207  2306 | 
  2208  2307 |             // Update the current heap end.
  2209  2308 |             m_current_heap_end = m_heap_region_start + size;
  2210  2309 | 
  2211  2310 |             // Set the output.
  2212  2311 |             *out = m_heap_region_start;
  2213  2312 |             R_SUCCEED();
  2214  2313 |         } else if (size == static_cast<size_t>(m_current_heap_end - m_heap_region_start)) {
  2215  2314 |             // The size requested is exactly the current size.
  2216  2315 |             *out = m_heap_region_start;
  2217  2316 |             R_SUCCEED();
  2218  2317 |         } else {
  2219  2318 |             // We have to allocate memory. Determine how much to allocate and where while the table
  2220  2319 |             // is locked.
  2221  2320 |             cur_address = m_current_heap_end;
  2222  2321 |             allocation_size = size - (m_current_heap_end - m_heap_region_start);
  2223  2322 |         }
  2224  2323 |     }
  2225  2324 | 
  2226  2325 |     // Reserve memory for the heap extension.
  2227  2326 |     KScopedResourceReservation memory_reservation(m_system.Kernel(),
  2228  2327 |         m_resource_limit, Svc::LimitableResource::PhysicalMemoryMax, allocation_size);
  2229  2328 |     R_UNLESS(memory_reservation.Succeeded(), ResultLimitReached);
  2230  2329 | 
  2231  2330 |     // Allocate pages for the heap extension.
  2232  2331 |     KPageGroup pg(m_system.Kernel(), m_block_info_manager);
  2233  2332 |     R_TRY(m_system.Kernel().MemoryManager().AllocateAndOpen(std::addressof(pg), allocation_size / PageSize,
  2234  2333 |                                                    m_allocate_option));
  2235  2334 | 
  2236  2335 |     // Close the opened pages when we're done with them.
  2237  2336 |     // If the mapping succeeds, each page will gain an extra reference, otherwise they will be freed
  2238  2337 |     // automatically.
  2239  2338 |     SCOPE_EXIT {
  2240  2339 |         pg.Close(m_system.Kernel());
  2241  2340 |     };
  2242  2341 | 
  2243  2342 |     // Clear all the newly allocated pages.
  2244  2343 |     for (const auto& it : pg) {
  2245  2344 |         ClearBackingRegion(m_system, it.GetAddress(), it.GetSize(), m_heap_fill_value);
  2246  2345 |     }
  2247  2346 | 
  2248  2347 |     // Map the pages.
  2249  2348 |     {
  2250  2349 |         // Lock the table.
  2251  2350 |         KScopedLightLock lk(m_general_lock);
  2252  2351 | 
  2253  2352 |         // Ensure that the heap hasn't changed since we began executing.
  2254  2353 |         ASSERT(cur_address == m_current_heap_end);
  2255  2354 | 
  2256  2355 |         // Check the memory state.
  2257  2356 |         size_t num_allocator_blocks;
  2258  2357 |         R_TRY(this->CheckMemoryState(std::addressof(num_allocator_blocks), m_current_heap_end,
  2259  2358 |                                      allocation_size, KMemoryState::All, KMemoryState::Free,
  2260  2359 |                                      KMemoryPermission::None, KMemoryPermission::None,
  2261  2360 |                                      KMemoryAttribute::None, KMemoryAttribute::None));
  2262  2361 | 
  2263  2362 |         // Create an update allocator.
  2264  2363 |         Result allocator_result;
  2265  2364 |         KMemoryBlockManagerUpdateAllocator allocator(
  2266  2365 |             std::addressof(allocator_result), m_memory_block_slab_manager, num_allocator_blocks);
  2267  2366 |         R_TRY(allocator_result);
  2268  2367 | 
  2269  2368 |         // We're going to perform an update, so create a helper.
  2270  2369 |         KScopedPageTableUpdater updater(this);
  2271  2370 | 
  2272  2371 |         // Map the pages.
  2273  2372 |         const size_t num_pages = allocation_size / PageSize;
  2274  2373 |         const KPageProperties map_properties = {KMemoryPermission::UserReadWrite, false, false,
  2275  2374 |                                                 (m_current_heap_end == m_heap_region_start)
  2276  2375 |                                                     ? DisableMergeAttribute::DisableHead
  2277  2376 |                                                     : DisableMergeAttribute::None};
  2278  2377 |         R_TRY(this->Operate(updater.GetPageList(), m_current_heap_end, num_pages, pg,
  2279  2378 |                             map_properties, OperationType::MapGroup, false));
  2280  2379 | 
  2281  2380 |         // We succeeded, so commit our memory reservation.
  2282  2381 |         memory_reservation.Commit();
  2283  2382 | 
  2284  2383 |         // Apply the memory block update.
  2285  2384 |         m_memory_block_manager.Update(
  2286  2385 |             std::addressof(allocator), m_current_heap_end, num_pages, KMemoryState::Normal,
  2287  2386 |             KMemoryPermission::UserReadWrite, KMemoryAttribute::None,
  2288  2387 |             m_heap_region_start == m_current_heap_end ? KMemoryBlockDisableMergeAttribute::Normal
  2289  2388 |                                                       : KMemoryBlockDisableMergeAttribute::None,
  2290  2389 |             KMemoryBlockDisableMergeAttribute::None);
  2291  2390 | 
  2292  2391 |         // Update the current heap end.
  2293  2392 |         m_current_heap_end = m_heap_region_start + size;
  2294  2393 | 
  2295  2394 |         // Set the output.
  2296  2395 |         *out = m_heap_region_start;
  2297  2396 |         R_SUCCEED();
  2298  2397 |     }
  2299  2398 | }
```

</details>

### P0-K02 · SVC SetHeapSize

Couche ABI au-dessus de KPageTable. Comparer validation d'alignement/taille et propagation Result ; les différences de wrappers 64/32 sont documentées séparément.

Encore : [svc_physical_memory.cpp:16–36](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp#L16-L36) — 21 lignes.

<details>
<summary>Lichii — 17–36 : 19 alignées, 2 propres Encore, 1 propres upstream</summary>

Source : [svc_physical_memory.cpp:17–36](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/kernel/svc/svc_physical_memory.cpp#L17-L36).

```diff
    16    17 | Result SetHeapSize(Core::System& system, u64* out_address, u64 size) {
    17    18 |     LOG_TRACE(Kernel_SVC, "called, heap_size={:#x}", size);
    18    19 | 
    19    20 |     // Validate size.
    20    21 |     R_UNLESS(Common::IsAligned(size, HeapSizeAlignment), ResultInvalidSize);
-   21       |     // Keep the NS1 limit when the kernel intends 8 GiB, but admit NS2's
-   22       |     // larger virtual heap when a 12 GiB guest memory layout is selected.
+         22 |     // Switch 2 titles size their heap from the total memory, which exceeds Switch 1's 8 GiB.
    23    23 |     const size_t max_heap_size =
    24    24 |         (std::max)(MainMemorySizeMax, KSystemControl::Init::GetIntendedMemorySize());
    25    25 |     R_UNLESS(size < max_heap_size, ResultInvalidSize);
    26    26 | 
    27    27 |     // Set the heap size.
    28    28 |     KProcessAddress address{};
    29    29 |     R_TRY(GetCurrentProcess(system.Kernel())
    30    30 |               .GetPageTable()
    31    31 |               .SetHeapSize(std::addressof(address), size));
    32    32 | 
    33    33 |     // We succeeded.
    34    34 |     *out_address = GetInteger(address);
    35    35 |     R_SUCCEED();
    36    36 | }
```

</details>

<details>
<summary>EglantinePS5 — 19–45 : 19 alignées, 2 propres Encore, 8 propres upstream</summary>

Source : [svc_physical_memory.cpp:19–45](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/kernel/svc/svc_physical_memory.cpp#L19-L45).

```diff
    16    19 | Result SetHeapSize(Core::System& system, u64* out_address, u64 size) {
+         20 |     MemoryStats::Note(MemoryStats::SetHeapSize, size, true);
    17    21 |     LOG_TRACE(Kernel_SVC, "called, heap_size={:#x}", size);
    18    22 | 
    19    23 |     // Validate size.
    20    24 |     R_UNLESS(Common::IsAligned(size, HeapSizeAlignment), ResultInvalidSize);
-   21       |     // Keep the NS1 limit when the kernel intends 8 GiB, but admit NS2's
-   22       |     // larger virtual heap when a 12 GiB guest memory layout is selected.
+         25 |     // Switch 2 titles size their heap from the total memory, which exceeds Switch 1's 8 GiB.
    23    26 |     const size_t max_heap_size =
    24    27 |         (std::max)(MainMemorySizeMax, KSystemControl::Init::GetIntendedMemorySize());
    25    28 |     R_UNLESS(size < max_heap_size, ResultInvalidSize);
    26    29 | 
    27    30 |     // Set the heap size.
    28    31 |     KProcessAddress address{};
    29    32 |     R_TRY(GetCurrentProcess(system.Kernel())
    30    33 |               .GetPageTable()
    31    34 |               .SetHeapSize(std::addressof(address), size));
    32    35 | 
    33    36 |     // We succeeded.
    34    37 |     *out_address = GetInteger(address);
+         38 |     MemoryStats::LastHeapSize().store(size, std::memory_order_relaxed);
+         39 |     if (size > MemoryStats::LargestHeapSize().load(std::memory_order_relaxed)) {
+         40 |         MemoryStats::LargestHeapSize().store(size, std::memory_order_relaxed);
+         41 |         LOG_INFO(Kernel_SVC, "SetHeapSize: the heap grows to {} MiB at {:#x}", size >> 20,
+         42 |                  GetInteger(address));
+         43 |     }
    35    44 |     R_SUCCEED();
    36    45 | }
```

</details>

### P0-K03 · SVC MapPhysicalMemory

Pour NS2, cette voie conditionne la résidence effective et les budgets. Encore doit conserver ses protections PS5 contre OOM/corruption ; toute différence avec les forks doit être classée validation, politique mémoire ou comportement invité.

Encore : [svc_physical_memory.cpp:39–85](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp#L39-L85) — 47 lignes.

<details>
<summary>Lichii — 39–85 : 45 alignées, 2 propres Encore, 2 propres upstream</summary>

Source : [svc_physical_memory.cpp:39–85](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/kernel/svc/svc_physical_memory.cpp#L39-L85).

```diff
    39    39 | Result MapPhysicalMemory(Core::System& system, u64 addr, u64 size) {
    40    40 |     LOG_DEBUG(Kernel_SVC, "called, addr={:#016x}, size={:#x}", addr, size);
    41    41 | 
-   42       |     if (!Common::IsAligned(addr, Core::Memory::YUZU_PAGESIZE)) {
+         42 |     if (!Common::IsAligned(addr, Core::Memory::LICHII_PAGESIZE)) {
    43    43 |         LOG_ERROR(Kernel_SVC, "Address is not aligned to 4KB, {:#016X}", addr);
    44    44 |         R_THROW(ResultInvalidAddress);
    45    45 |     }
    46    46 | 
-   47       |     if (!Common::IsAligned(size, Core::Memory::YUZU_PAGESIZE)) {
+         47 |     if (!Common::IsAligned(size, Core::Memory::LICHII_PAGESIZE)) {
    48    48 |         LOG_ERROR(Kernel_SVC, "Size is not aligned to 4KB, {:#X}", size);
    49    49 |         R_THROW(ResultInvalidSize);
    50    50 |     }
    51    51 | 
    52    52 |     if (size == 0) {
    53    53 |         LOG_ERROR(Kernel_SVC, "Size is zero");
    54    54 |         R_THROW(ResultInvalidSize);
    55    55 |     }
    56    56 | 
    57    57 |     if (!(addr < addr + size)) {
    58    58 |         LOG_ERROR(Kernel_SVC, "Size causes 64-bit overflow of address");
    59    59 |         R_THROW(ResultInvalidMemoryRegion);
    60    60 |     }
    61    61 | 
    62    62 |     KProcess* const current_process{GetCurrentProcessPointer(system.Kernel())};
    63    63 |     auto& page_table{current_process->GetPageTable()};
    64    64 | 
    65    65 |     if (current_process->GetTotalSystemResourceSize() == 0) {
    66    66 |         LOG_ERROR(Kernel_SVC, "System Resource Size is zero");
    67    67 |         R_THROW(ResultInvalidState);
    68    68 |     }
    69    69 | 
    70    70 |     if (!page_table.Contains(addr, size)) {
    71    71 |         LOG_ERROR(Kernel_SVC,
    72    72 |                   "Address is not within the address space, addr={:#016x}, size={:#016x}", addr,
    73    73 |                   size);
    74    74 |         R_THROW(ResultInvalidMemoryRegion);
    75    75 |     }
    76    76 | 
    77    77 |     if (!page_table.IsInAliasRegion(addr, size)) {
    78    78 |         LOG_ERROR(Kernel_SVC,
    79    79 |                   "Address is not within the alias region, addr={:#016x}, size={:#016x}", addr,
    80    80 |                   size);
    81    81 |         R_THROW(ResultInvalidMemoryRegion);
    82    82 |     }
    83    83 | 
    84    84 |     R_RETURN(page_table.MapPhysicalMemory(addr, size));
    85    85 | }
```

</details>

<details>
<summary>EglantinePS5 — 48–95 : 47 alignées, 0 propres Encore, 1 propres upstream</summary>

Source : [svc_physical_memory.cpp:48–95](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/kernel/svc/svc_physical_memory.cpp#L48-L95).

```diff
    39    48 | Result MapPhysicalMemory(Core::System& system, u64 addr, u64 size) {
+         49 |     MemoryStats::Note(MemoryStats::MapPhysicalMemory, size, true);
    40    50 |     LOG_DEBUG(Kernel_SVC, "called, addr={:#016x}, size={:#x}", addr, size);
    41    51 | 
    42    52 |     if (!Common::IsAligned(addr, Core::Memory::YUZU_PAGESIZE)) {
    43    53 |         LOG_ERROR(Kernel_SVC, "Address is not aligned to 4KB, {:#016X}", addr);
    44    54 |         R_THROW(ResultInvalidAddress);
    45    55 |     }
    46    56 | 
    47    57 |     if (!Common::IsAligned(size, Core::Memory::YUZU_PAGESIZE)) {
    48    58 |         LOG_ERROR(Kernel_SVC, "Size is not aligned to 4KB, {:#X}", size);
    49    59 |         R_THROW(ResultInvalidSize);
    50    60 |     }
    51    61 | 
    52    62 |     if (size == 0) {
    53    63 |         LOG_ERROR(Kernel_SVC, "Size is zero");
    54    64 |         R_THROW(ResultInvalidSize);
    55    65 |     }
    56    66 | 
    57    67 |     if (!(addr < addr + size)) {
    58    68 |         LOG_ERROR(Kernel_SVC, "Size causes 64-bit overflow of address");
    59    69 |         R_THROW(ResultInvalidMemoryRegion);
    60    70 |     }
    61    71 | 
    62    72 |     KProcess* const current_process{GetCurrentProcessPointer(system.Kernel())};
    63    73 |     auto& page_table{current_process->GetPageTable()};
    64    74 | 
    65    75 |     if (current_process->GetTotalSystemResourceSize() == 0) {
    66    76 |         LOG_ERROR(Kernel_SVC, "System Resource Size is zero");
    67    77 |         R_THROW(ResultInvalidState);
    68    78 |     }
    69    79 | 
    70    80 |     if (!page_table.Contains(addr, size)) {
    71    81 |         LOG_ERROR(Kernel_SVC,
    72    82 |                   "Address is not within the address space, addr={:#016x}, size={:#016x}", addr,
    73    83 |                   size);
    74    84 |         R_THROW(ResultInvalidMemoryRegion);
    75    85 |     }
    76    86 | 
    77    87 |     if (!page_table.IsInAliasRegion(addr, size)) {
    78    88 |         LOG_ERROR(Kernel_SVC,
    79    89 |                   "Address is not within the alias region, addr={:#016x}, size={:#016x}", addr,
    80    90 |                   size);
    81    91 |         R_THROW(ResultInvalidMemoryRegion);
    82    92 |     }
    83    93 | 
    84    94 |     R_RETURN(page_table.MapPhysicalMemory(addr, size));
    85    95 | }
```

</details>

### P0-K04 · SVC UnmapPhysicalMemory

Vérifier la symétrie de MapPhysicalMemory et les états mémoire admissibles. Un unmap prématuré pourrait expliquer un crash ; un unmap absent peut expliquer une pression mémoire ou une fermeture bloquée. Le diff seul ne tranche pas.

Encore : [svc_physical_memory.cpp:88–134](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp#L88-L134) — 47 lignes.

<details>
<summary>Lichii — 88–134 : 45 alignées, 2 propres Encore, 2 propres upstream</summary>

Source : [svc_physical_memory.cpp:88–134](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/kernel/svc/svc_physical_memory.cpp#L88-L134).

```diff
    88    88 | Result UnmapPhysicalMemory(Core::System& system, u64 addr, u64 size) {
    89    89 |     LOG_DEBUG(Kernel_SVC, "called, addr={:#016x}, size={:#x}", addr, size);
    90    90 | 
-   91       |     if (!Common::IsAligned(addr, Core::Memory::YUZU_PAGESIZE)) {
+         91 |     if (!Common::IsAligned(addr, Core::Memory::LICHII_PAGESIZE)) {
    92    92 |         LOG_ERROR(Kernel_SVC, "Address is not aligned to 4KB, {:#016X}", addr);
    93    93 |         R_THROW(ResultInvalidAddress);
    94    94 |     }
    95    95 | 
-   96       |     if (!Common::IsAligned(size, Core::Memory::YUZU_PAGESIZE)) {
+         96 |     if (!Common::IsAligned(size, Core::Memory::LICHII_PAGESIZE)) {
    97    97 |         LOG_ERROR(Kernel_SVC, "Size is not aligned to 4KB, {:#X}", size);
    98    98 |         R_THROW(ResultInvalidSize);
    99    99 |     }
   100   100 | 
   101   101 |     if (size == 0) {
   102   102 |         LOG_ERROR(Kernel_SVC, "Size is zero");
   103   103 |         R_THROW(ResultInvalidSize);
   104   104 |     }
   105   105 | 
   106   106 |     if (!(addr < addr + size)) {
   107   107 |         LOG_ERROR(Kernel_SVC, "Size causes 64-bit overflow of address");
   108   108 |         R_THROW(ResultInvalidMemoryRegion);
   109   109 |     }
   110   110 | 
   111   111 |     KProcess* const current_process{GetCurrentProcessPointer(system.Kernel())};
   112   112 |     auto& page_table{current_process->GetPageTable()};
   113   113 | 
   114   114 |     if (current_process->GetTotalSystemResourceSize() == 0) {
   115   115 |         LOG_ERROR(Kernel_SVC, "System Resource Size is zero");
   116   116 |         R_THROW(ResultInvalidState);
   117   117 |     }
   118   118 | 
   119   119 |     if (!page_table.Contains(addr, size)) {
   120   120 |         LOG_ERROR(Kernel_SVC,
   121   121 |                   "Address is not within the address space, addr={:#016x}, size={:#016x}", addr,
   122   122 |                   size);
   123   123 |         R_THROW(ResultInvalidMemoryRegion);
   124   124 |     }
   125   125 | 
   126   126 |     if (!page_table.IsInAliasRegion(addr, size)) {
   127   127 |         LOG_ERROR(Kernel_SVC,
   128   128 |                   "Address is not within the alias region, addr={:#016x}, size={:#016x}", addr,
   129   129 |                   size);
   130   130 |         R_THROW(ResultInvalidMemoryRegion);
   131   131 |     }
   132   132 | 
   133   133 |     R_RETURN(page_table.UnmapPhysicalMemory(addr, size));
   134   134 | }
```

</details>

<details>
<summary>EglantinePS5 — 98–145 : 47 alignées, 0 propres Encore, 1 propres upstream</summary>

Source : [svc_physical_memory.cpp:98–145](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/kernel/svc/svc_physical_memory.cpp#L98-L145).

```diff
    88    98 | Result UnmapPhysicalMemory(Core::System& system, u64 addr, u64 size) {
+         99 |     MemoryStats::Note(MemoryStats::UnmapPhysicalMemory, size, true);
    89   100 |     LOG_DEBUG(Kernel_SVC, "called, addr={:#016x}, size={:#x}", addr, size);
    90   101 | 
    91   102 |     if (!Common::IsAligned(addr, Core::Memory::YUZU_PAGESIZE)) {
    92   103 |         LOG_ERROR(Kernel_SVC, "Address is not aligned to 4KB, {:#016X}", addr);
    93   104 |         R_THROW(ResultInvalidAddress);
    94   105 |     }
    95   106 | 
    96   107 |     if (!Common::IsAligned(size, Core::Memory::YUZU_PAGESIZE)) {
    97   108 |         LOG_ERROR(Kernel_SVC, "Size is not aligned to 4KB, {:#X}", size);
    98   109 |         R_THROW(ResultInvalidSize);
    99   110 |     }
   100   111 | 
   101   112 |     if (size == 0) {
   102   113 |         LOG_ERROR(Kernel_SVC, "Size is zero");
   103   114 |         R_THROW(ResultInvalidSize);
   104   115 |     }
   105   116 | 
   106   117 |     if (!(addr < addr + size)) {
   107   118 |         LOG_ERROR(Kernel_SVC, "Size causes 64-bit overflow of address");
   108   119 |         R_THROW(ResultInvalidMemoryRegion);
   109   120 |     }
   110   121 | 
   111   122 |     KProcess* const current_process{GetCurrentProcessPointer(system.Kernel())};
   112   123 |     auto& page_table{current_process->GetPageTable()};
   113   124 | 
   114   125 |     if (current_process->GetTotalSystemResourceSize() == 0) {
   115   126 |         LOG_ERROR(Kernel_SVC, "System Resource Size is zero");
   116   127 |         R_THROW(ResultInvalidState);
   117   128 |     }
   118   129 | 
   119   130 |     if (!page_table.Contains(addr, size)) {
   120   131 |         LOG_ERROR(Kernel_SVC,
   121   132 |                   "Address is not within the address space, addr={:#016x}, size={:#016x}", addr,
   122   133 |                   size);
   123   134 |         R_THROW(ResultInvalidMemoryRegion);
   124   135 |     }
   125   136 | 
   126   137 |     if (!page_table.IsInAliasRegion(addr, size)) {
   127   138 |         LOG_ERROR(Kernel_SVC,
   128   139 |                   "Address is not within the alias region, addr={:#016x}, size={:#016x}", addr,
   129   140 |                   size);
   130   141 |         R_THROW(ResultInvalidMemoryRegion);
   131   142 |     }
   132   143 | 
   133   144 |     R_RETURN(page_table.UnmapPhysicalMemory(addr, size));
   134   145 | }
```

</details>

### Lecture de cette annexe

- **AS-GPU** : la principale divergence structurelle est le propriétaire PS5 natif 4K/sparse et sa quarantaine. Son existence est justifiée par l'environnement PS5 ; elle doit être vérifiée sur les mêmes séquences de map/remap/unmap que les jeux, pas supprimée pour ressembler aux forks.
- **NVMap** : les références sont directement liées aux pools d'images GSV. La comparaison permet de vérifier la symétrie duplication/libération autour de 429/430 et de VI2.
- **KPageTable/SVC** : les gros blocs communs ne prouvent pas la parité de résidence physique. Les différences PS5 doivent être croisées avec les budgets, les erreurs OOM et les rollbacks déjà qualifiés.

**Couverture ajoutée :** 12 fonctions, 24 comparaisons directes, 3851 lignes-source parcourues (répétitions incluses) ; 1094 lignes alignées, 1570 propres Encore, 93 propres upstream. Aucun statut console n'est modifié par cette annexe.

## Annexe IV — VI2 / présentation et loader NS2

Cette annexe suit deux frontières qui ne doivent pas être mélangées : **chargement du programme** puis **présentation de l'image**. Un jeu peut franchir le loader et rester bloqué dans GSV/VI2 ; inversement un crash avant GPFIFO peut être loader/kernel/JIT. Aucun code runtime n'est modifié par cette comparaison.

### P0-V01 · VI2 PresentClientBuffer

Homologue comportemental, noms différents. C'est le chemin le plus proche de la première frame : décodage du paquet VI2, image GSV, GraphicBuffer/NVMap, QueueBuffer, fence et pacing. Les différences de pacing host ne doivent pas masquer un échec antérieur de résolution d'image ou de QueueBuffer.

Encore : [graphics_supervisor.cpp:1229–1348](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L1229-L1348) — 120 lignes.

<details>
<summary>Lichii — 2083–2270 : 16 alignées, 104 propres Encore, 172 propres upstream</summary>

Source : [nx2_gsv.h:2083–2270](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L2083-L2270).

```diff
- 1229       |     void Present(HLERequestContext& ctx) {
- 1230       |         const auto* p=ctx.CommandBuffer();Result result=Kernel::ResultInvalidCombination;
- 1231       |         u64 mask{};
- 1232       |         if(p[0]==0xf5&&p[1]==24){
- 1233       |             Release();
- 1234       |             Client* c=Find(W(p,2));result=Kernel::ResultNotFound;
- 1235       |             if(c){
- 1236       |                 const u32 slot=GraphicsSupervisorProtocol::DecodeBufferSlot(p[4]);
- 1237       |                 result=Kernel::ResultInvalidState;
- 1238       |                 if(slot<15&&c->display&&c->layer&&!c->queued[slot]){
- 1239       |                     const auto img=m_owner->GetPresentImage(p[5]);
- 1240       |                     result=Kernel::ResultNotFound;
- 1241       |                     if(img){
- 1242       |                         const auto& pref=img->layout;
- 1243       |                         const u32 width=(pref[2]&0xffffU)+1;
- 1244       |                         const u32 height=(pref[2]>>16)+1;
- 1245       |                         const u32 outw=(p[7]&0xffffU)+1;
- 1246       |                         const u32 outh=(p[7]>>16)+1;
- 1247       |                         result=Kernel::ResultNotImplemented;
- 1248       |                         if(p[6]==0&&p[8]==3&&pref[4]==7&&
- 1249       |                             pref[6]==1&&outw<=width&&outh<=height){
- 1250       |                             const u32 fence=~p[22];
- 1251       |                             auto& nv=img->module->GetContainer();
- 1252       |                             result=Kernel::ResultInvalidCombination;
- 1253       |                             if(p[23]==0&&p[25]==0&&
- 1254       |                                 (fence==~u32{0}||
- 1255       |                                  nv.GetSyncpointManager().IsSyncpointAllocated(fence))){
- 1256       |                                 if(!c->producer){
- 1257       |                                     result=m_vi->GetContainer()->GetLayerProducerHandle(
- 1258       |                                         &c->producer,*c->layer);
- 1259       |                                     if(result.IsSuccess()){
- 1260       |                                         android::QueueBufferOutput output{};
- 1261       |                                         if(c->producer->Connect({},
- 1262       |                                             android::NativeWindowApi::Egl,false,&output)!=
- 1263       |                                             android::Status::NoError||
- 1264       |                                            c->producer->SetBufferCount(16)!=
- 1265       |                                             android::Status::NoError)
- 1266       |                                             result=Kernel::ResultInvalidState;
+       2083 |     void PresentClientBuffer(HLERequestContext& ctx) {
+       2084 |         const auto* w = ctx.CommandBuffer();
+       2085 |         ++m_presents;
+       2086 |         if (Kernel::Nx2ThreadStats::g_enabled) {
+       2087 |             Kernel::Nx2ThreadStats::OnPresent(&ctx.GetThread());
  1267  2088 |                                     }
- 1268       |                                     if(result.IsSuccess()){
- 1269       |                                         s32 binder{};
- 1270       |                                         result=m_vi->GetContainer()->OpenLayer(
- 1271       |                                             &binder,*c->layer,m_aruid);
- 1272       |                                         if(result.IsSuccess())result=m_vi->GetContainer()
- 1273       |                                             ->SetLayerVisibility(*c->layer,true);
+       2089 |         if (Common::DkbFrameTrace::Enabled()) {
+       2090 |             m_vsync->trace_present.store(m_presents, std::memory_order_relaxed);
  1274  2091 |                                     }
- 1275       |                                 }else result=ResultSuccess;
- 1276       |                                 // Release polling must be ready BEFORE
- 1277       |                                 // QueueBuffer publishes its producer slot.
- 1278       |                                 // If CreateEvent/Schedule throws afterwards,
- 1279       |                                 // a frame is live with no retirement path and
- 1280       |                                 // the TIPC caller never sees its accepted queue.
- 1281       |                                 if(result.IsSuccess() && !m_poll){
- 1282       |                                     try {
- 1283       |                                         auto weak=std::weak_ptr<IVi2Session>(
- 1284       |                                             std::static_pointer_cast<IVi2Session>(
- 1285       |                                                 shared_from_this()));
- 1286       |                                         auto timer=Core::Timing::CreateEvent(
- 1287       |                                             "NativeVi2Release",
- 1288       |                                             [weak](s64,std::chrono::nanoseconds)
- 1289       |                                                 ->std::optional<std::chrono::nanoseconds>{
- 1290       |                                                 if(auto self=weak.lock()){
- 1291       |                                                     const auto guard=self->LockService();
- 1292       |                                                     self->Release();
+       2092 |         Core::RecordGuestPresent();
+       2093 |         if (m_presents <= 4 || (m_presents % 600) == 0) {
+       2094 |             LOG_INFO(Service, "nx2:vi2 229 present #{} token={:#x} slot={} image={}", m_presents,
+       2095 |                      u64{w[2]} | (u64{w[3]} << 32), w[4], w[5]);
  1293  2096 |                                                 }
- 1294       |                                                 return std::nullopt;
- 1295       |                                             });
- 1296       |                                         system.CoreTiming().ScheduleLoopingEvent(
- 1297       |                                             std::chrono::milliseconds{1},
- 1298       |                                             std::chrono::milliseconds{1},timer);
- 1299       |                                         m_poll=std::move(timer);
- 1300       |                                     } catch (const std::bad_alloc&) {
- 1301       |                                         result=Kernel::ResultOutOfResource;
+       2097 |         // Wait for this frame's fence, so the game doesn't write the next frame's data (constant
+       2098 |         // buffers holding texture handles, vertex data, Pokopia's glyph atlas) while the GPU
+       2099 |         // thread still reads this frame's. But title 1's GPU waits on semaphores its CPU releases
+       2100 |         // only after this present returns: while a channel stays suspended on one, wait for the
+       2101 |         // previous frame's fence instead and let the game prepare frame N+1 meanwhile (waiting
+       2102 |         // for this frame there cost 8-56 ms of every 34-105 ms frame, or never finished).
+       2103 |         // EDEN_NX2_FRAMES_AHEAD=1 always waits for the previous frame, =0 always for this one.
+       2104 |         static const int frames_ahead_setting = [] {
+       2105 |             const char* value = std::getenv("EDEN_NX2_FRAMES_AHEAD");
+       2106 |             return value == nullptr ? -1 : value[0] == '1' ? 1 : 0;
+       2107 |         }();
+       2108 |         // Donkey Kong Bananza's channels wait on each other every frame, so it always ran a frame
+       2109 |         // ahead, where it rewrote memory the GPU thread hadn't read yet (misread commands, then
+       2110 |         // a freeze or crash; rubberbanding while moving). Title 1 runs ahead without either.
+       2111 |         constexpr u64 DonkeyKongBananzaProgramId = 0x040074A01BF12000ULL;
+       2112 |         // Ocarina waited ~12 ms a frame on its previous frame's fence here (#161).
+       2113 |         constexpr u64 OcarinaOfTimeProgramId = 0x0400486024DEC000ULL;
+       2114 |         int frames_ahead = frames_ahead_setting;
+       2115 |         const u64 app_program_id = system.GetApplicationProcessProgramID();
+       2116 |         if (frames_ahead == -1 && app_program_id == DonkeyKongBananzaProgramId) {
+       2117 |             frames_ahead = 0;
+       2118 |         } else if (frames_ahead == -1 && app_program_id == OcarinaOfTimeProgramId) {
+       2119 |             frames_ahead = 1;
  1302  2120 |                                     }
+       2121 |         constexpr u64 DuskbloodsNetworkTestProgramId = 0x0400D1D02399A000ULL;
+       2122 |         const bool duskbloods_auto_ahead =
+       2123 |             frames_ahead_setting == -1 && app_program_id == DuskbloodsNetworkTestProgramId;
+       2124 |         if (duskbloods_auto_ahead) {
+       2125 |             frames_ahead = 1;
  1303  2126 |                                 }
- 1304       |                                 if(result.IsSuccess()){
- 1305       |                                     auto native=std::make_shared<android::NvGraphicBuffer>();
- 1306       |                                     native->width=static_cast<s32>(width);
- 1307       |                                     native->height=static_cast<s32>(height);
- 1308       |                                     native->stride=static_cast<s32>(pref[5]*16);
- 1309       |                                     native->format=android::PixelFormat::Rgba8888;
- 1310       |                                     native->external_format=native->format;
- 1311       |                                     native->buffer_id=img->buffer_id;native->offset=img->offset;
- 1312       |                                     auto buffer=std::make_shared<android::GraphicBuffer>(
- 1313       |                                         nv.GetNvMapFile(),native);
- 1314       |                                     s32 idx{};result=Kernel::ResultOutOfResource;
- 1315       |                                     if(c->producer->AttachBuffer(&idx,buffer)==android::Status::NoError){
- 1316       |                                         android::QueueBufferInput input{};
- 1317       |                                         android::QueueBufferOutput output{};
- 1318       |                                         input.crop={0,0,static_cast<s32>(outw),
- 1319       |                                             static_cast<s32>(outh)};
- 1320       |                                         input.swap_interval=static_cast<s32>(GraphicsSupervisorProtocol::DecodePresentSwapInterval(p[12]));
- 1321       |                                         input.fence=android::Fence::NoFence();
- 1322       |                                         if(fence!=~u32{0}){
- 1323       |                                             input.fence.num_fences=1;
- 1324       |                                             input.fence.fences[0]={static_cast<s32>(fence),p[24]};
+       2127 |         const auto entered = std::chrono::steady_clock::now();
+       2128 |         static const bool fence_trace = [] {
+       2129 |             const char* value = std::getenv("EDEN_NX2_PRESENT_FENCE_TRACE");
+       2130 |             return value != nullptr && value[0] == '1';
+       2131 |         }();
+       2132 |         std::shared_ptr<TracedPresent> traced;
+       2133 |         if (fence_trace) {
+       2134 |             traced = TracePresentFence(~w[22], w[24], entered);
  1325  2135 |                                         }
- 1326       |                                         if(c->producer->QueueBuffer(idx,input,&output)==
- 1327       |                                             android::Status::NoError){
- 1328       |                                             c->queued[slot]=idx;c->images[slot]=p[5];
- 1329       |                                             c->recorders[slot]=static_cast<u8>(p[18] & 0xf);
- 1330       |                                             c->queued_modules[slot]=img->module;
- 1331       |                                             c->retained[slot]=buffer;
- 1332       |                                             c->available&=~(u64{1}<<slot);result=ResultSuccess;
- 1333       |                                         }else{
- 1334       |                                             c->producer->CancelBuffer(idx,input.fence);
- 1335       |                                             result=Kernel::ResultInvalidState;
+       2136 |         const bool auto_reached = frames_ahead == -1 && WaitForFrame(~w[22], w[24], true);
+       2137 |         if (frames_ahead == 1 || (frames_ahead == -1 && !auto_reached)) {
+       2138 |             LOG_DEBUG(Service, "nx2:vi2 present #{} fence ({}, {:#x}), waiting for ({}, {:#x}); now {:#x}",
+       2139 |                       m_presents, ~w[22], w[24], m_previous_fence_id, m_previous_fence_value,
+       2140 |                       ~w[22] < 192 ? system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(~w[22]) : 0U);
+       2141 |             // With EDEN_NX2_FRAMES_AHEAD=1, only run a frame ahead while the GPU keeps up. With
+       2142 |             // the previous frame still on the GPU here, the GPU is the limit and running ahead
+       2143 |             // gains nothing; and Splatoon Raiders, which reuses its command memory as if the GPU
+       2144 |             // were at most a frame behind, rewrote command lists Eden had not read yet (misread
+       2145 |             // commands, then crashes, with a slow GPU). Wait for this frame too then. Not when a
+       2146 |             // suspended channel brought us here: this frame can't finish before the present
+       2147 |             // returns.
+       2148 |             const bool gpu_behind = frames_ahead == 1 && m_previous_fence_id < 192 &&
+       2149 |                                     !system.Host1x().GetSyncpointManager().IsReadyGuest(
+       2150 |                                         m_previous_fence_id, m_previous_fence_value);
+       2151 |             WaitForFrame(m_previous_fence_id, m_previous_fence_value);
+       2152 |             if (gpu_behind) {
+       2153 |                 WaitForFrame(~w[22], w[24], duskbloods_auto_ahead);
  1336  2154 |                                         }
+       2155 |         } else if (frames_ahead == 0) {
+       2156 |             WaitForFrame(~w[22], w[24]);
  1337  2157 |                                     }
+       2158 |         m_previous_fence_id = ~w[22];
+       2159 |         m_previous_fence_value = w[24];
+       2160 |         const auto waited = std::chrono::steady_clock::now();
+       2161 |         const auto pacing = PresentInterval(w[12], ctx.GetThread().GetOwnerProcess());
+       2162 |         // With this frame's fence reached, return before its deadline and release the buffer
+       2163 |         // through a fence instead. Not on a wait that can return with the frame unfinished, and
+       2164 |         // not with timestamp recorders, which record after the pacing as before. Single-core
+       2165 |         // keeps the blocking path and its tick-based speed limiter.
+       2166 |         const bool queueable =
+       2167 |             system.IsMulticore() && frames_ahead == 0 && (w[18] & 0xf) == 0 &&
+       2168 |             (~w[22] >= 192 ||
+       2169 |              system.Host1x().GetSyncpointManager().IsReadyGuest(~w[22], w[24]));
+       2170 |         std::optional<Nx2PresentReleases::Release> release;
+       2171 |         std::chrono::steady_clock::time_point hold_until{};
+       2172 |         if (queueable) {
+       2173 |             release = QueueRelease(pacing, hold_until);
  1338  2174 |                                 }
+       2175 |         if (!Composite(w[5], ~w[22], w[24], w[7], w[8],
+       2176 |                        release ? release->on_composited : std::function<void()>{}) &&
+       2177 |             release) {
+       2178 |             // Nothing will read the image.
+       2179 |             release->on_composited();
  1339  2180 |                             }
+       2181 |         const auto composited = std::chrono::steady_clock::now();
+       2182 |         if (!release) {
+       2183 |             PaceToVblank(pacing);
+       2184 |         } else if (composited < hold_until) {
+       2185 |             SleepFor(std::chrono::duration_cast<std::chrono::nanoseconds>(hold_until - composited));
  1340  2186 |                         }
+       2187 |         const auto paced = std::chrono::steady_clock::now();
+       2188 |         if (const u32 recorder = w[18] & 0xf; recorder != 0) {
+       2189 |             m_recorded_ticks[recorder - 1] = system.CoreTiming().GetClockTicks();
  1341  2190 |                     }
+       2191 |         if (const auto* const process = system.ApplicationProcess(); process != nullptr) {
+       2192 |             UpdateFrameInterval(*process, entered);
  1342  2193 |                 }
- 1343       |                 mask=c->available;
+       2194 |         if (traced) {
+       2195 |             FinishPresentFence(*traced, frames_ahead == -1 && !auto_reached, paced);
  1344  2196 |             }
+       2197 |         if (Common::DkbFrameTrace::Enabled()) {
+       2198 |             const auto ms = [](auto duration) {
+       2199 |                 return std::chrono::duration<double, std::milli>(duration).count();
+       2200 |             };
+       2201 |             if (m_frame_trace.rate.Ready(paced)) {
+       2202 |                 LOG_INFO(Service,
+       2203 |                          "DKB frame present={} word12={:#x} requested_interval={} "
+       2204 |                          "requested_hz={} effective_interval={} effective_hz={} forced_interval={} "
+       2205 |                          "speed_limit={} speed_percent={} switches={} last_switch={:#x}->{:#x} "
+       2206 |                          "cpu_frame_wall_ms={:.3f} cpu_present_wall_ms={:.3f} fence_wall_ms={:.3f} "
+       2207 |                          "composite_wall_ms={:.3f} target_ms={:.3f} sleep_requested_ms={:.3f} "
+       2208 |                          "sleep_actual_wall_ms={:.3f} pace_wall_ms={:.3f} deadline_reset={}",
+       2209 |                          m_presents, w[12], w[12] >> 16, w[12] & 0xffff,
+       2210 |                          m_frame_trace.interval, m_frame_trace.refresh, m_frame_trace.forced,
+       2211 |                          Settings::values.use_speed_limit.GetValue(), Settings::SpeedLimit(),
+       2212 |                          m_frame_trace.switches, m_frame_trace.switch_from,
+       2213 |                          m_frame_trace.switch_to,
+       2214 |                          m_frame_trace.last_present == std::chrono::steady_clock::time_point{}
+       2215 |                              ? -1.0 : ms(entered - m_frame_trace.last_present),
+       2216 |                          ms(paced - entered), ms(waited - entered), ms(composited - waited),
+       2217 |                          m_frame_trace.target_ms, m_frame_trace.sleep_requested_ms,
+       2218 |                          m_frame_trace.sleep_actual_ms, ms(paced - composited),
+       2219 |                          m_frame_trace.deadline_reset);
+       2220 |                 m_frame_trace.switches = 0;
  1345  2221 |         }
- 1346       |         IPC::ResponseBuilder rb{ctx,8};rb.Push(result.raw);rb.Push(mask);
- 1347       |         for(u32 i=0;i<4;++i)rb.Push<u32>(0);
+       2222 |             m_frame_trace.last_present = entered;
  1348  2223 |     }
+       2224 |         // Where each frame's time goes on the present thread, averaged per 600 presents: the
+       2225 |         // game is blocked here while Eden's GPU thread catches up (fence) and composites.
+       2226 |         {
+       2227 |             using us = std::chrono::microseconds;
+       2228 |             // long long like the stats: microseconds::rep is long on Linux (std::max needs one type).
+       2229 |             const auto to_us = [](auto d) -> long long {
+       2230 |                 return std::chrono::duration_cast<us>(d).count();
+       2231 |             };
+       2232 |             m_stats.fence_us += to_us(waited - entered);
+       2233 |             m_stats.composite_us += to_us(composited - waited);
+       2234 |             m_stats.pace_us += to_us(paced - composited);
+       2235 |             m_stats.max_fence_us = (std::max<long long>)(m_stats.max_fence_us, static_cast<long long>(to_us(waited - entered)));
+       2236 |             // Counted at the reply: the game gets its buffers back with this frame unfinished.
+       2237 |             if (const u32 fence_id = ~w[22]; fence_id < 192 &&
+       2238 |                 !system.Host1x().GetSyncpointManager().IsReadyGuest(fence_id, w[24])) {
+       2239 |                 ++m_stats.ran_ahead;
+       2240 |             }
+       2241 |             if (m_stats.last_present != std::chrono::steady_clock::time_point{}) {
+       2242 |                 const long long frame = to_us(entered - m_stats.last_present);
+       2243 |                 m_stats.frame_us += frame;
+       2244 |                 m_stats.max_frame_us = (std::max)(m_stats.max_frame_us, frame);
+       2245 |                 m_stats.hitches += frame > 100'000 ? 1 : 0;
+       2246 |                 // Vblanks the game asked for (its steps where it times by them, as Mario Kart
+       2247 |                 // World's dynamic mode does): against the frame time, its speed vs real time.
+       2248 |                 m_stats.vblanks += std::clamp<u32>(w[12] >> 16, 1, 4);
+       2249 |             }
+       2250 |             m_stats.last_present = entered;
+       2251 |             if (++m_stats.presents == 600) {
+       2252 |                 LOG_INFO(Service,
+       2253 |                          "nx2:vi2 last 600 presents: frame {} us (max {}, {} over 100 ms), "
+       2254 |                          "blocked on the GPU fence {} us (max {}), composite {} us, vblank "
+       2255 |                          "pacing {} us, {} ran a frame ahead, {} vblanks asked ({}% of real "
+       2256 |                          "time at 60 Hz)",
+       2257 |                          m_stats.frame_us / 599, m_stats.max_frame_us, m_stats.hitches,
+       2258 |                          m_stats.fence_us / 600, m_stats.max_fence_us, m_stats.composite_us / 600,
+       2259 |                          m_stats.pace_us / 600, m_stats.ran_ahead, m_stats.vblanks,
+       2260 |                          m_stats.frame_us > 0 ? m_stats.vblanks * 1'000'000 / 60 * 100 /
+       2261 |                                                     m_stats.frame_us
+       2262 |                                               : 0);
+       2263 |                 m_stats = {.last_present = entered};
+       2264 |             }
+       2265 |         }
+       2266 |         constexpr u64 AvailableSlots = 0x7fff;
+       2267 |         TipcReplyWords(ctx, {static_cast<u32>(AvailableSlots),
+       2268 |                              static_cast<u32>(AvailableSlots >> 32),
+       2269 |                              release ? ~release->id : 0U, 0, release ? release->value : 0U, 0});
+       2270 |     }
```

</details>

<details>
<summary>EglantinePS5 — 1822–1961 : 14 alignées, 106 propres Encore, 126 propres upstream</summary>

Source : [nx2_gsv.h:1822–1961](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L1822-L1961).

```diff
- 1229       |     void Present(HLERequestContext& ctx) {
- 1230       |         const auto* p=ctx.CommandBuffer();Result result=Kernel::ResultInvalidCombination;
- 1231       |         u64 mask{};
- 1232       |         if(p[0]==0xf5&&p[1]==24){
- 1233       |             Release();
- 1234       |             Client* c=Find(W(p,2));result=Kernel::ResultNotFound;
- 1235       |             if(c){
- 1236       |                 const u32 slot=GraphicsSupervisorProtocol::DecodeBufferSlot(p[4]);
- 1237       |                 result=Kernel::ResultInvalidState;
- 1238       |                 if(slot<15&&c->display&&c->layer&&!c->queued[slot]){
- 1239       |                     const auto img=m_owner->GetPresentImage(p[5]);
- 1240       |                     result=Kernel::ResultNotFound;
- 1241       |                     if(img){
- 1242       |                         const auto& pref=img->layout;
- 1243       |                         const u32 width=(pref[2]&0xffffU)+1;
- 1244       |                         const u32 height=(pref[2]>>16)+1;
- 1245       |                         const u32 outw=(p[7]&0xffffU)+1;
- 1246       |                         const u32 outh=(p[7]>>16)+1;
- 1247       |                         result=Kernel::ResultNotImplemented;
- 1248       |                         if(p[6]==0&&p[8]==3&&pref[4]==7&&
- 1249       |                             pref[6]==1&&outw<=width&&outh<=height){
- 1250       |                             const u32 fence=~p[22];
- 1251       |                             auto& nv=img->module->GetContainer();
- 1252       |                             result=Kernel::ResultInvalidCombination;
- 1253       |                             if(p[23]==0&&p[25]==0&&
- 1254       |                                 (fence==~u32{0}||
- 1255       |                                  nv.GetSyncpointManager().IsSyncpointAllocated(fence))){
- 1256       |                                 if(!c->producer){
- 1257       |                                     result=m_vi->GetContainer()->GetLayerProducerHandle(
- 1258       |                                         &c->producer,*c->layer);
- 1259       |                                     if(result.IsSuccess()){
- 1260       |                                         android::QueueBufferOutput output{};
- 1261       |                                         if(c->producer->Connect({},
- 1262       |                                             android::NativeWindowApi::Egl,false,&output)!=
- 1263       |                                             android::Status::NoError||
- 1264       |                                            c->producer->SetBufferCount(16)!=
- 1265       |                                             android::Status::NoError)
- 1266       |                                             result=Kernel::ResultInvalidState;
- 1267       |                                     }
- 1268       |                                     if(result.IsSuccess()){
- 1269       |                                         s32 binder{};
- 1270       |                                         result=m_vi->GetContainer()->OpenLayer(
- 1271       |                                             &binder,*c->layer,m_aruid);
- 1272       |                                         if(result.IsSuccess())result=m_vi->GetContainer()
- 1273       |                                             ->SetLayerVisibility(*c->layer,true);
- 1274       |                                     }
- 1275       |                                 }else result=ResultSuccess;
- 1276       |                                 // Release polling must be ready BEFORE
- 1277       |                                 // QueueBuffer publishes its producer slot.
- 1278       |                                 // If CreateEvent/Schedule throws afterwards,
- 1279       |                                 // a frame is live with no retirement path and
- 1280       |                                 // the TIPC caller never sees its accepted queue.
- 1281       |                                 if(result.IsSuccess() && !m_poll){
- 1282       |                                     try {
- 1283       |                                         auto weak=std::weak_ptr<IVi2Session>(
- 1284       |                                             std::static_pointer_cast<IVi2Session>(
- 1285       |                                                 shared_from_this()));
- 1286       |                                         auto timer=Core::Timing::CreateEvent(
- 1287       |                                             "NativeVi2Release",
- 1288       |                                             [weak](s64,std::chrono::nanoseconds)
- 1289       |                                                 ->std::optional<std::chrono::nanoseconds>{
- 1290       |                                                 if(auto self=weak.lock()){
- 1291       |                                                     const auto guard=self->LockService();
- 1292       |                                                     self->Release();
+       1822 |     void PresentClientBuffer(HLERequestContext& ctx) {
+       1823 |         const auto* w = ctx.CommandBuffer();
+       1824 |         ++m_presents;
+       1825 |         if (Kernel::Nx2ThreadStats::g_enabled) {
+       1826 |             Kernel::Nx2ThreadStats::OnPresent(&ctx.GetThread());
  1293  1827 |                                                 }
- 1294       |                                                 return std::nullopt;
- 1295       |                                             });
- 1296       |                                         system.CoreTiming().ScheduleLoopingEvent(
- 1297       |                                             std::chrono::milliseconds{1},
- 1298       |                                             std::chrono::milliseconds{1},timer);
- 1299       |                                         m_poll=std::move(timer);
- 1300       |                                     } catch (const std::bad_alloc&) {
- 1301       |                                         result=Kernel::ResultOutOfResource;
+       1828 |         if (Common::DkbFrameTrace::Enabled()) {
+       1829 |             m_vsync->trace_present.store(m_presents, std::memory_order_relaxed);
  1302  1830 |                                     }
+       1831 |         const u64 present = Core::g_nx2_present_count.fetch_add(1, std::memory_order_relaxed) + 1;
+       1832 |         if (Core::g_nx2_present_time_services.load(std::memory_order_relaxed) != 0) {
+       1833 |             const u64 present_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
+       1834 |                                        std::chrono::steady_clock::now().time_since_epoch())
+       1835 |                                        .count();
+       1836 |             Core::g_nx2_present_times_ns[present % Core::g_nx2_present_times_ns.size()].store(
+       1837 |                 present_ns, std::memory_order_relaxed);
  1303  1838 |                                 }
- 1304       |                                 if(result.IsSuccess()){
- 1305       |                                     auto native=std::make_shared<android::NvGraphicBuffer>();
- 1306       |                                     native->width=static_cast<s32>(width);
- 1307       |                                     native->height=static_cast<s32>(height);
- 1308       |                                     native->stride=static_cast<s32>(pref[5]*16);
- 1309       |                                     native->format=android::PixelFormat::Rgba8888;
- 1310       |                                     native->external_format=native->format;
- 1311       |                                     native->buffer_id=img->buffer_id;native->offset=img->offset;
- 1312       |                                     auto buffer=std::make_shared<android::GraphicBuffer>(
- 1313       |                                         nv.GetNvMapFile(),native);
- 1314       |                                     s32 idx{};result=Kernel::ResultOutOfResource;
- 1315       |                                     if(c->producer->AttachBuffer(&idx,buffer)==android::Status::NoError){
- 1316       |                                         android::QueueBufferInput input{};
- 1317       |                                         android::QueueBufferOutput output{};
- 1318       |                                         input.crop={0,0,static_cast<s32>(outw),
- 1319       |                                             static_cast<s32>(outh)};
- 1320       |                                         input.swap_interval=static_cast<s32>(GraphicsSupervisorProtocol::DecodePresentSwapInterval(p[12]));
- 1321       |                                         input.fence=android::Fence::NoFence();
- 1322       |                                         if(fence!=~u32{0}){
- 1323       |                                             input.fence.num_fences=1;
- 1324       |                                             input.fence.fences[0]={static_cast<s32>(fence),p[24]};
+       1839 |         if (m_presents <= 4 || (m_presents % 600) == 0) {
+       1840 |             LOG_INFO(Service, "nx2:vi2 229 present #{} token={:#x} slot={} image={}", m_presents,
+       1841 |                      u64{w[2]} | (u64{w[3]} << 32), w[4], w[5]);
  1325  1842 |                                         }
- 1326       |                                         if(c->producer->QueueBuffer(idx,input,&output)==
- 1327       |                                             android::Status::NoError){
- 1328       |                                             c->queued[slot]=idx;c->images[slot]=p[5];
- 1329       |                                             c->recorders[slot]=static_cast<u8>(p[18] & 0xf);
- 1330       |                                             c->queued_modules[slot]=img->module;
- 1331       |                                             c->retained[slot]=buffer;
- 1332       |                                             c->available&=~(u64{1}<<slot);result=ResultSuccess;
- 1333       |                                         }else{
- 1334       |                                             c->producer->CancelBuffer(idx,input.fence);
- 1335       |                                             result=Kernel::ResultInvalidState;
+       1843 |         // Wait for this frame's fence, so the game doesn't write the next frame's data (constant
+       1844 |         // buffers holding texture handles, vertex data, Pokopia's glyph atlas) while the GPU
+       1845 |         // thread still reads this frame's. But title 1's GPU waits on semaphores its CPU releases
+       1846 |         // only after this present returns: while a channel stays suspended on one, wait for the
+       1847 |         // previous frame's fence instead and let the game prepare frame N+1 meanwhile (waiting
+       1848 |         // for this frame there cost 8-56 ms of every 34-105 ms frame, or never finished).
+       1849 |         // EDEN_NX2_FRAMES_AHEAD=1 always waits for the previous frame, =0 always for this one.
+       1850 |         static const int frames_ahead_setting = [] {
+       1851 |             const char* value = std::getenv("EDEN_NX2_FRAMES_AHEAD");
+       1852 |             return value == nullptr ? -1 : value[0] == '1' ? 1 : 0;
+       1853 |         }();
+       1854 |         // Donkey Kong Bananza's channels wait on each other every frame, so it always ran a frame
+       1855 |         // ahead, where it rewrote memory the GPU thread hadn't read yet (misread commands, then
+       1856 |         // a freeze or crash; rubberbanding while moving). Title 1 runs ahead without either.
+       1857 |         constexpr u64 DonkeyKongBananzaProgramId = 0x040074A01BF12000ULL;
+       1858 |         // Ocarina waited ~12 ms a frame on its previous frame's fence here (#161).
+       1859 |         constexpr u64 OcarinaOfTimeProgramId = 0x0400486024DEC000ULL;
+       1860 |         int frames_ahead = frames_ahead_setting;
+       1861 |         const u64 app_program_id = system.GetApplicationProcessProgramID();
+       1862 |         if (frames_ahead == -1 && app_program_id == DonkeyKongBananzaProgramId) {
+       1863 |             frames_ahead = 0;
+       1864 |         } else if (frames_ahead == -1 && app_program_id == OcarinaOfTimeProgramId) {
+       1865 |             frames_ahead = 1;
  1336  1866 |                                         }
+       1867 |         const auto entered = std::chrono::steady_clock::now();
+       1868 |         if (frames_ahead == 1 || (frames_ahead == -1 && !WaitForFrame(~w[22], w[24], true))) {
+       1869 |             LOG_DEBUG(Service, "nx2:vi2 present #{} fence ({}, {:#x}), waiting for ({}, {:#x}); now {:#x}",
+       1870 |                       m_presents, ~w[22], w[24], m_previous_fence_id, m_previous_fence_value,
+       1871 |                       ~w[22] < 192 ? system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(~w[22]) : 0U);
+       1872 |             // With EDEN_NX2_FRAMES_AHEAD=1, only run a frame ahead while the GPU keeps up. With
+       1873 |             // the previous frame still on the GPU here, the GPU is the limit and running ahead
+       1874 |             // gains nothing; and Splatoon Raiders, which reuses its command memory as if the GPU
+       1875 |             // were at most a frame behind, rewrote command lists Eden had not read yet (misread
+       1876 |             // commands, then crashes, with a slow GPU). Wait for this frame too then. Not when a
+       1877 |             // suspended channel brought us here: this frame can't finish before the present
+       1878 |             // returns.
+       1879 |             const bool gpu_behind = frames_ahead == 1 && m_previous_fence_id < 192 &&
+       1880 |                                     !system.Host1x().GetSyncpointManager().IsReadyGuest(
+       1881 |                                         m_previous_fence_id, m_previous_fence_value);
+       1882 |             WaitForFrame(m_previous_fence_id, m_previous_fence_value);
+       1883 |             if (gpu_behind) {
+       1884 |                 WaitForFrame(~w[22], w[24]);
  1337  1885 |                                     }
+       1886 |         } else if (frames_ahead == 0) {
+       1887 |             WaitForFrame(~w[22], w[24]);
  1338  1888 |                                 }
+       1889 |         m_previous_fence_id = ~w[22];
+       1890 |         m_previous_fence_value = w[24];
+       1891 |         const auto waited = std::chrono::steady_clock::now();
+       1892 |         Composite(w[5], ~w[22], w[24], w[7]);
+       1893 |         const auto composited = std::chrono::steady_clock::now();
+       1894 |         PaceToVblank(w[12], ctx.GetThread().GetOwnerProcess());
+       1895 |         const auto paced = std::chrono::steady_clock::now();
+       1896 |         if (Common::DkbFrameTrace::Enabled()) {
+       1897 |             const auto ms = [](auto duration) {
+       1898 |                 return std::chrono::duration<double, std::milli>(duration).count();
+       1899 |             };
+       1900 |             if (m_frame_trace.rate.Ready(paced)) {
+       1901 |                 LOG_INFO(Service,
+       1902 |                          "DKB frame present={} word12={:#x} requested_interval={} "
+       1903 |                          "requested_hz={} effective_interval={} effective_hz={} forced_interval={} "
+       1904 |                          "speed_limit={} speed_percent={} switches={} last_switch={:#x}->{:#x} "
+       1905 |                          "cpu_frame_wall_ms={:.3f} cpu_present_wall_ms={:.3f} fence_wall_ms={:.3f} "
+       1906 |                          "composite_wall_ms={:.3f} target_ms={:.3f} sleep_requested_ms={:.3f} "
+       1907 |                          "sleep_actual_wall_ms={:.3f} pace_wall_ms={:.3f} deadline_reset={}",
+       1908 |                          m_presents, w[12], w[12] >> 16, w[12] & 0xffff,
+       1909 |                          m_frame_trace.interval, m_frame_trace.refresh, m_frame_trace.forced,
+       1910 |                          Settings::values.use_speed_limit.GetValue(), Settings::SpeedLimit(),
+       1911 |                          m_frame_trace.switches, m_frame_trace.switch_from,
+       1912 |                          m_frame_trace.switch_to,
+       1913 |                          m_frame_trace.last_present == std::chrono::steady_clock::time_point{}
+       1914 |                              ? -1.0 : ms(entered - m_frame_trace.last_present),
+       1915 |                          ms(paced - entered), ms(waited - entered), ms(composited - waited),
+       1916 |                          m_frame_trace.target_ms, m_frame_trace.sleep_requested_ms,
+       1917 |                          m_frame_trace.sleep_actual_ms, ms(paced - composited),
+       1918 |                          m_frame_trace.deadline_reset);
+       1919 |                 m_frame_trace.switches = 0;
  1339  1920 |                             }
+       1921 |             m_frame_trace.last_present = entered;
  1340  1922 |                         }
+       1923 |         // Where each frame's time goes on the present thread, averaged per 600 presents: the
+       1924 |         // game is blocked here while Eden's GPU thread catches up (fence) and composites.
+       1925 |         {
+       1926 |             using us = std::chrono::microseconds;
+       1927 |             // long long like the stats: microseconds::rep is long on Linux (std::max needs one type).
+       1928 |             const auto to_us = [](auto d) -> long long {
+       1929 |                 return std::chrono::duration_cast<us>(d).count();
+       1930 |             };
+       1931 |             m_stats.fence_us += to_us(waited - entered);
+       1932 |             m_stats.composite_us += to_us(composited - waited);
+       1933 |             m_stats.pace_us += to_us(paced - composited);
+       1934 |             m_stats.max_fence_us = (std::max<long long>)(m_stats.max_fence_us, static_cast<long long>(to_us(waited - entered)));
+       1935 |             // Counted at the reply: the game gets its buffers back with this frame unfinished.
+       1936 |             if (const u32 fence_id = ~w[22]; fence_id < 192 &&
+       1937 |                 !system.Host1x().GetSyncpointManager().IsReadyGuest(fence_id, w[24])) {
+       1938 |                 ++m_stats.ran_ahead;
  1341  1939 |                     }
+       1940 |             if (m_stats.last_present != std::chrono::steady_clock::time_point{}) {
+       1941 |                 const long long frame = to_us(entered - m_stats.last_present);
+       1942 |                 m_stats.frame_us += frame;
+       1943 |                 m_stats.max_frame_us = (std::max)(m_stats.max_frame_us, frame);
+       1944 |                 m_stats.hitches += frame > 100'000 ? 1 : 0;
  1342  1945 |                 }
- 1343       |                 mask=c->available;
+       1946 |             m_stats.last_present = entered;
+       1947 |             if (++m_stats.presents == 600) {
+       1948 |                 LOG_INFO(Service,
+       1949 |                          "nx2:vi2 last 600 presents: frame {} us (max {}, {} over 100 ms), "
+       1950 |                          "blocked on the GPU fence {} us (max {}), composite {} us, vblank "
+       1951 |                          "pacing {} us, {} ran a frame ahead",
+       1952 |                          m_stats.frame_us / 599, m_stats.max_frame_us, m_stats.hitches,
+       1953 |                          m_stats.fence_us / 600, m_stats.max_fence_us, m_stats.composite_us / 600,
+       1954 |                          m_stats.pace_us / 600, m_stats.ran_ahead);
+       1955 |                 m_stats = {.last_present = entered};
  1344  1956 |             }
  1345  1957 |         }
- 1346       |         IPC::ResponseBuilder rb{ctx,8};rb.Push(result.raw);rb.Push(mask);
- 1347       |         for(u32 i=0;i<4;++i)rb.Push<u32>(0);
+       1958 |         constexpr u64 AvailableSlots = 0x7fff;
+       1959 |         TipcReplyWords(ctx, {static_cast<u32>(AvailableSlots),
+       1960 |                              static_cast<u32>(AvailableSlots >> 32), 0, 0, 0, 0});
  1348  1961 |     }
```

</details>

### P0-V02 · VI2 QueryDisplayRefreshRate

Comparer forme exacte de réponse et politique 60/120 Hz. Un mauvais payload peut faire échouer l'initialisation VI2 avant la présentation ; ce n'est pas une optimisation de cadence.

Encore : [graphics_supervisor.cpp:770–777](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L770-L777) — 8 lignes.

<details>
<summary>Lichii — 3071–3073 : 1 alignées, 7 propres Encore, 2 propres upstream</summary>

Source : [nx2_gsv.h:3071–3073](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L3071-L3073).

```diff
-  770       |     void QueryRefreshRate(HLERequestContext& ctx) {
-  771       |         const Result result = ValidateDisplayStatus(ctx, 103);
-  772       |         IPC::ResponseBuilder rb{ctx, 4};
-  773       |         rb.Push(result.raw);
-  774       |         rb.Push<u32>(result.IsSuccess()
-  775       |                           ? GraphicsSupervisorProtocol::Vi2NominalRefreshRateHz : 0);
-  776       |         rb.Push<u32>(0); // SDK's refresh-rate capability boolean.
+       3071 |     void QueryDisplayRefreshRate(HLERequestContext& ctx) {
+       3072 |         TipcReplyWords(ctx, {60, 0});
   777  3073 |     }
```

</details>

<details>
<summary>EglantinePS5 — 2374–2376 : 1 alignées, 7 propres Encore, 2 propres upstream</summary>

Source : [nx2_gsv.h:2374–2376](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L2374-L2376).

```diff
-  770       |     void QueryRefreshRate(HLERequestContext& ctx) {
-  771       |         const Result result = ValidateDisplayStatus(ctx, 103);
-  772       |         IPC::ResponseBuilder rb{ctx, 4};
-  773       |         rb.Push(result.raw);
-  774       |         rb.Push<u32>(result.IsSuccess()
-  775       |                           ? GraphicsSupervisorProtocol::Vi2NominalRefreshRateHz : 0);
-  776       |         rb.Push<u32>(0); // SDK's refresh-rate capability boolean.
+       2374 |     void QueryDisplayRefreshRate(HLERequestContext& ctx) {
+       2375 |         TipcReplyWords(ctx, {60, 0});
   777  2376 |     }
```

</details>

### P0-V03 · VI2 QueryDisplayHdrStatus

Comparer format HDR/SDR, luminance et codes de résultat. Encore vise un contrat statique PS5 ; Lichii interroge davantage le moniteur hôte. Seule la forme attendue par l'invité est pertinente au démarrage.

Encore : [graphics_supervisor.cpp:778–786](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L778-L786) — 9 lignes.

<details>
<summary>Lichii — 3146–3149 : 1 alignées, 8 propres Encore, 3 propres upstream</summary>

Source : [nx2_gsv.h:3146–3149](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L3146-L3149).

```diff
-  778       |     void QueryHdrStatus(HLERequestContext& ctx) {
-  779       |         const Result result = ValidateDisplayStatus(ctx, 104);
-  780       |         IPC::ResponseBuilder rb{ctx, 5};
-  781       |         rb.Push(result.raw);
-  782       |         rb.Push<u64>(result.IsSuccess()
-  783       |                           ? GraphicsSupervisorProtocol::Vi2SdrOutputFormat : 0);
-  784       |         rb.Push<u32>(result.IsSuccess()
-  785       |                           ? GraphicsSupervisorProtocol::Vi2SdrPeakNits : 0);
+       3146 |     void QueryDisplayHdrStatus(HLERequestContext& ctx) {
+       3147 |         const auto status = m_hdr_notifications.RecordStatus(QueryHostHdrOutput());
+       3148 |         TipcReplyWords(ctx, {status.enabled ? 2U : 1U, 0, status.peak_luminance});
   786  3149 |     }
```

</details>

<details>
<summary>EglantinePS5 — 2392–2394 : 1 alignées, 8 propres Encore, 2 propres upstream</summary>

Source : [nx2_gsv.h:2392–2394](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L2392-L2394).

```diff
-  778       |     void QueryHdrStatus(HLERequestContext& ctx) {
-  779       |         const Result result = ValidateDisplayStatus(ctx, 104);
-  780       |         IPC::ResponseBuilder rb{ctx, 5};
-  781       |         rb.Push(result.raw);
-  782       |         rb.Push<u64>(result.IsSuccess()
-  783       |                           ? GraphicsSupervisorProtocol::Vi2SdrOutputFormat : 0);
-  784       |         rb.Push<u32>(result.IsSuccess()
-  785       |                           ? GraphicsSupervisorProtocol::Vi2SdrPeakNits : 0);
+       2392 |     void QueryDisplayHdrStatus(HLERequestContext& ctx) {
+       2393 |         TipcReplyWords(ctx, {1, 0, 400});
   786  2394 |     }
```

</details>

### P0-V04 · VI2 QueryDisplayHdrPaperWhite

Même objectif : vérifier l'ABI et les valeurs admissibles, pas reproduire les mécanismes desktop de détection HDR.

Encore : [graphics_supervisor.cpp:787–793](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp#L787-L793) — 7 lignes.

<details>
<summary>Lichii — 3140–3142 : 1 alignées, 6 propres Encore, 2 propres upstream</summary>

Source : [nx2_gsv.h:3140–3142](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/hle/service/nx2_gsv.h#L3140-L3142).

```diff
-  787       |     void QueryPaperWhite(HLERequestContext& ctx) {
-  788       |         const Result result = ValidateDisplayStatus(ctx, 105);
-  789       |         IPC::ResponseBuilder rb{ctx, 3};
-  790       |         rb.Push(result.raw);
-  791       |         rb.Push<u32>(result.IsSuccess()
-  792       |                           ? GraphicsSupervisorProtocol::Vi2SdrPaperWhiteNits : 0);
+       3140 |     void QueryDisplayHdrPaperWhite(HLERequestContext& ctx) {
+       3141 |         TipcReplyWords(ctx, {m_hdr_notifications.RecordPaperWhite(QueryHostHdrOutput())});
   793  3142 |     }
```

</details>

<details>
<summary>EglantinePS5 — 2380–2382 : 1 alignées, 6 propres Encore, 2 propres upstream</summary>

Source : [nx2_gsv.h:2380–2382](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/hle/service/nx2_gsv.h#L2380-L2382).

```diff
-  787       |     void QueryPaperWhite(HLERequestContext& ctx) {
-  788       |         const Result result = ValidateDisplayStatus(ctx, 105);
-  789       |         IPC::ResponseBuilder rb{ctx, 3};
-  790       |         rb.Push(result.raw);
-  791       |         rb.Push<u32>(result.IsSuccess()
-  792       |                           ? GraphicsSupervisorProtocol::Vi2SdrPaperWhiteNits : 0);
+       2380 |     void QueryDisplayHdrPaperWhite(HLERequestContext& ctx) {
+       2381 |         TipcReplyWords(ctx, {203});
   793  2382 |     }
```

</details>

### P0-L01 · Loader NX OpenNative

Ouverture du contenu natif NS2 et choix de program index. À vérifier pour NUP/ExeFS : session, control, RomFS et modules doivent provenir du même programme.

Encore : [nx.cpp:613–642](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L613-L642) — 30 lignes.

<details>
<summary>Lichii — 635–664 : 30 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:635–664](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L635-L664).

```diff
   613   635 |     void OpenNative(u32 pi, std::size_t program_index) {
   614   636 |         const auto base = BaseOf(selected);
   615   637 |         if (base == Absent) {
   616   638 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   617   639 |             return;
   618   640 |         }
   619   641 |         program_id = Archive().programs()[pi].id;
   620   642 |         auto package = SnapshotPackage(base);
   621   643 |         if (package == nullptr) {
   622   644 |             return;
   623   645 |         }
   624   646 |         // RomFS updates also need the base NCA in the content provider.
   625   647 |         native_extras.push_back(package);
   626   648 |         native = std::make_unique<AppLoader_NSP>(std::move(package),
   627   649 |                                                  system->GetFileSystemController(),
   628   650 |                                                  system->GetContentProvider(), program_id,
   629   651 |                                                  program_index);
   630   652 |         const auto& owner = Archive().applications()[app];
   631   653 |         for (u32 si = owner.first_snapshot; si < owner.first_snapshot + owner.snapshot_count;
   632   654 |              ++si) {
   633   655 |             const auto type = Archive().snapshots()[si].type;
   634   656 |             if ((type == Update || type == AddOn) && !Archive().snapshots()[si].addon_title_id()) {
   635   657 |                 if (auto extra = SnapshotPackage(si)) {
   636   658 |                     native_extras.push_back(std::move(extra));
   637   659 |                 }
   638   660 |             }
   639   661 |         }
   640   662 |         LoadNacp(selected);
   641   663 |         status = ResultStatus::Success;
   642   664 |     }
```

</details>

<details>
<summary>EglantinePS5 — 632–659 : 28 alignées, 2 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:632–659](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/loader/nx.cpp#L632-L659).

```diff
   613   632 |     void OpenNative(u32 pi, std::size_t program_index) {
   614   633 |         const auto base = BaseOf(selected);
   615   634 |         if (base == Absent) {
   616   635 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   617   636 |             return;
   618   637 |         }
   619   638 |         program_id = Archive().programs()[pi].id;
   620   639 |         auto package = SnapshotPackage(base);
   621   640 |         if (package == nullptr) {
   622   641 |             return;
   623   642 |         }
-  624       |         // RomFS updates also need the base NCA in the content provider.
-  625       |         native_extras.push_back(package);
   626   643 |         native = std::make_unique<AppLoader_NSP>(std::move(package),
   627   644 |                                                  system->GetFileSystemController(),
   628   645 |                                                  system->GetContentProvider(), program_id,
   629   646 |                                                  program_index);
   630   647 |         const auto& owner = Archive().applications()[app];
   631   648 |         for (u32 si = owner.first_snapshot; si < owner.first_snapshot + owner.snapshot_count;
   632   649 |              ++si) {
   633   650 |             const auto type = Archive().snapshots()[si].type;
   634   651 |             if ((type == Update || type == AddOn) && !Archive().snapshots()[si].addon_title_id()) {
   635   652 |                 if (auto extra = SnapshotPackage(si)) {
   636   653 |                     native_extras.push_back(std::move(extra));
   637   654 |                 }
   638   655 |             }
   639   656 |         }
   640   657 |         LoadNacp(selected);
   641   658 |         status = ResultStatus::Success;
   642   659 |     }
```

</details>

### P0-L02 · Loader NX Open

Comparer détection du conteneur, application id demandé, programme sélectionné, NACP et RomFS. Un succès partiel de parsing ne garantit pas que le code lancé correspond au bon programme.

Encore : [nx.cpp:644–713](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L644-L713) — 70 lignes.

<details>
<summary>Lichii — 666–735 : 69 alignées, 1 propres Encore, 1 propres upstream</summary>

Source : [nx.cpp:666–735](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L666-L735).

```diff
   644   666 |     void Open(FileSys::VirtualFile nx_file, u64 requested, std::size_t program_index) {
-  645       |         auto opened = FileSys::OpenNxSession(nx_file);
+        667 |         auto opened = FileSys::OpenNxSession(nx_file, HostPath(nx_file));
   646   668 |         if (!opened) {
   647   669 |             LOG_ERROR(Loader, "Cannot open NX archive {}: {}", nx_file->GetName(),
   648   670 |                       opened.error.message);
   649   671 |             return;
   650   672 |         }
   651   673 |         session = std::move(*opened.value);
   652   674 |         const auto& a = Archive();
   653   675 |         for (u32 i = 0; i < a.applications().size(); ++i) {
   654   676 |             const auto& owner = a.applications()[i];
   655   677 |             if (owner.platform != 1 && owner.platform != 2) {
   656   678 |                 continue;
   657   679 |             }
   658   680 |             bool matches = requested == 0 || owner.id == requested;
   659   681 |             for (u32 p = owner.first_program;
   660   682 |                  p != Absent && p < owner.first_program + owner.program_count; ++p) {
   661   683 |                 matches |= a.programs()[p].id == requested;
   662   684 |             }
   663   685 |             if (matches && app == Absent) {
   664   686 |                 app = i;
   665   687 |             }
   666   688 |         }
   667   689 |         if (app == Absent) {
   668   690 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   669   691 |             return;
   670   692 |         }
   671   693 |         const auto& owner = a.applications()[app];
   672   694 |         u32 pi = Absent;
   673   695 |         for (u32 p = owner.first_program;
   674   696 |              p != Absent && p < owner.first_program + owner.program_count; ++p) {
   675   697 |             program_ids.push_back(a.programs()[p].id);
   676   698 |             const bool wanted = requested != 0 && requested != owner.id
   677   699 |                                     ? a.programs()[p].id == requested
   678   700 |                                     : a.programs()[p].kind == 0;
   679   701 |             if (wanted && pi == Absent) {
   680   702 |                 pi = p;
   681   703 |             }
   682   704 |         }
   683   705 |         if (pi == Absent) {
   684   706 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   685   707 |             return;
   686   708 |         }
   687   709 |         // A program with its own snapshots is selected here; a native snapshot holding every
   688   710 |         // program leaves the index to the NSP.
   689   711 |         if (program_index != 0) {
   690   712 |             const u64 target = a.programs()[pi].id + program_index;
   691   713 |             for (u32 p = owner.first_program;
   692   714 |                  p != Absent && p < owner.first_program + owner.program_count; ++p) {
   693   715 |                 if (a.programs()[p].id == target && Latest(p) != Absent) {
   694   716 |                     pi = p;
   695   717 |                     program_index = 0;
   696   718 |                 }
   697   719 |             }
   698   720 |         }
   699   721 |         selected = Latest(pi);
   700   722 |         if (selected == Absent) {
   701   723 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   702   724 |             return;
   703   725 |         }
   704   726 |         if (IsTree(selected)) {
   705   727 |             if (program_index != 0) {
   706   728 |                 status = ResultStatus::ErrorNSPMissingProgramNCA;
   707   729 |                 return;
   708   730 |             }
   709   731 |             OpenTree(pi);
   710   732 |         } else {
   711   733 |             OpenNative(pi, program_index);
   712   734 |         }
   713   735 |     }
```

</details>

<details>
<summary>EglantinePS5 — 661–730 : 69 alignées, 1 propres Encore, 1 propres upstream</summary>

Source : [nx.cpp:661–730](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/loader/nx.cpp#L661-L730).

```diff
   644   661 |     void Open(FileSys::VirtualFile nx_file, u64 requested, std::size_t program_index) {
-  645       |         auto opened = FileSys::OpenNxSession(nx_file);
+        662 |         auto opened = FileSys::OpenNxSession(nx_file, HostPath(nx_file));
   646   663 |         if (!opened) {
   647   664 |             LOG_ERROR(Loader, "Cannot open NX archive {}: {}", nx_file->GetName(),
   648   665 |                       opened.error.message);
   649   666 |             return;
   650   667 |         }
   651   668 |         session = std::move(*opened.value);
   652   669 |         const auto& a = Archive();
   653   670 |         for (u32 i = 0; i < a.applications().size(); ++i) {
   654   671 |             const auto& owner = a.applications()[i];
   655   672 |             if (owner.platform != 1 && owner.platform != 2) {
   656   673 |                 continue;
   657   674 |             }
   658   675 |             bool matches = requested == 0 || owner.id == requested;
   659   676 |             for (u32 p = owner.first_program;
   660   677 |                  p != Absent && p < owner.first_program + owner.program_count; ++p) {
   661   678 |                 matches |= a.programs()[p].id == requested;
   662   679 |             }
   663   680 |             if (matches && app == Absent) {
   664   681 |                 app = i;
   665   682 |             }
   666   683 |         }
   667   684 |         if (app == Absent) {
   668   685 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   669   686 |             return;
   670   687 |         }
   671   688 |         const auto& owner = a.applications()[app];
   672   689 |         u32 pi = Absent;
   673   690 |         for (u32 p = owner.first_program;
   674   691 |              p != Absent && p < owner.first_program + owner.program_count; ++p) {
   675   692 |             program_ids.push_back(a.programs()[p].id);
   676   693 |             const bool wanted = requested != 0 && requested != owner.id
   677   694 |                                     ? a.programs()[p].id == requested
   678   695 |                                     : a.programs()[p].kind == 0;
   679   696 |             if (wanted && pi == Absent) {
   680   697 |                 pi = p;
   681   698 |             }
   682   699 |         }
   683   700 |         if (pi == Absent) {
   684   701 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   685   702 |             return;
   686   703 |         }
   687   704 |         // A program with its own snapshots is selected here; a native snapshot holding every
   688   705 |         // program leaves the index to the NSP.
   689   706 |         if (program_index != 0) {
   690   707 |             const u64 target = a.programs()[pi].id + program_index;
   691   708 |             for (u32 p = owner.first_program;
   692   709 |                  p != Absent && p < owner.first_program + owner.program_count; ++p) {
   693   710 |                 if (a.programs()[p].id == target && Latest(p) != Absent) {
   694   711 |                     pi = p;
   695   712 |                     program_index = 0;
   696   713 |                 }
   697   714 |             }
   698   715 |         }
   699   716 |         selected = Latest(pi);
   700   717 |         if (selected == Absent) {
   701   718 |             status = ResultStatus::ErrorNSPMissingProgramNCA;
   702   719 |             return;
   703   720 |         }
   704   721 |         if (IsTree(selected)) {
   705   722 |             if (program_index != 0) {
   706   723 |                 status = ResultStatus::ErrorNSPMissingProgramNCA;
   707   724 |                 return;
   708   725 |             }
   709   726 |             OpenTree(pi);
   710   727 |         } else {
   711   728 |             OpenNative(pi, program_index);
   712   729 |         }
   713   730 |     }
```

</details>

### P0-L03 · AppLoader_NX::Load

Point d'entrée final vers le KProcess. Comparer ordre des modules, registration du contenu, RomFSFactory et erreurs propagées. C'est un endroit où une divergence peut expliquer un crash avant GPU, mais pas un freeze après deux GPFIFO.

Encore : [nx.cpp:837–860](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L837-L860) — 24 lignes.

<details>
<summary>Lichii — 854–877 : 24 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:854–877](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L854-L877).

```diff
   837   854 | AppLoader::LoadResult AppLoader_NX::Load(Kernel::KProcess& process, Core::System& system) {
   838   855 |     if (is_loaded) {
   839   856 |         return {ResultStatus::ErrorAlreadyLoaded, {}};
   840   857 |     }
   841   858 |     if (impl->status != ResultStatus::Success) {
   842   859 |         return {impl->status, {}};
   843   860 |     }
   844   861 |     RegisterFrontendContent(system);
   845   862 |     if (!impl->tree) {
   846   863 |         const auto result = impl->native->Load(process, system);
   847   864 |         is_loaded = result.first == ResultStatus::Success;
   848   865 |         return result;
   849   866 |     }
   850   867 |     const auto result = impl->tree_executable->Load(process, system);
   851   868 |     if (result.first != ResultStatus::Success) {
   852   869 |         return result;
   853   870 |     }
   854   871 |     system.GetFileSystemController().RegisterProcess(
   855   872 |         process.GetProcessId(), impl->program_id,
   856   873 |         std::make_shared<FileSys::RomFSFactory>(*this, system.GetContentProvider(),
   857   874 |                                                 system.GetFileSystemController()));
   858   875 |     is_loaded = true;
   859   876 |     return result;
   860   877 | }
```

</details>

<details>
<summary>EglantinePS5 — 819–847 : 23 alignées, 1 propres Encore, 6 propres upstream</summary>

Source : [nx.cpp:819–847](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/loader/nx.cpp#L819-L847).

```diff
   837   819 | AppLoader::LoadResult AppLoader_NX::Load(Kernel::KProcess& process, Core::System& system) {
   838   820 |     if (is_loaded) {
   839   821 |         return {ResultStatus::ErrorAlreadyLoaded, {}};
   840   822 |     }
   841   823 |     if (impl->status != ResultStatus::Success) {
   842   824 |         return {impl->status, {}};
   843   825 |     }
-  844       |     RegisterFrontendContent(system);
+        826 |     // The frontend owns this provider; the game list fills it the same way.
+        827 |     if (const auto* slot = system.GetContentProviderUnion().GetSlotProvider(
+        828 |             FileSys::ContentProviderUnionSlot::FrontendManual)) {
+        829 |         RegisterContent(*const_cast<FileSys::ManualContentProvider*>(
+        830 |             static_cast<const FileSys::ManualContentProvider*>(slot)));
+        831 |     }
   845   832 |     if (!impl->tree) {
   846   833 |         const auto result = impl->native->Load(process, system);
   847   834 |         is_loaded = result.first == ResultStatus::Success;
   848   835 |         return result;
   849   836 |     }
   850   837 |     const auto result = impl->tree_executable->Load(process, system);
   851   838 |     if (result.first != ResultStatus::Success) {
   852   839 |         return result;
   853   840 |     }
   854   841 |     system.GetFileSystemController().RegisterProcess(
   855   842 |         process.GetProcessId(), impl->program_id,
   856   843 |         std::make_shared<FileSys::RomFSFactory>(*this, system.GetContentProvider(),
   857   844 |                                                 system.GetFileSystemController()));
   858   845 |     is_loaded = true;
   859   846 |     return result;
   860   847 | }
```

</details>

### P0-L04 · AppLoader_NX::ReadRomFS

Comparer base/update et programme courant. Important pour Pokopia NUP et MKW update : un RomFS valide mais d'un mauvais index peut charger loin avant de diverger.

Encore : [nx.cpp:878–892](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L878-L892) — 15 lignes.

<details>
<summary>Lichii — 895–909 : 15 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:895–909](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L895-L909).

```diff
   878   895 | ResultStatus AppLoader_NX::ReadRomFS(FileSys::VirtualFile& out_file) {
   879   896 |     if (impl->status != ResultStatus::Success) {
   880   897 |         return impl->status;
   881   898 |     }
   882   899 |     if (!impl->tree) {
   883   900 |         return impl->native->ReadRomFS(out_file);
   884   901 |     }
   885   902 |     std::call_once(impl->tree_romfs_once, [this] {
   886   903 |         if (impl->tree_romfs_dir != nullptr) {
   887   904 |             impl->tree_romfs = FileSys::CreateRomFS(impl->tree_romfs_dir);
   888   905 |         }
   889   906 |     });
   890   907 |     out_file = impl->tree_romfs;
   891   908 |     return out_file != nullptr ? ResultStatus::Success : ResultStatus::ErrorNoRomFS;
   892   909 | }
```

</details>

<details>
<summary>EglantinePS5 — 865–879 : 15 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:865–879](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/loader/nx.cpp#L865-L879).

```diff
   878   865 | ResultStatus AppLoader_NX::ReadRomFS(FileSys::VirtualFile& out_file) {
   879   866 |     if (impl->status != ResultStatus::Success) {
   880   867 |         return impl->status;
   881   868 |     }
   882   869 |     if (!impl->tree) {
   883   870 |         return impl->native->ReadRomFS(out_file);
   884   871 |     }
   885   872 |     std::call_once(impl->tree_romfs_once, [this] {
   886   873 |         if (impl->tree_romfs_dir != nullptr) {
   887   874 |             impl->tree_romfs = FileSys::CreateRomFS(impl->tree_romfs_dir);
   888   875 |         }
   889   876 |     });
   890   877 |     out_file = impl->tree_romfs;
   891   878 |     return out_file != nullptr ? ResultStatus::Success : ResultStatus::ErrorNoRomFS;
   892   879 | }
```

</details>

### P0-L05 · AppLoader_NX::ReadPatchedRomFS

La fonction peut être absente d'un fork ; l'absence est consignée au lieu d'inventer une parité. Encore/Lichii distinguent le RomFS patché du brut.

Encore : [nx.cpp:894–919](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L894-L919) — 26 lignes.

<details>
<summary>Lichii — 911–936 : 26 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:911–936](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L911-L936).

```diff
   894   911 | ResultStatus AppLoader_NX::ReadPatchedRomFS(FileSys::VirtualFile& out_file) {
   895   912 |     if (impl->status != ResultStatus::Success || impl->tree) {
   896   913 |         return ReadRomFS(out_file);
   897   914 |     }
   898   915 |     const auto package = impl->SnapshotPackage(impl->BaseOf(impl->selected));
   899   916 |     if (package == nullptr) {
   900   917 |         return ResultStatus::ErrorNSPMissingProgramNCA;
   901   918 |     }
   902   919 |     const FileSys::NSP nsp{package, impl->program_id};
   903   920 |     const auto base_nca = nsp.GetNCA(impl->program_id, FileSys::ContentRecordType::Program);
   904   921 |     if (base_nca == nullptr || base_nca->GetRomFS() == nullptr) {
   905   922 |         return ResultStatus::ErrorNoRomFS;
   906   923 |     }
   907   924 |     // The updates of the archive are found through the frontend provider, as when it runs.
   908   925 |     auto& system = *impl->system;
   909   926 |     if (const auto* slot = system.GetContentProviderUnion().GetSlotProvider(
   910   927 |             FileSys::ContentProviderUnionSlot::FrontendManual)) {
   911   928 |         RegisterContent(*const_cast<FileSys::ManualContentProvider*>(
   912   929 |             static_cast<const FileSys::ManualContentProvider*>(slot)));
   913   930 |     }
   914   931 |     const FileSys::PatchManager pm{impl->program_id, system.GetFileSystemController(),
   915   932 |                                    system.GetContentProvider()};
   916   933 |     out_file = pm.PatchRomFS(base_nca.get(), base_nca->GetRomFS(),
   917   934 |                              FileSys::ContentRecordType::Program, nullptr, false);
   918   935 |     return out_file != nullptr ? ResultStatus::Success : ResultStatus::ErrorNoRomFS;
   919   936 | }
```

</details>

EglantinePS5 : fonction absente ou non extraite au SHA examiné ; aucune parité supposée.

### P0-L06 · AppLoader_NX::ReadNSOModules

Comparer la liste et l'ordre des NSO réellement exposés. nxnative documente explicitement que l'absence d'un module attendu peut arrêter le boot ; ici on vérifie uniquement le loader Encore/forks.

Encore : [nx.cpp:1029–1035](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/465d7e9c82f364dcde05354d67ec1b5bf5e2682d/encore-active/ns2-runtime/nx/core/loader/nx.cpp#L1029-L1035) — 7 lignes.

<details>
<summary>Lichii — 1046–1052 : 7 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:1046–1052](https://github.com/zortos293/Lichii/blob/0288882f36692a94b56fa85177abdad0ec8be59d/src/core/loader/nx.cpp#L1046-L1052).

```diff
  1029  1046 | ResultStatus AppLoader_NX::ReadNSOModules(Modules& modules) {
  1030  1047 |     if (impl->status != ResultStatus::Success) {
  1031  1048 |         return impl->status;
  1032  1049 |     }
  1033  1050 |     return impl->tree ? impl->tree_executable->ReadNSOModules(modules)
  1034  1051 |                       : impl->native->ReadNSOModules(modules);
  1035  1052 | }
```

</details>

<details>
<summary>EglantinePS5 — 974–980 : 7 alignées, 0 propres Encore, 0 propres upstream</summary>

Source : [nx.cpp:974–980](https://github.com/heydemoura/EglantinePS5/blob/75a552ff945521eb31adf34f34ccb73a003809dc/Eglantine/src/core/loader/nx.cpp#L974-L980).

```diff
  1029   974 | ResultStatus AppLoader_NX::ReadNSOModules(Modules& modules) {
  1030   975 |     if (impl->status != ResultStatus::Success) {
  1031   976 |         return impl->status;
  1032   977 |     }
  1033   978 |     return impl->tree ? impl->tree_executable->ReadNSOModules(modules)
  1034   979 |                       : impl->native->ReadNSOModules(modules);
  1035   980 | }
```

</details>

### Lecture de cette annexe

- **VI2 229** est volontairement comparé comme homologue comportemental : Encore l'appelle `Present`, les forks `PresentClientBuffer`. La divergence de code est massive parce qu'Encore passe par le vrai nvnflinger/NVMap tandis que les forks portent aussi pacing/trace desktop. Le critère PS5 reste : image propriétaire valide → QueueBuffer accepté → fence/release → frame visible.
- **Loader NX** est beaucoup plus proche entre Encore et Lichii/Eglantine. Les petites différences doivent donc être examinées avec plus de poids que les gros écarts purement hôte de VI2.
- L'absence d'une fonction dans un fork n'est pas assimilée à un bug Encore.

**Couverture ajoutée :** 10 fonctions, 19 comparaisons, 1274 lignes-source parcourues (répétitions incluses), 1 homologue(s) absent(s)/non extrait(s). Aucun résultat console ni statut « résolu » n'est changé.
