# Eden Encore — الإعدادات · العربية

[نظرة عامة](README.ar.md) · [التثبيت والتحديث](INSTALL.ar.md) · [الإعدادات](SETTINGS.ar.md) · [حل المشكلات](TROUBLESHOOTING.ar.md) · [الدعم](SUPPORT.ar.md) · [إمكانية الوصول](ACCESSIBILITY.ar.md) · [Languages](../../LANGUAGES.md)

تبدأ الإعدادات الموصى بها بمحرك Vulkan ودقة إخراج 1440p ومقياس لعب 1.25x وFSR 1 بحدة 50% وFXAA وتحديث 60 Hz. يختلف إخراج التلفاز عن دقة اللعبة الداخلية. لا تفترض أن تحسين الصورة أو توليد الإطارات يزيد سرعة محاكاة اللعبة.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** تبدأ الإعدادات الموصى بها بمحرك Vulkan ودقة إخراج 1440p ومقياس لعب 1.25x وFSR 1 بحدة 50% وFXAA وتحديث 60 Hz. يختلف إخراج التلفاز عن دقة اللعبة الداخلية. لا تفترض أن تحسين الصورة أو توليد الإطارات يزيد سرعة محاكاة اللعبة.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## إمكانية الوصول

تتيح الواجهة تكبير النص والتباين العالي وتقليل الحركة من إعدادات إمكانية الوصول، وهي خيارات منفصلة ومعطلة افتراضياً. يعتمد التنقل على التركيز المرئي ووحدة التحكم، ولا يعني ذلك دعم أدوات المساعدة داخل جميع الألعاب.

## حل المشكلات

إذا لم يبدأ التطبيق، تحقق من وجود eboot.bin وsce_sys وui/lang في المجلد الصحيح. إذا اختفت الألعاب، تحقق من مجلد roms تحت جذر التخزين المحدد. إذا بقيت اللغة الإنجليزية، تحقق من ملفات الترجمة. استخدم التشغيل الآمن لإعادة ضبط إعدادات لعبة واحدة دون حذف الحفظ.

لا تحذف /data/prosperoeden/؛ فقد يحتوي إعداداتك وملفات الحفظ والمفاتيح. احتفظ بنسخة من بيانات التخزين الخارجي أيضاً.

---

آخر إصدار PS5 مُجمّع علناً يعود إلى 15 أكتوبر 2026؛ إصدار 30 أكتوبر مجرد نسخة من الحزمة نفسها. لا تتضمن المسودة الجديدة ملفات تشغيل، ولم يُتحقق بعد من ألعاب الجيل الثاني على الجهاز.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)