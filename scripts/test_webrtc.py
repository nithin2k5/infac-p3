import time
from inference_sdk import InferenceHTTPClient
from inference_sdk.webrtc import WebcamSource, StreamConfig

client = InferenceHTTPClient.init(api_url="https://serverless.roboflow.com", api_key="INxX0Lc0epqPhQXpIWj9")
source = WebcamSource(resolution=(640, 480))
config = StreamConfig(stream_output=["output_image"], data_output=["predictions"])

try:
    print("Starting stream...")
    session = client.webrtc.stream(
        source=source,
        workflow="infacep4/2",
        workspace="infac",
        image_input="image",
        config=config
    )
    print("Session formed. Running...")
    
    @session.on_data()
    def handler(d, m):
        print(d)
        
    session.run()
except Exception as e:
    print("FAILED:", e)
