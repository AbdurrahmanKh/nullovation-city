# Setting up an image service

Read this only when the user asks how to set up a service, what size to use, or how to animate. The concepts and prompts never repeat it.

## What the city needs from the file

- 256 px wide, the width of a plot at the city's detail. The height is whatever the building needs.
- A transparent background.
- The plot is part of the art: its surface is a flat diamond twice as wide as it is tall, spanning nearly the full image width (x 5 to 250 of 256, outline included), with its front corner at the bottom edge, centered. Draw the surface and everything on it; the city draws nothing under it.
- No empty margins; the canvas ends where the art ends.
- A PNG for a still building, a GIF for an animated one.
- Colors from the city palette. In the tool, Tools in the side bar has Download palette, which saves the palette as a PNG for services that accept a forced palette.

## PixelLab

- Put the subject-only prompt in the description. Style lives in its settings: outline, shading, and detail, with a transparent background. A dark single-color outline and a high level of detail suit the city.
- Size: Pro Flash accepts custom sizes in 4 px steps up to 256 px, in beta. Bitforge's largest area is 200 by 200, too small for a 256 px wide building.
- Animation: the animation tools take the finished still as the start frame and the animation prompt as the motion description; the frame count is a setting. Animate with text v3 makes up to 16 frames. Animate with text (Pro) gives 4 frames at 171 to 256 px. PixMiniMax, in beta, makes 4 to 40 frames at up to 256 px.
- For a closer match across buildings, an approved building can be set as a style reference, though the prompts aim to work without one.

## Any other service

Use the full prompt. If the service has settings for size, background, or palette, set them as above; if not, the full prompt already asks for isometric 2:1 pixel art with a 1 px dark outline on a transparent background.

Service features change often; if a detail here seems out of date, say so and check the service's own documentation.
