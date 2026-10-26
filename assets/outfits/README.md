# High-resolution wardrobe portraits

Each selectable outfit uses its own 1024 × 1536 portrait instead of stretching a 232–303px crop from a contact sheet. These are AI-restored illustrations based on the existing wardrobe sheets, not recovered original source files; fine details may differ.

Generated with the built-in image generation tool. Source references: `../wardrobe-everyday.webp` (kimono, casual, winter, traditional) and `../wardrobe-fashion.webp` (the ten fashion styles). The original room image remains separate.

Prompt template used once per outfit:

> Use case: identity-preserve. Technical restoration of ONLY the existing panel [outfit name and row/column] from the supplied atlas. Output ONE isolated full portrait panel, 1024x1536 pixels, filling the frame with this SAME existing illustration and scene, excluding the atlas borders, other panels, labels and icons. Maintain the character identity, face, exact existing clothing, pose, body proportions, background and scene. Faithfully restore soft small linework into crisp high-resolution anime artwork for a phone-screen wallpaper. Do not create a grid. No text. No redesign, no changes to costume, body or skin exposure, no extra people or objects. This is an image-quality restoration of the single specified panel.

Assets are encoded as WebP for mobile download size. The app loads full portraits directly, uses lazy image previews, and caches visited images through the service worker. It no longer crops or recompresses the selected art in a browser canvas.
