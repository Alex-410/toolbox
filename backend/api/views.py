from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


CAMERA_TOOLS = [
    {
        "id": "brightness",
        "name": "Brightness Adjustment",
        "description": "Adjust image brightness level",
        "type": "color",
    },
    {
        "id": "contrast",
        "name": "Contrast Adjustment",
        "description": "Adjust image contrast level",
        "type": "color",
    },
    {
        "id": "saturation",
        "name": "Saturation Adjustment",
        "description": "Adjust image color saturation",
        "type": "color",
    },
    {
        "id": "sharpness",
        "name": "Sharpness Enhancement",
        "description": "Enhance image sharpness and detail",
        "type": "filter",
    },
    {
        "id": "blur",
        "name": "Blur Effect",
        "description": "Apply Gaussian blur to image",
        "type": "filter",
    },
    {
        "id": "edge_detection",
        "name": "Edge Detection",
        "description": "Detect edges using Canny algorithm",
        "type": "detection",
    },
    {
        "id": "noise_reduction",
        "name": "Noise Reduction",
        "description": "Reduce image noise and grain",
        "type": "filter",
    },
    {
        "id": "grayscale",
        "name": "Grayscale Conversion",
        "description": "Convert image to grayscale",
        "type": "color",
    },
]


@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"})


@api_view(['GET'])
def tools_list(request):
    return Response({"tools": CAMERA_TOOLS})


@api_view(['POST'])
def process_image(request):
    tool_id = request.data.get("tool_id")
    image = request.data.get("image")

    if not tool_id:
        return Response(
            {"error": "tool_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_ids = [tool["id"] for tool in CAMERA_TOOLS]
    if tool_id not in valid_ids:
        return Response(
            {"error": f"Unknown tool_id: {tool_id}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "tool_id": tool_id,
            "status": "pending",
            "message": "Processing not yet implemented",
        },
        status=status.HTTP_202_ACCEPTED,
    )
