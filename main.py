import os

# Apply symlink patch
import symlink_patch

import base64
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from DepthFlow import DepthScene
from ShaderFlow.Message import ShaderMessage
from DepthFlow.Motion import Components, Presets, Target

# Additional imports for Inferless
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class CustomScene(DepthScene):
    def setup(self):
        super().setup()
        logger.info("Setting up CustomScene")
        # Add animations
        self.add_animation(Presets.Orbital(depth=0.5, intensity=0.5))
        self.add_animation(Presets.Dolly())
        self.add_animation(Components.Sine(target=Target.OffsetY, amplitude=0.1, cycles=2))
        self.add_animation(Components.Linear(
            target=Target.Zoom,
            start=0, end=1,
            low=1, high=1.15
        ))
        logger.info("Animations added to CustomScene")

    def update(self):
        self.animate()
        logger.debug("CustomScene updated")

    def handle(self, message: ShaderMessage):
        super().handle(message)
        logger.debug(f"Handled ShaderMessage: {message}")

class InferRequest(BaseModel):
    image: str
    depth: str

app = FastAPI()

def process_scene(image_bytes, depth_bytes):
    logger.info("Starting scene processing")
    model = CustomScene(backend='headless')
    logger.info("CustomScene model created")
    model.input(image=image_bytes, depth=depth_bytes)
    logger.info("Input provided to the model")
    output_path = "/tmp/output.mp4"
    logger.info(f"Processing scene. Output path: {output_path}")
    model.main(output=output_path, fps=12, time=5, ssaa=1, quality=0, height=640, width=360)
    logger.info("Scene processing completed")
    return output_path

@app.get("/v2")
@app.get("/v2/models/depth-flow-model")
def version():
    logger.info("Version endpoint called")
    return {"name": "depth-flow-model"}

@app.get("/v2/health/live")
@app.get("/v2/health/ready")
@app.get("/v2/models/depth-flow-model/ready")
def health():
    logger.info("Health check endpoint called")
    return {"status": "running"}

@app.post("/v2/models/depth-flow-model/infer")
def infer(request: InferRequest):
    logger.info("Inference request received")
    try:
        image_bytes = base64.b64decode(request.image)
        depth_bytes = base64.b64decode(request.depth)
        logger.info("Input images decoded from base64")

        output_path = process_scene(image_bytes, depth_bytes)

        logger.info("Reading output video file")
        with open(output_path, "rb") as video_file:
            video_bytes = video_file.read()

        logger.info("Encoding video to base64")
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        logger.info("Cleaning up temporary file")
        os.remove(output_path)

        logger.info("Inference completed successfully")
        return {
            "message": "Processing complete",
            "video": video_base64,
            "fps": 12,
            "duration": 5,
            "width": 360,
            "height": 640
        }
    except Exception as e:
        logger.error(f"Error during inference: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=8080)