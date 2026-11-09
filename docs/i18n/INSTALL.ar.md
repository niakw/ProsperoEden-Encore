# Eden Encore — التثبيت والتحديث · العربية

[نظرة عامة](README.ar.md) · [التثبيت والتحديث](INSTALL.ar.md) · [الإعدادات](SETTINGS.ar.md) · [حل المشكلات](TROUBLESHOOTING.ar.md) · [الدعم](SUPPORT.ar.md) · [إمكانية الوصول](ACCESSIBILITY.ar.md) · [Languages](../../LANGUAGES.md)

نزّل آخر حزمة منشورة بالفعل من صفحة الإصدارات، ثم احتفظ بنسخة احتياطية من التطبيق والبيانات. في تثبيت ZIP/FTP انسخ مجلد PPSA99008 كاملاً إلى /data/homebrew/PPSA99008/. لا تخلط هذه الطريقة مع FFPFSC/ShadowMountPlus، وتحقق من بصمة SHA-256 عند توفيرها.

## ZIP / FTP

```text
/data/homebrew/PPSA99008/      (application: eboot.bin, sce_sys, ui/lang)
/data/prosperoeden/            (persistent personal data)
/data/prosperoeden/roms/      (games)
/data/prosperoeden/updates/   (updates)
/data/prosperoeden/firmware/  (owned compatible firmware)
/data/prosperoeden/keys/      (user-provided keys)
```

لا تحذف /data/prosperoeden/؛ فقد يحتوي إعداداتك وملفات الحفظ والمفاتيح. احتفظ بنسخة من بيانات التخزين الخارجي أيضاً.

**FFPFSC / ShadowMountPlus:** follow the [separate image-based method](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), not a mixed ZIP/FTP installation. `PPSA99008` is the same application ID as the original native project; back up before replacing.

## حل المشكلات

إذا لم يبدأ التطبيق، تحقق من وجود eboot.bin وsce_sys وui/lang في المجلد الصحيح. إذا اختفت الألعاب، تحقق من مجلد roms تحت جذر التخزين المحدد. إذا بقيت اللغة الإنجليزية، تحقق من ملفات الترجمة. استخدم التشغيل الآمن لإعادة ضبط إعدادات لعبة واحدة دون حذف الحفظ.

آخر إصدار PS5 مُجمّع علناً يعود إلى 15 أكتوبر 2026؛ إصدار 30 أكتوبر مجرد نسخة من الحزمة نفسها. لا تتضمن المسودة الجديدة ملفات تشغيل، ولم يُتحقق بعد من ألعاب الجيل الثاني على الجهاز.

[Authentic R1 FTP release — 15 October 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · [Detailed English installation](../../INSTALL.md)