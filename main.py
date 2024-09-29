import os

# Apply symlink patch
import symlink_patch

import base64
from DepthFlow import DepthScene
from ShaderFlow.Message import ShaderMessage
from DepthFlow.Motion import Components, Presets, Target

# Additional imports for Inferless
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

FPS = 30
DURATION = 6
WIDTH = 1152
HEIGHT = 648
SSAA = 2
QUALITY = 100

class CustomScene(DepthScene):
    def setup(self):
        super().setup()

        # Add animations
        self.add_animation(Presets.Orbital(depth=0.5, intensity=0.5))
        self.add_animation(Presets.Dolly())
        self.add_animation(Components.Sine(target=Target.OffsetY, amplitude=0.1, cycles=2))
        self.add_animation(Components.Linear(
            target=Target.Zoom,
            start=0, end=1,
            low=1, high=1.15
        ))

    def update(self):
        self.animate()  # This will apply all the animations we added

    def handle(self, message: ShaderMessage):
        super().handle(message)

class InferRequest(BaseModel):
    image: str
    depth: str

app = FastAPI()

def process_scene(image_bytes, depth_bytes):
    model = CustomScene(backend='headless')
    model.input(image=image_bytes, depth=depth_bytes)
    output_path = "/tmp/output.mp4"
    model.main(output=output_path, fps=FPS, time=DURATION, ssaa=SSAA, quality=QUALITY, height=HEIGHT, width=WIDTH)
    return output_path

@app.get("/v2")
@app.get("/v2/models/motion-forge")
def version():
    return {"name": "motion-forge"}

@app.get("/v2/health/live")
@app.get("/v2/health/ready")
@app.get("/v2/models/motion-forge/ready")
def health():
    return {"status": "running"}

@app.post("/v2/models/motion-forge/infer")
def infer(request: InferRequest):
    try:
        image_bytes = base64.b64decode(request.image)
        depth_bytes = base64.b64decode(request.depth)

        output_path = process_scene(image_bytes, depth_bytes)

        # Read the output video file
        with open(output_path, "rb") as video_file:
            video_bytes = video_file.read()

        # Encode video to base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        # Clean up the temporary file
        os.remove(output_path)

        return {
            "message": "Processing complete",
            "video": video_base64,
            "fps": FPS,
            "duration": DURATION,
            "width": WIDTH,
            "height": HEIGHT,
            "ssaa": SSAA,
            "quality": QUALITY
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)