#!/usr/bin/env python3
"""
Example script demonstrating batch video processing with RoboflowDetector

Usage:
    python example_video_processing.py path/to/your/video.mp4
"""

import sys
import os
from roboflow_detector import RoboflowDetector


def main():
    if len(sys.argv) != 2:
        print("Usage: python example_video_processing.py <video_path>")
        print("Example: python example_video_processing.py my_video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print("🎥 Roboflow Batch Video Processing Example")
    print("=" * 50)

    # Initialize detector
    detector = RoboflowDetector()

    # Check capabilities
    caps = detector.get_capabilities()
    print(f"\n📊 Detector Capabilities:")
    print(f"   Static Images: {'✅' if caps['static_images'] else '❌'}")
    print(f"   Real-time Streaming: {'✅' if caps['real_time_streaming'] else '❌'}")
    print(f"   Batch Video Processing: {'✅' if caps['batch_video_processing'] else '❌'}")

    if not caps['batch_video_processing']:
        print("\n❌ Batch video processing is not available.")
        print("   Install roboflow package: pip install roboflow")
        sys.exit(1)

    try:
        print(f"\n🎬 Processing video: {os.path.basename(video_path)}")
        print(f"   Size: {os.path.getsize(video_path) / (1024*1024):.1f} MB")

        # Process video (this will submit and wait for results)
        results = detector.process_video_batch(video_path, fps=5, timeout=600)

        # Display results
        print("\n✅ Processing completed successfully!")
        print(f"   Status: {results.get('status', 'Unknown')}")
        print(f"   Frames processed: {len(results.get('predictions', []))}")

        # Show some predictions if available
        predictions = results.get('predictions', [])
        if predictions:
            print(f"\n📈 Sample predictions:")
            for i, frame_pred in enumerate(predictions[:3]):  # Show first 3 frames
                frame_num = frame_pred.get('frame_number', i+1)
                detections = frame_pred.get('detections', [])
                print(f"   Frame {frame_num}: {len(detections)} detection(s)")

                # Show first detection details
                if detections:
                    det = detections[0]
                    bbox = det.get('bounding_box', {})
                    print(f"      └─ Class: {det.get('class', 'Unknown')}")
                    print(f"         Confidence: {det.get('confidence', 0):.1f}%")
                    print(f"         Position: ({bbox.get('x', 0)}, {bbox.get('y', 0)})")

        print(f"\n📋 Full results saved to: results_{os.path.basename(video_path)}.json")

        # Optionally save full results
        import json
        output_file = f"results_{os.path.splitext(os.path.basename(video_path))[0]}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()