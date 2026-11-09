# Eden Encore — حل المشكلات · العربية

[نظرة عامة](README.ar.md) · [التثبيت والتحديث](INSTALL.ar.md) · [الإعدادات](SETTINGS.ar.md) · [حل المشكلات](TROUBLESHOOTING.ar.md) · [الدعم](SUPPORT.ar.md) · [إمكانية الوصول](ACCESSIBILITY.ar.md) · [Languages](../../LANGUAGES.md)

إذا لم يبدأ التطبيق، تحقق من وجود eboot.bin وsce_sys وui/lang في المجلد الصحيح. إذا اختفت الألعاب، تحقق من مجلد roms تحت جذر التخزين المحدد. إذا بقيت اللغة الإنجليزية، تحقق من ملفات الترجمة. استخدم التشغيل الآمن لإعادة ضبط إعدادات لعبة واحدة دون حذف الحفظ.

## التثبيت والتحديث

نزّل آخر حزمة منشورة بالفعل من صفحة الإصدارات، ثم احتفظ بنسخة احتياطية من التطبيق والبيانات. في تثبيت ZIP/FTP انسخ مجلد PPSA99008 كاملاً إلى /data/homebrew/PPSA99008/. لا تخلط هذه الطريقة مع FFPFSC/ShadowMountPlus، وتحقق من بصمة SHA-256 عند توفيرها.

```text
/data/homebrew/PPSA99008/   application / eboot.bin / sce_sys / ui/lang
/data/prosperoeden/         settings / saves / keys / firmware / roms
```

## الإعدادات

تبدأ الإعدادات الموصى بها بمحرك Vulkan ودقة إخراج 1440p ومقياس لعب 1.25x وFSR 1 بحدة 50% وFXAA وتحديث 60 Hz. يختلف إخراج التلفاز عن دقة اللعبة الداخلية. لا تفترض أن تحسين الصورة أو توليد الإطارات يزيد سرعة محاكاة اللعبة.

## الدعم

عند الإبلاغ عن مشكلة، أرفق رقم إصدار Encore ونسخة النظام والخطوات اللازمة لإعادة المشكلة والإعدادات والسجلات المنقحة. استخدم صفحة Issues الرسمية ولا تنشر مفاتيح أو ملفات حفظ أو بيانات شخصية.

**Safe Launch** resets problematic game-specific settings only; do not erase saves to diagnose a launch issue.

لا تحذف /data/prosperoeden/؛ فقد يحتوي إعداداتك وملفات الحفظ والمفاتيح. احتفظ بنسخة من بيانات التخزين الخارجي أيضاً.

---

آخر إصدار PS5 مُجمّع علناً يعود إلى 15 أكتوبر 2026؛ إصدار 30 أكتوبر مجرد نسخة من الحزمة نفسها. لا تتضمن المسودة الجديدة ملفات تشغيل، ولم يُتحقق بعد من ألعاب الجيل الثاني على الجهاز.

[Detailed English troubleshooting](../../TROUBLESHOOTING.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)