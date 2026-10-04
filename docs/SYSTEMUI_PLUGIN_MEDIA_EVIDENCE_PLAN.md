# Remaining SystemUIPlugin media XML evidence

Codex proved the media plugin class topology from DEX, but the actual resource
XML for `media_card_section` and related page roots was not present in the hard
input package.

The compact ColorOS 17 resource table resolves the current obfuscated resource
paths as:

- `layout/media_card_page_root -> res/Jc.xml`
- `layout/media_card_section -> res/OG.xml`
- `layout/media_immersive_bg_fullscreen -> res/di.xml`
- `layout/media_immersive_card_section -> res/jK.xml`
- `layout/media_mini_card_section -> res/wN.xml`
- `layout/media_multi_card_section -> res/Dy.xml`
- `layout/immersive_bg_page_root -> res/8o.xml`
- `layout/immersive_card_page_root -> res/lV.xml`
- `layout/mini_card_page_root -> res/Ww.xml`
- `layout/multi_page_root -> res/Mq.xml`
- `layout/normal_card_media_player_lyric_item -> res/9_.xml`
- `layout/page_bg -> res/60.xml`

These paths are build-specific and are **not** treated as stable API.

`scripts/ColorOS17_SystemUIPlugin_MediaEvidence_v1.sh` extracts only those
binary XML blobs plus `resources.arsc` and `AndroidManifest.xml` from the
user's live SystemUIPlugin APK. It does not upload/copy the full plugin APK.

After that evidence is decoded off-device, the media release gate can be
reduced from `NEEDS_RESOURCE_XML + NEEDS_RUNTIME_TRACE` to runtime-only if the
layout confirms the expected binder/root topology.
